import os
import sys
from dotenv import load_dotenv

# Add admin_dashboard directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "admin_dashboard"))
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

from app import fetch_all

try:
    print("Executing query on database...")
    jobs = fetch_all("SELECT id, title, company, location, job_type, category, target_batch, is_active, created_at FROM jobs ORDER BY created_at DESC")
    print(f"[SUCCESS] Query completed. Curated jobs found: {len(jobs)}")
    if jobs:
        print(f"First job target_batch: {jobs[0]['target_batch']}")
except Exception as e:
    print(f"[ERROR] Query failed: {e}")
