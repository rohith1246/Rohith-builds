import os
import psycopg2
from dotenv import load_dotenv

# Load env from admin_dashboard
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

db_url = os.environ.get("DATABASE_URL")
print(f"Connecting to: {db_url}")

conn = psycopg2.connect(db_url)
cur = conn.cursor()
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name='jobs'")
cols = [r[0] for r in cur.fetchall()]
print(f"Columns in 'jobs' table: {cols}")

# Let's also check if it's missing and run the ALTER query directly here if so!
if 'target_batch' not in cols:
    print("Column 'target_batch' is missing! Adding it now...")
    cur.execute("ALTER TABLE jobs ADD COLUMN target_batch VARCHAR(100) DEFAULT '2025, 2026'")
    conn.commit()
    print("Column 'target_batch' added successfully!")
else:
    print("Column 'target_batch' already exists!")

conn.close()
