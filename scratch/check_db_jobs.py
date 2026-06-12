import os
import sys
from dotenv import load_dotenv
from psycopg2 import connect
from psycopg2.extras import RealDictCursor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

def check_jobs():
    database_url = os.getenv("DATABASE_URL")
    print(f"Connecting to database...")
    conn = connect(database_url)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT id, title, company, apply_url, created_at FROM jobs ORDER BY id DESC LIMIT 5")
            rows = cursor.fetchall()
            print(f"Found {len(rows)} recent jobs in database:")
            for r in rows:
                print(f"  - ID: {r['id']}, Title: {r['title']}, Company: {r['company']}, Apply URL: {r['apply_url']}, Created At: {r['created_at']}")
    except Exception as e:
        print(f"Error querying jobs: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_jobs()
