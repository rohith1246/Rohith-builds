from datetime import date, datetime

from flask import abort, flash, jsonify, redirect, render_template, request, Response, send_file, session, url_for
from flask_login import current_user, login_required

from extensions import csrf
from gemini_helper import rohi_chat
from models import Course, CourseDay, CourseEnrollment, db, LessonProgress, LessonReview, UserCourseProgress
from modules.auth.helpers import send_lesson_review_email
from .badge import generate_badge
from . import learn_bp    



@learn_bp.route("/api/rohi-chat", methods=["POST"])
@csrf.exempt
def rohi_chat_api() -> Response:
    """API endpoint to chat with Rohi the AI tutor."""
    data: dict[str, str] = request.get_json() or {}
    message: str | None = data.get("message")
    course_slug: str | None = data.get("course_slug")
    lesson_slug: str | None = data.get("lesson_slug")

    # Guest limit
    if not current_user.is_authenticated:
        used: int = session.get("rohi_guest_count", 0)
        if used >= 3:
            return jsonify({
                "limit_reached": True,
                "message": "Please sign up to continue chatting with Rohi."
            }), 403
        session["rohi_guest_count"] = used + 1
    else:
        today: date = date.today()
        if current_user.rohi_last_reset_date != today:
            current_user.rohi_messages_today = 0
            current_user.rohi_last_reset_date = today
            db.session.commit()
        if current_user.rohi_messages_today >= 20:
            return jsonify({
                "reply": "You've reached today's limit of 20 messages. Come back tomorrow! Meanwhile explore the lessons at /learn"
            })

    # Retrieve history from session
    history: list[dict[str, str]] = session.get("rohi_history", [])
    history = history[-10:]

    # Context change detection
    last_course: str | None = session.get("rohi_last_course")
    last_lesson: str | None = session.get("rohi_last_lesson")
    if last_course != course_slug or last_lesson != lesson_slug:
        history = []
        session["rohi_history"] = []
        session["rohi_last_course"] = course_slug
        session["rohi_last_lesson"] = lesson_slug

    lesson_context: str = ""
    if course_slug and lesson_slug:
        course: Course | None = Course.query.filter_by(slug=course_slug).first()
        if course:
            lesson: CourseDay | None = CourseDay.query.filter_by(course_id=course.id, slug=lesson_slug).first()
            if lesson:
                lesson_context = f"Course: {course.title}\nLesson: {lesson.title}\nContent:\n{lesson.content}"

    # Call rohi_chat with history and lesson_context
    response: str = rohi_chat(
        message=message,
        lesson_context=lesson_context,
        history=history
    )

    # Increment counter for authenticated users
    if current_user.is_authenticated:
        current_user.rohi_messages_today += 1
        db.session.commit()

    # Append to sliding history and save
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    session["rohi_history"] = history

    return jsonify({
        "reply": response
    })


@learn_bp.route("/api/rohi-chat/clear", methods=["POST"])
@csrf.exempt
def clear_rohi_chat() -> Response:
    """API endpoint to clear Rohi conversation session history."""
    session["rohi_history"] = []
    session.pop("rohi_last_course", None)
    session.pop("rohi_last_lesson", None)
    return jsonify({"success": True})

# ==========================================
# LEARN HOME
# ==========================================

@learn_bp.route("/learn")
def learn() -> str:
    """Render the learning course portal homepage."""

    courses = Course.query.all()

    for course in courses:

        course.total_days = CourseDay.query.filter_by(
            course_id=course.id
        ).count()

    return render_template(
        "learn.html",
        courses=courses
    )


@learn_bp.route("/learn/course/<course_slug>")
def course_page(course_slug: str) -> str:
    """Render the page for a specific course."""

    course = Course.query.filter_by(
        slug=course_slug
    ).first_or_404()

    days = CourseDay.query.filter_by(
        course_id=course.id
    ).order_by(
        CourseDay.day_number.asc()
    ).all()

    is_enrolled = False
    completed_ids = []
    next_day = None

    if current_user.is_authenticated:

        enrollment = CourseEnrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()

        is_enrolled = enrollment is not None

        completed_ids = [
            p.course_day_id
            for p in LessonProgress.query.filter_by(
                user_id=current_user.id,
                completed=True
            ).all()
        ]

        for day in days:
            if day.id not in completed_ids:
                next_day = day
                break

    completed_count = len(
        [d for d in days if d.id in completed_ids]
    )

    progress_percent = 0

    if len(days) > 0:
        progress_percent = int(
            (completed_count / len(days)) * 100
        )

    return render_template(
        "learn/course.html",
        course=course,
        days=days,
        enrolled=is_enrolled,
        completed_day_ids=completed_ids,
        completed_count=completed_count,
        progress_percent=progress_percent,
        next_day=next_day
    )

    
@learn_bp.route("/learn/<course_slug>/<lesson_slug>")
def lesson_page(course_slug: str, lesson_slug: str) -> str:
    """Render the page for a specific course lesson."""

    course = Course.query.filter_by(
        slug=course_slug
    ).first_or_404()

    day = CourseDay.query.filter_by(
        course_id=course.id,
        slug=lesson_slug
    ).first_or_404()
    
    next_day = CourseDay.query.filter(
        CourseDay.course_id == course.id,
        CourseDay.day_number > day.day_number
    ).order_by(
        CourseDay.day_number.asc()
    ).first()

    previous_day = CourseDay.query.filter(
        CourseDay.course_id == course.id,
        CourseDay.day_number < day.day_number
    ).order_by(
        CourseDay.day_number.desc()
    ).first()

    completed = False

    if current_user.is_authenticated:

        completed = LessonProgress.query.filter_by(
            user_id=current_user.id,
            course_day_id=day.id,
            completed=True
        ).first() is not None

    return render_template(
        "learn/lesson.html",
        course=course,
        day=day,
        completed=completed,
        next_day=next_day,
        previous_day=previous_day
    )      
# ==========================================
# PYTHON COURSE PAGE
# ==========================================


# ==========================================
# AI AGENT COURSE PAGE
# ==========================================


# ==========================================
# SINGLE LESSON PAGE
# ==========================================

import json


# ==========================================
# AI AGENT LESSON PAGE
# ==========================================


# ==========================================
# ENROLL COURSE
# ==========================================

@learn_bp.route("/course/<int:course_id>/enroll")
@login_required
def enroll_course(course_id: int) -> Response:
    """Enroll the current user in a course."""
    course = Course.query.get(course_id)
    existing = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=course_id
    ).first()

    if not existing:

        enrollment = CourseEnrollment(
            user_id=current_user.id,
            course_id=course_id
        )

        db.session.add(enrollment)
        db.session.commit()

    flash("Successfully enrolled!", "success")

    return redirect(
    url_for(
        "learn.course_page",
        course_slug=course.slug
    )
)


# ==========================================
# COMPLETE LESSON
# ==========================================
@learn_bp.route("/lesson/<int:day_id>/complete")
@login_required
def complete_lesson(day_id: int) -> Response:
    """Mark a lesson as completed by the current user and award XP."""

    day = CourseDay.query.get_or_404(day_id)

    course = Course.query.get_or_404(day.course_id)

    enrollment = CourseEnrollment.query.filter_by(
        user_id=current_user.id,
        course_id=day.course_id
    ).first()

    if not enrollment:

        flash(
            "Please enroll in the course before completing lessons.",
            "warning"
        )

        return redirect(
            url_for(
                "learn.enroll_course",
                course_id=day.course_id
            )
        )

    existing = LessonProgress.query.filter_by(
        user_id=current_user.id,
        course_day_id=day_id
    ).first()

    if not existing:

        progress = LessonProgress(
            user_id=current_user.id,
            course_day_id=day_id,
            completed=True,
            completed_at=datetime.utcnow()
        )
        db.session.add(progress)

        # Retrieve or initialize user course progress record
        progress_rec = UserCourseProgress.query.filter_by(
            user_id=current_user.id,
            course_id=day.course_id
        ).first()

        if not progress_rec:
            progress_rec = UserCourseProgress(
                user_id=current_user.id,
                course_id=day.course_id,
                current_day=day.day_number,
                completed_days=0,
                total_xp=0
            )
            db.session.add(progress_rec)

        progress_rec.completed_days += 1
        progress_rec.total_xp += (day.xp_reward or 50)
        progress_rec.last_completed_at = datetime.utcnow()

        # Update current_day to next day in progress sequence
        if day.day_number >= progress_rec.current_day:
            progress_rec.current_day = day.day_number + 1

        # Update user learning streak
        today = datetime.utcnow().date()
        if not current_user.last_active_date:
            current_user.current_streak = 1
        else:
            diff = (today - current_user.last_active_date).days
            if diff == 1:
                current_user.current_streak += 1
            elif diff > 1:
                current_user.current_streak = 1
        current_user.last_active_date = today

        db.session.commit()

    flash("Lesson completed!", "success")

    next_day = CourseDay.query.filter(
        CourseDay.course_id == day.course_id,
        CourseDay.day_number > day.day_number
    ).order_by(
        CourseDay.day_number.asc()
    ).first()

    if next_day:
        return redirect(
            url_for(
                "learn.lesson_page",
                course_slug=course.slug,
                lesson_slug=next_day.slug
            )
        )
    else:
        return redirect(
            url_for(
                "learn.course_page",
                course_slug=course.slug
            )
        )


@learn_bp.route("/learn/lesson/<int:day_id>/review", methods=["POST"])
@login_required
def submit_review(day_id: int) -> Response:
    """Asynchronously submit a rating review for a lesson."""
    day: CourseDay = CourseDay.query.get_or_404(day_id)
    
    data: dict[str, Any] = request.get_json() or {}
    rating: Any = data.get("rating")
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Invalid rating value. Must be 1 to 5."}), 400
        
    existing: LessonReview | None = LessonReview.query.filter_by(user_id=current_user.id, course_day_id=day.id).first()
    if existing:
        existing.rating = rating
        existing.created_at = datetime.utcnow()
    else:
        review: LessonReview = LessonReview(
            user_id=current_user.id,
            course_day_id=day.id,
            rating=rating
        )
        db.session.add(review)
        
    db.session.commit()
    
    send_lesson_review_email(current_user, day, rating)
    
    return jsonify({"success": True, "message": "Rating saved successfully!"})


# ──────────────────────────────────────────────────────────
#  COURSE COMPLETION BADGE
# ──────────────────────────────────────────────────────────

from models import User  # noqa: E402 (local import to avoid circular)

def _resolve_badge_or_404(username: str, course_slug: str):
    """
    Return (user, course, completed_at) for ANY user+course combination.
    Aborts 404 if user/course not found, 403 if course not 100% complete.
    This is called by the PUBLIC routes so anyone can view a shared badge.
    """
    from models import User
    user = User.query.filter_by(username=username).first_or_404()
    course = Course.query.filter_by(slug=course_slug, is_published=True).first_or_404()
    total_days = CourseDay.query.filter_by(course_id=course.id, is_published=True).count()
    if total_days == 0:
        abort(404)
    completed_count = (
        LessonProgress.query
        .join(CourseDay, LessonProgress.course_day_id == CourseDay.id)
        .filter(
            LessonProgress.user_id == user.id,
            CourseDay.course_id == course.id,
            LessonProgress.completed == True
        ).count()
    )
    progress = int((completed_count / total_days) * 100)
    if progress < 100:
        abort(404)   # 404 not 403 — don't reveal incomplete badges exist
    last = (
        LessonProgress.query
        .join(CourseDay, LessonProgress.course_day_id == CourseDay.id)
        .filter(
            LessonProgress.user_id == user.id,
            CourseDay.course_id == course.id,
            LessonProgress.completed == True
        )
        .order_by(LessonProgress.completed_at.desc())
        .first()
    )
    completed_at = last.completed_at if last and last.completed_at else datetime.utcnow()
    return user, course, completed_at


# ── Public badge image — no login needed ──────────────────
@learn_bp.route("/badge/<username>/<course_slug>/image")
def badge_image(username: str, course_slug: str) -> Response:
    """Public PNG badge — accessible to anyone with the link."""
    import io
    user, course, completed_at = _resolve_badge_or_404(username, course_slug)
    png_bytes = generate_badge(
        course_title=course.title,
        username=user.username,
        completed_date=completed_at
    )
    return send_file(
        io.BytesIO(png_bytes),
        mimetype="image/png",
        download_name=f"rohithbuilds-badge-{course_slug}.png",
        as_attachment=request.args.get("dl") == "1"
    )


# ── Public badge share page — no login needed ─────────────
@learn_bp.route("/badge/<username>/<course_slug>")
def badge_page(username: str, course_slug: str) -> str:
    """
    Publicly viewable badge page.
    Anyone with this URL can see the badge — perfect for sharing on
    LinkedIn, X/Twitter, WhatsApp, etc.
    """
    user, course, completed_at = _resolve_badge_or_404(username, course_slug)
    badge_img_url = url_for(
        "learn.badge_image",
        username=username,
        course_slug=course_slug,
        _external=True
    )
    share_text = (
        f"I just completed '{course.title}' on Rohith Builds! "
        f"🏆 #AI #Learning #RohithBuilds"
    )
    return render_template(
        "learn/badge.html",
        badge_user=user,
        course=course,
        completed_at=completed_at,
        badge_img_url=badge_img_url,
        share_text=share_text
    )


# ── Private redirect — login required, goes to your public badge ─
@learn_bp.route("/badge/<course_slug>")
@login_required
def my_badge(course_slug: str):
    """
    Logged-in user's shortcut — verifies completion then
    redirects to their public badge URL.
    """
    course = Course.query.filter_by(slug=course_slug, is_published=True).first_or_404()
    total_days = CourseDay.query.filter_by(course_id=course.id, is_published=True).count()
    if total_days == 0:
        abort(404)
    completed_count = (
        LessonProgress.query
        .join(CourseDay, LessonProgress.course_day_id == CourseDay.id)
        .filter(
            LessonProgress.user_id == current_user.id,
            CourseDay.course_id == course.id,
            LessonProgress.completed == True
        ).count()
    )
    if int((completed_count / total_days) * 100) < 100:
        flash("Complete the course first to unlock your badge!", "error")
        return redirect(url_for("learn.course_page", course_slug=course_slug))
    return redirect(url_for(
        "learn.badge_page",
        username=current_user.username,
        course_slug=course_slug
    ))
