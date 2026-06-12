import os
import sys
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
import time
from dotenv import load_dotenv

# Load env variables from admin_dashboard
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

# Import groq wrapper
sys.path.append(os.path.join(BASE_DIR, "admin_dashboard"))
from app import call_groq_with_fallback, safe_json_loads

def test_fetch_job_links():
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    keywords = ['python developer', 'backend developer']
    links = set()
    for kw in keywords:
        url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={quote_plus(kw)}&location=India&f_TPR=r604800&start=0"
        print(f"Searching for '{kw}'...")
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            count = 0
            for a in soup.find_all('a', href=True):
                href = a['href']
                if '/jobs/view/' in href:
                    clean_u = href.split("?")[0].split("#")[0].strip()
                    if clean_u not in links:
                        links.add(clean_u)
                        count += 1
            print(f"Found {count} links for '{kw}'")
        else:
            print(f"Failed to fetch for '{kw}', code: {res.status_code}")
    return list(links)

def test_parse_job(link):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    print(f"Crawling URL: {link}")
    res = requests.get(link, headers=headers, timeout=10)
    if res.status_code != 200:
        print(f"Failed to fetch job page: {res.status_code}")
        return
        
    soup = BeautifulSoup(res.text, 'html.parser')
    for script in soup(["script", "style", "nav", "footer", "header"]):
        script.decompose()
    text_content = soup.get_text(separator=' ')
    text_content = re.sub(r'\s+', ' ', text_content).strip()
    cropped_text = text_content[:5000]
    
    # Extract outbound links
    ext_match = re.search(r'https?://[^\s\'"]*(?:lever\.co|greenhouse\.io)[^\s\'"]*', text_content)
    if ext_match:
        apply_url = ext_match.group(0).strip()
        apply_url = re.sub(r'[.,;:)\]\s]+$', '', apply_url)
        print(f"Found outbound direct ATS apply URL: {apply_url}")
    else:
        apply_url = link
        print(f"No direct ATS URL, using LinkedIn URL: {apply_url}")
        
    system_prompt = """
You are an expert tech recruiter and AI assistant for Rohith Builds. 
Your task is to analyze a raw job description page and determine if it represents a Junior, Entry-Level, or Internship software developer position matching our target profiles: Python Developer, Backend Developer, or AI / LLM Engineer (based in India or remote for India).

--- SCHEMA REQUIREMENTS ---
If the job fits our criteria, return a JSON object with:
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

If the job does NOT fit the criteria (e.g. it is senior, requires 3+ years experience, is not Python/Backend/AI, or is not in India/Remote), return exactly the JSON object:
{"is_fit": false}

--- OUTPUT RULES ---
- Output ONLY the raw JSON object. Do not wrap in markdown code blocks.
- Ensure all strings are properly escaped.
"""
    user_content = f"Job Page URL: {link}\n\nRaw Text:\n{cropped_text}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ]
    
    print("Calling Groq to parse job details...")
    ai_output = call_groq_with_fallback(messages, max_tokens=1000)
    cleaned = ai_output.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9]*\n", "", cleaned)
        cleaned = re.sub(r"\n```$", "", cleaned)
    cleaned = cleaned.strip()
    
    parsed = safe_json_loads(cleaned)
    print(f"Parsed JSON outcome:\n{parsed}")

def run_test():
    links = test_fetch_job_links()
    if links:
        print(f"Successfully fetched {len(links)} links.")
        # Test parsing on the first link
        test_parse_job(links[0])
    else:
        print("No links found.")

if __name__ == "__main__":
    run_test()
