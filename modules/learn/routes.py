from datetime import date, datetime, timezone
from typing import Any

from flask import abort, flash, jsonify, redirect, render_template, request, Response, send_file, session, url_for
from flask_login import current_user, login_required

from extensions import csrf
from gemini_helper import rohi_chat
from models import Course, CourseDay, CourseEnrollment, db, LessonProgress, LessonReview, UserCourseProgress, ChatMessage, UserMemory
from modules.auth.helpers import send_lesson_review_email
from .badge import generate_badge
from modules.rate_limiter import rate_limit
from . import learn_bp


@learn_bp.route("/api/rohi-chat", methods=["POST"])
@rate_limit(limit=20, period=3600)
def rohi_chat_api() -> Response:
    """API endpoint to chat with Rohi the AI tutor."""
    import logging
    import re
    from threading import Thread
    from flask import current_app

    data: dict[str, str] = request.get_json() or {}
    message: str | None = data.get("message")
    course_slug: str | None = data.get("course_slug")
    lesson_slug: str | None = data.get("lesson_slug")

    if not message or not message.strip():
        return jsonify({"success": False, "message": "Message content cannot be empty."}), 400

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
                "limit_reached": True,
                "message": "You've reached today's limit of 20 messages. Come back tomorrow! Meanwhile explore the lessons at /learn"
            }), 429

    # Retrieve history (persistent DB for logged in, session for guests)
    history: list[dict[str, str]] = []
    if current_user.is_authenticated:
        msgs = ChatMessage.query.filter_by(user_id=current_user.id).order_by(ChatMessage.created_at.desc()).limit(10).all()
        for msg in reversed(msgs):
            history.append({"role": "user" if msg.role == "user" else "assistant", "content": msg.content})
    else:
        history = session.get("rohi_history", [])
        history = history[-10:]

    # Context change detection
    last_course: str | None = session.get("rohi_last_course")
    last_lesson: str | None = session.get("rohi_last_lesson")
    if last_course != course_slug or last_lesson != lesson_slug:
        history = []
        if current_user.is_authenticated:
            # We don't wipe the DB history, but we reset sliding context history
            # (or we can delete old context-dependent messages to keep sliding focus clear)
            pass
        session["rohi_history"] = []
        session["rohi_last_course"] = course_slug
        session["rohi_last_lesson"] = lesson_slug

    lesson_context: str = ""
    # 1. Lesson-specific context
    if course_slug and lesson_slug:
        course: Course | None = Course.query.filter_by(slug=course_slug).first()
        if course:
            lesson: CourseDay | None = CourseDay.query.filter_by(course_id=course.id, slug=lesson_slug).first()
            if lesson:
                lesson_context = f"Course: {course.title}\nLesson: {lesson.title}\nContent:\n{lesson.content}"
    
    # 2. General context using keyword RAG search
    else:
        # Search CourseDay content for keywords in the message
        words = re.findall(r'\w+', (message or "").lower())
        stopwords = {"what", "is", "how", "to", "the", "a", "an", "of", "and", "in", "on", "for", "with", "python", "ai", "rohi"}
        keywords = [w for w in words if len(w) > 2 and w not in stopwords]
        if keywords:
            from sqlalchemy import or_
            conditions = []
            for kw in keywords[:5]:
                conditions.append(CourseDay.content.ilike(f"%{kw}%"))
                conditions.append(CourseDay.title.ilike(f"%{kw}%"))
            if conditions:
                matched_lesson = CourseDay.query.filter(or_(*conditions)).first()
                if matched_lesson:
                    course = Course.query.get(matched_lesson.course_id)
                    course_title = course.title if course else "Unknown Course"
                    lesson_context = f"RAG RETRIEVED LESSON CONTEXT (Matches search keywords: {', '.join(keywords[:3])}):\nCourse: {course_title}\nLesson: {matched_lesson.title}\nContent:\n{matched_lesson.content}"

    # 3. User memories / behavior profile
    memories_str: str = ""
    if current_user.is_authenticated:
        user_mems = UserMemory.query.filter_by(user_id=current_user.id).all()
        if user_mems:
            memories_str = "\nSTUDENT PROFILE (What you know about this student from prior chat history):\n"
            for mem in user_mems:
                memories_str += f"- {mem.memory_key.replace('_', ' ').capitalize()}: {mem.memory_value}\n"

    # Combine context
    combined_context: str = (lesson_context or "") + (memories_str or "")

    # Call rohi_chat
    response: str = rohi_chat(
        message=message,
        lesson_context=combined_context,
        history=history
    )

    # Save to ChatMessage persistent history and update today's count
    if current_user.is_authenticated:
        current_user.rohi_messages_today += 1
        
        user_msg = ChatMessage(user_id=current_user.id, role="user", content=message)
        ai_msg = ChatMessage(user_id=current_user.id, role="assistant", content=response)
        db.session.add(user_msg)
        db.session.add(ai_msg)
        db.session.commit()

        # Asynchronously extract new memories from user message in background thread
        app = current_app._get_current_object()
        def extract_memory_thread():
            with app.app_context():
                try:
                    extract_and_save_user_memory(current_user.id, message)
                except Exception as e:
                    logging.error(f"[Memory Extraction] Thread execution failed. Error: {e}")
        Thread(target=extract_memory_thread).start()
    else:
        # Append to guest session history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": response})
        session["rohi_history"] = history

    return jsonify({
        "reply": response
    })


def extract_and_save_user_memory(user_id: int, user_message: str):
    """Analyze student message to extract personal profile details or learning preferences."""
    import logging
    system_prompt = """
    You are a student profile extractor. Analyze the student's message and extract any personal profile details or learning preferences.
    Keys to look for:
    - graduation_year (e.g. 2025, 2026, 2027)
    - career_interest (e.g. Python, AI, Backend, Frontend)
    - experience_level (e.g. beginner, student, intermediate)
    - struggling_with (e.g. loops, recursion, decorators, databases)
    - name (if they explicitly state their name)
    
    Output format MUST be strictly:
    key=value
    
    Example:
    graduation_year=2026
    struggling_with=recursion
    
    Only output keys if they are clearly and explicitly mentioned in the message. Do not make assumptions. If nothing is found, output nothing. Do not explain your output.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    from gemini_helper import call_gemini, call_groq_with_fallback
    extracted = call_gemini(messages, max_tokens=100)
    if not extracted:
        extracted = call_groq_with_fallback(messages, max_tokens=100)
        
    if extracted:
        lines = extracted.strip().split("\n")
        db_updated = False
        for line in lines:
            if "=" in line:
                parts = line.split("=", 1)
                key = parts[0].strip().lower()
                val = parts[1].strip()
                if key in ["graduation_year", "career_interest", "experience_level", "struggling_with", "name"] and val:
                    # Save/update memory in DB
                    mem = UserMemory.query.filter_by(user_id=user_id, memory_key=key).first()
                    if mem:
                        if key == "struggling_with" and mem.memory_value != val:
                            if val not in mem.memory_value:
                                mem.memory_value = f"{mem.memory_value}, {val}"
                                db_updated = True
                        elif mem.memory_value != val:
                            mem.memory_value = val
                            db_updated = True
                    else:
                        mem = UserMemory(user_id=user_id, memory_key=key, memory_value=val)
                        db.session.add(mem)
                        db_updated = True
        if db_updated:
            db.session.commit()
            logging.info(f"[Memory Extraction] Extracted and saved memories for user_id {user_id}")


@learn_bp.route("/api/rohi-chat/clear", methods=["POST"])
def clear_rohi_chat() -> Response:
    """API endpoint to clear Rohi conversation session history and DB history."""
    if current_user.is_authenticated:
        # Delete ChatMessage history for the user
        ChatMessage.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
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

    # Query all courses and sort them so that 'developer-setup-guide' is first,
    # followed by 'ai-agent-course', and then the rest of the courses.
    all_courses = Course.query.all()
    courses = sorted(
        all_courses,
        key=lambda c: (
            0 if c.slug == "developer-setup-guide"
            else (1 if c.slug == "ai-agent-course" else 2),
            c.id
        )
    )

    for course in courses:

        course.total_days = CourseDay.query.filter_by(
            course_id=course.id
        ).count()

        course.enrollment_count = CourseEnrollment.query.filter_by(
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
    is_enrolled = False
    preceding_completed = True
    preceding_day = None

    if current_user.is_authenticated:
        enrollment = CourseEnrollment.query.filter_by(
            user_id=current_user.id,
            course_id=course.id
        ).first()
        is_enrolled = enrollment is not None

        completed = LessonProgress.query.filter_by(
            user_id=current_user.id,
            course_day_id=day.id,
            completed=True
        ).first() is not None

        preceding_day = CourseDay.query.filter(
            CourseDay.course_id == course.id,
            CourseDay.day_number < day.day_number
        ).order_by(
            CourseDay.day_number.desc()
        ).first()
        if preceding_day:
            preceding_progress = LessonProgress.query.filter_by(
                user_id=current_user.id,
                course_day_id=preceding_day.id,
                completed=True
            ).first()
            if not preceding_progress:
                preceding_completed = False

    return render_template(
        "learn/lesson.html",
        course=course,
        day=day,
        completed=completed,
        next_day=next_day,
        previous_day=previous_day,
        enrolled=is_enrolled,
        preceding_completed=preceding_completed,
        preceding_day=preceding_day
    )  

@learn_bp.route("/course/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll_course(course_id: int) -> Response:
    """Enroll the current user in a course."""
    course = db.session.get(Course, course_id)
    if not course or not course.is_published:
        flash("Course not found.", "danger")
        return redirect(url_for("learn.learn"))
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
@learn_bp.route("/lesson/<int:day_id>/complete", methods=["POST"])
@login_required
def complete_lesson(day_id: int) -> Response:
    """Mark a lesson as completed by the current user and award XP."""

    day = CourseDay.query.get_or_404(day_id)
    if not day.is_published:
        flash("This lesson is not available yet.", "warning")
        return redirect(url_for("learn.learn"))

    course = Course.query.get_or_404(day.course_id)
    if not course.is_published:
        flash("This course is not available yet.", "warning")
        return redirect(url_for("learn.learn"))

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

    # Enforce sequential completion progression
    preceding_day = CourseDay.query.filter(
        CourseDay.course_id == day.course_id,
        CourseDay.day_number < day.day_number
    ).order_by(
        CourseDay.day_number.desc()
    ).first()
    
    if preceding_day:
        completed_preceding = LessonProgress.query.filter_by(
            user_id=current_user.id,
            course_day_id=preceding_day.id,
            completed=True
        ).first()
        if not completed_preceding:
            flash(f"You cannot mark this lesson as completed until you complete Day {preceding_day.day_number}.", "warning")
            return redirect(url_for("learn.lesson_page", course_slug=course.slug, lesson_slug=day.slug))

    existing = LessonProgress.query.filter_by(
        user_id=current_user.id,
        course_day_id=day_id
    ).first()

    if not existing:

        progress = LessonProgress(
            user_id=current_user.id,
            course_day_id=day_id,
            completed=True,
            completed_at=datetime.now(timezone.utc)
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
        progress_rec.last_completed_at = datetime.now(timezone.utc)

        # Update overall user XP
        current_user.xp = (current_user.xp or 0) + (day.xp_reward or 50)

        # Update current_day to next day in progress sequence
        if day.day_number >= progress_rec.current_day:
            progress_rec.current_day = day.day_number + 1

        # Update user learning streak (only once per day)
        today = datetime.now(timezone.utc).date()
        if not current_user.last_active_date or current_user.last_active_date < today:
            if current_user.last_active_date:
                diff = (today - current_user.last_active_date).days
                current_user.current_streak = current_user.current_streak + 1 if diff == 1 else 1
            else:
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
    
    completed = LessonProgress.query.filter_by(
        user_id=current_user.id,
        course_day_id=day.id,
        completed=True
    ).first() is not None

    if not completed:
        return jsonify({"success": False, "message": "You must complete this lesson before submitting a review."}), 403
    
    data: dict[str, Any] = request.get_json() or {}
    rating: Any = data.get("rating")
    
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Invalid rating value. Must be 1 to 5."}), 400
        
    existing: LessonReview | None = LessonReview.query.filter_by(user_id=current_user.id, course_day_id=day.id).first()
    if existing:
        existing.rating = rating
        existing.created_at = datetime.now(timezone.utc)
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
    course = Course.query.filter_by(slug=course_slug).first_or_404()
    total_days = CourseDay.query.filter_by(course_id=course.id).count()
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
    completed_at = last.completed_at if last and last.completed_at else datetime.now(timezone.utc)
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
