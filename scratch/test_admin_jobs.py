import sys
import os
from flask import json

# Add admin_dashboard directory to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard"))

# Make sure .env is loaded in context
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "admin_dashboard", ".env"))

# Import admin app
from app import app, safe_json_loads

def test_admin_jobs():
    print("Initializing admin test client...")
    client = app.test_client()

    # Log in the admin
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        sess['admin_username'] = 'rohith'

    # 1. Test GET /jobs list page
    print("Testing GET /jobs...")
    response = client.get('/jobs')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    html = response.data.decode('utf-8')
    assert "Manage Job Listings" in html or "jobs" in html, "Manage page title missing"
    print("[SUCCESS] GET /jobs returned 200.")

    # 2. Test GET /jobs/create page
    print("Testing GET /jobs/create...")
    response = client.get('/jobs/create')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    html = response.data.decode('utf-8')
    assert "Post a New Job" in html, "Form title missing"
    assert "AI Job Parser" in html, "AI Parser widget missing"
    print("[SUCCESS] GET /jobs/create returned 200.")

    # 3. Test POST /api/jobs/parse-ai
    print("Testing POST /api/jobs/parse-ai (AI Job Parser)...")
    raw_posting = """
    Software Engineer - Backend (Python)
    Swiggy - Bengaluru, Karnataka, India (Hybrid)
    
    About the role:
    We are looking for an entry level Software Engineer to build database applications.
    Requirements:
    - 0-1 years of experience with Python programming.
    - Experience writing SQL database queries (PostgreSQL/MySQL).
    - Basic understanding of web servers like Flask or FastAPI.
    - Good problem solving skills.
    
    Salary: 5,00,000 to 7,00,000 INR per year.
    To apply send resume to careers@swiggy.com or apply on our website.
    """
    
    response = client.post(
        '/api/jobs/parse-ai',
        data=json.dumps({"raw_text": raw_posting}),
        content_type='application/json'
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = json.loads(response.data.decode('utf-8'))
    assert data.get("success") is True, f"API failed: {data.get('error')}"
    
    parsed = data.get("data")
    print(f"AI Parsed Data: {str(parsed).encode('utf-8')}")
    
    assert "title" in parsed, "title missing in parsed output"
    assert "company" in parsed, "company missing in parsed output"
    assert "location" in parsed, "location missing in parsed output"
    assert "job_type" in parsed, "job_type missing in parsed output"
    assert "skills" in parsed, "skills missing in parsed output"
    assert "description" in parsed, "description missing in parsed output"
    assert "course_match" in parsed, "course_match missing in parsed output"
    
    print("[SUCCESS] AI Job Parser parsed LinkedIn text correctly.")
    print(f"Role: parsed title successfully")
    print(f"Skills Extracted: parsed skills successfully")
    print(f"Course Match suggestion: parsed course match successfully")

if __name__ == "__main__":
    test_admin_jobs()
