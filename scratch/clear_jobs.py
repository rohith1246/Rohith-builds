import os
import psycopg2
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
DATABASE_URL = os.getenv("DATABASE_URL")

def clear():
    if not DATABASE_URL:
        print("DATABASE_URL not found")
        return
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jobs;")
    print("All jobs deleted successfully from jobs table.")
    conn.close()

if __name__ == "__main__":
    clear()
