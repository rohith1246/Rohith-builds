from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

CATEGORIES = [
    # Retention Engines
    ("Academic Cheat Codes", "Academic Cheat Codes"),
    ("Vibe Coding", "Vibe Coding"),
    ("Developer DX & Docs", "Developer DX & Docs"),
    ("Career Pivot Playbook", "Career Pivot Playbook"),
    ("Legal Plain English", "Legal Plain English"),
    ("Prompt Engineering", "Prompt Engineering"),
    ("Learning Any Skill Fast", "Learning Any Skill Fast"),
    ("Productivity Systems & SOPs", "Productivity Systems & SOPs"),
    # Viral Engines
    ("Roast Me & Brutal Feedback", "Roast Me & Brutal Feedback"),
    ("Brain Rot & Chaos Content", "Brain Rot & Chaos Content"),
    ("Rizz & Social Scripts", "Rizz & Social Scripts"),
    ("LinkedIn That Doesn't Suck", "LinkedIn That Doesn't Suck"),
    ("Negotiation & Power Dynamics", "Negotiation & Power Dynamics"),
    ("Food & Recipe Remixer", "Food & Recipe Remixer"),
    # Monetization Engines
    ("Side Hustle Launchpad", "Side Hustle Launchpad"),
    ("Startup Founder Toolkit", "Startup Founder Toolkit"),
    ("Creator Monetization Vault", "Creator Monetization Vault"),
    ("Cold Outreach That Converts", "Cold Outreach That Converts"),
    ("Marketing That Hits Different", "Marketing That Hits Different"),
    ("Business Model & Pricing Lab", "Business Model & Pricing Lab"),
    # Creator Ecosystems
    ("Personal Brand OS", "Personal Brand OS"),
    ("Lore Drops & Fictional Worlds", "Lore Drops & Fictional Worlds"),
    ("AI Agent & Automation Builder", "AI Agent & Automation Builder"),
    ("Fictional Character Depth Dives", "Fictional Character Depth Dives"),
    # Community Ecosystems
    ("Dark Academia & Aesthetic Writing", "Dark Academia & Aesthetic Writing"),
    ("Therapy Speak & Emotional Processing", "Therapy Speak & Emotional Processing"),
    ("Manifesting & Future Self", "Manifesting & Future Self"),
    ("Gamemaster & Worldbuilding", "Gamemaster & Worldbuilding"),
    ("Gamer Psychology & Meta", "Gamer Psychology & Meta"),
    ("Soft Skills & People Fluency", "Soft Skills & People Fluency"),
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

    submit = SubmitField("Publish Lesson")    