"""Resume Reviewer & ATS Score Checker module."""

import io
import json
import logging
import re
from typing import Any

from flask import Blueprint, render_template, request, flash, redirect, url_for
from pypdf import PdfReader

from gemini_helper import call_groq_with_fallback

resume_bp = Blueprint("resume", __name__, url_prefix="/resume")


# ──────────────────────────────────────────────────────────────
# ATS Scoring Constants
# ──────────────────────────────────────────────────────────────

SECTION_HEADINGS = [
    "education", "experience", "work experience", "professional experience",
    "skills", "technical skills", "projects", "certifications",
    "achievements", "awards", "summary", "objective", "internship",
    "internships", "training", "publications", "volunteer",
]

ACTION_VERBS = [
    "led", "built", "designed", "developed", "implemented", "created",
    "managed", "delivered", "optimized", "improved", "achieved",
    "launched", "engineered", "automated", "deployed", "integrated",
    "collaborated", "analyzed", "researched", "maintained", "reduced",
    "increased", "streamlined", "architected", "mentored", "spearheaded",
    "resolved", "configured", "orchestrated", "migrated", "refactored",
    "tested", "debugged", "contributed", "presented", "published",
]

TECH_KEYWORDS = [
    "python", "javascript", "java", "c++", "c#", "typescript", "go", "rust",
    "react", "angular", "vue", "node", "express", "flask", "django", "fastapi",
    "html", "css", "sql", "nosql", "mongodb", "postgresql", "mysql", "redis",
    "docker", "kubernetes", "aws", "azure", "gcp", "git", "github", "linux",
    "api", "rest", "graphql", "machine learning", "deep learning", "ai",
    "tensorflow", "pytorch", "pandas", "numpy", "scikit", "nlp",
    "agile", "scrum", "ci/cd", "jenkins", "terraform", "figma",
    "data structures", "algorithms", "oop", "microservices", "serverless",
]

COMMON_ERRORS = [
    "teh", "recieve", "seperate", "occured", "definately", "accomodate",
    "acheive", "achivement", "aquire", "calender", "collegue", "comittee",
    "concensus", "copywrite", "correspondance", "dependant", "develope",
    "embarass", "enviroment", "excellant", "foriegn", "goverment",
    "immediatly", "independant", "knowlege", "liason", "manouvre",
    "neccessary", "occassion", "occurence", "persistant", "priviledge",
    "profesional", "recomend", "refered", "responsibilty", "succesful",
]


# ──────────────────────────────────────────────────────────────
# ATS Scoring Engine (100% Rule-Based, Deterministic)
# ──────────────────────────────────────────────────────────────

def check_contact_info(text: str) -> dict[str, Any]:
    """Check for email, phone number, and LinkedIn URL. Max 15 points."""
    score = 0
    details = []

    # Email
    if re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text):
        score += 5
        details.append("✅ Email address found")
    else:
        details.append("❌ No email address detected")

    # Phone
    if re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text) or \
       re.search(r"\+91[\s-]?\d{5}[\s-]?\d{5}", text) or \
       re.search(r"\d{10}", text):
        score += 5
        details.append("✅ Phone number found")
    else:
        details.append("❌ No phone number detected")

    # LinkedIn
    if re.search(r"linkedin\.com/in/", text, re.IGNORECASE):
        score += 5
        details.append("✅ LinkedIn profile found")
    else:
        details.append("⚠️ No LinkedIn profile link — add it for recruiter trust")

    return {"name": "Contact Information", "score": score, "max": 15, "details": details}


def check_section_headings(text: str) -> dict[str, Any]:
    """Check for standard resume section headings. Max 15 points."""
    text_lower = text.lower()
    found = []
    missing_critical = []

    for heading in SECTION_HEADINGS:
        # Check if heading appears as a standalone word/line
        if re.search(rf"\b{re.escape(heading)}\b", text_lower):
            found.append(heading.title())

    score = 0
    details = []

    # Critical sections
    critical = {"education", "experience", "skills", "projects"}
    critical_found = {h for h in found if h.lower() in critical or
                      any(c in h.lower() for c in critical)}

    score = min(15, len(found) * 3)

    if len(critical_found) >= 3:
        details.append(f"✅ {len(found)} standard sections found: {', '.join(found[:6])}")
    elif len(found) >= 2:
        details.append(f"⚠️ {len(found)} sections found, but consider adding more standard headings")
    else:
        details.append("❌ Few recognizable section headings — ATS may fail to parse your resume")

    # Check for missing critical sections
    for section in ["Education", "Experience", "Skills"]:
        if not any(section.lower() in f.lower() for f in found):
            missing_critical.append(section)

    if missing_critical:
        details.append(f"❌ Missing critical sections: {', '.join(missing_critical)}")

    return {"name": "Section Headings", "score": score, "max": 15, "details": details}


def check_impact_statements(text: str) -> dict[str, Any]:
    """Check for measurable impact (numbers, percentages, metrics). Max 15 points."""
    # Find quantifiable achievements
    metrics = re.findall(r"\d+[%+]|\$\d+|\d+\s*(?:users|customers|clients|projects|teams|members|applications|requests|endpoints|tests)", text, re.IGNORECASE)
    percentages = re.findall(r"\d+\s*%", text)
    numbers_in_context = re.findall(r"(?:reduced|increased|improved|grew|saved|managed|handled|processed|served|built|deployed|completed)\s+\w*\s*\d+", text, re.IGNORECASE)

    total_metrics = len(metrics) + len(percentages) + len(numbers_in_context)

    if total_metrics >= 5:
        score = 15
        details = [f"✅ Excellent! {total_metrics} measurable impact statements found"]
    elif total_metrics >= 3:
        score = 10
        details = [f"⚠️ {total_metrics} metrics found — aim for 5+ quantified achievements"]
    elif total_metrics >= 1:
        score = 5
        details = [f"⚠️ Only {total_metrics} metric(s) found — add numbers like '30% improvement' or 'served 500+ users'"]
    else:
        score = 0
        details = ["❌ No measurable impact found — add metrics like 'Reduced load time by 40%'"]

    return {"name": "Measurable Impact", "score": score, "max": 15, "details": details}


def check_action_verbs(text: str) -> dict[str, Any]:
    """Check for strong action verbs. Max 10 points."""
    text_lower = text.lower()
    found_verbs = [v for v in ACTION_VERBS if re.search(rf"\b{v}\b", text_lower)]

    if len(found_verbs) >= 6:
        score = 10
        details = [f"✅ {len(found_verbs)} strong action verbs used: {', '.join(found_verbs[:5])}..."]
    elif len(found_verbs) >= 3:
        score = 7
        details = [f"⚠️ {len(found_verbs)} action verbs found — use more power words like 'Architected', 'Spearheaded', 'Optimized'"]
    elif len(found_verbs) >= 1:
        score = 4
        details = [f"⚠️ Only {len(found_verbs)} action verb(s) — replace 'Worked on' with 'Built', 'Designed', 'Deployed'"]
    else:
        score = 0
        details = ["❌ No action verbs detected — start bullet points with verbs like 'Led', 'Built', 'Implemented'"]

    return {"name": "Action Verbs", "score": score, "max": 10, "details": details}


def check_length(text: str) -> dict[str, Any]:
    """Check if resume is optimal length. Max 10 points."""
    word_count = len(text.split())

    if 300 <= word_count <= 1000:
        score = 10
        details = [f"✅ Good length: {word_count} words (ideal range: 300-1000)"]
    elif 200 <= word_count < 300:
        score = 6
        details = [f"⚠️ {word_count} words — a bit short, consider expanding your experience and projects"]
    elif 1000 < word_count <= 1500:
        score = 7
        details = [f"⚠️ {word_count} words — slightly long, keep it concise for a 1-page resume"]
    elif word_count > 1500:
        score = 4
        details = [f"⚠️ {word_count} words — too long for entry-level. Aim for 1 page (300-800 words)"]
    else:
        score = 2
        details = [f"❌ Only {word_count} words — too short. Add more detail about projects and experience"]

    return {"name": "Resume Length", "score": score, "max": 10, "details": details}


def check_spelling(text: str) -> dict[str, Any]:
    """Check for common spelling errors. Max 10 points."""
    text_lower = text.lower()
    found_errors = [err for err in COMMON_ERRORS if err in text_lower]

    if len(found_errors) == 0:
        score = 10
        details = ["✅ No common spelling errors detected"]
    elif len(found_errors) <= 2:
        score = 6
        details = [f"⚠️ {len(found_errors)} possible spelling issue(s): {', '.join(found_errors)}"]
    else:
        score = 2
        details = [f"❌ {len(found_errors)} spelling errors found: {', '.join(found_errors[:5])}"]

    return {"name": "Spelling & Grammar", "score": score, "max": 10, "details": details}


def check_tech_keywords(text: str) -> dict[str, Any]:
    """Check for technical skills keywords. Max 15 points."""
    text_lower = text.lower()
    found_keywords = [kw for kw in TECH_KEYWORDS if re.search(rf"\b{re.escape(kw)}\b", text_lower)]

    if len(found_keywords) >= 8:
        score = 15
        details = [f"✅ {len(found_keywords)} technical keywords found: {', '.join(found_keywords[:8])}..."]
    elif len(found_keywords) >= 5:
        score = 10
        details = [f"⚠️ {len(found_keywords)} keywords — add more specific technologies to match job descriptions"]
    elif len(found_keywords) >= 2:
        score = 5
        details = [f"⚠️ Only {len(found_keywords)} tech keywords — ATS filters by keywords, add more"]
    else:
        score = 0
        details = ["❌ Very few technical keywords — ATS will likely filter this resume out"]

    return {"name": "Technical Keywords", "score": score, "max": 15, "details": details}


def check_formatting(text: str) -> dict[str, Any]:
    """Check for clean formatting (no special chars, tables). Max 10 points."""
    score = 10
    details = []
    issues = []

    # Check for excessive special characters
    special_chars = re.findall(r"[★☆●◆▪▸►◄▬═╔╗╚╝║│─┼┌┐└┘├┤┬┴]", text)
    if len(special_chars) > 3:
        score -= 3
        issues.append("special characters/symbols that ATS cannot parse")

    # Check for table-like formatting
    if re.search(r"\|.*\|.*\|", text):
        score -= 3
        issues.append("table-like formatting (use plain text instead)")

    # Check for image references
    if re.search(r"\.(jpg|jpeg|png|gif|svg|bmp)", text, re.IGNORECASE):
        score -= 2
        issues.append("image references (ATS cannot read images)")

    # Check for excessive blank lines
    blank_lines = len(re.findall(r"\n\s*\n\s*\n", text))
    if blank_lines > 5:
        score -= 2
        issues.append("excessive blank lines")

    score = max(0, score)

    if not issues:
        details.append("✅ Clean formatting — ATS-compatible")
    else:
        details.append(f"⚠️ Formatting issues found: {', '.join(issues)}")

    return {"name": "Clean Formatting", "score": score, "max": 10, "details": details}


def calculate_ats_score(text: str) -> dict[str, Any]:
    """Run all 8 ATS checks and return combined score."""
    checks = [
        check_contact_info(text),
        check_section_headings(text),
        check_impact_statements(text),
        check_action_verbs(text),
        check_length(text),
        check_spelling(text),
        check_tech_keywords(text),
        check_formatting(text),
    ]

    total_score = sum(c["score"] for c in checks)
    max_score = sum(c["max"] for c in checks)

    # Score color
    if total_score >= 70:
        grade = "Excellent"
        color = "#34d399"
    elif total_score >= 50:
        grade = "Good"
        color = "#fbbf24"
    elif total_score >= 30:
        grade = "Needs Work"
        color = "#fb923c"
    else:
        grade = "Poor"
        color = "#f87171"

    return {
        "total_score": total_score,
        "max_score": max_score,
        "grade": grade,
        "color": color,
        "checks": checks,
    }


# ──────────────────────────────────────────────────────────────
# AI Feedback (Groq-Powered)
# ──────────────────────────────────────────────────────────────

def get_ai_feedback(text: str, ats_score: int) -> dict[str, Any]:
    """Get structured AI feedback on the resume using Groq."""
    system_prompt = """You are an expert tech recruiter and resume coach specializing in Indian tech industry placements.
You will receive a candidate's resume text and their ATS score.

Analyze the resume and return a JSON object with exactly these keys:
1. "strengths": An array of exactly 3 strings — the strongest points about this resume.
2. "improvements": An array of exactly 5 strings — specific, actionable improvement suggestions.
3. "missing_keywords": An array of 5-8 strings — technical keywords that are commonly expected but missing.
4. "rewritten_bullet": A string — take the weakest bullet point from the resume and rewrite it with metrics and action verbs as an example.
5. "overall_summary": A 2-sentence summary of the resume's quality.

Output ONLY the raw JSON object. No markdown, no code blocks, no extra text."""

    user_prompt = f"ATS Score: {ats_score}/100\n\nResume Text:\n{text[:4000]}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    try:
        ai_output = call_groq_with_fallback(messages, max_tokens=800)

        # Extract JSON robustly
        ai_clean = ai_output.strip()
        first_brace = ai_clean.find("{")
        last_brace = ai_clean.rfind("}")
        if first_brace != -1 and last_brace != -1:
            ai_clean = ai_clean[first_brace:last_brace + 1]

        return json.loads(ai_clean, strict=False)
    except Exception as e:
        logging.error(f"AI resume feedback failed: {e}")
        return {
            "strengths": ["Unable to analyze at this time"],
            "improvements": ["Please try again in a moment"],
            "missing_keywords": [],
            "rewritten_bullet": "",
            "overall_summary": "AI analysis is temporarily unavailable. Your ATS score above is still accurate.",
        }


# ──────────────────────────────────────────────────────────────
# PDF Text Extraction
# ──────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_storage) -> str:
    """Extract text from uploaded PDF file."""
    try:
        reader = PdfReader(io.BytesIO(file_storage.read()))
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        return "\n".join(text_parts).strip()
    except Exception as e:
        logging.error(f"PDF extraction failed: {e}")
        return ""


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────

@resume_bp.route("/", methods=["GET"])
def resume_landing() -> str:
    """Render the resume reviewer landing page."""
    return render_template("resume.html")


@resume_bp.route("/", methods=["POST"])
def resume_analyze() -> str:
    """Process resume text or PDF and return ATS score + AI feedback."""
    resume_text = ""

    # Check for PDF upload first
    uploaded_file = request.files.get("resume_pdf")
    if uploaded_file and uploaded_file.filename and uploaded_file.filename.lower().endswith(".pdf"):
        resume_text = extract_text_from_pdf(uploaded_file)
        if not resume_text:
            flash("Could not extract text from the PDF. Please paste your resume text instead.", "error")
            return redirect(url_for("resume.resume_landing"))
    else:
        # Fall back to pasted text
        resume_text = request.form.get("resume_text", "").strip()

    if not resume_text or len(resume_text) < 50:
        flash("Please paste your resume text (minimum 50 characters) or upload a PDF.", "error")
        return redirect(url_for("resume.resume_landing"))

    # 1. Calculate deterministic ATS score
    ats_result = calculate_ats_score(resume_text)

    # 2. Get AI-powered feedback
    ai_feedback = get_ai_feedback(resume_text, ats_result["total_score"])

    return render_template(
        "resume_results.html",
        ats=ats_result,
        feedback=ai_feedback,
        resume_text=resume_text[:200] + "..." if len(resume_text) > 200 else resume_text,
        word_count=len(resume_text.split()),
    )
