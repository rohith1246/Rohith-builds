from datetime import datetime
import logging
from flask import jsonify, render_template, request, Response, url_for, current_app
from flask_login import login_required, current_user
from models import db, PortfolioGrade, TrackedPortfolio, PortfolioHistory
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

        # Update history if tracked by any user
        is_tracked = TrackedPortfolio.query.filter_by(username=normalized_username).first() is not None
        if is_tracked:
            # Check if there is already a history record for today (UTC)
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing_today = PortfolioHistory.query.filter(
                PortfolioHistory.username == normalized_username,
                PortfolioHistory.created_at >= today_start
            ).first()
            if not existing_today:
                new_history = PortfolioHistory(
                    username=normalized_username,
                    score=grade_result["score"],
                    stars=github_data.get("stars", 0),
                    followers=github_data.get("followers", 0),
                    public_repos=github_data.get("total_repos", 0)
                )
                db.session.add(new_history)
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


@portfolio_grader_bp.route("/tools/portfolio-grader/tracker", methods=["GET"])
@login_required
def tracker_page() -> str:
    """Render the user's tracked portfolio growth dashboard."""
    # Find any portfolios tracked by this user
    tracked = TrackedPortfolio.query.filter_by(user_id=current_user.id).first()
    
    if not tracked:
        # User has no tracked portfolios yet
        return render_template(
            "portfolio_grader_tracker.html",
            tracked_profile=None,
            history_data=None
        )
    
    # Load history points to plot
    history = PortfolioHistory.query.filter_by(username=tracked.username).order_by(PortfolioHistory.created_at.asc()).all()
    latest_grade = PortfolioGrade.query.filter_by(username=tracked.username).first()
    
    # Prepare chart metrics JSON for Chart.js
    chart_data = {
        "dates": [h.created_at.strftime("%b %d") for h in history],
        "scores": [h.score for h in history],
        "stars": [h.stars for h in history],
        "followers": [h.followers for h in history],
        "repos": [h.public_repos for h in history]
    }
    
    # Generate contextual growth advice based on their current score
    suggestions = []
    if latest_grade:
        score = latest_grade.score
        if score < 50:
            suggestions = [
                "⚠️ Your repository documentation is severely lacking. Every project must have a clear README detailing what it is and how to run it.",
                "⚠️ Clear out old, inactive forks or tutorial repository placeholders that clutter your profile.",
                "⚠️ Add a working link or a video demo to your top repositories so founders can immediately see your features."
            ]
        elif score < 75:
            suggestions = [
                "💡 Write cleaner READMEs with clear setup instructions and system design architecture diagrams.",
                "💡 Work on stack diversity: introduce backend testing (unit tests) or containerization (Docker) to show production engineering skills.",
                "💡 Add a small landing page or portfolio index mapping your projects to specific developer roles."
            ]
        else:
            suggestions = [
                "🚀 Your profile looks strong! Work on open source contributions or build tools that solve actual community problems.",
                "🚀 Optimize performance or add clean API/SDK documentations to make your libraries reusable by other developers.",
                "🚀 Start sharing your build logs and system architectures actively on X/Twitter and LinkedIn to build distribution."
            ]
    else:
        suggestions = ["⚡ Submit a grading scan first to receive custom action items!"]
        
    return render_template(
        "portfolio_grader_tracker.html",
        tracked_profile=tracked,
        latest_grade=latest_grade,
        history_data=chart_data,
        suggestions=suggestions,
        raw_history=history[::-1] # latest first for list view
    )


@portfolio_grader_bp.route("/tools/portfolio-grader/tracker/add", methods=["POST"])
@login_required
def add_tracker() -> Response:
    """Link a GitHub username to the user's account for active growth tracking."""
    username = request.form.get("username", "").strip().lower()
    if not username:
        return jsonify({"success": False, "message": "GitHub username is required"}), 400
        
    # Check if they are already tracking this user
    existing = TrackedPortfolio.query.filter_by(user_id=current_user.id, username=username).first()
    if existing:
        return jsonify({"success": True, "message": "Already tracking this username."})
        
    # Check if a grade cached record exists. If not, we trigger a lightweight GitHub fetch
    # to save initial history points.
    grade = PortfolioGrade.query.filter_by(username=username).first()
    score = grade.score if grade else 50 # default starting score if not evaluated yet
    
    stars = 0
    followers = 0
    repos = 0
    try:
        gh_data = fetch_github_data(username)
        stars = gh_data.get("stars", 0)
        followers = gh_data.get("followers", 0)
        repos = gh_data.get("total_repos", 0)
    except Exception:
        pass # fallback to default 0s if fetch fails
        
    # Limit to 1 active profile tracking per account.
    TrackedPortfolio.query.filter_by(user_id=current_user.id).delete()
    
    new_tracked = TrackedPortfolio(
        user_id=current_user.id,
        username=username,
        last_scanned_at=datetime.utcnow()
    )
    db.session.add(new_tracked)
    
    # Save first history record
    new_history = PortfolioHistory(
        username=username,
        score=score,
        stars=stars,
        followers=followers,
        public_repos=repos
    )
    db.session.add(new_history)
    
    try:
        db.session.commit()
        return jsonify({"success": True, "message": f"Successfully tracking @{username}."})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Failed to save: {str(e)}"}), 500


@portfolio_grader_bp.route("/tools/portfolio-grader/tracker/sync", methods=["POST"])
@login_required
def sync_tracker() -> Response:
    """Sync the tracked portfolio by running a fresh GitHub API fetch and full LLM evaluation."""
    username = request.form.get("username", "").strip().lower()
    if not username:
        return jsonify({"success": False, "message": "Username is required"}), 400
        
    # Verify owner
    tracked = TrackedPortfolio.query.filter_by(user_id=current_user.id, username=username).first()
    if not tracked:
        return jsonify({"success": False, "message": "You are not tracking this portfolio."}), 403
        
    # Enforce a 24-hour sync cooldown to protect AI keys, but allow admins to bypass
    admin_email = current_app.config.get("ADMIN_EMAIL")
    is_admin = current_user.email == admin_email
    
    if tracked.last_scanned_at and not is_admin:
        from datetime import timedelta
        if datetime.utcnow() - tracked.last_scanned_at < timedelta(hours=24):
            # Check how much time is left
            time_left = timedelta(hours=24) - (datetime.utcnow() - tracked.last_scanned_at)
            hours_left = int(time_left.total_seconds() // 3600)
            mins_left = int((time_left.total_seconds() % 3600) // 60)
            return jsonify({
                "success": False,
                "message": f"Please wait {hours_left}h {mins_left}m before scanning again to protect API limits."
            }), 429
            
    # Fetch github data and grade
    try:
        github_data = fetch_github_data(username)
        # Run standard LLM evaluation without resume file to keep it lightweight
        grade_result = evaluate_portfolio(github_data, None)
        
        # Save to cache
        cached = PortfolioGrade.query.filter_by(username=username).first()
        if cached:
            cached.score = grade_result["score"]
            cached.punchline = grade_result["punchline"]
            cached.bullet_points = grade_result["bullet_points"]
            cached.created_at = datetime.utcnow()
        else:
            new_grade = PortfolioGrade(
                username=username,
                score=grade_result["score"],
                punchline=grade_result["punchline"],
                bullet_points=grade_result["bullet_points"]
            )
            db.session.add(new_grade)
            
        # Update tracked scanned time
        tracked.last_scanned_at = datetime.utcnow()
        
        # Save history point
        new_history = PortfolioHistory(
            username=username,
            score=grade_result["score"],
            stars=github_data.get("stars", 0),
            followers=github_data.get("followers", 0),
            public_repos=github_data.get("total_repos", 0)
        )
        db.session.add(new_history)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Re-evaluation completed successfully!",
            "score": grade_result["score"],
            "stars": github_data.get("stars", 0),
            "followers": github_data.get("followers", 0)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "message": f"Sync failed: {str(e)}"}), 500
