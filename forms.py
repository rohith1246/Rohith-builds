from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User


CATEGORIES = [
    ("AI Fundamentals", "AI Fundamentals"),
    ("Prompt Engineering", "Prompt Engineering"),
    ("Coding & Development", "Coding & Development"),
    ("Python", "Python"),
    ("AI Automation", "AI Automation"),
    ("Learning & Study", "Learning & Study"),
    ("Productivity Systems", "Productivity Systems"),
    ("Career & Resume", "Career & Resume"),
    ("Communication Skills", "Communication Skills"),
    ("Content Creation", "Content Creation"),
    ("Business & Startups", "Business & Startups"),
    ("Personal Development", "Personal Development"),
]


class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"placeholder": "Choose a username"},
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Min 6 characters"},
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
        render_kw={"placeholder": "Repeat password"},
    )
    submit = SubmitField("Create Account")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken. Please choose another.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already registered. Please log in.")


class LoginForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Your password"},
    )
    submit = SubmitField("Sign In")


class ForgotPasswordForm(FlaskForm):
    email = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    submit = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Min 6 characters"},
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
        render_kw={"placeholder": "Repeat new password"},
    )
    submit = SubmitField("Reset Password")


class PromptForm(FlaskForm):
    title = StringField(
        "Prompt Title",
        validators=[DataRequired(), Length(min=3, max=200)],
        render_kw={"placeholder": "Give your prompt a catchy title"},
    )
    content = TextAreaField(
        "Prompt Content",
        validators=[DataRequired(), Length(min=10)],
        render_kw={"placeholder": "Write your full AI prompt here...", "rows": 8},
    )
    category = SelectField(
        "Category",
        choices=CATEGORIES,
        validators=[DataRequired()],
    )
    submit = SubmitField("Publish Prompt")
    
    
    
    
from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    TextAreaField,
    IntegerField,
    SubmitField
)
from wtforms.validators import DataRequired
from flask_wtf.file import FileField


class CourseDayForm(FlaskForm):

    title = StringField(
        "Title",
        validators=[DataRequired()]
    )

    slug = StringField(
        "Slug",
        validators=[DataRequired()]
    )

    day_number = IntegerField(
        "Day Number",
        validators=[DataRequired()]
    )

    short_description = TextAreaField(
        "Short Description"
    )

    image = FileField(
    "Lesson Image"
    )

    estimated_minutes = IntegerField(
        "Estimated Minutes"
    )

    xp_reward = IntegerField(
        "XP Reward"
    )

    content = TextAreaField(
        "Lesson Content",
        validators=[DataRequired()]
    )
    course_id = SelectField(
    "Course",
    coerce=int
    )
    
    submit = SubmitField("Publish Lesson")    