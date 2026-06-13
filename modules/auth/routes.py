from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.exc import IntegrityError

from models import (
    db,
    User,
    Prompt,
    Favorite,
    CourseEnrollment,
    LessonProgress
)
from models import CourseDay, UserCourseProgress, Course
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from forms import RegisterForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from .helpers import send_verification_email, verify_token, send_password_reset_email, verify_reset_token
from . import auth_bp


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if current_user.is_authenticated:
        return redirect(url_for("home.home"))

    form = RegisterForm()

    if form.validate_on_submit():

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            is_verified=False
        )

        db.session.add(user)

        try:

            db.session.commit()

            if send_verification_email(user):
                flash(
                    "Verification email sent. Please check spam/promotions folder.",
                    "verification"
                )
            else:
                flash(
                    "Account created! Email failed — resend from your dashboard.",
                    "warning"
                )

            return redirect(url_for("auth.login"))

        except IntegrityError:

            db.session.rollback()
            flash("Something went wrong. Please try again.", "danger")

    return render_template("register.html", form=form)


@auth_bp.route("/verify-email/<token>")
def verify_email(token):

    email = verify_token(token)

    if not email:
        flash("Verification link is invalid or expired.", "danger")
        return redirect(url_for("auth.register"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("User not found. Please sign up.", "danger")
        return redirect(url_for("auth.register"))

    if user.is_verified:
        flash("Email already verified! Log in now.", "info")
        return redirect(url_for("auth.login"))

    user.is_verified = True
    db.session.commit()

    flash("✅ Email verified! You can now use all features.", "success")

    return redirect(url_for("auth.login"))


@auth_bp.route("/resend-verification", methods=["POST"])
@login_required
def resend_verification():

    if current_user.is_verified:
        flash("Your email is already verified!", "info")
        return redirect(url_for("home.home"))

    if send_verification_email(current_user):
        flash(
            "Verification email sent. Please check spam/promotions folder.",
            "verification"
        )
    else:
        flash("Failed to send email. Please try again.", "danger")

    return redirect(url_for("home.home"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(
            user.password_hash,
            form.password.data
        ):

            login_user(user)

            flash(f"Welcome back, {user.username}!", "success")

            if not user.is_verified:
                flash(
                    "Your account still needs verification. Check spam/promotions folder or resend from your dashboard.",
                    "verification"
                )

            return redirect(
                request.args.get("next") or url_for("auth.dashboard")
            )

        flash("Invalid email or password.", "danger")

    return render_template("login.html", form=form)


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():

    if current_user.is_authenticated:
        return redirect(url_for("home.home"))

    form = ForgotPasswordForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Always show success to prevent email enumeration
        if user:
            send_password_reset_email(user)

        flash(
            "If that email is registered, you'll receive a reset link shortly. Check your spam folder too!",
            "info"
        )
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):

    if current_user.is_authenticated:
        return redirect(url_for("home.home"))

    email = verify_reset_token(token)

    if not email:
        flash("This password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash("✅ Password reset successfully! You can now log in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form, token=token)


@auth_bp.route("/logout")
@login_required
def logout():

    logout_user()

    flash("Logged out. See you soon!", "info")

    return redirect(url_for("home.home"))


@auth_bp.route("/dashboard")
@login_required
def dashboard():
    # Latest prompts (limit 10)
    my_prompts = (
        Prompt.query
        .filter_by(user_id=current_user.id)
        .order_by(Prompt.created_at.desc())
        .limit(10)
        .all()
    )

    # Favorites (recent first). If Favorite has created_at use it, otherwise fall back to id ordering.
    fav_query = Favorite.query.filter_by(user_id=current_user.id)

    if hasattr(Favorite, "created_at"):
        fav_query = fav_query.order_by(Favorite.created_at.desc())
    else:
        fav_query = fav_query.order_by(Favorite.id.desc())

    fav_records = fav_query.limit(10).all()

    fav_prompts = []
    for f in fav_records:
        p = Prompt.query.get(f.prompt_id)
        if p:
            fav_prompts.append(p)

    fav_count = Favorite.query.filter_by(user_id=current_user.id).count()

    # Likes total for user's prompts
    total_likes = db.session.query(func.coalesce(func.sum(Prompt.likes), 0)).filter(Prompt.user_id == current_user.id).scalar() or 0

    # Enrollments + related course info (eager load course)
    enrollments = (
        CourseEnrollment.query.options(joinedload(CourseEnrollment.course))
        .filter_by(user_id=current_user.id)
        .all()
    )

    course_ids = [e.course_id for e in enrollments]

    # Suggested courses: published courses the user hasn't enrolled in
    suggested_courses = []
    try:
        q = Course.query.filter(Course.is_published == True)
        if course_ids:
            q = q.filter(~Course.id.in_(course_ids))
        suggested_courses = q.order_by(Course.created_at.desc()).limit(3).all()
    except Exception:
        suggested_courses = []

    # All days for enrolled courses (grouped)
    days = []
    if course_ids:
        days = (
            CourseDay.query
            .filter(CourseDay.course_id.in_(course_ids))
            .order_by(CourseDay.course_id.asc(), CourseDay.day_number.asc())
            .all()
        )

    from collections import defaultdict

    days_by_course = defaultdict(list)
    for d in days:
        days_by_course[d.course_id].append(d)

    # Completed lessons mapping per course
    completed_entries = []
    if course_ids:
        completed_entries = (
            db.session.query(CourseDay.course_id, LessonProgress.course_day_id)
            .join(LessonProgress, LessonProgress.course_day_id == CourseDay.id)
            .filter(
                LessonProgress.user_id == current_user.id,
                LessonProgress.completed == True,
                CourseDay.course_id.in_(course_ids),
            )
            .all()
        )

    completed_by_course = defaultdict(set)
    for course_id, day_id in completed_entries:
        completed_by_course[course_id].add(day_id)

    # Build course info payload (no N+1 queries for days)
    courses_info = []
    for enrollment in enrollments:
        course = enrollment.course
        course_days = days_by_course.get(course.id, [])
        total_days = len(course_days)
        completed_count = len(completed_by_course.get(course.id, set()))

        progress_percent = 0
        if total_days > 0:
            progress_percent = int((completed_count / total_days) * 100)

        courses_info.append({
            "enrollment": enrollment,
            "course": course,
            "total_days": total_days,
            "completed": completed_count,
            "progress": progress_percent,
        })

    # Overall stats
    total_enrolled = len(enrollments)

    total_completed_lessons = (
        db.session.query(func.count(LessonProgress.id))
        .filter(LessonProgress.user_id == current_user.id, LessonProgress.completed == True)
        .scalar()
    ) or 0

    total_xp = (
        db.session.query(func.coalesce(func.sum(UserCourseProgress.total_xp), 0))
        .filter(UserCourseProgress.user_id == current_user.id)
        .scalar()
    ) or 0

    # Completion rate across enrolled courses (weighted by lessons)
    total_days_all = sum(info["total_days"] for info in courses_info)
    completion_rate = 0
    if total_days_all > 0:
        completion_rate = int((sum(info["completed"] for info in courses_info) / total_days_all) * 100)

    # Recent activity: enrollments, lesson completions, prompt creations, favorites
    recent_events = []

    # Enrollments
    for e in enrollments:
        recent_events.append({
            "type": "enrolled",
            "label": f"Enrolled in {e.course.title}",
            "time": e.enrolled_at,
            "meta": {"course": e.course}
        })

    # Lesson completions
    lesson_completions = (
        db.session.query(LessonProgress, CourseDay, Course)
        .join(CourseDay, LessonProgress.course_day_id == CourseDay.id)
        .join(Course, Course.id == CourseDay.course_id)
        .filter(LessonProgress.user_id == current_user.id, LessonProgress.completed == True)
        .order_by(LessonProgress.completed_at.desc())
        .limit(20)
        .all()
    )

    for lp, day, course in lesson_completions:
        recent_events.append({
            "type": "lesson_completed",
            "label": f"Completed {day.title} ({course.title})",
            "time": lp.completed_at,
            "meta": {"course": course, "day": day}
        })

    # Prompt creations
    recent_prompts = (
        Prompt.query.filter_by(user_id=current_user.id)
        .order_by(Prompt.created_at.desc())
        .limit(10)
        .all()
    )

    for p in recent_prompts:
        recent_events.append({
            "type": "prompt_created",
            "label": f"Created prompt: {p.title}",
            "time": p.created_at,
            "meta": {"prompt": p}
        })

    # Favorites (if created_at available use it)
    for f in fav_records:
        fav_time = getattr(f, "created_at", None)
        recent_events.append({
            "type": "prompt_favorited",
            "label": f"Favorited: {Prompt.query.get(f.prompt_id).title}",
            "time": fav_time,
            "meta": {"prompt_id": f.prompt_id}
        })

    # sort newest first (items without time are placed after timed events)
    from datetime import datetime

    recent_events = sorted(
        recent_events,
        key=lambda e: e["time"] or datetime(1970, 1, 1),
        reverse=True,
    )

    # Achievements
    achievements = {
        "first_lesson": total_completed_lessons >= 1,
        "ten_lessons": total_completed_lessons >= 10,
        "first_prompt": (
            db.session.query(func.count(Prompt.id)).filter(Prompt.user_id == current_user.id).scalar() or 0
        ) >= 1,
        "first_course_complete": any(info["progress"] == 100 for info in courses_info),
    }
    return render_template(
        "dashboard.html",
        prompts=my_prompts,
        fav_prompts=fav_prompts,
        fav_count=fav_count,
        total_likes=total_likes,
        enrolled_courses=enrollments,
        courses_info=courses_info,
        completed_lessons=total_completed_lessons,
        total_xp=total_xp,
        total_enrolled=total_enrolled,
        completion_rate=completion_rate,
        recent_events=recent_events,
        achievements=achievements,
        suggested_courses=suggested_courses
    )


import secrets
import re
import urllib.parse
import requests
from flask import session, abort

@auth_bp.route("/login/google")
def google_login():
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    if not client_id:
        flash("Google OAuth is not configured on this server.", "danger")
        return redirect(url_for("auth.login"))
        
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    
    redirect_uri = url_for("auth.google_callback", _external=True)
    
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account"
    }
    
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(auth_url)


@auth_bp.route("/login/google/callback")
def google_callback():
    # Verify state
    session_state = session.pop("oauth_state", None)
    request_state = request.args.get("state")
    if not session_state or session_state != request_state:
        abort(400, "Invalid OAuth state parameter.")
        
    code = request.args.get("code")
    if not code:
        flash("Failed to authenticate with Google.", "danger")
        return redirect(url_for("auth.login"))
        
    client_id = current_app.config.get("GOOGLE_CLIENT_ID")
    client_secret = current_app.config.get("GOOGLE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        flash("Google OAuth is not configured on this server.", "danger")
        return redirect(url_for("auth.login"))
        
    redirect_uri = url_for("auth.google_callback", _external=True)
    
    # Exchange authorization code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        token_resp = requests.post(token_url, data=data, timeout=10)
        token_resp.raise_for_status()
        token_data = token_resp.json()
    except Exception as e:
        current_app.logger.error(f"Google OAuth token exchange failed: {e}")
        flash("Failed to retrieve access token from Google.", "danger")
        return redirect(url_for("auth.login"))
        
    access_token = token_data.get("access_token")
    if not access_token:
        flash("Google did not return an access token.", "danger")
        return redirect(url_for("auth.login"))
        
    # Get user profile information
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        userinfo_resp = requests.get(userinfo_url, headers=headers, timeout=10)
        userinfo_resp.raise_for_status()
        userinfo = userinfo_resp.json()
    except Exception as e:
        current_app.logger.error(f"Google OAuth userinfo request failed: {e}")
        flash("Failed to retrieve user profile info from Google.", "danger")
        return redirect(url_for("auth.login"))
        
    email = userinfo.get("email")
    email_verified = userinfo.get("email_verified")
    name = userinfo.get("name", "")
    google_id = userinfo.get("sub")
    
    if not email or not email_verified:
        flash("Google account must have a verified email address.", "danger")
        return redirect(url_for("auth.login"))
        
    # Find existing user by Google ID or by Email
    user = None
    if google_id:
        user = User.query.filter_by(google_id=google_id).first()
        
    if not user:
        user = User.query.filter_by(email=email).first()
        if user and google_id:
            # Link Google ID to existing account
            user.google_id = google_id
            db.session.commit()
            
    if user:
        # Log existing user in
        if not user.is_verified:
            user.is_verified = True
            db.session.commit()
        login_user(user)
        flash(f"Welcome back, {user.username}!", "success")
        return redirect(url_for("auth.dashboard"))
        
    # Register new user
    base_username = name.lower().replace(" ", "")
    if not base_username:
        base_username = email.split("@")[0]
    base_username = re.sub(r"[^a-zA-Z0-9]", "", base_username)
    
    username = base_username
    suffix = 1
    while User.query.filter_by(username=username).first():
        username = f"{base_username}{suffix}"
        suffix += 1
        
    random_pass = secrets.token_urlsafe(32)
    password_hash = generate_password_hash(random_pass)
    
    new_user = User(
        username=username,
        email=email,
        password_hash=password_hash,
        is_verified=True,
        google_id=google_id
    )
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    flash("Your account has been created successfully with Google!", "success")
    return redirect(url_for("auth.dashboard"))
