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
        return redirect(url_for("home.home"))

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
                request.args.get("next") or url_for("home.home")
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

    my_prompts = Prompt.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Prompt.created_at.desc()
    ).all()

    fav_count = Favorite.query.filter_by(
        user_id=current_user.id
    ).count()

    total_likes = sum(p.likes for p in my_prompts)

    enrolled_courses = CourseEnrollment.query.filter_by(
        user_id=current_user.id
    ).all()

    completed_lessons = LessonProgress.query.filter_by(
        user_id=current_user.id
    ).count()

    return render_template(
        "dashboard.html",
        prompts=my_prompts,
        fav_count=fav_count,
        total_likes=total_likes,
        enrolled_courses=enrolled_courses,
        completed_lessons=completed_lessons
    )