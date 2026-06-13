from flask import render_template, request, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
import re
from datetime import datetime
from models import db, Job, CourseEnrollment, LessonProgress, CourseDay, JobApplication
from extensions import csrf
from . import jobs_bp


@jobs_bp.route("/jobs")
def board():
    # Get filters from query parameters
    job_type = request.args.get("type", "All")
    category = request.args.get("role", "All")
    location_filter = request.args.get("location", "All")
    batch_filter = request.args.get("batch", "All")
    search_query = request.args.get("search", "").strip()
    page = request.args.get("page", 1, type=int)

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
            batch_pattern = f"%{batch_filter}%"
            query = query.filter(
                or_(
                    Job.target_batch.ilike(batch_pattern),
                    Job.experience_level.ilike("%fresher%"),
                    Job.title.ilike("%fresher%")
                )
            )

    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.company.ilike(search_pattern),
                Job.skills.ilike(search_pattern),
                Job.description.ilike(search_pattern)
            )
        )

    # Grand total of active jobs (before filters)
    total_jobs_count = Job.query.filter_by(is_active=True).count()
    filters_active = (job_type != "All" or category != "All" or location_filter != "All" or batch_filter != "All" or bool(search_query))

    PER_PAGE = 15
    pagination = query.order_by(Job.created_at.desc()).paginate(page=page, per_page=PER_PAGE, error_out=False)
    jobs = pagination.items
    applied_job_ids = set()
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
@csrf.exempt
def record_job_click(job_id):
    job = Job.query.get_or_404(job_id)
    job.clicks = (job.clicks or 0) + 1
    
    applied = False
    if current_user.is_authenticated:
        existing_app = JobApplication.query.filter_by(user_id=current_user.id, job_id=job_id).first()
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

