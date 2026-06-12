import sys
import os

# Add admin_dashboard directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

from app import app
from models import db, Job

def test_job_clicks():
    print("Initializing test client...")
    client = app.test_client()
    client.get("/") # Trigger before_request database migration hook
    
    with app.app_context():
        # Create a test job
        test_job = Job(
            title="Test Developer for Clicks",
            company="Clicks Test Inc.",
            location="Remote",
            job_type="Job",
            category="Python",
            experience_level="Freshers",
            skills="Python",
            description="Testing click counts functionality.",
            apply_url="https://clicks-test.com/apply",
            clicks=0
        )
        db.session.add(test_job)
        db.session.commit()
        job_id = test_job.id
        print(f"Created test job ID: {job_id}")

    try:
        # Trigger Click API
        url = f"/api/jobs/{job_id}/click"
        print(f"Triggering POST to {url}...")
        response = client.post(url)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.get_json()
        print(f"API Response: {data}")
        assert data.get("success") is True, "Expected success: True"
        assert data.get("clicks_count") == 1, f"Expected clicks_count 1, got {data.get('clicks_count')}"
        
        # Verify in DB
        with app.app_context():
            job_db = Job.query.get(job_id)
            print(f"Database clicks value: {job_db.clicks}")
            assert job_db.clicks == 1, f"Expected DB clicks 1, got {job_db.clicks}"
            
        print("[SUCCESS] Click tracking endpoint verified successfully!")
        
    finally:
        # Clean up
        with app.app_context():
            job_db = Job.query.get(job_id)
            if job_db:
                db.session.delete(job_db)
                db.session.commit()
                print("Cleaned up test job from database.")

if __name__ == "__main__":
    test_job_clicks()
