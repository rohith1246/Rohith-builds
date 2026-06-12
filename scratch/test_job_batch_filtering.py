import os
import sys

# Add root directory to path to import app and models
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from app import app
from models import db, Job

def setup_test_jobs():
    print("Setting up test jobs in database...")
    
    # Delete any existing test jobs first
    Job.query.filter(Job.company.ilike("TestBatchCorp%")).delete()
    
    # Create test jobs
    j1 = Job(
        title="Python Developer",
        company="TestBatchCorp 2025-2026",
        location="Bengaluru",
        job_type="Job",
        category="Python",
        experience_level="Freshers",
        skills="Python, SQL",
        description="Curated test job.",
        apply_url="https://example.com/test-1",
        target_batch="2025, 2026",
        is_active=True
    )
    
    j2 = Job(
        title="Web Developer Intern",
        company="TestBatchCorp 2026-2027",
        location="Remote",
        job_type="Internship",
        category="Frontend",
        experience_level="Freshers",
        skills="HTML, CSS, JS",
        description="Curated test job.",
        apply_url="https://example.com/test-2",
        target_batch="2026, 2027",
        is_active=True
    )
    
    j3 = Job(
        title="QA Automation Engineer",
        company="TestBatchCorp QA-Experience",
        location="Hybrid",
        job_type="Job",
        category="QA / Testing",
        experience_level="2+ years",
        skills="Selenium, Java",
        description="Curated test job.",
        apply_url="https://example.com/test-3",
        target_batch="Experience",
        is_active=True
    )
    
    j4 = Job(
        title="Associate Software Engineer",
        company="TestBatchCorp 2025 Only",
        location="Chennai",
        job_type="Job",
        category="Software Engineer",
        experience_level="0-1 years", # Not explicitly "Freshers" but target_batch has 2025
        skills="Java, Spring",
        description="Curated test job.",
        apply_url="https://example.com/test-4",
        target_batch="2025",
        is_active=True
    )
    
    db.session.add(j1)
    db.session.add(j2)
    db.session.add(j3)
    db.session.add(j4)
    db.session.commit()
    print("[SUCCESS] Test jobs added.")

def run_tests():
    client = app.test_client()
    
    with app.app_context():
        from app import _initialize_database
        _initialize_database()
        setup_test_jobs()
        
        try:
            # 1. Test All Jobs
            print("\n1. Testing GET /jobs with batch=All...")
            res = client.get('/jobs?batch=All')
            assert res.status_code == 200, f"Expected 200, got {res.status_code}"
            html = res.data.decode('utf-8')
            assert "TestBatchCorp 2025-2026" in html, "Job 1 missing"
            assert "TestBatchCorp 2026-2027" in html, "Job 2 missing"
            assert "TestBatchCorp QA-Experience" in html, "Job 3 missing"
            assert "TestBatchCorp 2025 Only" in html, "Job 4 missing"
            print("[SUCCESS] All jobs returned properly.")
            
            # 2. Test 2025 Filter
            print("\n2. Testing GET /jobs with batch=2025...")
            res = client.get('/jobs?batch=2025')
            html = res.data.decode('utf-8')
            assert "TestBatchCorp 2025-2026" in html, "Job 1 (2025, 2026) should be returned"
            assert "TestBatchCorp 2026-2027" in html, "Job 2 (Internship with 'Freshers' experience) should be returned under Fresher wildcard"
            assert "TestBatchCorp 2025 Only" in html, "Job 4 (2025 only) should be returned"
            assert "TestBatchCorp QA-Experience" not in html, "Job 3 (Experience) should NOT be returned"
            print("[SUCCESS] 2025 filter returned correct jobs.")
            
            # 3. Test 2027 Filter
            print("\n3. Testing GET /jobs with batch=2027...")
            res = client.get('/jobs?batch=2027')
            html = res.data.decode('utf-8')
            assert "TestBatchCorp 2026-2027" in html, "Job 2 (2026, 2027) should be returned"
            assert "TestBatchCorp 2025-2026" in html, "Job 1 (fresher job) should be returned under Fresher wildcard"
            assert "TestBatchCorp 2025 Only" not in html, "Job 4 (non-fresher target_batch 2025) should NOT be returned"
            assert "TestBatchCorp QA-Experience" not in html, "Job 3 (Experience) should NOT be returned"
            print("[SUCCESS] 2027 filter returned correct jobs.")
            
            # 4. Test Experience Filter
            print("\n4. Testing GET /jobs with batch=Experience...")
            res = client.get('/jobs?batch=Experience')
            html = res.data.decode('utf-8')
            assert "TestBatchCorp QA-Experience" in html, "Job 3 (Experience) should be returned"
            assert "TestBatchCorp 2025-2026" not in html, "Job 1 should NOT be returned"
            assert "TestBatchCorp 2026-2027" not in html, "Job 2 should NOT be returned"
            assert "TestBatchCorp 2025 Only" not in html, "Job 4 should NOT be returned"
            print("[SUCCESS] Experience filter returned correct jobs.")
            
            # 5. Test Category Filter for new category (QA / Testing)
            print("\n5. Testing GET /jobs with category=qa_testing...")
            res = client.get('/jobs?role=qa_testing')
            html = res.data.decode('utf-8')
            assert "TestBatchCorp QA-Experience" in html, "Job 3 (QA / Testing category) should be returned"
            assert "TestBatchCorp 2025-2026" not in html, "Job 1 should NOT be returned"
            print("[SUCCESS] QA / Testing category filter verified.")

            # 6. Test Category Filter for new category (Frontend)
            print("\n6. Testing GET /jobs with role=frontend...")
            res = client.get('/jobs?role=frontend')
            html = res.data.decode('utf-8')
            assert "TestBatchCorp 2026-2027" in html, "Job 2 (Frontend category) should be returned"
            assert "TestBatchCorp 2025-2026" not in html, "Job 1 should NOT be returned"
            print("[SUCCESS] Frontend category filter verified.")

        finally:
            # Clean up test records
            print("\nCleaning up test jobs...")
            Job.query.filter(Job.company.ilike("TestBatchCorp%")).delete()
            db.session.commit()
            print("Cleanup complete.")

if __name__ == "__main__":
    run_tests()
