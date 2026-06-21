import logging
import os
from typing import Any

from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer
import sendgrid
from sendgrid.helpers.mail import Mail

from models import CourseDay, User


def generate_verification_token(email: str) -> str:
    """Generate a secure email verification token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirm-salt")


def verify_token(token: str, expiration: int = 3600) -> str | None:
    """Verify and decode the email verification token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
    except Exception:
        return None


def generate_reset_token(email: str) -> str:
    """Generate a secure password reset token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset-salt")


def verify_reset_token(token: str, expiration: int = 3600) -> str | None:
    """Verify and decode the password reset token."""
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None


def send_verification_email(user: User) -> bool:
    """Send an email verification link to the user via SendGrid."""
    token: str = generate_verification_token(user.email)
    verify_url: str = url_for("auth.verify_email", token=token, _external=True)
    try:
        html_content: str = render_template(
            "email/verify_email.html",
            username=user.username.title(),
            verify_url=verify_url
        )
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        message = Mail(
            from_email="rohithbuildsofficial@gmail.com",
            to_emails=user.email,
            subject="Verify Your Email - RohithBuilds",
            html_content=html_content
        )
        response = sg.send(message)
        logging.info(f"[OK] SendGrid sent: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"[ERROR] SendGrid error: {e}")
        return False


def send_password_reset_email(user: User) -> bool:
    """Send a password reset link to the user via SendGrid."""
    token: str = generate_reset_token(user.email)
    reset_url: str = url_for("auth.reset_password", token=token, _external=True)
    try:
        html_content: str = render_template(
            "email/reset_password.html",
            username=user.username.title(),
            reset_url=reset_url
        )
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        message = Mail(
            from_email="rohithbuildsofficial@gmail.com",
            to_emails=user.email,
            subject="Reset Your Password - RohithBuilds",
            html_content=html_content
        )
        response = sg.send(message)
        logging.info(f"[OK] SendGrid password reset sent: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"[ERROR] SendGrid reset error: {e}")
        return False


def send_lesson_review_email(user: User, lesson: CourseDay, rating: int) -> bool:
    """Send a lesson review notification to the admin via SendGrid."""
    try:
        admin_email: str = current_app.config.get("ADMIN_EMAIL", "rohithbuildsofficial@gmail.com")
        html_content: str = f"""
        <h3>New Lesson Review Received</h3>
        <p><strong>Lesson:</strong> Day {lesson.day_number} — {lesson.title} ({lesson.course.title})</p>
        <p><strong>Learner:</strong> {user.username} ({user.email})</p>
        <p><strong>Rating:</strong> {rating} / 5 Stars</p>
        <p>Sent from RohithBuilds Admin Review System.</p>
        """
        sg = sendgrid.SendGridAPIClient(api_key=os.environ.get("SENDGRID_API_KEY"))
        message = Mail(
            from_email="rohithbuildsofficial@gmail.com",
            to_emails=admin_email,
            subject=f"New Rating: Day {lesson.day_number} ({rating}/5 Stars)",
            html_content=html_content
        )
        response = sg.send(message)
        logging.info(f"[OK] SendGrid review email sent: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"[ERROR] SendGrid review email error: {e}")
        return False

