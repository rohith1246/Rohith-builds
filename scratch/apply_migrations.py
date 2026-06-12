import os
from dotenv import load_dotenv
load_dotenv(override=True)

from sqlalchemy import create_engine, inspect, text

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("No DATABASE_URL found.")
    exit(1)

print(f"Connecting to: {db_url.split('@')[-1] if '@' in db_url else db_url}")
engine = create_engine(db_url)

with engine.connect() as conn:
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    print(f"Tables: {table_names}")
    
    if "prompts" in table_names:
        columns = [col["name"] for col in inspector.get_columns("prompts")]
        if "copies" not in columns:
            conn.execute(text("ALTER TABLE prompts ADD COLUMN copies INTEGER DEFAULT 0"))
            print("Added column 'copies' to 'prompts'")
        if "view_count" not in columns:
            conn.execute(text("ALTER TABLE prompts ADD COLUMN view_count INTEGER DEFAULT 0"))
            print("Added column 'view_count' to 'prompts'")
            
    if "users" in table_names:
        columns = [col["name"] for col in inspector.get_columns("users")]
        if "is_verified" not in columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
            print("Added column 'is_verified' to 'users'")
            
    if "course_days" in table_names:
        columns = [col["name"] for col in inspector.get_columns("course_days")]
        if "image" not in columns:
            conn.execute(text("ALTER TABLE course_days ADD COLUMN image VARCHAR(300)"))
            print("Added column 'image' to 'course_days'")
            
    conn.commit()
    print("Committed all migrations successfully.")
