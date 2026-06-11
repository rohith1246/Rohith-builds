from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request,
    session
)

from flask_login import (
    login_required,
    current_user
)
from extensions import csrf
from datetime import datetime

from . import learn_bp

from models import (
    db,
    Course,
    CourseDay,
    CourseEnrollment,
    LessonProgress,
    LessonReview
)


from gemini_helper import rohi_chat
from flask import jsonify    



@learn_bp.route("/api/rohi-chat", methods=["POST"])
@csrf.exempt

def rohi_chat_api():

    data = request.get_json()
    
    

    message = data.get("message")
    course_slug = data.get("course_slug")
    lesson_slug = data.get("lesson_slug")
    
    
    # Guest limit
    if not current_user.is_authenticated:

        used = session.get("rohi_guest_count", 0)

        if used >= 3:

            return jsonify({
            "limit_reached": True,
            "message": "Please sign up to continue chatting with Rohi."
        }), 403

        session["rohi_guest_count"] = used + 1

# Global Rohi mode
    if not course_slug or not lesson_slug:

        response = rohi_chat(
            message=message,
            course_name="RohithBuilds",
            lesson_title="General Learning",
            lesson_content=""
        )

        return jsonify({
        "reply": response
        })

# Lesson mode
    course = Course.query.filter_by(
        slug=course_slug
    ).first_or_404()

    lesson = CourseDay.query.filter_by(
        course_id=course.id,
        slug=lesson_slug
    ).first_or_404()
    response = rohi_chat(

        message=message,

        course_name=course.title,

        lesson_title=lesson.title,

        lesson_content=lesson.content
    )

    return jsonify({
        "reply": response
    })

# ==========================================
# LEARN HOME
# ==========================================

@learn_bp.route("/learn")
def learn():

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
def course_page(course_slug):

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
def lesson_page(course_slug, lesson_slug):

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
def enroll_course(course_id):
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
def complete_lesson(day_id):

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
def submit_review(day_id):
    """Asynchronously submit a star rating review for a lesson."""
    day = CourseDay.query.get_or_404(day_id)
    
    data = request.get_json() or {}
    rating = data.get("rating")
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Invalid rating value. Must be 1 to 5."}), 400
        
    existing = LessonReview.query.filter_by(user_id=current_user.id, course_day_id=day.id).first()
    if existing:
        existing.rating = rating
        existing.created_at = datetime.utcnow()
    else:
        review = LessonReview(
            user_id=current_user.id,
            course_day_id=day.id,
            rating=rating
        )
        db.session.add(review)
        
    db.session.commit()
    
    from modules.auth.helpers import send_lesson_review_email
    send_lesson_review_email(current_user, day, rating)
    
    return jsonify({"success": True, "message": "Rating saved successfully!"})
    
