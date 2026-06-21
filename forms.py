from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import IntegerField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from models import User

CATEGORIES: list[tuple[str, str]] = [
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
    """Form for registering a new user account."""
    username: StringField = StringField(
        "Username",
        validators=[DataRequired(), Length(min=3, max=80)],
        render_kw={"placeholder": "Choose a username"},
    )
    email: StringField = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    password: PasswordField = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Min 6 characters"},
    )
    confirm_password: PasswordField = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
        render_kw={"placeholder": "Repeat password"},
    )
    submit: SubmitField = SubmitField("Create Account")

    def validate_username(self, username: StringField) -> None:
        """Verify that the username is not already registered."""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username already taken. Please choose another.")

    def validate_email(self, email: StringField) -> None:
        """Verify that the email is not already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Email already registered. Please log in.")


class LoginForm(FlaskForm):
    """Form for logging in an existing user."""
    email: StringField = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    password: PasswordField = PasswordField(
        "Password",
        validators=[DataRequired()],
        render_kw={"placeholder": "Your password"},
    )
    submit: SubmitField = SubmitField("Sign In")


class ForgotPasswordForm(FlaskForm):
    """Form for requesting a password reset email."""
    email: StringField = StringField(
        "Email",
        validators=[DataRequired(), Email()],
        render_kw={"placeholder": "your@email.com"},
    )
    submit: SubmitField = SubmitField("Send Reset Link")


class ResetPasswordForm(FlaskForm):
    """Form for resetting a user password."""
    password: PasswordField = PasswordField(
        "New Password",
        validators=[DataRequired(), Length(min=6)],
        render_kw={"placeholder": "Min 6 characters"},
    )
    confirm_password: PasswordField = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match")],
        render_kw={"placeholder": "Repeat new password"},
    )
    submit: SubmitField = SubmitField("Reset Password")


class PromptForm(FlaskForm):
    """Form for creating or editing an AI prompt."""
    title: StringField = StringField(
        "Prompt Title",
        validators=[DataRequired(), Length(min=3, max=200)],
        render_kw={"placeholder": "Give your prompt a catchy title"},
    )
    content: TextAreaField = TextAreaField(
        "Prompt Content",
        validators=[DataRequired(), Length(min=10)],
        render_kw={"placeholder": "Write your full AI prompt here...", "rows": 8},
    )
    category: SelectField = SelectField(
        "Category",
        choices=CATEGORIES,
        validators=[DataRequired()],
    )
    submit: SubmitField = SubmitField("Publish Prompt")


class CourseDayForm(FlaskForm):
    """Form for creating or editing a course lesson."""
    title: StringField = StringField(
        "Title",
        validators=[DataRequired()]
    )

    slug: StringField = StringField(
        "Slug",
        validators=[DataRequired()]
    )

    day_number: IntegerField = IntegerField(
        "Day Number",
        validators=[DataRequired()]
    )

    short_description: TextAreaField = TextAreaField(
        "Short Description"
    )

    image: FileField = FileField(
        "Lesson Image"
    )

    estimated_minutes: IntegerField = IntegerField(
        "Estimated Minutes"
    )

    xp_reward: IntegerField = IntegerField(
        "XP Reward"
    )

    content: TextAreaField = TextAreaField(
        "Lesson Content",
        validators=[DataRequired()]
    )
    
    course_id: SelectField = SelectField(
        "Course",
        coerce=int
    )
    
    submit: SubmitField = SubmitField("Publish Lesson")
    