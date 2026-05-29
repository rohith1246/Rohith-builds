from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import (
    login_required,
    current_user
)

from datetime import datetime

from . import learn_bp

from models import (
    db,
    Course,
    CourseDay,
    CourseEnrollment,
    LessonProgress
)


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


# ==========================================
# PYTHON COURSE PAGE
# ==========================================

@learn_bp.route("/learn/python-ai-course")
def python_ai_course():

    course = Course.query.filter_by(
        slug="python-ai-course"
    ).first_or_404()

    days = CourseDay.query.filter_by(
        course_id=course.id
    ).order_by(
        CourseDay.day_number.asc()
    ).all()

    enrolled = False

    if current_user.is_authenticated:

        enrolled = CourseEnrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first() is not None

    return render_template(
        "learn/python_course.html",
        course=course,
        days=days,
        enrolled=enrolled
    )


# ==========================================
# SINGLE LESSON PAGE
# ==========================================

@learn_bp.route("/learn/python-ai-course/<slug>")
def python_course_day(slug):

    day = CourseDay.query.filter_by(
        slug=slug
    ).first_or_404()

    completed = False

    if current_user.is_authenticated:

        completed = LessonProgress.query.filter_by(
            user_id=current_user.id,
            course_day_id=day.id
        ).first() is not None

    return render_template(
        "learn/python_day.html",
        day=day,
        completed=completed
    )


# ==========================================
# ENROLL COURSE
# ==========================================

@learn_bp.route("/course/<int:course_id>/enroll")
@login_required
def enroll_course(course_id):

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
        url_for("learn.python_ai_course")
    )


# ==========================================
# COMPLETE LESSON
# ==========================================

@learn_bp.route("/lesson/<int:day_id>/complete")
@login_required
def complete_lesson(day_id):

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

    return redirect(
        request.referrer or
        url_for("learn.python_ai_course")
    )