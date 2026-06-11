import os
import sys

# Reconfigure stdout for UTF-8 encoding on Windows to prevent emoji print crashes
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from admin_dashboard
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin_dashboard")))

from app import app, call_groq_with_fallback, fetch_one
import json
import re

def test_ai_lesson_generation():
    with app.app_context():
        # Get a course from DB
        course = fetch_one("SELECT id, title FROM courses LIMIT 1")
        if not course:
            print("No courses found in database to test with.")
            return
            
        course_id = course["id"]
        course_title = course["title"]
        topic = "Intro to Vector Embeddings"
        additional_context = "Explain semantic search using a Zomato search example (e.g., searching for 'something sweet' retrieves desserts)."
        next_day = 10
        
        print(f"Simulating lesson draft generation for:")
        print(f"- Course: {course_title} (ID: {course_id})")
        print(f"- Topic: {topic}")
        print(f"- Context: {additional_context}")
        
        system_prompt = """
You are an expert AI curriculum designer and content developer for Rohith Builds.
Your task is to generate a comprehensive, high-quality, and engaging educational lesson for a course.

ABOUT ROHITH BUILDS:
- Completely free learning platform (rohith-builds.onrender.com)
- Target audience: Developers and students learning Python, Backend, and AI systems.
- Brand style: Warm, professional, and practical. Example contexts utilize Indian developer references (like Zomato, IRCTC, cricket, Aadhaar) to build local relevance.

Your response MUST be a valid JSON object with the following keys:
1. "title": A short, engaging title for this specific lesson (e.g. "Vector Databases & Search").
2. "short_description": A 1-2 sentence summary of what the student will learn in this lesson.
3. "content_html": The complete HTML content of the lesson, formatted using only the specified HTML structure.
4. "xp_reward": Suggested integer XP reward for completing the lesson (typically 50).
5. "estimated_minutes": Suggested completion time in minutes (typically 10-15).

HTML STRUCTURE RULES:
- Wrap everything inside a single <div class="lesson-content-wrapper"> container.
- Use the following sections in order, using the specified class names:
  1. <h2 class="lesson-section-title">Why Should I Care?</h2>
     Followed by 1-2 paragraph blocks `<p class="lesson-text">...</p>` explaining the real-world value of this topic.
  2. <h2 class="lesson-section-title">Core Concept</h2>
     Followed by paragraphs `<p class="lesson-text">...</p>` defining the concept clearly. Include a styled note block if needed:
     `<div class="lesson-note"><b>Note:</b> ...</div>`
  3. <h2 class="lesson-section-title">How It Works</h2>
     Explain the technical workflow. Include code blocks with classes `<div class="lesson-code"><pre><code class="language-python">...</code></pre></div>`. Make sure the code is syntactically correct, minimal, and well-commented.
  4. <div class="lesson-challenge"><h3>Mini Challenge</h3><p class="lesson-text">...</p></div>
     A small hands-on task for the student to attempt themselves (e.g., modifying the code).
  5. <div class="lesson-takeaways"><h3>Key Takeaways</h3><ul><li>...</li></ul></div>
     A bulleted list of 3-4 key concepts to remember.

OUTPUT RULES:
- You must output ONLY the JSON object. Do not wrap the JSON in Markdown backticks (no ```json ... ```).
- Ensure the JSON is parseable and all strings/quotes are properly escaped. Do not include markdown code block formats around the JSON.
"""
        user_content = f"""
Course Title: {course_title}
Topic of the Lesson: {topic}
Additional Context/Instructions: {additional_context}
Next Lesson Day Number: Day {next_day}

Please generate the complete JSON lesson draft.
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        print("Calling Groq to generate lesson draft...")
        raw_draft = call_groq_with_fallback(messages, max_tokens=1800)
        
        # Clean markdown wrappers if returned
        cleaned = raw_draft.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z0-9]*\n", "", cleaned)
            cleaned = re.sub(r"\n```$", "", cleaned)
        cleaned = cleaned.strip()
        
        try:
            draft_data = json.loads(cleaned)
            print("\n--- SUCCESSFULLY GENERATED AND PARSED LESSON ---")
            print(f"Suggested Title: {draft_data.get('title')}")
            print(f"Suggested XP: {draft_data.get('xp_reward')}")
            print(f"Suggested Duration: {draft_data.get('estimated_minutes')} mins")
            print(f"Short Description: {draft_data.get('short_description')}")
            print("\nPreviewing first 300 characters of Content HTML:")
            print(draft_data.get("content_html", "")[:300] + "...")
            print("-------------------------------------------------\n")
            
            # Simple content structure validations
            html = draft_data.get("content_html", "")
            if "lesson-content-wrapper" in html and "Why Should I Care?" in html and "Core Concept" in html:
                print("SUCCESS: HTML structure validation passed.")
            else:
                print("WARNING: HTML structure did not contain all expected classes or section headers.")
                
        except Exception as err:
            print(f"ERROR: Failed to parse Groq response as JSON. Error: {err}")
            print("\nRaw Response received from Groq:")
            print(raw_draft)

if __name__ == "__main__":
    test_ai_lesson_generation()
