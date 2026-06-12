import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import json

# Add admin_dashboard directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "admin_dashboard"))

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

from app import call_groq_with_fallback, safe_json_loads, execute_query, fetch_one

def test_indeed_snippet_parsing():
    # A mock indeed job item containing a snippet from a real junior job posted 2 days ago
    job_item = {
        "url": "https://in.indeed.com/viewjob?jk=mock123456indeed",
        "source": "indeed",
        "title": "Junior Python Developer",
        "snippet": "We are looking for a skilled Junior Python Developer to join our team in Bengaluru. Experience: 0-1 years. Skills required: Python, Django, SQL. Responsibilities: writing clean code, database queries. Posted 2 days ago."
    }
    
    url = job_item["url"]
    source = job_item["source"]
    search_title = job_item["title"]
    search_snippet = job_item["snippet"]
    
    cropped_text = f"Title: {search_title}\nSnippet: {search_snippet}"
    apply_url = url
    
    print("\n--- Testing Groq AI Parsing with Snippet ---")
    
    system_prompt = """
You are an expert tech recruiter and AI assistant for Rohith Builds. 
Your task is to analyze a raw job description (which may be a full page's text or a search result snippet) and determine if it represents a Junior, Entry-Level, or Internship software developer position matching our target profiles: Python Developer, Backend Developer, or AI / LLM Engineer (based in India or remote for India).

--- FRESHNESS REQUIREMENT ---
You must only accept jobs posted within the last 4 days. If the job text explicitly indicates that the job was posted more than 4 days ago (e.g. "posted 5+ days ago", "1 week ago", "10 days ago", "30+ days ago"), you MUST reject the job and return {"is_fit": false}. If the posting date is unknown, within the last 4 days, or recently posted (e.g., "1 day ago", "2 days ago", "just posted"), it is acceptable.

--- SCHEMA REQUIREMENTS ---
If the job fits our criteria and is fresh (last 4 days), return a JSON object with:
1. "title": Job title (e.g., "Junior Backend Developer")
2. "company": Company name
3. "location": e.g., "Bengaluru", "Mumbai (Remote)", "India"
4. "job_type": Exactly "Job" (if full-time/contract) or "Internship"
5. "category": Exactly "Python", "Backend", or "AI / LLM"
6. "experience_level": e.g. "Freshers / 0-2 years", "0-1 years"
7. "salary": e.g. "₹5LPA - ₹8LPA" (provide a realistic Indian market estimate for junior roles if not specified, or set to null if completely unknown)
8. "skills": Comma-separated list of 3-5 main technical skills (e.g., "Python, Flask, SQL")
9. "description": Clean, bulleted description highlighting responsibilities and requirements (use simple text, no HTML tags)
10. "course_match": A brief explanation of why this fits Rohith Builds outcomes (e.g. "Fits Phase 2 Backend outcomes")

If the job does NOT fit the criteria (e.g. it is senior, requires 3+ years experience, is not Python/Backend/AI, is not in India/Remote, or is explicitly older than 4 days), return exactly the JSON object:
{"is_fit": false}

--- OUTPUT RULES ---
- Output ONLY the raw JSON object. Do not wrap in markdown code blocks.
- Ensure all strings are properly escaped.
"""
    user_content = f"Job Page URL: {url}\n\nRaw Text:\n{cropped_text}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    print("Calling Groq...")
    ai_output = call_groq_with_fallback(messages, max_tokens=1000)
    cleaned = ai_output.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    cleaned = cleaned.strip()
    
    parsed = safe_json_loads(cleaned)
    print(f"Parsed JSON:\n{json.dumps(parsed, indent=2)}")
    
    if parsed.get("is_fit") is False:
        print("Skipping - Not a fit.")
        return
        
    print("\n--- Testing DB Insertion ---")
    title = parsed.get("title")
    company = parsed.get("company", "Test Company")
    location = parsed.get("location", "India")
    job_type = parsed.get("job_type", "Job")
    category = parsed.get("category", "Python")
    experience_level = parsed.get("experience_level", "Freshers")
    salary = parsed.get("salary")
    skills = parsed.get("skills", "Python")
    description = parsed.get("description", "")
    course_match = parsed.get("course_match")
    
    # Check if exists
    existing = fetch_one("SELECT id FROM jobs WHERE apply_url = %s", [apply_url])
    if existing:
        print(f"Job already exists (id: {existing['id']}), deleting it first to test insertion...")
        execute_query("DELETE FROM jobs WHERE id = %s", [existing['id']])
        
    execute_query("""
        INSERT INTO jobs (title, company, logo_url, location, job_type, category, experience_level, salary, skills, description, course_match, apply_url, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
    """, [title, company, None, location, job_type, category, experience_level, salary, skills, description, course_match, apply_url])
    
    # Verify insert
    new_job = fetch_one("SELECT * FROM jobs WHERE apply_url = %s", [apply_url])
    if new_job:
        print(f"[SUCCESS] Auto-Added Job: {new_job['title']} at {new_job['company']} (ID: {new_job['id']})")
        # Delete test job to keep database clean
        execute_query("DELETE FROM jobs WHERE id = %s", [new_job['id']])
        print("Cleaned up test job from DB.")
    else:
        print("[FAILED] Job insertion failed.")

if __name__ == "__main__":
    test_indeed_snippet_parsing()
