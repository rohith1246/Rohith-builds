import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

def check():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, company FROM jobs;")
    rows = cursor.fetchall()
    print(f"Total jobs: {len(rows)}")
    for r in rows:
        print(f"ID: {r[0]} | Title: {r[1]} | Company: {r[2]}")
    conn.close()

if __name__ == "__main__":
    check()
