import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "admin_dashboard"))

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

from app import execute_query, fetch_one

def test_duplicate_checking():
    print("Initializing duplicate checking test...")
    
    # Define first job parameters
    title = "Mock SDE Intern"
    company = "Scraper Dups Inc."
    location = "Remote"
    job_type = "Internship"
    category = "Python"
    experience_level = "Freshers"
    skills = "Python, SQL"
    description = "A mock developer role for duplicate testing."
    apply_url_1 = "https://scraper-dups.com/apply1"
    apply_url_2 = "https://scraper-dups.com/apply2" # Different URL
    
    # 1. Clean up any leftover jobs with these URLs or Title/Company
    execute_query("DELETE FROM jobs WHERE LOWER(company) = LOWER(%s)", [company])
    
    try:
        # 2. Insert first job
        print(f"Inserting first job: '{title}' at '{company}' with URL: '{apply_url_1}'")
        execute_query("""
            INSERT INTO jobs (title, company, logo_url, location, job_type, category, experience_level, salary, skills, description, course_match, apply_url, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
        """, [title, company, None, location, job_type, category, experience_level, "₹25,000/month", skills, description, "Fits outcomes", apply_url_1])
        
        # Verify first job is in DB
        first_job = fetch_one("SELECT id FROM jobs WHERE apply_url = %s", [apply_url_1])
        assert first_job is not None, "First job was not inserted successfully."
        print(f"[OK] First job inserted (ID: {first_job['id']})")
        
        # 3. Simulate duplicate insertion check (as done in the scraper thread)
        print(f"Checking duplication for second job: '{title}' at '{company}' with URL: '{apply_url_2}'")
        
        # Check by URL (fast path)
        existing_by_url = fetch_one("SELECT id FROM jobs WHERE apply_url = %s", [apply_url_2])
        is_duplicate = False
        
        if existing_by_url:
            print("Duplicate found by URL.")
            is_duplicate = True
        else:
            # Check by Title & Company (slow path / our new check)
            duplicate_job = fetch_one("""
                SELECT id FROM jobs 
                WHERE LOWER(title) = LOWER(%s) AND LOWER(company) = LOWER(%s)
            """, [title, company])
            if duplicate_job:
                print(f"[MATCH] Duplicate found by Title & Company (ID: {duplicate_job['id']})")
                is_duplicate = True
                
        # Assert that duplicate was indeed detected
        assert is_duplicate is True, "FAIL: Duplicate job was NOT detected by Title & Company."
        print("[SUCCESS] Duplicate check correctly flagged the duplicate job!")
        
        # Attempting insertion only if not duplicate
        if not is_duplicate:
            execute_query("""
                INSERT INTO jobs (title, company, logo_url, location, job_type, category, experience_level, salary, skills, description, course_match, apply_url, is_active, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, NOW())
            """, [title, company, None, location, job_type, category, experience_level, "₹25,000/month", skills, description, "Fits outcomes", apply_url_2])
            
        # Verify second job was NOT inserted
        second_job = fetch_one("SELECT id FROM jobs WHERE apply_url = %s", [apply_url_2])
        assert second_job is None, "FAIL: Duplicate job was inserted in the database!"
        print("[SUCCESS] Duplicate job insertion prevented.")
        
    finally:
        # Clean up
        execute_query("DELETE FROM jobs WHERE LOWER(company) = LOWER(%s)", [company])
        print("Database cleaned up.")

if __name__ == "__main__":
    test_duplicate_checking()
