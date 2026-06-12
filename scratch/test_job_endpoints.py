import sys
import os
from flask import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Job

def test_jobs():
    print("Initializing test client...")
    client = app.test_client()

    with app.app_context():
        # Get a job ID to test matching
        job = Job.query.first()
        if not job:
            print("[ERROR] No jobs found in database to run tests against.")
            return
        
        job_id = job.id
        print(f"Testing with Job ID: {job_id} ({job.title} at {job.company})")

    # 1. Test Jobs Board page
    print("Testing GET /jobs...")
    response = client.get('/jobs')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    html = response.data.decode('utf-8')
    assert "Indian Tech Jobs &amp; Internships" in html or "Indian Tech Jobs" in html, "Page title missing"
    assert job.company in html, "Curated job company name not rendered"
    print("[SUCCESS] GET /jobs returned 200 and matches company name.")

    # 2. Test Filters
    print("Testing GET /jobs with type=Internship...")
    response = client.get('/jobs?type=Internship')
    assert response.status_code == 200
    print("[SUCCESS] GET /jobs with type filter returned 200.")

    # 3. Test Job Click API
    print(f"Testing POST /api/jobs/{job_id}/click...")
    response = client.post(f'/api/jobs/{job_id}/click')
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = json.loads(response.data.decode('utf-8'))
    assert data.get("success") is True, "Expected success to be True"
    assert "clicks_count" in data, "clicks_count missing in click response"
    print(f"[SUCCESS] Job click API returned 200, new click count: {data.get('clicks_count')}")

if __name__ == "__main__":
    test_jobs()
