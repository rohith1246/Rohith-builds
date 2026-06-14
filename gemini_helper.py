import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv(override=True)

ROHI_SYSTEM_PROMPT = """
You are Rohi, the AI tutor for Rohith Builds.
You are friendly, helpful, and speak like a 
senior Indian developer mentoring a junior.

ABOUT ROHITH BUILDS PLATFORM:
- Free AI-powered learning platform for 
  Indian developers
- URL: rohith-builds.onrender.com
- Built by Rohith Vuppula (@rohith_builds)

WHAT THE PLATFORM HAS:
1. COURSES:
   - 100 Days Python to AI Master
     (Day 1 to Day 100, structured lessons)
   - 7-Day AI Agent Course
     (Build real AI agent with Python + Groq)

2. PROMPT VAULT:
   - 220+ curated AI prompts for developers
   - Categories: coding, debugging, system 
     design, career, productivity
   - Users can like, copy, favorite prompts

3. JOBS BOARD (/jobs):
   - 53+ curated junior developer jobs
   - Auto-scraped from LinkedIn, Naukri, Indeed
   - Filters: Python, Backend, AI, Frontend,
     Fullstack, Remote/Hybrid/Onsite
   - Updated daily
   - Filter by graduation batch: 
     2025, 2026, 2027, Experience

4. IMPROVE PROMPT TOOL (/improve):
   - Paste any AI prompt
   - Get optimized version instantly
   - Free, no signup needed

5. AI JOB AGENT:
   - Upload your resume
   - Set target roles and salary
   - AI matches you to jobs automatically
   - Drafts personalized cover letters

6. ROHI (YOU):
   - AI tutor available 24/7
   - Powered by Groq LLM
   - Answers questions about lessons
   - Helps with Python, AI, Backend concepts

WHAT YOU CAN HELP WITH:
- Explain any lesson concept
- Answer Python and AI questions
- Help debug code
- Guide students to right course/feature
- Explain platform features
- Career advice for Indian developers
- Recommend which lesson to start with

PLATFORM NAVIGATION GUIDE:
- Start learning: /learn
- Browse jobs: /jobs  
- Explore prompts: /vault
- Improve a prompt: /improve
- Your dashboard: /dashboard
- AI Agent: /jobs/agent

TEACHING STYLE:
- Use Indian examples: Zomato, Swiggy, 
  IRCTC, Aadhaar, cricket, IPL
- Be conversational, not robotic
- Encourage students when they struggle
- Always connect concepts to real projects
- Keep answers concise (3-5 lines max)
  unless student asks for more detail

CURRENT LESSON CONTEXT:
{lesson_context}

CONVERSATION HISTORY:
{history}

Remember: You are not just a lesson tutor.
You are the guide for the entire 
Rohith Builds platform and community.
"""

def call_groq_with_fallback(messages, max_tokens=300):
    key_primary = os.getenv("GROQ_API_KEY", "").strip()
    key_secondary = os.getenv("GROQ_API_KEY_SECONDARY", "").strip()

    # Fallback chain:
    # 1. Primary key + llama-3.3-70b-versatile
    # 2. Primary key + llama-3.1-8b-instant
    # 3. Secondary key + llama-3.3-70b-versatile
    # 4. Secondary key + llama-3.1-8b-instant
    # 5. Primary key + mixtral-8x7b-32768
    # 6. Secondary key + mixtral-8x7b-32768
    steps = [
        (key_primary, "llama-3.3-70b-versatile"),
        (key_primary, "llama-3.1-8b-instant"),
        (key_secondary, "llama-3.3-70b-versatile"),
        (key_secondary, "llama-3.1-8b-instant"),
        (key_primary, "mixtral-8x7b-32768"),
        (key_secondary, "mixtral-8x7b-32768"),
    ]

    valid_steps = [(k, m) for k, m in steps if k]
    if not valid_steps:
        return "Rohi is taking a short break. Please try again in a moment."

    last_err = None
    for key, model in valid_steps:
        try:
            client = Groq(api_key=key, timeout=5.0)
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=0.7,
                max_tokens=max_tokens
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            last_err = e
            print(f"[Fallback] Groq model {model} failed. Trying next option. Error: {e}")
            continue

    print(f"[Fallback] All Groq models and keys failed. Last error: {last_err}")
    return "Rohi is taking a short break. Please try again in a moment."

def improve_prompt(user_prompt):
    system_prompt = """
    You are an expert AI prompt optimizer.

    Rewrite the user's prompt into a clearer,
    more detailed, structured,
    high-performing AI prompt.

    Keep the intent same.
    Make it more specific and useful.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    return call_groq_with_fallback(messages, max_tokens=1000)

def rohi_chat(message, lesson_context="", history=None):
    history_str = ""
    if history:
        for h in history:
            role = "Student" if h["role"] == "user" else "Rohi"
            history_str += f"{role}: {h['content']}\n"

    system_prompt = ROHI_SYSTEM_PROMPT.format(
        lesson_context=lesson_context or "",
        history=history_str
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    return call_groq_with_fallback(messages, max_tokens=200)