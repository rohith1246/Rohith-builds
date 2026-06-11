import os
import sys

# Reconfigure stdout for UTF-8 encoding on Windows to prevent emoji print crashes
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from admin_dashboard
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin_dashboard")))

from app import app, execute_query, fetch_one

def test_course_creation():
    with app.app_context():
        title = "Mock Test Course AI"
        slug = "mock-test-course-ai"
        description = "A temporary mock course for validating SQL operations."
        difficulty = "Advanced"
        thumbnail = "uploads/thumbnails/test.png"
        is_published = False
        
        print(f"Attempting to insert course: '{title}'...")
        try:
            # Clean up existing test course if present
            execute_query("DELETE FROM courses WHERE slug = %s", [slug])
            
            # Execute insert
            execute_query("""
                INSERT INTO courses (title, slug, description, difficulty, thumbnail, is_published, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """, [title, slug, description, difficulty, thumbnail, is_published])
            print("Insert completed successfully.")
            
            # Verify insert
            row = fetch_one("SELECT * FROM courses WHERE slug = %s", [slug])
            if row:
                print(f"SUCCESS: Course found in database. Title: '{row['title']}', Difficulty: '{row['difficulty']}'")
            else:
                print("ERROR: Course was not found after insertion.")
                
            # Clean up
            execute_query("DELETE FROM courses WHERE slug = %s", [slug])
            print("Cleanup completed successfully.")
            
        except Exception as e:
            print(f"ERROR: Course creation query failed. Details: {e}")

if __name__ == "__main__":
    test_course_creation()
