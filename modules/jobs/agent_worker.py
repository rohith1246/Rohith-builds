import json
import logging
import os
import re
from threading import Thread
import time
from typing import Any
import xml.etree.ElementTree as ET

from flask import Flask
from groq import Groq
import requests

from models import AgentApplicationLog, AgentJobOpportunity, db, Job, User, UserAgentConfig

# Global dictionary to track agent status: user_id -> string status
AGENT_STATUSES = {}
AGENT_RESTART_REQUESTED = {}

def update_status(user_id: int | None, status: str) -> None:
    """Update the background status of the agent for a user."""
    if user_id is not None:
        AGENT_STATUSES[user_id] = status


def call_groq_with_fallback(client: Groq, messages: list[dict[str, str]]) -> Any:
    """Call Groq API using a sequence of fallback models to bypass rate limits."""
    models: list[str] = [
        "llama-3.3-70b-versatile",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
    ]
    last_exception: Exception | None = None
    for i, model in enumerate(models):
        try:
            logging.info(f"Attempting match evaluation using Groq model: {model}...")
            chat_completion = client.chat.completions.create(
                messages=messages,  # type: ignore
                model=model,
                response_format={"type": "json_object"},
                temperature=0.3
            )
            return chat_completion
        except Exception as e:
            last_exception = e
            err_msg: str = str(e).lower()
            if "429" in err_msg or "rate_limit" in err_msg or "limit reached" in err_msg or "overloaded" in err_msg:
                logging.info(f"Model {model} hit rate limit or overloaded. Trying fallback model...")
            else:
                logging.info(f"Model {model} failed with exception: {e}. Trying fallback model...")
                
    if last_exception:
        raise last_exception

# Helper to clean HTML description tags
def clean_html(html_text: str | None) -> str:
    """Remove HTML tags and clean formatting from text descriptions."""
    if not html_text:
        return ""
    # Remove script and style elements
    html_text = re.sub(r'<script[^>]*>([\s\S]*?)</script>', '', html_text)
    html_text = re.sub(r'<style[^>]*>([\s\S]*?)</style>', '', html_text)
    # Remove HTML tags
    text: str = re.sub(r'<[^>]*>', ' ', html_text)
    # Replace multiple spaces/newlines
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# RSS Crawlers
def crawl_weworkremotely() -> list[dict[str, str]]:
    """Crawl programming job listings from WeWorkRemotely RSS feed."""
    jobs: list[dict[str, str]] = []
    url: str = "https://weworkremotely.com/categories/remote-programming-jobs.rss"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            root = ET.fromstring(r.content)
            for item in root.findall('.//item'):
                title_elem = item.find('title')
                desc_elem = item.find('description')
                link_elem = item.find('link')
                
                title: str = title_elem.text if title_elem is not None else ""
                desc_html: str = desc_elem.text if desc_elem is not None else ""
                apply_url: str = link_elem.text if link_elem is not None else ""
                
                # Split company and title from WeWorkRemotely title (e.g. "Company: Title")
                company: str = "WeWorkRemotely Hiring"
                job_title: str = title
                if ":" in title:
                    parts = title.split(":", 1)
                    company = parts[0].strip()
                    job_title = parts[1].strip()
                
                description: str = clean_html(desc_html)
                
                # Extract email using regex
                emails: list[str] = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', description)
                recruiter_email: str = emails[0] if emails else f"careers@{company.lower().replace(' ', '')}.com"
                
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
        logging.error(f"Error crawling WeWorkRemotely: {e}")
    return jobs

# Greenhouse Crawlers
def crawl_greenhouse_board(board: str) -> list[dict[str, str]]:
    """Crawl job listings from a specific Greenhouse board."""
    jobs: list[dict[str, str]] = []
    url: str = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for j in data.get("jobs", []):
                title: str = j.get("title", "")
                apply_url: str = j.get("absolute_url", "")
                location: str = j.get("location", {}).get("name", "Remote")
                content: str = clean_html(j.get("content", ""))
                
                emails: list[str] = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                recruiter_email: str = emails[0] if emails else f"careers@{board}.com"
                
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
        logging.error(f"Error crawling Greenhouse board {board}: {e}")
    return jobs

# Lever Crawlers
def crawl_lever_company(company: str) -> list[dict[str, str]]:
    """Crawl job listings from a specific Lever company page."""
    jobs: list[dict[str, str]] = []
    url: str = f"https://api.lever.co/v0/postings/{company}"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if r.status_code == 200:
            data = r.json()
            for j in data:
                title: str = j.get("text", "")
                apply_url: str = j.get("hostedUrl") or j.get("applyUrl") or ""
                location: str = j.get("categories", {}).get("location", "Remote")
                description: str = clean_html(j.get("description", "") + " " + j.get("lists", [{}])[0].get("content", ""))
                
                emails: list[str] = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', description)
                recruiter_email: str = emails[0] if emails else f"careers@{company}.com"
                
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
        logging.error(f"Error crawling Lever company {company}: {e}")
    return jobs

# Sync curated jobs from local Placement Portal into Agent opportunities pool
def sync_curated_jobs() -> None:
    """Sync curated jobs from standard database to Agent pool."""
    try:
        # Delete any opportunities that are not from "Placement Portal"
        deleted_count: int = AgentJobOpportunity.query.filter(AgentJobOpportunity.source != "Placement Portal").delete(synchronize_session=False)
        db.session.commit()
        if deleted_count > 0:
            logging.info(f"Cleaned up {deleted_count} external job opportunities from Agent pool.")

        curated_jobs: list[Job] = Job.query.filter_by(is_active=True).all()
        existing_urls: set[str] = set(r[0] for r in db.session.query(AgentJobOpportunity.apply_url).all())
        
        new_jobs_count: int = 0
        for j in curated_jobs:
            if not j.apply_url:
                continue
            if j.apply_url not in existing_urls:
                emails: list[str] = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', j.description or "")
                recruiter_email: str = emails[0] if emails else f"careers@{j.company.lower().replace(' ', '')}.com"
                
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
        logging.info(f"Synced {new_jobs_count} curated jobs from Placement Portal.")
    except Exception as e:
        logging.error(f"Error syncing curated jobs: {e}")

# Run crawler to find new job opportunities (only syncs curated jobs in database-only architecture)
def crawl_and_save_opportunities(user_id: int | None = None) -> int:
    """Sync curated jobs in the database-only architecture."""
    # Sync curated jobs from local Placement Portal
    update_status(user_id, "Syncing curated jobs from database...")
    sync_curated_jobs()
    return 0


# Pre-filter helper
def pre_filter_job(title: str, location: str, config: UserAgentConfig) -> bool:
    """Apply basic checks to filter jobs by role and location config."""
    if not config.target_roles:
        roles_match: bool = True
    else:
        roles: list[str] = [r.strip().lower() for r in config.target_roles.split(",") if r.strip()]
        # Expand role synonyms
        roles_expanded: list[str] = []
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
        locations_match: bool = True
    else:
        locs: list[str] = [l.strip().lower() for l in config.target_locations.split(",") if l.strip()]
        # Expand location aliases
        locs_expanded: list[str] = []
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
def match_user_with_jobs(user_id: int) -> int:
    """Evaluate matching relevance score for jobs and generate recruiter pitch."""
    user: User | None = User.query.get(user_id)
    if not user:
        return 0
        
    config: UserAgentConfig | None = UserAgentConfig.query.filter_by(user_id=user_id).first()
    if not config or not config.is_active or not config.resume_text:
        return 0
        
    # Get Groq client
    api_key: str | None = os.getenv("GROQ_API_KEY")
    if not api_key:
        logging.error("GROQ_API_KEY is not set. Cannot run match worker.")
        return 0
    client = Groq(api_key=api_key)
    
    # Subquery for evaluated job ids to exclude them
    evaluated_ids_subquery = db.session.query(AgentApplicationLog.job_opportunity_id).filter_by(user_id=user_id)
    
    # Fetch all job opportunities that haven't been evaluated yet (only from Placement Portal)
    all_opps: list[AgentJobOpportunity] = (AgentJobOpportunity.query
                .filter(~AgentJobOpportunity.id.in_(evaluated_ids_subquery))
                .filter(AgentJobOpportunity.source == "Placement Portal")
                .all())
                
    # Tokenize the resume text to lowercase alphanumeric words for fast lookup
    resume_words: set[str] = set(re.findall(r'[a-zA-Z0-9]+', (config.resume_text or "").lower()))
    
    # Calculate relevance score for each job based on keyword overlap
    scored_opportunities: list[tuple[int, AgentJobOpportunity]] = []
    for job in all_opps:
        score: int = 0
        # Title matches (higher weight)
        title_words: list[str] = re.findall(r'[a-zA-Z0-9]+', (job.title or "").lower())
        for w in title_words:
            if w in resume_words:
                score += 10
        # Description/skills match (1 point per matching word)
        desc_words: list[str] = re.findall(r'[a-zA-Z0-9]+', (job.description or "").lower())
        matched_words: set[str] = resume_words.intersection(desc_words)
        score += len(matched_words)
        
        scored_opportunities.append((score, job))
        
    # Sort by relevance score descending and take the top 15 most relevant
    scored_opportunities.sort(key=lambda x: x[0], reverse=True)
    opportunities: list[AgentJobOpportunity] = [job for score, job in scored_opportunities[:15]]
                     
    matches_processed: int = 0
    total_opps: int = len(opportunities)
    
    if total_opps == 0:
        update_status(user_id, "No new jobs to evaluate.")
        time.sleep(1)
        return 0
    
    for idx, job in enumerate(opportunities):
        # Check for abort/restart request
        if AGENT_RESTART_REQUESTED.get(user_id):
            logging.info(f"Abort matching requested for user_id={user_id}")
            break

        # Update progress status
        update_status(user_id, f"Evaluating match {idx + 1}/{total_opps} against resume: {job.title} at {job.company}...")
            
        # Match using Groq Llama 3
        system_prompt: str = """
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

        user_prompt: str = f"""
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
            
            content: str = chat_completion.choices[0].message.content.strip()
            
            # Clean markdown codeblocks if they exist
            if content.startswith("```"):
                content = re.sub(r'^```(?:json)?\n', '', content)
                content = re.sub(r'\n```$', '', content)
                
            res_data: dict[str, Any] = json.loads(content)
            
            fit_score: int = int(res_data.get("fit_score", 0))
            explanation: str = res_data.get("explanation", "")
            subject: str = res_data.get("subject", f"Application for {job.title} - {user.username}")
            pitch_body: str = res_data.get("pitch_body", "")
            
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
            logging.error(f"Error matching job {job.id} for user {user_id}: {e}")
            db.session.rollback()
            time.sleep(5)  # Sleep longer on error/rate-limit
            
    db.session.commit() # Save all skipped logs
    return matches_processed

# Full pipeline wrapper to run in background thread
def run_job_agent_pipeline_async(app: Flask, user_id: int) -> Thread | None:
    """Start background job agent crawler and matching thread."""
    # Prevent duplicate thread executions for the same user, request restart if running
    status: str = AGENT_STATUSES.get(user_id, "Idle")
    if status != "Idle":
        logging.info(f"Pipeline already running for user_id={user_id}. Requesting restart...")
        AGENT_RESTART_REQUESTED[user_id] = True
        return None

    def job() -> None:
        with app.app_context():
            while True:
                # Clear the restart request flag at start of run
                AGENT_RESTART_REQUESTED[user_id] = False
                
                db.session.remove() # Clean up session in thread
                logging.info(f"Starting async job agent pipeline for user_id={user_id}...")
                try:
                    update_status(user_id, "Starting agent pipeline...")
                    # 1. Crawl new jobs
                    crawl_and_save_opportunities(user_id)
                    
                    if AGENT_RESTART_REQUESTED.get(user_id):
                        logging.info(f"Restart requested during crawling for user_id={user_id}. Restarting...")
                        AgentApplicationLog.query.filter_by(user_id=user_id).delete()
                        db.session.commit()
                        continue
                        
                    # 2. Match with user
                    match_user_with_jobs(user_id)
                    
                    if AGENT_RESTART_REQUESTED.get(user_id):
                        logging.info(f"Restart requested during matching for user_id={user_id}. Restarting...")
                        AgentApplicationLog.query.filter_by(user_id=user_id).delete()
                        db.session.commit()
                        continue
                        
                except Exception as e:
                    logging.error(f"Error in job agent pipeline: {e}")
                    db.session.rollback()
                finally:
                    db.session.commit()
                    db.session.remove() # Release DB connection back to pool
                
                if not AGENT_RESTART_REQUESTED.get(user_id):
                    break
            
            update_status(user_id, "Idle")
            logging.info(f"Finished async job agent pipeline for user_id={user_id}")
            
    thread = Thread(target=job)
    thread.daemon = True
    thread.start()
    return thread
