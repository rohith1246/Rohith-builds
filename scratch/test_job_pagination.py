import sys
import os
import unittest
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import db, Job

class TestJobPagination(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Clean up any existing test jobs
        Job.query.filter(Job.company == "Mock Pagination Company").delete()
        db.session.commit()

    def tearDown(self):
        # Clean up test jobs
        Job.query.filter(Job.company == "Mock Pagination Company").delete()
        db.session.commit()
        self.app_context.pop()

    def test_jobs_pagination_logic(self):
        print("\nSeeding 20 mock jobs for pagination test...")
        
        # Insert 20 jobs with distinct timestamps and unique non-overlapping titles
        now = datetime.utcnow()
        for i in range(20):
            # i=0 is Developer-A (newest, now - 0 sec), i=19 is Developer-T (oldest, now - 19 sec)
            title_char = chr(65 + i) # A to T
            job = Job(
                title=f"Developer-{title_char}",
                company="Mock Pagination Company",
                location="Bengaluru",
                job_type="Job",
                category="Backend",
                experience_level="Freshers",
                salary="₹6LPA",
                skills="Python, SQL",
                description=f"This is mock job description {title_char}",
                course_match=f"Course Match {title_char}",
                apply_url="https://rohith-builds.onrender.com",
                is_active=True,
                created_at=now - timedelta(seconds=i)
            )
            db.session.add(job)
        db.session.commit()
        
        # Test Page 1 (should return items 0 to 14: Developer-A to Developer-O)
        print("Testing GET /jobs?page=1...")
        response = self.client.get('/jobs?page=1')
        self.assertEqual(response.status_code, 200)
        html = response.data.decode('utf-8')
        
        # Developer-A to Developer-O must be on Page 1
        self.assertIn("Developer-A", html)
        self.assertIn("Developer-O", html)
        # Developer-P to Developer-T should not be on Page 1
        self.assertNotIn("Developer-P", html)
        self.assertNotIn("Developer-T", html)
        
        # Test Page 2 (should return items 15 to 19: Developer-P to Developer-T)
        print("Testing GET /jobs?page=2...")
        response_page2 = self.client.get('/jobs?page=2')
        self.assertEqual(response_page2.status_code, 200)
        html_page2 = response_page2.data.decode('utf-8')
        
        # Developer-P to Developer-T should be on Page 2
        self.assertIn("Developer-P", html_page2)
        self.assertIn("Developer-T", html_page2)
        # Developer-A should NOT be on Page 2
        self.assertNotIn("Developer-A", html_page2)
        
        # Check pagination controls HTML elements exist
        self.assertIn("jobs-pagination", html)
        self.assertIn("page-number active", html)
        self.assertIn("page=2", html)
        
        print("[SUCCESS] Pagination logic tested: Page 1 has Developer-A to Developer-O, Page 2 has Developer-P to Developer-T.")

if __name__ == "__main__":
    unittest.main()
