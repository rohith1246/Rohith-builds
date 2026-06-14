import os
import re
import time
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from threading import Thread
from flask import current_app
from models import db, UserAgentConfig, AgentJobOpportunity, AgentApplicationLog, User, Job
from groq import Groq

# Global dictionary to track agent status: user_id -> string status
AGENT_STATUSES = {}
AGENT_RESTART_REQUESTED = {}

def update_status(user_id, status):
    if user_id is not None:
        AGENT_STATUSES[user_id] = status

# Groq API Caller with Rate Limit (429) and general exception Fallback Sequence
def call_groq_with_fallback(client, messages):
    models = [
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "qwen/qwen3-32b",
        "llama-3.1-8b-instant",
        "groq/compound-mini"
    ]
    last_exception = None
    for i, model in enumerate(models):
        try:
            print(f"Attempting match evaluation using Groq model: {model}...")
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model,
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return chat_completion
        except Exception as e:
            last_exception = e
            err_msg = str(e).lower()
            if "429" in err_msg or "rate_limit" in err_msg or "limit reached" in err_msg or "overloaded" in err_msg:
                print(f"Model {model} hit rate limit or overloaded. Trying fallback model...")
            else:
                print(f"Model {model} failed with exception: {e}. Trying fallback model...")
                
    if last_exception:
        raise last_exception

# Helper to clean HTML description tags
def clean_html(html_text):
    if not html_text:
        return ""
    # Remove script and style elements
    html_text = re.sub(r'<script[^>]*>([\s\S]*?)</script>', '', html_text)
    html_text = re.sub(r'<style[^>]*>([\s\S]*?)</style>', '', html_text)
    # Remove HTML tags
    text = re.sub(r'<[^>]*>', ' ', html_text)
    # Replace multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# RSS Crawlers
def crawl_weworkremotely():
    jobs = []
    url = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                desc_elem = item.find('description')
                link_elem = item.find('link')
                
                title = title_elem.text if title_elem is not None else ""
                desc_html = desc_elem.text if desc_elem is not None else ""
                apply_url = link_elem.text if link_elem is not None else ""
                
                # Split company and title from WeWorkRemotely title (e.g. "Company: Title")
                company = "WeWorkRemotely Hiring"
                job_title = title
                if ":" in title:
                    parts = title.split(":", 1)
                    company = parts[0].strip()
                    job_title = parts[1].strip()
                
                description = clean_html(desc_html)
                
                # Extract email using regex
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', description)
                recruiter_email = emails[0] if emails else f"careers@{company.lower().replace(' ', '')}.com"
                
                jobs.append({
                    "title": job_title,
                    "company": company,
                    "location": "Remote",
                    "description": description[:4000],
                    "apply_url": apply_url,
                    "recruiter_email": recruiter_email,
                    "source": "WeWorkRemotely"
                })
    except Exception as e:
        print(f"Error crawling WeWorkRemotely: {e}")
    return jobs

# Greenhouse Crawlers
def crawl_greenhouse_board(board):
    jobs = []
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for j in data.get("jobs", []):
                title = j.get("title")
                apply_url = j.get("absolute_url")
                location = j.get("location", {}).get("name", "Remote")
                content = clean_html(j.get("content", ""))
                
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                recruiter_email = emails[0] if emails else f"careers@{board}.com"
                
                jobs.append({
                    "title": title,
                    "company": board.capitalize(),
                    "location": location,
                    "description": content[:4000],
                    "apply_url": apply_url,
                    "recruiter_email": recruiter_email,
                    "source": f"Greenhouse ({board})"
                })
    except Exception as e:
        print(f"Error crawling Greenhouse board {board}: {e}")
    return jobs

# Lever Crawlers
def crawl_lever_company(company):
    jobs = []
    url = f"https://api.lever.co/v0/postings/{company}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for j in data:
                title = j.get("text")
                apply_url = j.get("hostedUrl") or j.get("applyUrl")
                location = j.get("categories", {}).get("location", "Remote")
                description = clean_html(j.get("description", "") + " " + j.get("lists", [{}])[0].get("content", ""))
                
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', description)
                recruiter_email = emails[0] if emails else f"careers@{company}.com"
                
                jobs.append({
                    "title": title,
                    "company": company.capitalize(),
                    "location": location,
                    "description": description[:4000],
                    "apply_url": apply_url,
                    "recruiter_email": recruiter_email,
                    "source": f"Lever ({company})"
                })
    except Exception as e:
        print(f"Error crawling Lever company {company}: {e}")
    return jobs

# Sync curated jobs from local Placement Portal into Agent opportunities pool
def sync_curated_jobs():
    try:
        # Delete any opportunities that are not from "Placement Portal"
        deleted_count = AgentJobOpportunity.query.filter(AgentJobOpportunity.source != "Placement Portal").delete(synchronize_session=False)
        db.session.commit()
        if deleted_count > 0:
            print(f"Cleaned up {deleted_count} external job opportunities from Agent pool.")

        curated_jobs = Job.query.filter_by(is_active=True).all()
        existing_urls = set(r[0] for r in db.session.query(AgentJobOpportunity.apply_url).all())
        
        new_jobs_count = 0
        for j in curated_jobs:
            if not j.apply_url:
                continue
            if j.apply_url not in existing_urls:
                emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', j.description or "")
                recruiter_email = emails[0] if emails else f"careers@{j.company.lower().replace(' ', '')}.com"
                
                opp = AgentJobOpportunity(
                    title=j.title,
                    company=j.company,
                    location=j.location,
                    description=j.description,
                    apply_url=j.apply_url,
                    recruiter_email=recruiter_email,
                    source="Placement Portal"
                )
                db.session.add(opp)
                existing_urls.add(j.apply_url)
                new_jobs_count += 1
                
        db.session.commit()
        print(f"Synced {new_jobs_count} curated jobs from Placement Portal.")
    except Exception as e:
        print(f"Error syncing curated jobs: {e}")

# Run crawler to find new job opportunities (only syncs curated jobs in database-only architecture)
def crawl_and_save_opportunities(user_id=None):
    # Sync curated jobs from local Placement Portal
    update_status(user_id, "Syncing curated jobs from database...")
    sync_curated_jobs()
    return 0


# Pre-filter helper
def pre_filter_job(title, location, config):
    if not config.target_roles:
        roles_match = True
    else:
        roles = [r.strip().lower() for r in config.target_roles.split(",") if r.strip()]
        # Expand role synonyms
        roles_expanded = []
        for role in roles:
            roles_expanded.append(role)
            if "developer" in role:
                roles_expanded.append(role.replace("developer", "engineer"))
            if "engineer" in role:
                roles_expanded.append(role.replace("engineer", "developer"))
            if "fullstack" in role:
                roles_expanded.append(role.replace("fullstack", "full-stack"))
                roles_expanded.append(role.replace("fullstack", "full stack"))
            if "full-stack" in role:
                roles_expanded.append(role.replace("full-stack", "fullstack"))
                roles_expanded.append(role.replace("full-stack", "full stack"))
        
        roles_match = any(role in title.lower() for role in roles_expanded)
        
    if not roles_match:
        return False
        
    if not config.target_locations:
        locations_match = True
    else:
        locs = [l.strip().lower() for l in config.target_locations.split(",") if l.strip()]
        # Expand location aliases
        locs_expanded = []
        for loc in locs:
            locs_expanded.append(loc)
            if loc in ["banglore", "bangalore", "bengaluru"]:
                locs_expanded.extend(["banglore", "bangalore", "bengaluru"])
                
        locations_match = False
        for loc in locs_expanded:
            if loc in location.lower():
                locations_match = True
                break
            if loc == "remote" and "remote" in location.lower():
                locations_match = True
                break
            if loc == "remote" and "distributed" in location.lower():
                locations_match = True
                break
                
    return locations_match

# Core matching logic using Groq LLM
def match_user_with_jobs(user_id):
    user = User.query.get(user_id)
    if not user:
        return 0
        
    config = UserAgentConfig.query.filter_by(user_id=user_id).first()
    if not config or not config.is_active or not config.resume_text:
        return 0
        
    # Get Groq client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("GROQ_API_KEY is not set. Cannot run match worker.")
        return 0
    client = Groq(api_key=api_key)
    
    # Subquery for evaluated job ids to exclude them
    evaluated_ids_subquery = db.session.query(AgentApplicationLog.job_opportunity_id).filter_by(user_id=user_id)
    
    # Fetch all job opportunities that haven't been evaluated yet (only from Placement Portal)
    all_opps = (AgentJobOpportunity.query
                .filter(~AgentJobOpportunity.id.in_(evaluated_ids_subquery))
                .filter(AgentJobOpportunity.source == "Placement Portal")
                .all())
                
    # Tokenize the resume text to lowercase alphanumeric words for fast lookup
    resume_words = set(re.findall(r'[a-zA-Z0-9]+', (config.resume_text or "").lower()))
    
    # Calculate relevance score for each job based on keyword overlap
    scored_opportunities = []
    for job in all_opps:
        score = 0
        # Title matches (higher weight)
        title_words = re.findall(r'[a-zA-Z0-9]+', (job.title or "").lower())
        for w in title_words:
            if w in resume_words:
                score += 10
        # Description/skills match (1 point per matching word)
        desc_words = re.findall(r'[a-zA-Z0-9]+', (job.description or "").lower())
        matched_words = resume_words.intersection(desc_words)
        score += len(matched_words)
        
        scored_opportunities.append((score, job))
        
    # Sort by relevance score descending and take the top 15 most relevant
    scored_opportunities.sort(key=lambda x: x[0], reverse=True)
    opportunities = [job for score, job in scored_opportunities[:15]]
                     
    matches_processed = 0
    total_opps = len(opportunities)
    
    if total_opps == 0:
        update_status(user_id, "No new jobs to evaluate.")
        time.sleep(1)
        return 0
    
    for idx, job in enumerate(opportunities):
        # Check for abort/restart request
        if AGENT_RESTART_REQUESTED.get(user_id):
            print(f"Abort matching requested for user_id={user_id}")
            break

        # Update progress status
        update_status(user_id, f"Evaluating match {idx + 1}/{total_opps} against resume: {job.title} at {job.company}...")
            
        # Match using Groq Llama 3
        system_prompt = """
You are a career matching AI agent. Your job is to evaluate if a candidate's resume matches a job opportunity, and if so, draft a high-converting personalized cold email pitch.

You must respond with a JSON object. The JSON object MUST contain:
1. "fit_score": an integer between 0 and 100 indicating how well the candidate's skills, experience, and projects match the job requirements.
2. "explanation": a 2-3 sentence explanation of why this fit score was given, highlighting matching skills or gaps.
3. "subject": a professional email subject line for applying (e.g. "Application for Backend Developer - [Candidate Name]").
4. "pitch_body": a highly personalized, compelling cold email pitch body to the recruiter. 

Guidelines for the pitch_body:
- Write in the first person ("I") from the candidate's perspective.
- Make it highly specific, referencing the candidate's actual projects, skills, and experience from their resume, and mapping them directly to the job requirements.
- Keep it concise, friendly, and professional.
- Structure it with clean paragraph breaks (double newlines \n\n) between:
  1. The greeting (e.g., "Hi Hiring Team at [Company Name],")
  2. The introduction & matching experience
  3. The specific project/skill alignment
  4. The call to action (short chat/review request)
  5. The sign-off (e.g., "Best regards,\n[Candidate Name]")
- Ensure all placeholders like [Candidate Name] are pre-filled using the candidate's name if found in the resume, or fallback to the candidate's name.

Respond ONLY with the raw JSON object. Do not include markdown code block formatting (like ```json) or any conversational text.
"""

        user_prompt = f"""
Candidate Resume:
{config.resume_text}

Job Posting:
Title: {job.title}
Company: {job.company}
Location: {job.location}
Description:
{job.description}
"""

        try:
            # Groq API call with fallback sequence
            chat_completion = call_groq_with_fallback(
                client,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            content = chat_completion.choices[0].message.content.strip()
            
            # Clean markdown codeblocks if they exist
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n', '', content)
                content = re.sub(r'\n```$', '', content)
                
            res_data = json.loads(content)
            
            fit_score = int(res_data.get("fit_score", 0))
            explanation = res_data.get("explanation", "")
            subject = res_data.get("subject", f"Application for {job.title} - {user.username}")
            pitch_body = res_data.get("pitch_body", "")
            
            # Save the match evaluation
            log = AgentApplicationLog(
                user_id=user_id,
                job_opportunity_id=job.id,
                fit_score=fit_score,
                match_explanation=explanation,
                drafted_subject=subject,
                drafted_body=pitch_body,
                status="Matched" if fit_score >= 50 else "Skipped"
            )
            db.session.add(log)
            db.session.commit()
            
            matches_processed += 1
            
            # Sleep to comply with Groq free-tier rate limits
            time.sleep(3)
            
        except Exception as e:
            print(f"Error matching job {job.id} for user {user_id}: {e}")
            db.session.rollback()
            time.sleep(5)  # Sleep longer on error/rate-limit
            
    db.session.commit() # Save all skipped logs
    return matches_processed

# Full pipeline wrapper to run in background thread
def run_job_agent_pipeline_async(app, user_id):
    # Prevent duplicate thread executions for the same user, request restart if running
    status = AGENT_STATUSES.get(user_id, "Idle")
    if status != "Idle":
        print(f"Pipeline already running for user_id={user_id}. Requesting restart...")
        AGENT_RESTART_REQUESTED[user_id] = True
        return None

    def job():
        with app.app_context():
            while True:
                # Clear the restart request flag at start of run
                AGENT_RESTART_REQUESTED[user_id] = False
                
                db.session.remove() # Clean up session in thread
                print(f"Starting async job agent pipeline for user_id={user_id}...")
                try:
                    update_status(user_id, "Starting agent pipeline...")
                    # 1. Crawl new jobs
                    crawl_and_save_opportunities(user_id)
                    
                    if AGENT_RESTART_REQUESTED.get(user_id):
                        print(f"Restart requested during crawling for user_id={user_id}. Restarting...")
                        AgentApplicationLog.query.filter_by(user_id=user_id).delete()
                        db.session.commit()
                        continue
                        
                    # 2. Match with user
                    match_user_with_jobs(user_id)
                    
                    if AGENT_RESTART_REQUESTED.get(user_id):
                        print(f"Restart requested during matching for user_id={user_id}. Restarting...")
                        AgentApplicationLog.query.filter_by(user_id=user_id).delete()
                        db.session.commit()
                        continue
                        
                except Exception as e:
                    print(f"Error in job agent pipeline: {e}")
                    db.session.rollback()
                finally:
                    db.session.commit()
                    db.session.remove() # Release DB connection back to pool
                
                if not AGENT_RESTART_REQUESTED.get(user_id):
                    break
            
            update_status(user_id, "Idle")
            print(f"Finished async job agent pipeline for user_id={user_id}")
            
    thread = Thread(target=job)
    thread.daemon = True
    thread.start()
    return thread
