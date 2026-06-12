import sys
import os
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# Import root app first
import app as root_app

# Clear sys.modules['app'] to allow importing the admin dashboard app
if 'app' in sys.modules:
    del sys.modules['app']

sys.path.insert(0, os.path.join(BASE_DIR, "admin_dashboard"))
import app as admin_app

from flask import render_template

class TestTotalJobsSection(unittest.TestCase):
    def setUp(self):
        # Set database URLs for tests
        os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///test.db")

    def test_public_jobs_template(self):
        print("\nTesting public jobs template compile & content...")
        with root_app.app.test_request_context():
            from models import Job
            mock_jobs = [
                Job(title="Python Developer", company="Test Swiggy", location="Remote", job_type="Job", category="Python", skills="Python", description="Test")
            ]
            
            # Test unfiltered state
            html = render_template(
                "jobs.html",
                jobs=mock_jobs,
                selected_type="All",
                selected_role="All",
                selected_location="All",
                search_query="",
                now=__import__("datetime").datetime.utcnow(),
                total_jobs_count=50,
                filters_active=False
            )
            self.assertIn("Total Curated Jobs", html)
            self.assertIn("50", html)
            print("[OK] Unfiltered state verified.")
            
            # Test filtered state
            html_filtered = render_template(
                "jobs.html",
                jobs=mock_jobs,
                selected_type="Job",
                selected_role="All",
                selected_location="All",
                search_query="",
                now=__import__("datetime").datetime.utcnow(),
                total_jobs_count=50,
                filters_active=True
            )
            self.assertIn("Showing", html_filtered)
            self.assertIn("1", html_filtered)
            self.assertIn("50", html_filtered)
            print("[OK] Filtered state verified.")
            print("[OK] Public jobs template verified successfully.")

    def test_main_admin_dashboard_template(self):
        print("\nTesting main admin dashboard template compile & content...")
        with root_app.app.test_request_context():
            html = render_template(
                "admin/dashboard.html",
                user_count=10,
                total_enrollments=5,
                course_count=2,
                prompt_count=20,
                job_count=15, # Our new metric
                active_learners=2,
                recent_users=[],
                recent_enrollments=[],
                db_type="PostgreSQL",
                backup_count=0,
                last_backup_time="Never",
                favorites_count=0,
                likes_count=0,
                collections_count=0,
                lesson_reviews=[]
            )
            self.assertIn("Curated Jobs", html)
            self.assertIn("15", html)
            print("[OK] Main admin dashboard template verified successfully.")

    def test_local_admin_dashboard_logic_and_templates(self):
        print("\nTesting local admin dashboard templates...")
        with admin_app.app.test_request_context():
            # Test dashboard.html stats iteration
            mock_stats = [
                {"label": "Total users", "value": 100, "extra": None},
                {"label": "Curated job listings", "value": 25, "extra": None}
            ]
            html_dash = render_template(
                "dashboard.html",
                stats=mock_stats,
                page_title="Dashboard",
                active_page="dashboard"
            )
            self.assertIn("Curated job listings", html_dash)
            self.assertIn("25", html_dash)
            
            # Test jobs_manage.html list count header
            mock_jobs_list = [
                {"id": 1, "title": "Developer", "company": "Virtusa", "location": "Remote", "job_type": "Job", "category": "Python", "is_active": True}
            ]
            html_manage = render_template(
                "jobs_manage.html",
                jobs=mock_jobs_list,
                active_page="jobs"
            )
            self.assertIn("Total Curated: 1", html_manage)
            print("[OK] Local admin dashboard templates verified successfully.")

if __name__ == "__main__":
    unittest.main()
