import os
from flask import current_app, render_template, url_for
from itsdangerous import URLSafeTimedSerializer
import sendgrid
from sendgrid.helpers.mail import Mail


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-confirm-salt")


def verify_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="email-confirm-salt", max_age=expiration)
    except Exception:
        return None


def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset-salt")


def verify_reset_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    try:
        return serializer.loads(token, salt="password-reset-salt", max_age=expiration)
    except Exception:
        return None


def send_verification_email(user):
    token = generate_verification_token(user.email)
    verify_url = url_for("auth.verify_email", token=token, _external=True)
    try:
        html_content = render_template(
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
        print(f"[OK] SendGrid sent: {response.status_code}")
        return True
    except Exception as e:
        print(f"[ERROR] SendGrid error: {e}")
        return False


def send_password_reset_email(user):
    token = generate_reset_token(user.email)
    reset_url = url_for("auth.reset_password", token=token, _external=True)
    try:
        html_content = render_template(
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
        print(f"[OK] SendGrid password reset sent: {response.status_code}")
        return True
    except Exception as e:
        print(f"[ERROR] SendGrid reset error: {e}")
        return False


def send_lesson_review_email(user, lesson, rating):
    try:
        admin_email = current_app.config.get("ADMIN_EMAIL", "rohithbuildsofficial@gmail.com")
        html_content = f"""
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
        print(f"[OK] SendGrid review email sent: {response.status_code}")
        return True
    except Exception as e:
        print(f"[ERROR] SendGrid review email error: {e}")
        return False
