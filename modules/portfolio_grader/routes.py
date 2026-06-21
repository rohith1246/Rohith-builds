from datetime import datetime
import logging
from flask import jsonify, render_template, request, Response, url_for
from models import db, PortfolioGrade
from extensions import csrf
from . import portfolio_grader_bp
from .grader_helper import fetch_github_data, evaluate_portfolio, extract_resume_text

@portfolio_grader_bp.route("/tools/portfolio-grader", methods=["GET"])
def grader_page() -> str:
    """Render the main Portfolio Grader form page."""
    return render_template("portfolio_grader.html")


@portfolio_grader_bp.route("/tools/portfolio-grader/grade", methods=["POST"])
@csrf.exempt  # Exempt from CSRF for API ease, or standard form can use AJAX. Let's make it robust
def grade_portfolio() -> Response:
    """Handle portfolio grading requests. Returns JSON result."""
    username = request.form.get("username", "").strip()
    if not username:
        return jsonify({"success": False, "message": "GitHub username is required"}), 400

    normalized_username = username.lower()

    # Check database cache (4-hour duration checked via .is_expired())
    try:
        cached = PortfolioGrade.query.filter_by(username=normalized_username).first()
        if cached and not cached.is_expired():
            share_url = url_for(
                "portfolio_grader.share_page",
                username=normalized_username,
                _external=True
            )
            return jsonify({
                "success": True,
                "score": cached.score,
                "punchline": cached.punchline,
                "bullet_points": cached.bullet_points,
                "share_url": share_url,
                "cached": True
            })
    except Exception as e:
        logging.error(f"[Grader] Error reading from cache database: {e}")
        # Continue to fetch fresh if cache read fails for some reason

    # Parse resume if uploaded
    resume_text = None
    if "resume" in request.files:
        resume_file = request.files["resume"]
        if resume_file and resume_file.filename != "":
            try:
                resume_text = extract_resume_text(resume_file)
            except ValueError as ve:
                return jsonify({"success": False, "message": str(ve)}), 400
            except Exception as e:
                logging.error(f"[Grader] Resume parsing error: {e}")
                return jsonify({"success": False, "message": "Failed to parse resume file."}), 500

    # Fetch GitHub details
    try:
        github_data = fetch_github_data(normalized_username)
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 404
    except Exception as e:
        logging.error(f"[Grader] GitHub fetch error for {normalized_username}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    # Evaluate portfolio via LLM (Groq with Gemini fallback)
    try:
        grade_result = evaluate_portfolio(github_data, resume_text)
    except Exception as e:
        logging.error(f"[Grader] LLM evaluation error for {normalized_username}: {e}")
        return jsonify({"success": False, "message": str(e)}), 500

    # Update or insert cache record
    try:
        cached = PortfolioGrade.query.filter_by(username=normalized_username).first()
        if cached:
            cached.score = grade_result["score"]
            cached.punchline = grade_result["punchline"]
            cached.bullet_points = grade_result["bullet_points"]
            cached.created_at = datetime.utcnow()
        else:
            new_grade = PortfolioGrade(
                username=normalized_username,
                score=grade_result["score"],
                punchline=grade_result["punchline"],
                bullet_points=grade_result["bullet_points"]
            )
            db.session.add(new_grade)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logging.error(f"[Grader] Error saving results to cache database: {e}")
        # Return success anyway as the calculation succeeded

    share_url = url_for(
        "portfolio_grader.share_page",
        username=normalized_username,
        _external=True
    )

    return jsonify({
        "success": True,
        "score": grade_result["score"],
        "punchline": grade_result["punchline"],
        "bullet_points": grade_result["bullet_points"],
        "share_url": share_url,
        "cached": False
    })


@portfolio_grader_bp.route("/tools/portfolio-grader/share/<username>", methods=["GET"])
def share_page(username: str) -> str:
    """Render the public shareable card page for a graded user."""
    normalized_username = username.strip().lower()
    grade = PortfolioGrade.query.filter_by(username=normalized_username).first()
    
    if not grade:
        # Redirect to the grader form if the username hasn't been graded yet
        return render_template(
            "portfolio_grader_share.html",
            error=f"No portfolio grade found for @{username}. Enter their username below to grade it!"
        )

    share_url = url_for(
        "portfolio_grader.share_page",
        username=normalized_username,
        _external=True
    )
    
    # Twitter & LinkedIn text templates
    tweet_text = f"Founder-Ready Score: {grade.score}% 🚀 \"{grade.punchline}\" Check your GitHub grade on Rohith Builds!"
    
    return render_template(
        "portfolio_grader_share.html",
        grade=grade,
        share_url=share_url,
        tweet_text=tweet_text
    )
