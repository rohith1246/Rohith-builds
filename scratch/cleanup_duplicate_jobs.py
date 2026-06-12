import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

def cleanup():
    if not DATABASE_URL:
        print("DATABASE_URL not found in .env file.")
        return
    
    print("Connecting to Neon PostgreSQL database...")
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Find all jobs to see state before cleanup
    cursor.execute("SELECT COUNT(*) FROM jobs;")
    before_count = cursor.fetchone()[0]
    print(f"Total jobs before cleanup: {before_count}")
    
    # Query to find and delete duplicate jobs keeping only the oldest one (minimum id) per group
    cursor.execute("""
        DELETE FROM jobs
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM jobs
            GROUP BY LOWER(title), LOWER(company)
        );
    """)
    deleted_count = cursor.rowcount
    conn.commit()
    
    # See state after cleanup
    cursor.execute("SELECT COUNT(*) FROM jobs;")
    after_count = cursor.fetchone()[0]
    print(f"Deleted {deleted_count} duplicate jobs.")
    print(f"Total jobs after cleanup: {after_count}")
    
    conn.close()

if __name__ == "__main__":
    cleanup()
