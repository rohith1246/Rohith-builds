import os
import sys

# Reconfigure stdout for UTF-8 encoding on Windows to prevent emoji print crashes
if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure we can import from admin_dashboard
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "admin_dashboard")))

from app import app, draft_reddit_reply

def test_draft():
    title = "Best resources to learn Python and LLMs as an absolute beginner?"
    text = "Hi everyone, I am from India and want to learn Python from scratch and then move on to building AI applications and LLMs. I have no programming background. What are the best free resources available that explain concepts simply?"
    subreddit = "learnpython"
    
    print("Generating draft reply for Reddit...")
    reply = draft_reddit_reply(title, text, subreddit)
    print("\n--- GENERATED REDDIT DRAFT ---")
    print(reply)
    print("------------------------------\n")

if __name__ == "__main__":
    test_draft()
