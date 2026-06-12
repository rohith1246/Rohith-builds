import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "admin_dashboard", ".env"))

from app import app
from models import db
from sqlalchemy import inspect, text

def migrate():
    with app.app_context():
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(f"Table names in database: {table_names}")
        
        if "jobs" in table_names:
            columns = [col["name"] for col in inspector.get_columns("jobs")]
            print(f"Columns in 'jobs' table: {columns}")
            if "clicks" not in columns:
                print("Adding 'clicks' column to 'jobs' table...")
                try:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE jobs ADD COLUMN clicks INTEGER DEFAULT 0"))
                        conn.commit()
                    print("Successfully added 'clicks' column!")
                except Exception as e:
                    print(f"Error adding column: {e}")
            else:
                print("'clicks' column already exists in 'jobs' table.")
        else:
            print("'jobs' table does not exist in database!")

if __name__ == "__main__":
    migrate()
