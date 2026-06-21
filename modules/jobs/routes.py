from datetime import datetime
import io
import logging
import os
import re
import time as time_mod
from typing import Any

from flask import current_app, jsonify, render_template, request, Response, url_for
from flask_login import current_user, login_required
import pypdf
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from extensions import csrf
from models import AgentApplicationLog, AgentJobOpportunity, CourseDay, CourseEnrollment, db, Job, JobApplication, LessonProgress, UserAgentConfig
from . import jobs_bp
from .agent_worker import AGENT_STATUSES, run_job_agent_pipeline_async


@jobs_bp.route("/jobs")
def board() -> str:
    """Render the job board page with filters and pagination."""
    # Get filters from query parameters
    job_type: str = request.args.get("type", "All")
    category: str = request.args.get("role", "All")
    location_filter: str = request.args.get("location", "All")
    batch_filter: str = request.args.get("batch", "All")
    search_query: str = request.args.get("search", "").strip()
    page: int = request.args.get("page", 1, type=int)

    # Base query
    query = Job.query.filter_by(is_active=True)

    # Apply filters
    if job_type != "All":
        query = query.filter(Job.job_type.ilike(job_type))

    if category != "All":
        # Handle backend mapping
        if category == "python":
            query = query.filter(Job.category.ilike("%Python%"))
        elif category == "backend":
            query = query.filter(Job.category.ilike("%Backend%"))
        elif category == "ai_llm":
            query = query.filter(or_(Job.category.ilike("%AI%"), Job.category.ilike("%LLM%"), Job.category.ilike("%Agent%")))
        elif category == "frontend":
            query = query.filter(or_(Job.category.ilike("%Frontend%"), Job.category.ilike("%Web%")))
        elif category == "fullstack":
            query = query.filter(Job.category.ilike("%Fullstack%"))
        elif category == "qa_testing":
            query = query.filter(or_(Job.category.ilike("%QA%"), Job.category.ilike("%Test%"), Job.category.ilike("%Testing%")))
        else:
            query = query.filter(Job.category.ilike(f"%{category}%"))

    if location_filter != "All":
        if location_filter == "remote":
            query = query.filter(Job.location.ilike("%Remote%"))
        elif location_filter == "hybrid":
            query = query.filter(Job.location.ilike("%Hybrid%"))
        elif location_filter == "onsite":
            query = query.filter(~Job.location.ilike("%Remote%"), ~Job.location.ilike("%Hybrid%"))

    if batch_filter != "All":
        if batch_filter == "Experience":
            query = query.filter(Job.target_batch.ilike("%Experience%"))
        else:
            # For 2025, 2026, 2027: match explicit batch OR fresher/entry-level roles
            batch_pattern: str = f"%{batch_filter}%"
            query = query.filter(
                or_(
                    Job.target_batch.ilike(batch_pattern),
                    Job.experience_level.ilike("%fresher%"),
                    Job.title.ilike("%fresher%")
                )
            )

    if search_query:
        search_pattern: str = f"%{search_query}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
                Job.skills.ilike(search_pattern),
                Job.description.ilike(search_pattern)
            )
        )

    # Grand total of active jobs (before filters)
    total_jobs_count: int = Job.query.filter_by(is_active=True).count()
    filters_active: bool = (job_type != "All" or category != "All" or location_filter != "All" or batch_filter != "All" or bool(search_query))

    PER_PAGE: int = 15
    pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    jobs: list[Job] = pagination.items
    applied_job_ids: set[int] = set()
    if current_user.is_authenticated:
        applied_job_ids = {app.job_id for app in JobApplication.query.filter_by(user_id=current_user.id).all()}

    return render_template(
        "jobs.html",
        jobs=jobs,
        pagination=pagination,
        selected_type=job_type,
        selected_role=category,
        selected_location=location_filter,
        selected_batch=batch_filter,
        search_query=search_query,
        now=datetime.utcnow(),
        total_jobs_count=total_jobs_count,
        filters_active=filters_active,
        applied_job_ids=applied_job_ids
    )


@jobs_bp.route("/api/jobs/<int:job_id>/click", methods=["POST"])
def record_job_click(job_id: int) -> Response:
    """Record click metrics and log user application interest in a job."""
    job: Job = Job.query.get_or_404(job_id)
    job.clicks = (job.clicks or 0) + 1
    
    applied: bool = False
    if current_user.is_authenticated:
        existing_app: JobApplication | None = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first()
        if not existing_app:
            new_app = JobApplication(user_id=current_user.id, job_id=job_id)
            db.session.add(new_app)
            applied = True
        else:
            applied = True
            
    db.session.commit()
    return jsonify({
        "success": True,
        "clicks_count": job.clicks,
        "applied": applied
    })


# ==========================================
# AI Job Agent Routes
# ==========================================


@jobs_bp.route("/jobs/agent")
@login_required
def agent_dashboard() -> str:
    """Render the AI Job Agent dashboard and handle automated cleanup."""
    # Clean up any non-Placement Portal opportunities and their logs immediately on dashboard load
    try:
        deleted_count: int = AgentJobOpportunity.query.filter(AgentJobOpportunity.source != "Placement Portal").delete(synchronize_session=False)
        if deleted_count > 0:
            db.session.commit()
            logging.info(f"Cleaned up {deleted_count} external jobs from agent_dashboard load.")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error cleaning up old agent jobs: {e}")

    # Fetch or create agent config
    config: UserAgentConfig | None = UserAgentConfig.query.filter_by(user_id=current_user.id).first()
    if not config:
        config = UserAgentConfig(user_id=current_user.id)
        db.session.add(config)
        db.session.commit()

    # Get matched jobs logs (sorted by fit score and date desc, only from local Placement Portal)
    matches: list[AgentApplicationLog] = (AgentApplicationLog.query
               .join(AgentJobOpportunity)
               .filter(AgentApplicationLog.user_id == current_user.id)
               .filter(AgentJobOpportunity.source == "Placement Portal")
               .filter(AgentApplicationLog.fit_score >= 50)
               .filter(AgentApplicationLog.status != "Skipped")
               .order_by(AgentApplicationLog.fit_score.desc(), AgentApplicationLog.created_at.desc())
               .all())

    return render_template(
        "jobs_agent.html",
        config=config,
        matches=matches
    )


@jobs_bp.route("/jobs/agent/config", methods=["POST"])
@login_required
def save_agent_config() -> Response:
    """Save user target roles, locations, salary, and toggle state."""
    config: UserAgentConfig | None = UserAgentConfig.query.filter_by(user_id=current_user.id).first()
    if not config:
        config = UserAgentConfig(user_id=current_user.id)
        db.session.add(config)

    config.target_roles = request.form.get("target_roles", "").strip()
    config.target_locations = request.form.get("target_locations", "").strip()
    config.min_salary = request.form.get("min_salary", "").strip()
    
    # Toggle logic (is_active can be passed as form parameter)
    is_active: bool = request.form.get("is_active") == "true"
    config.is_active = is_active

    # Delete all previous logs so they get re-evaluated with fresh pitches under new preferences
    AgentApplicationLog.query.filter_by(user_id=current_user.id).delete()

    db.session.commit()

    # Trigger or restart the matcher async if active and resume exists
    if config.is_active and config.resume_text:
        run_job_agent_pipeline_async(current_app._get_current_object(), current_user.id)

    return jsonify({
        "success": True,
        "message": "Preferences saved successfully.",
        "is_active": config.is_active
    })


@jobs_bp.route("/jobs/agent/resume", methods=["POST"])
@login_required
def upload_resume() -> Response:
    """Upload, secure, and parse resume text from PDF using pypdf."""
    if 'resume' not in request.files:
        return jsonify({"success": False, "message": "No file uploaded"}), 400
        
    file = request.files['resume']
    if file.filename == '':
        return jsonify({"success": False, "message": "No file selected"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"success": False, "message": "Only PDF files are supported"}), 400

    try:
        # 1. Read bytes and parse text using pypdf
        file_bytes: bytes = file.read()
        if not file_bytes:
            return jsonify({"success": False, "message": "Uploaded file is empty."}), 400

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        extracted_text: str = ""
        for page in reader.pages:
            extracted_text += page.extract_text() or ""
            
        extracted_text = extracted_text.strip()
        if not extracted_text:
            return jsonify({"success": False, "message": "Could not extract text from the PDF. Ensure it is not a scanned image."}), 400

        # 2. Get or create agent config
        config: UserAgentConfig | None = UserAgentConfig.query.filter_by(user_id=current_user.id).first()
        if not config:
            config = UserAgentConfig(user_id=current_user.id)
            db.session.add(config)

        # 3. Save PDF file locally
        upload_dir: str = os.path.join(current_app.root_path, 'static', 'uploads', 'resumes')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename: str = secure_filename(f"resume_{current_user.id}_{int(time_mod.time())}.pdf")
        file_path: str = os.path.join(upload_dir, filename)
        
        # Write bytes directly to file
        with open(file_path, 'wb') as f:
            f.write(file_bytes)

        # Update database fields
        config.resume_text = extracted_text
        config.resume_filename = filename
        
        # Clear previous logs so they get re-evaluated against the new resume
        AgentApplicationLog.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()

        # Trigger async pipeline if agent is active
        if config.is_active:
            run_job_agent_pipeline_async(current_app._get_current_object(), current_user.id)

        return jsonify({
            "success": True,
            "message": "Resume uploaded and parsed successfully.",
            "filename": filename,
            "char_count": len(extracted_text)
        })

    except Exception as e:
        return jsonify({"success": False, "message": f"Error parsing PDF: {str(e)}"}), 500


@jobs_bp.route("/jobs/agent/run", methods=["POST"])
@login_required
def trigger_agent_run() -> Response:
    """Manually trigger background job agent scanning and matching."""
    config: UserAgentConfig | None = UserAgentConfig.query.filter_by(user_id=current_user.id).first()
    if not config or not config.resume_text:
        return jsonify({"success": False, "message": "Please upload a PDF resume before running the agent."}), 400

    run_job_agent_pipeline_async(current_app._get_current_object(), current_user.id)

    return jsonify({
        "success": True,
        "message": "Job agent scanning started in background."
    })


@jobs_bp.route("/jobs/agent/apply/<int:log_id>", methods=["POST"])
@login_required
def mark_applied(log_id: int) -> Response:
    """API endpoint to mark a matched job status as 'Applied'."""
    log: AgentApplicationLog = AgentApplicationLog.query.filter_by(id=log_id, user_id=current_user.id).first_or_404()
    log.status = "Applied"
    log.applied_at = datetime.utcnow()
    db.session.commit()
    return jsonify({
        "success": True,
        "message": "Application logged successfully."
    })


@jobs_bp.route("/jobs/agent/status", methods=["GET"])
@login_required
def get_agent_status() -> Response:
    """API endpoint to get current background running status of the agent."""
    status: str = AGENT_STATUSES.get(current_user.id, "Idle")
    return jsonify({
        "success": True,
        "status": status
    })



