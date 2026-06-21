import csv
from datetime import datetime
import json
from io import BytesIO
import os
from typing import Any, Callable
import zipfile

from flask import Response, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, or_
from werkzeug.utils import secure_filename

from models import (
    Course,
    CourseDay,
    CourseEnrollment,
    Favorite,
    Job,
    LessonProgress,
    LessonReview,
    Prompt,
    PromptCollection,
    PromptCollectionItem,
    PromptLike,
    User,
    UserCourseProgress,
    db,
)
from . import admin_bp

# ==========================================
# ADMIN AUTH GUARD
# ==========================================


def admin_required(f: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to restrict access to admin users only."""
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if current_user.email != current_app.config["ADMIN_EMAIL"]:
            flash("Admin access only.", "danger")
            return redirect(url_for("auth.dashboard"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ==========================================
# MAIN DASHBOARD
# ==========================================

@admin_bp.route("/admin", endpoint="admin")
@login_required
@admin_required
def admin_dashboard() -> str:
    """Main admin dashboard with all stats including enrollment analytics and system health."""

    # ── User stats ──────────────────────────────────────────────────────────
    user_count = User.query.count()
    verified_count = User.query.filter_by(is_verified=True).count()

    # ── Course stats ─────────────────────────────────────────────────────────
    course_count = Course.query.count()
    published_courses = Course.query.filter_by(is_published=True).count()
    total_lessons = CourseDay.query.count()

    # ── Enrollment stats ─────────────────────────────────────────────────────
    total_enrollments = CourseEnrollment.query.count()
    unique_enrolled_users = (
        db.session.query(func.count(func.distinct(CourseEnrollment.user_id))).scalar() or 0
    )

    # ── Prompt stats ─────────────────────────────────────────────────────────
    prompt_count = Prompt.query.count()
    total_likes = db.session.query(func.coalesce(func.sum(Prompt.likes), 0)).scalar() or 0
    total_copies = db.session.query(func.coalesce(func.sum(Prompt.copies), 0)).scalar() or 0

    # ── Job stats ────────────────────────────────────────────────────────────
    try:
        job_count = Job.query.count()
    except Exception:
        job_count = 0

    # ── Lesson completion stats ───────────────────────────────────────────────
    total_completed_lessons = LessonProgress.query.filter_by(completed=True).count()

    # ── Active learners: users with at least 1 completed lesson ───────────────
    try:
        active_learners = (
            db.session.query(func.count(func.distinct(LessonProgress.user_id)))
            .filter(LessonProgress.completed == True)
            .scalar() or 0
        )
    except Exception:
        active_learners = 0

    # ── Recent activity ───────────────────────────────────────────────────────
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_enrollments = (
        CourseEnrollment.query.order_by(CourseEnrollment.enrolled_at.desc()).limit(5).all()
    )

    # ── Backup Stats ──────────────────────────────────────────────────────────
    backup_count = 0
    last_backup_time = "Never"
    try:
        backup_root = os.path.join(current_app.root_path, "backups")
        if os.path.exists(backup_root):
            zip_files = []
            for root, dirs, files in os.walk(backup_root):
                for f in files:
                    if f.endswith('.zip'):
                        zip_files.append(os.path.join(root, f))
            backup_count = len(zip_files)
            if zip_files:
                latest_file = max(zip_files, key=os.path.getmtime)
                mtime = os.path.getmtime(latest_file)
                last_backup_time = datetime.fromtimestamp(mtime).strftime('%b %d, %Y %I:%M %p')
    except Exception:
        pass

    # ── Database row counts ───────────────────────────────────────────────────
    try:
        favorites_count = Favorite.query.count()
    except Exception:
        favorites_count = 0
    try:
        likes_count = PromptLike.query.count()
    except Exception:
        likes_count = 0
    try:
        collections_count = PromptCollection.query.count()
    except Exception:
        collections_count = 0

    # ── Full enrollment analytics table (limited to 10 for performance) ───────
    enrollment_analytics = []
    try:
        all_enrollments = (
            CourseEnrollment.query
            .order_by(CourseEnrollment.enrolled_at.desc())
            .limit(10)
            .all()
        )

        # Pre-fetch total lessons per course to avoid N+1 queries
        course_lesson_counts = dict(
            db.session.query(CourseDay.course_id, func.count(CourseDay.id))
            .group_by(CourseDay.course_id)
            .all()
        )

        # Pre-fetch completed lesson counts per (user_id, course_id)
        completed_rows = (
            db.session.query(
                CourseDay.course_id,
                LessonProgress.user_id,
                func.count(LessonProgress.id).label("done")
            )
            .join(CourseDay, LessonProgress.course_day_id == CourseDay.id)
            .filter(LessonProgress.completed == True)
            .group_by(CourseDay.course_id, LessonProgress.user_id)
            .all()
        )
        completed_map = {(r.course_id, r.user_id): r.done for r in completed_rows}

        for enr in all_enrollments:
            user = enr.user        # uses relationship
            course = enr.course    # uses relationship
            if not user or not course:
                continue

            total_course_lessons = course_lesson_counts.get(course.id, 0)
            lessons_done = completed_map.get((course.id, user.id), 0)
            progress_pct = (
                int((lessons_done / total_course_lessons) * 100)
                if total_course_lessons > 0 else 0
            )

            enrollment_analytics.append({
                "username": user.username,
                "email": user.email,
                "course": course.title,
                "enrolled_at": enr.enrolled_at,
                "lessons_completed": lessons_done,
                "total_lessons": total_course_lessons,
                "progress_pct": progress_pct,
            })
    except Exception as e:
        current_app.logger.error("Enrollment analytics error: %s", e)
        enrollment_analytics = []

    lesson_reviews = LessonReview.query.order_by(LessonReview.created_at.desc()).all()
    db_type = "SQLite" if current_app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite") else "PostgreSQL"

    return render_template(
        "admin/dashboard.html",
        # existing stats
        user_count=user_count,
        verified_count=verified_count,
        course_count=course_count,
        published_courses=published_courses,
        total_lessons=total_lessons,
        total_enrollments=total_enrollments,
        unique_enrolled_users=unique_enrolled_users,
        prompt_count=prompt_count,
        total_likes=total_likes,
        total_copies=total_copies,
        total_completed_lessons=total_completed_lessons,
        recent_users=recent_users,
        recent_enrollments=recent_enrollments,
        # new enrollment analytics
        active_learners=active_learners,
        enrollment_analytics=enrollment_analytics,
        # DB & backup stats
        db_type=db_type,
        backup_count=backup_count,
        last_backup_time=last_backup_time,
        favorites_count=favorites_count,
        likes_count=likes_count,
        collections_count=collections_count,
        # lesson reviews
        lesson_reviews=lesson_reviews,
        # jobs stats
        job_count=job_count
    )


@admin_bp.route("/admin/api/stats", endpoint="api_stats")
@login_required
@admin_required
def api_stats() -> Response:
    """Returns JSON analytics data for admin dashboard monitoring charts."""
    from datetime import datetime, timedelta

    # 1. User Registrations (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    users_recent = (
        db.session.query(User.created_at)
        .filter(User.created_at >= thirty_days_ago)
        .all()
    )
    user_growth = {}
    for i in range(30):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        user_growth[d.isoformat()] = 0
        
    for u in users_recent:
        if u.created_at:
            d_str = u.created_at.date().isoformat()
            if d_str in user_growth:
                user_growth[d_str] += 1
                
    user_growth_sorted = [{"date": k, "count": v} for k, v in sorted(user_growth.items())]

    # 2. Course Enrollments
    courses = Course.query.all()
    enrollment_data = []
    for c in courses:
        count = CourseEnrollment.query.filter_by(course_id=c.id).count()
        enrollment_data.append({"course": c.title, "count": count})

    # 3. Prompt Categories
    categories_data = []
    try:
        cat_counts = (
            db.session.query(Prompt.category, func.count(Prompt.id))
            .group_by(Prompt.category)
            .all()
        )
        for cat, count in cat_counts:
            categories_data.append({"category": cat or "General", "count": count})
    except Exception:
        categories_data = []

    # 4. Lesson Completions (last 15 days)
    fifteen_days_ago = datetime.utcnow() - timedelta(days=15)
    completions_recent = (
        db.session.query(LessonProgress.completed_at)
        .filter(LessonProgress.completed == True, LessonProgress.completed_at >= fifteen_days_ago)
        .all()
    )
    completions_map = {}
    for i in range(15):
        d = (datetime.utcnow() - timedelta(days=i)).date()
        completions_map[d.isoformat()] = 0
        
    for c in completions_recent:
        if c.completed_at:
            d_str = c.completed_at.date().isoformat()
            if d_str in completions_map:
                completions_map[d_str] += 1
                
    completions_sorted = [{"date": k, "count": v} for k, v in sorted(completions_map.items())]

    return jsonify({
        "user_growth": user_growth_sorted,
        "course_enrollments": enrollment_data,
        "prompt_categories": categories_data,
        "lesson_completions": completions_sorted
    })

# ==========================================
# COURSES MANAGEMENT
# ==========================================

@admin_bp.route("/admin/courses", endpoint="courses")
@login_required
@admin_required
def manage_courses() -> str:
    """List all courses."""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Course.query
    if search:
        query = query.filter(or_(
            Course.title.ilike(f'%{search}%'),
            Course.slug.ilike(f'%{search}%')
        ))
    
    courses = query.order_by(Course.created_at.desc()).paginate(page=page, per_page=10)
    return render_template("admin/courses.html", courses=courses, search=search)

@admin_bp.route("/admin/courses/create", methods=["GET", "POST"], endpoint="create_course")
@login_required
@admin_required
def create_course() -> Any:
    """Create a new course."""
    if request.method == "POST":
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        description = request.form.get('description', '').strip()
        difficulty = request.form.get('difficulty', 'Beginner')
        
        if not title or not slug:
            flash("Title and slug are required.", "danger")
            return redirect(url_for("admin.create_course"))
        
        if Course.query.filter_by(slug=slug).first():
            flash("Slug already exists.", "danger")
            return redirect(url_for("admin.create_course"))
        
        # Handle thumbnail upload
        thumbnail = None
        if 'thumbnail' in request.files and request.files['thumbnail'].filename:
            file = request.files['thumbnail']
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, "static/uploads/thumbnails")
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            thumbnail = f"uploads/thumbnails/{filename}"
        
        course = Course(
            title=title,
            slug=slug,
            description=description,
            difficulty=difficulty,
            thumbnail=thumbnail,
            is_published=False
        )
        
        db.session.add(course)
        db.session.commit()
        
        flash(f"Course '{title}' created successfully.", "success")
        return redirect(url_for("admin.courses"))
    
    return render_template("admin/create_course.html")

@admin_bp.route("/admin/courses/<int:course_id>/edit", methods=["GET", "POST"], endpoint="edit_course")
@login_required
@admin_required
def edit_course(course_id: int) -> Any:
    """Edit an existing course."""
    course = Course.query.get_or_404(course_id)
    
    if request.method == "POST":
        course.title = request.form.get('title', '').strip() or course.title
        course.description = request.form.get('description', '').strip() or course.description
        course.difficulty = request.form.get('difficulty', course.difficulty)
        course.is_published = request.form.get('is_published') == 'on'
        
        if 'thumbnail' in request.files and request.files['thumbnail'].filename:
            file = request.files['thumbnail']
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, "static/uploads/thumbnails")
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            course.thumbnail = f"uploads/thumbnails/{filename}"
        
        db.session.commit()
        flash(f"Course '{course.title}' updated.", "success")
        return redirect(url_for("admin.courses"))
    
    return render_template("admin/edit_course.html", course=course)

@admin_bp.route("/admin/courses/<int:course_id>/delete", methods=["POST"], endpoint="delete_course")
@login_required
@admin_required
def delete_course(course_id: int) -> Response:
    """Delete a course."""
    course = Course.query.get_or_404(course_id)
    course_title = course.title
    
    db.session.delete(course)
    db.session.commit()
    
    flash(f"Course '{course_title}' deleted.", "success")
    return redirect(url_for("admin.courses"))

# ==========================================
# LESSONS MANAGEMENT
# ==========================================

@admin_bp.route("/admin/lessons", endpoint="lessons")
@login_required
@admin_required
def manage_lessons() -> str:
    """List all lessons."""
    course_id = request.args.get('course_id', type=int)
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    courses = Course.query.all()
    query = CourseDay.query
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    
    if search:
        query = query.filter(or_(
            CourseDay.title.ilike(f'%{search}%'),
            CourseDay.slug.ilike(f'%{search}%')
        ))
    
    lessons = query.order_by(CourseDay.course_id, CourseDay.day_number).paginate(page=page, per_page=15)
    return render_template("admin/lessons.html", lessons=lessons, courses=courses, course_id=course_id, search=search)

@admin_bp.route("/admin/lessons/create", methods=["GET", "POST"], endpoint="create_lesson")
@login_required
@admin_required
def create_lesson() -> Any:
    """Create a new lesson."""
    courses = Course.query.all()
    
    if request.method == "POST":
        course_id = request.form.get('course_id', type=int)
        title = request.form.get('title', '').strip()
        slug = request.form.get('slug', '').strip()
        short_description = request.form.get('short_description', '').strip()
        day_number = request.form.get('day_number', type=int)
        xp_reward = request.form.get('xp_reward', 50, type=int)
        estimated_minutes = request.form.get('estimated_minutes', 10, type=int)
        content_type = request.form.get('content_type', 'text')  # text, html, markdown, jupyter
        
        if not all([course_id, title, slug, day_number]):
            flash("All required fields must be filled.", "danger")
            return redirect(url_for("admin.create_lesson"))
        
        # Handle content upload
        content = request.form.get('content', '').strip() if content_type == 'text' else ''
        
        if content_type in ['html', 'markdown', 'jupyter']:
            if 'content_file' not in request.files or not request.files['content_file'].filename:
                flash("Content file required for HTML/Markdown/Jupyter.", "danger")
                return redirect(url_for("admin.create_lesson"))
            
            file = request.files['content_file']
            filename = secure_filename(file.filename)
            
            ext_map = {'html': '.html', 'markdown': '.md', 'jupyter': '.ipynb'}
            if not filename.endswith(ext_map.get(content_type, '')):
                filename = f"{os.path.splitext(filename)[0]}{ext_map.get(content_type, '')}"
            
            upload_folder = os.path.join(current_app.root_path, f"static/uploads/lessons/{content_type}")
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            content = f"uploads/lessons/{content_type}/{filename}"
        
        # Handle image upload
        image = None
        if 'image' in request.files and request.files['image'].filename:
            img_file = request.files['image']
            img_filename = secure_filename(img_file.filename)
            img_upload_folder = os.path.join(current_app.root_path, "static/uploads/lesson_images")
            os.makedirs(img_upload_folder, exist_ok=True)
            img_filepath = os.path.join(img_upload_folder, img_filename)
            img_file.save(img_filepath)
            image = f"uploads/lesson_images/{img_filename}"
        
        lesson = CourseDay(
            course_id=course_id,
            day_number=day_number,
            title=title,
            slug=slug,
            short_description=short_description,
            image=image,
            xp_reward=xp_reward,
            estimated_minutes=estimated_minutes,
            content=content,
            is_published=False
        )
        
        db.session.add(lesson)
        db.session.commit()
        
        flash(f"Lesson '{title}' created successfully.", "success")
        return redirect(url_for("admin.lessons"))
    
    default_course_id = request.args.get('course_id', type=int)
    next_day_number = 1
    if default_course_id:
        max_day = db.session.query(db.func.max(CourseDay.day_number)).filter_by(course_id=default_course_id).scalar()
        next_day_number = (max_day or 0) + 1
        
    return render_template(
        "admin/create_lesson.html", 
        courses=courses, 
        default_course_id=default_course_id,
        next_day_number=next_day_number
    )

@admin_bp.route("/admin/lessons/<int:lesson_id>/edit", methods=["GET", "POST"], endpoint="edit_lesson")
@login_required
@admin_required
def edit_lesson(lesson_id: int) -> Any:
    """Edit an existing lesson."""
    lesson = CourseDay.query.get_or_404(lesson_id)
    courses = Course.query.all()
    
    if request.method == "POST":
        lesson.title = request.form.get('title', '').strip() or lesson.title
        lesson.slug = request.form.get('slug', '').strip() or lesson.slug
        lesson.short_description = request.form.get('short_description', '').strip() or lesson.short_description
        lesson.day_number = request.form.get('day_number', lesson.day_number, type=int)
        lesson.xp_reward = request.form.get('xp_reward', lesson.xp_reward, type=int)
        lesson.estimated_minutes = request.form.get('estimated_minutes', lesson.estimated_minutes, type=int)
        lesson.is_published = request.form.get('is_published') == 'on'
        
        # Update content if provided
        content_input = request.form.get('content', '').strip()
        if content_input:
            lesson.content = content_input
        
        # Handle new image
        if 'image' in request.files and request.files['image'].filename:
            img_file = request.files['image']
            img_filename = secure_filename(img_file.filename)
            img_upload_folder = os.path.join(current_app.root_path, "static/uploads/lesson_images")
            os.makedirs(img_upload_folder, exist_ok=True)
            img_filepath = os.path.join(img_upload_folder, img_filename)
            img_file.save(img_filepath)
            lesson.image = f"uploads/lesson_images/{img_filename}"
        
        db.session.commit()
        flash(f"Lesson '{lesson.title}' updated.", "success")
        return redirect(url_for("admin.lessons"))
    
    return render_template("admin/edit_lesson.html", lesson=lesson, courses=courses)

@admin_bp.route("/admin/lessons/<int:lesson_id>/delete", methods=["POST"], endpoint="delete_lesson")
@login_required
@admin_required
def delete_lesson(lesson_id: int) -> Response:
    """Delete a lesson."""
    lesson = CourseDay.query.get_or_404(lesson_id)
    lesson_title = lesson.title
    course_id = lesson.course_id
    
    # Delete uploaded content file if it exists on disk
    if lesson.content and lesson.content.startswith("uploads/"):
        file_path = os.path.join(current_app.root_path, "static", lesson.content)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                current_app.logger.error("Failed to delete lesson content file: %s", e)
                
    # Delete uploaded lesson image if it exists on disk
    if lesson.image and lesson.image.startswith("uploads/"):
        img_path = os.path.join(current_app.root_path, "static", lesson.image)
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except Exception as e:
                current_app.logger.error("Failed to delete lesson image file: %s", e)
                
    db.session.delete(lesson)
    db.session.commit()
    
    flash(f"Lesson '{lesson_title}' deleted.", "success")
    return redirect(url_for("admin.lessons", course_id=course_id))

@admin_bp.route("/admin/lessons/reorder", methods=["POST"], endpoint="reorder_lessons")
@login_required
@admin_required
def reorder_lessons() -> Response:
    """Reorder lessons within a course."""
    data = request.get_json()
    course_id = data.get('course_id', type=int)
    lesson_ids = data.get('lesson_ids', [])
    
    for idx, lesson_id in enumerate(lesson_ids, 1):
        lesson = CourseDay.query.get(lesson_id)
        if lesson and lesson.course_id == course_id:
            lesson.day_number = idx
    
    db.session.commit()
    return jsonify({"success": True, "message": "Lessons reordered."})

# ==========================================
# LEARNING HISTORY (Who has learned what & when)
# ==========================================

@admin_bp.route("/admin/learning-history", endpoint="learning_history")
@login_required
@admin_required
def learning_history() -> str:
    """List all completed lessons with user details and timestamps."""
    search = request.args.get('search', '')
    course_id = request.args.get('course_id', type=int)
    page = request.args.get('page', 1, type=int)
    
    courses = Course.query.all()
    query = LessonProgress.query.filter_by(completed=True)
    
    if course_id:
        query = query.join(CourseDay).filter(CourseDay.course_id == course_id)
        
    if search:
        query = query.join(User).join(CourseDay).filter(or_(
            User.username.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%'),
            CourseDay.title.ilike(f'%{search}%')
        ))
        
    # Order by completion time descending (latest completions first)
    history = (
        query.order_by(LessonProgress.completed_at.desc())
        .paginate(page=page, per_page=25)
    )
    
    return render_template(
        "admin/learning_history.html",
        history=history,
        courses=courses,
        course_id=course_id,
        search=search
    )

@admin_bp.route("/admin/learning-history/<int:progress_id>/delete", methods=["POST"], endpoint="delete_progress_record")
@login_required
@admin_required
def delete_progress_record(progress_id: int) -> Response:
    """Delete a specific lesson completion progress record (mark it as incomplete)."""
    record = LessonProgress.query.get_or_404(progress_id)
    username = record.user.username if record.user else "User"
    lesson_title = record.course_day.title if record.course_day else "Lesson"
    
    db.session.delete(record)
    db.session.commit()
    
    flash(f"Successfully marked '{lesson_title}' as incomplete for '{username}'.", "success")
    return redirect(request.referrer or url_for("admin.learning_history"))


# ==========================================
# USERS MANAGEMENT
# ==========================================

@admin_bp.route("/admin/users", endpoint="users")
@login_required
@admin_required
def manage_users() -> str:
    """List all users with search and filters."""
    search = request.args.get('search', '')
    verified = request.args.get('verified', '')
    page = request.args.get('page', 1, type=int)
    
    query = User.query
    
    if search:
        query = query.filter(or_(
            User.username.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%')
        ))
    
    if verified == 'verified':
        query = query.filter_by(is_verified=True)
    elif verified == 'unverified':
        query = query.filter_by(is_verified=False)
    
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/users.html", users=users, search=search, verified=verified)

@admin_bp.route("/admin/users/<int:user_id>/verify", methods=["POST"], endpoint="verify_user")
@login_required
@admin_required
def verify_user(user_id: int) -> Response:
    """Verify a user."""
    user = User.query.get_or_404(user_id)
    user.is_verified = True
    db.session.commit()
    flash(f"✅ {user.username} verified.", "success")
    return redirect(request.referrer or url_for("admin.users"))

@admin_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"], endpoint="delete_user")
@login_required
@admin_required
def delete_user_admin(user_id: int) -> Response:
    """Delete a user."""
    user = User.query.get_or_404(user_id)
    
    if user.email == current_app.config["ADMIN_EMAIL"]:
        flash("Cannot delete admin user.", "danger")
        return redirect(url_for("admin.users"))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f"User '{username}' deleted.", "success")
    return redirect(request.referrer or url_for("admin.users"))

# ==========================================
# ENROLLMENTS MANAGEMENT
# ==========================================

@admin_bp.route("/admin/enrollments", endpoint="enrollments")
@login_required
@admin_required
def manage_enrollments() -> str:
    """List all enrollments."""
    course_id = request.args.get('course_id', type=int)
    user_id = request.args.get('user_id', type=int)
    page = request.args.get('page', 1, type=int)
    
    courses = Course.query.all()
    query = CourseEnrollment.query
    
    if course_id:
        query = query.filter_by(course_id=course_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    enrollments = query.order_by(CourseEnrollment.enrolled_at.desc()).paginate(page=page, per_page=20)
    return render_template("admin/enrollments.html", enrollments=enrollments, courses=courses, course_id=course_id, user_id=user_id)

@admin_bp.route("/admin/enrollments/create", methods=["GET", "POST"], endpoint="create_enrollment")
@login_required
@admin_required
def create_enrollment() -> Any:
    """Enroll a user in a course."""
    users = User.query.all()
    courses = Course.query.all()
    
    if request.method == "POST":
        user_id = request.form.get('user_id', type=int)
        course_id = request.form.get('course_id', type=int)
        
        existing = CourseEnrollment.query.filter_by(user_id=user_id, course_id=course_id).first()
        if existing:
            flash("User already enrolled in this course.", "warning")
            return redirect(url_for("admin.create_enrollment"))
        
        enrollment = CourseEnrollment(user_id=user_id, course_id=course_id)
        db.session.add(enrollment)
        db.session.commit()
        
        flash("Enrollment created.", "success")
        return redirect(url_for("admin.enrollments"))
    
    return render_template("admin/create_enrollment.html", users=users, courses=courses)

@admin_bp.route("/admin/enrollments/<int:enrollment_id>/delete", methods=["POST"], endpoint="delete_enrollment")
@login_required
@admin_required
def delete_enrollment(enrollment_id: int) -> Response:
    """Remove a user from a course."""
    enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
    db.session.delete(enrollment)
    db.session.commit()
    flash("Enrollment removed.", "success")
    return redirect(request.referrer or url_for("admin.enrollments"))

@admin_bp.route("/admin/enrollments/<int:enrollment_id>/reset", methods=["POST"], endpoint="reset_progress")
@login_required
@admin_required
def reset_progress(enrollment_id: int) -> Response:
    """Reset a user's progress in a course."""
    enrollment = CourseEnrollment.query.get_or_404(enrollment_id)
    
    # Delete lesson progress
    LessonProgress.query.filter_by(
        user_id=enrollment.user_id,
        course_day_id=CourseDay.id
    ).delete(synchronize_session=False)
    
    # Delete/reset course progress
    UserCourseProgress.query.filter_by(
        user_id=enrollment.user_id,
        course_id=enrollment.course_id
    ).delete(synchronize_session=False)
    
    db.session.commit()
    flash("Progress reset for this enrollment.", "success")
    return redirect(request.referrer or url_for("admin.enrollments"))

# ==========================================
# PROMPTS MANAGEMENT (in Admin)
# ==========================================

@admin_bp.route("/admin/prompts", endpoint="admin_prompts")
@login_required
@admin_required
def manage_prompts() -> str:
    """List all prompts in admin."""
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    query = Prompt.query
    if search:
        query = query.filter(or_(
            Prompt.title.ilike(f'%{search}%'),
            Prompt.content.ilike(f'%{search}%')
        ))
    
    prompts = query.order_by(Prompt.created_at.desc()).paginate(page=page, per_page=15)
    return render_template("admin/prompts.html", prompts=prompts, search=search)

@admin_bp.route("/admin/prompts/<int:prompt_id>/delete", methods=["POST"], endpoint="delete_prompt_admin")
@login_required
@admin_required
def delete_prompt_admin(prompt_id: int) -> Response:
    """Delete a prompt from admin panel."""
    prompt = Prompt.query.get_or_404(prompt_id)
    prompt_title = prompt.title
    db.session.delete(prompt)
    db.session.commit()
    flash(f"Prompt '{prompt_title}' deleted.", "success")
    return redirect(request.referrer or url_for("admin.admin_prompts"))

# ==========================================
# DATABASE BACKUP & EXPORT
# ==========================================

@admin_bp.route("/admin/backup", endpoint="backup")
@login_required
@admin_required
def backup_page() -> str:
    """Database backup & export page."""
    return render_template("admin/backup.html")

@admin_bp.route("/admin/backup/export-courses", methods=["POST"], endpoint="export_courses")
@login_required
@admin_required
def export_courses() -> Response:
    """Export all courses as JSON."""
    courses = Course.query.all()
    data = []
    
    for course in courses:
        data.append({
            'id': course.id,
            'title': course.title,
            'slug': course.slug,
            'description': course.description,
            'difficulty': course.difficulty,
            'is_published': course.is_published,
            'created_at': course.created_at.isoformat()
        })
    
    filename = f"courses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return send_file(
        BytesIO(json.dumps(data, indent=2).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route("/admin/backup/export-lessons", methods=["POST"], endpoint="export_lessons")
@login_required
@admin_required
def export_lessons() -> Response:
    """Export all lessons as JSON."""
    lessons = CourseDay.query.all()
    data = []
    
    for lesson in lessons:
        data.append({
            'id': lesson.id,
            'course_id': lesson.course_id,
            'day_number': lesson.day_number,
            'title': lesson.title,
            'slug': lesson.slug,
            'short_description': lesson.short_description,
            'xp_reward': lesson.xp_reward,
            'estimated_minutes': lesson.estimated_minutes,
            'is_published': lesson.is_published,
            'created_at': lesson.created_at.isoformat()
        })
    
    filename = f"lessons_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return send_file(
        BytesIO(json.dumps(data, indent=2).encode()),
        mimetype='application/json',
        as_attachment=True,
        download_name=filename
    )

@admin_bp.route("/admin/backup/export-full", methods=["POST"], endpoint="export_full_db")
@login_required
@admin_required
def export_full_db() -> Response:
    """Export full database as ZIP with courses, lessons, users, enrollments."""
    
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        
        # Courses
        courses = Course.query.all()
        courses_data = [{'id': c.id, 'title': c.title, 'slug': c.slug, 'description': c.description, 'difficulty': c.difficulty, 'is_published': c.is_published, 'created_at': c.created_at.isoformat()} for c in courses]
        zf.writestr('courses.json', json.dumps(courses_data, indent=2))
        
        # Lessons
        lessons = CourseDay.query.all()
        lessons_data = [{'id': l.id, 'course_id': l.course_id, 'day_number': l.day_number, 'title': l.title, 'slug': l.slug, 'xp_reward': l.xp_reward, 'estimated_minutes': l.estimated_minutes, 'is_published': l.is_published, 'created_at': l.created_at.isoformat()} for l in lessons]
        zf.writestr('lessons.json', json.dumps(lessons_data, indent=2))
        
        # Users
        users = User.query.all()
        users_data = [{'id': u.id, 'username': u.username, 'email': u.email, 'is_verified': u.is_verified, 'created_at': u.created_at.isoformat()} for u in users]
        zf.writestr('users.json', json.dumps(users_data, indent=2))
        
        # Enrollments
        enrollments = CourseEnrollment.query.all()
        enrollments_data = [{'id': e.id, 'user_id': e.user_id, 'course_id': e.course_id, 'enrolled_at': e.enrolled_at.isoformat()} for e in enrollments]
        zf.writestr('enrollments.json', json.dumps(enrollments_data, indent=2))
    
    zip_buffer.seek(0)
    filename = f"rohithbuilds_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=filename)


# ==========================================
# ADMIN BACKUPS PAGE (CSV exports + ZIP)
# ==========================================


@admin_bp.route("/admin/backups", endpoint="backups")
@login_required
@admin_required
def backups_page_list() -> str:
    """List existing backups and provide export UI."""
    backup_root = os.path.join(current_app.root_path, "backups")
    backups = []

    if os.path.exists(backup_root):
        for date_dir in sorted(os.listdir(backup_root), reverse=True):
            date_path = os.path.join(backup_root, date_dir)
            if not os.path.isdir(date_path):
                continue
            files = []
            for fname in sorted(os.listdir(date_path), reverse=True):
                fpath = os.path.join(date_path, fname)
                if os.path.isfile(fpath):
                    files.append({
                        "name": fname,
                        "relpath": f"{date_dir}/{fname}",
                        "size": os.path.getsize(fpath)
                    })
            backups.append({"date": date_dir, "files": files})

    return render_template("admin/backups.html", backups=backups)


@admin_bp.route("/admin/backups/export", methods=["POST"], endpoint="export_backup")
@login_required
@admin_required
def export_backup() -> Response:
    """Export specified tables to CSV, save under backups/YYYY-MM-DD/, and create ZIP."""
    backup_root = os.path.join(current_app.root_path, "backups")
    date_folder = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(backup_root, date_folder)
    os.makedirs(out_dir, exist_ok=True)

    def fmt(v):
        if v is None:
            return ""
        if isinstance(v, datetime):
            return v.isoformat()
        try:
            return json.dumps(v)
        except Exception:
            return str(v)

    created_files = []

    # USERS
    users = User.query.all()
    users_csv = os.path.join(out_dir, "users.csv")
    with open(users_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "username", "email", "is_verified", "created_at"]) 
        for u in users:
            writer.writerow([u.id, u.username, u.email, u.is_verified, fmt(u.created_at)])
    created_files.append(users_csv)

    # COURSES
    courses = Course.query.all()
    courses_csv = os.path.join(out_dir, "courses.csv")
    with open(courses_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "title", "slug", "description", "difficulty", "is_published", "created_at"]) 
        for c in courses:
            writer.writerow([c.id, c.title, c.slug, c.description or "", c.difficulty, c.is_published, fmt(c.created_at)])
    created_files.append(courses_csv)

    # COURSE DAYS
    days = CourseDay.query.all()
    days_csv = os.path.join(out_dir, "course_days.csv")
    with open(days_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "course_id", "day_number", "title", "slug", "short_description", "xp_reward", "estimated_minutes", "is_published", "created_at"]) 
        for d in days:
            writer.writerow([d.id, d.course_id, d.day_number, d.title, d.slug, d.short_description or "", d.xp_reward, d.estimated_minutes, d.is_published, fmt(d.created_at)])
    created_files.append(days_csv)

    # ENROLLMENTS
    enrolls = CourseEnrollment.query.all()
    enroll_csv = os.path.join(out_dir, "course_enrollments.csv")
    with open(enroll_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "user_id", "course_id", "enrolled_at"]) 
        for e in enrolls:
            writer.writerow([e.id, e.user_id, e.course_id, fmt(e.enrolled_at)])
    created_files.append(enroll_csv)

    # LESSON PROGRESS
    progresses = LessonProgress.query.all()
    prog_csv = os.path.join(out_dir, "lesson_progress.csv")
    with open(prog_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "user_id", "course_day_id", "completed", "completed_at"]) 
        for p in progresses:
            writer.writerow([p.id, p.user_id, p.course_day_id, p.completed, fmt(p.completed_at)])
    created_files.append(prog_csv)

    # PROMPTS
    prompts = Prompt.query.all()
    prompts_csv = os.path.join(out_dir, "prompts.csv")
    with open(prompts_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["id", "title", "content", "category", "likes", "copies", "user_id", "created_at"]) 
        for pr in prompts:
            writer.writerow([pr.id, pr.title, pr.content or "", pr.category or "", pr.likes, pr.copies, pr.user_id, fmt(pr.created_at)])
    created_files.append(prompts_csv)

    # PROMPT COLLECTIONS
    try:
        collections = PromptCollection.query.all()
        collections_csv = os.path.join(out_dir, "prompt_collections.csv")
        with open(collections_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "name", "slug", "description"]) 
            for pc in collections:
                writer.writerow([pc.id, pc.name, pc.slug, pc.description or ""])
        created_files.append(collections_csv)
    except Exception:
        pass

    # PROMPT COLLECTION ITEMS
    try:
        items = PromptCollectionItem.query.all()
        items_csv = os.path.join(out_dir, "prompt_collection_items.csv")
        with open(items_csv, "w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(["id", "collection_id", "prompt_id"]) 
            for it in items:
                writer.writerow([it.id, it.collection_id, it.prompt_id])
        created_files.append(items_csv)
    except Exception:
        pass

    # Create ZIP
    zip_name = f"rohithbuilds_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(out_dir, zip_name)
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for p in created_files:
            if os.path.exists(p):
                zf.write(p, arcname=os.path.basename(p))
        manifest = {"generated_at": datetime.now().isoformat(), "files": [os.path.basename(p) for p in created_files]}
        zf.writestr('manifest.json', json.dumps(manifest, indent=2))

    # Return ZIP for download
    try:
        return send_file(zip_path, mimetype='application/zip', as_attachment=True, download_name=zip_name)
    except Exception:
        flash('Backup created but failed to send file. Check backups directory on server.', 'warning')
        return redirect(url_for('admin.backups'))


@admin_bp.route("/admin/backups/download/<path:relpath>", endpoint="download_backup")
@login_required
@admin_required
def download_backup(relpath: str) -> Response:
    """Download a backup file (safe join)."""
    backup_root = os.path.join(current_app.root_path, 'backups')
    safe_path = os.path.normpath(os.path.join(backup_root, relpath))
    if not safe_path.startswith(os.path.abspath(backup_root)) or not os.path.exists(safe_path):
        flash('Requested file not found.', 'danger')
        return redirect(url_for('admin.backups'))
    return send_file(safe_path, as_attachment=True)


@admin_bp.route("/admin/backups/restore", endpoint="backup_restore")
@login_required
@admin_required
def backup_restore() -> str:
    """Render restore instructions page."""
    return render_template('admin/backup_restore.html')


@admin_bp.route("/admin/reviews/<int:review_id>/delete", methods=["POST"], endpoint="delete_review")
@login_required
@admin_required
def delete_review(review_id: int) -> Response:
    """Delete a lesson review."""
    review = LessonReview.query.get_or_404(review_id)
    db.session.delete(review)
    db.session.commit()
    flash("Review deleted successfully.", "success")
    return redirect(url_for("admin.admin"))
