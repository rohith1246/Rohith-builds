import io
import json
import logging
import os
import re
import requests
import pypdf
from groq import Groq
from google import genai
from google.genai import types

SYSTEM_PROMPT = """
You are a witty, blunt startup founder reviewing a developer's portfolio to decide if they are "founder-ready". 
A founder-ready engineer can ship fast, write clear documentation (READMEs), maintain active repositories, and demonstrate practical product ownership.

Act as a seasoned, direct, and witty startup mentor/founder. Be blunt, conversational, and direct, but constructive. Do not be cruel or make them feel hopeless. Mix sharp developer humor with startup jargon (e.g., "MVP", "tech debt", "shipping to prod", "VC funding", "tutorial hell"). Reference specific repository names, README presence, languages, last commit dates, and resume details they provided.

Analyze the user's GitHub repositories and their optional resume.
You MUST return a JSON object with the following fields:
1. "score": An integer from 0 to 100 representing their founder-readiness.
2. "punchline": A one-line witty, punchy, founder-style critique summarizing their profile.
3. "bullet_points": A list of exactly 3 to 4 specific, actionable feedback items. Each point must feel earned and refer to their actual repositories, README status, primary languages, or resume highlights. Do not make generic recommendations.

Format your output STRICTLY as a JSON object, with no markdown code blocks (like ```json), no formatting wrapper, and no conversational text before or after the JSON.

Example JSON output format:
{
  "score": 68,
  "punchline": "Your code has potential, but your repositories look like a tech-debt graveyard.",
  "bullet_points": [
    "Add a README to 'react-chat-app'. Undocumented code is just a secret folder. Let builders see what you built.",
    "Your commit history on 'python-helper' shows zero activity since 2024. Founders want shipping code, not archeology projects.",
    "Your resume lists 'REST APIs' but you don't have a single backend repository showing API architecture. Build and show a FastAPI service."
  ]
}
"""

def extract_resume_text(file_storage) -> str:
    """Extract text content from an uploaded FileStorage object (PDF or TXT)."""
    filename = file_storage.filename.lower()
    file_bytes = file_storage.read()
    
    if not file_bytes:
        return ""

    if filename.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in reader.pages:
                text += page.extract_text() or ""
            return text.strip()
        except Exception as e:
            logging.error(f"[Grader] Error parsing PDF resume: {e}")
            raise ValueError(f"Could not parse PDF file: {str(e)}")
    elif filename.endswith(".txt"):
        try:
            return file_bytes.decode("utf-8", errors="ignore").strip()
        except Exception as e:
            logging.error(f"[Grader] Error parsing TXT resume: {e}")
            raise ValueError(f"Could not decode text file: {str(e)}")
    else:
        raise ValueError("Unsupported file format. Only PDF and TXT files are accepted.")


def fetch_github_data(username: str) -> dict:
    """
    Fetch public repositories of the user and check README status.
    Returns a dict with repositories details.
    """
    token = os.getenv("GITHUB_TOKEN", "").strip()
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "RohithBuilds-Grader"
    }
    if token:
        headers["Authorization"] = f"token {token}"

    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    try:
        response = requests.get(repos_url, headers=headers, timeout=10)
    except Exception as e:
        logging.error(f"[Grader] Network error fetching GitHub data for {username}: {e}")
        raise RuntimeError("Failed to connect to GitHub. Please try again later.")

    if response.status_code == 404:
        raise ValueError(f"GitHub user '{username}' not found.")
    elif response.status_code != 200:
        logging.error(f"[Grader] GitHub API returned status {response.status_code}: {response.text}")
        raise RuntimeError(f"GitHub API error (Status: {response.status_code}).")

    repos = response.json()
    if not isinstance(repos, list):
        raise RuntimeError("Unexpected response format from GitHub API.")

    # Fetch user details to get followers
    user_url = f"https://api.github.com/users/{username}"
    followers = 0
    try:
        user_res = requests.get(user_url, headers=headers, timeout=10)
        if user_res.status_code == 200:
            user_data = user_res.json()
            followers = user_data.get("followers", 0)
    except Exception as e:
        logging.warning(f"[Grader] Failed to fetch user profile followers for {username}: {e}")

    total_stars = sum(r.get("stargazers_count", 0) for r in repos)

    processed_repos = []
    for r in repos:
        processed_repos.append({
            "name": r.get("name", ""),
            "language": r.get("language") or "Unknown",
            "stars": r.get("stargazers_count", 0),
            "last_commit": r.get("pushed_at") or r.get("updated_at") or "",
            "description": r.get("description", "")
        })

    # Sort repos: star count descending, then last commit date descending
    processed_repos.sort(key=lambda x: (x["stars"], x["last_commit"]), reverse=True)

    # Check README status for top 8 repositories to prevent rate limiting
    top_repos = processed_repos[:8]
    for r in top_repos:
        repo_name = r["name"]
        readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"
        try:
            readme_res = requests.head(readme_url, headers=headers, timeout=5)
            r["has_readme"] = (readme_res.status_code == 200)
        except Exception:
            r["has_readme"] = False

    # For the remaining repos, assume has_readme is False
    for r in processed_repos[8:]:
        r["has_readme"] = False

    return {
        "username": username,
        "repos": processed_repos[:15],  # Send top 15 to the AI
        "total_repos": len(repos),
        "followers": followers,
        "stars": total_stars
    }


def evaluate_portfolio(github_data: dict, resume_text: str | None) -> dict:
    """
    Sends GitHub data and resume text to Groq (with Gemini fallback) to grade the portfolio.
    Returns a parsed JSON dict.
    """
    # Build prompt input format
    repos_summary = []
    for r in github_data["repos"]:
        repos_summary.append(
            f"- Repo: {r['name']} | Language: {r['language']} | Stars: {r['stars']} | Last Push: {r['last_commit'][:10]} | Has README: {r['has_readme']}"
        )
    repos_str = "\n".join(repos_summary)

    user_prompt = f"GitHub Username: {github_data['username']}\n"
    user_prompt += f"Total Public Repositories: {github_data['total_repos']}\n"
    user_prompt += f"Repositories Sample:\n{repos_str}\n\n"
    if resume_text:
        user_prompt += f"Candidate Resume Text:\n{resume_text}\n"
    else:
        user_prompt += "No Resume provided.\n"

    # Try Groq first (Primary)
    groq_success = False
    raw_response = ""

    key_primary = os.getenv("GROQ_API_KEY", "").strip()
    key_secondary = os.getenv("GROQ_API_KEY_SECONDARY", "").strip()
    
    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    
    steps = []
    if key_primary:
        steps.extend([(key_primary, m) for m in models])
    if key_secondary:
        steps.extend([(key_secondary, m) for m in models])

    for key, model in steps:
        try:
            logging.info(f"[Grader] Attempting Groq model {model}...")
            client = Groq(api_key=key, timeout=10.0)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                model=model,
                response_format={"type": "json_object"},
                temperature=0.7
            )
            raw_response = chat_completion.choices[0].message.content.strip()
            if raw_response:
                groq_success = True
                logging.info(f"[Grader] Groq model {model} succeeded.")
                break
        except Exception as e:
            logging.warning(f"[Grader] Groq model {model} failed. Error: {e}")
            continue

    # Fallback to Gemini if Groq failed
    if not groq_success:
        logging.info("[Grader] Groq failed. Falling back to Gemini...")
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not gemini_key:
            raise RuntimeError("Both Groq failed and GEMINI_API_KEY is not configured.")
        
        try:
            # Using new Google GenAI SDK
            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    temperature=0.7,
                )
            )
            raw_response = response.text.strip()
            logging.info("[Grader] Gemini generation succeeded.")
        except Exception as e:
            logging.error(f"[Grader] Gemini fallback also failed. Error: {e}")
            raise RuntimeError(f"AI evaluation failed. (Gemini error: {e})")

    # Clean raw_response if it contains markdown codeblocks
    if raw_response.startswith("```"):
        raw_response = re.sub(r'^```(?:json)?\n', '', raw_response)
        raw_response = re.sub(r'\n```$', '', raw_response)
    raw_response = raw_response.strip()

    # Parse and validate JSON
    try:
        data = json.loads(raw_response)
        # Verify required fields
        if "score" not in data or "punchline" not in data or "bullet_points" not in data:
            raise ValueError("Missing required fields in LLM response.")
        
        # Ensure bullet points is a list
        if not isinstance(data["bullet_points"], list):
            data["bullet_points"] = [str(data["bullet_points"])]
        
        # Ensure score is an int
        data["score"] = int(data["score"])
        return data
    except Exception as e:
        logging.error(f"[Grader] Failed to parse JSON from AI response: {raw_response}. Error: {e}")
        return {
            "score": 65,
            "punchline": "Your code is out there, but our parser had a stroke reading the AI's review.",
            "bullet_points": [
                "Your portfolio was successfully analyzed, but the AI response was malformed.",
                "Ensure your repositories have clear descriptions and README files.",
                "Keep shipping and building clean code!"
            ]
        }
