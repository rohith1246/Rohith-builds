import os
import sys
from dotenv import load_dotenv

# Reconfigure stdout for UTF-8 encoding on Windows to prevent emoji print crashes
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from admin_dashboard
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin_dashboard")))

from app import app, fetch_one, call_groq_with_fallback

def test_nudge_draft():
    with app.app_context():
        # Get a user id to draft for
        student = fetch_one("SELECT id, username FROM users LIMIT 1")
        if not student:
            print("No students found in DB to test with.")
            return
            
        print(f"Testing draft generation for student: {student['username']} (ID: {student['id']})")
        
        # Test calling the retention/draft route function logic
        user_id = student['id']
        student_data = fetch_one("""
            SELECT u.username, u.email, cd.day_number, cd.title AS lesson_title, c.title AS course_title
            FROM users u
            LEFT JOIN (
                SELECT user_id, MAX(completed_at) AS max_completed_at
                FROM lesson_progress
                WHERE completed = TRUE
                GROUP BY user_id
            ) latest_overall ON latest_overall.user_id = u.id
            LEFT JOIN lesson_progress lp ON lp.user_id = u.id AND lp.completed_at = latest_overall.max_completed_at AND lp.completed = TRUE
            LEFT JOIN course_days cd ON cd.id = lp.course_day_id
            LEFT JOIN courses c ON c.id = cd.course_id
            WHERE u.id = %s
        """, [user_id])
        
        if not student_data or not student_data.get("course_title"):
            student_data = fetch_one("""
                SELECT u.username, u.email, 0 AS day_number, 'None' AS lesson_title, c.title AS course_title
                FROM users u
                JOIN course_enrollments ce ON ce.user_id = u.id
                JOIN courses c ON c.id = ce.course_id
                WHERE u.id = %s
                ORDER BY ce.enrolled_at DESC
                LIMIT 1
            """, [user_id])
            
        if not student_data:
            print("Student not enrolled in any courses.")
            return

        username = student_data["username"]
        day_number = student_data.get("day_number") or 0
        lesson_title = student_data.get("lesson_title") or "None (Signed Up)"
        course_title = student_data.get("course_title") or "their course"
        next_day = day_number + 1 if day_number > 0 else 1

        system_prompt = f"""
You are Rohith Vuppula, the founder of Rohith Builds (rohith-builds.onrender.com).
Write a short, friendly, personalized email check-in to a student named {username} who has been inactive on the platform.

CONTEXT:
- Student name: {username}
- Last Completed Lesson: {("Day " + str(day_number) + " - " + lesson_title) if day_number > 0 else "None (Signed Up)"}
- Platform: Rohith Builds (rohith-builds.onrender.com)

YOUR GOAL:
Write a message that:
1. Sounds warm, casual, and supportive. Like a peer checking in.
2. Directly mentions {("their last completed lesson: " + lesson_title) if day_number > 0 else "that they signed up recently"} and asks if they got stuck.
3. Offers help: Mention they can reply directly to this email if they need a hand with setup, code, or anything else.
4. Encourage them to take the next step (Day {next_day}).
5. Always refer to the platform generally as 'Rohith Builds' or 'rohith-builds.onrender.com' (e.g., 'checking in on your learning journey on Rohith Builds') instead of mentioning any specific course name, as the website has multiple different courses. Frame their progress under the general platform name 'Rohith Builds'.
6. Include a clickable HTML link to the website like: <a href="https://rohith-builds.onrender.com">rohith-builds.onrender.com</a>. Make sure it is a proper HTML link in the email body so they can click it.
7. Keep it under 100 words. Start directly with the message content.
8. Do NOT include any placeholders, subject lines, or greetings like "Hi {username}," as the template handle this.
9. End with a friendly sign-off like:
"Let me know if you need any help!

Best,
Rohith"
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Draft the email check-in for {username}."}
        ]
        
        print("Calling Groq...")
        draft = call_groq_with_fallback(messages, max_tokens=200)
        print("\n--- GENERATED DRAFT ---")
        print(draft)
        print("-----------------------\n")
        
        if "rohith-builds.onrender.com" in draft and "<a href=" in draft:
            print("SUCCESS: Clickable link is present in the draft.")
        else:
            print("WARNING: Clickable link or domain not found or formatted incorrectly in the draft.")

if __name__ == "__main__":
    test_nudge_draft()
