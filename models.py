from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Database model for user accounts."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    rohi_messages_today = db.Column(db.Integer, default=0)
    rohi_last_reset_date = db.Column(db.Date)
    current_streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.Date, nullable=True)
    xp = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prompts = db.relationship(
        "Prompt",
        backref="author",
        lazy=True,
        cascade="all, delete-orphan"
    )

    favorites = db.relationship(
        "Favorite",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    liked_prompts = db.relationship(
        "PromptLike",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<User {self.username}>"


class Prompt(db.Model):
    """Database model for user-created prompts."""
    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    content = db.Column(db.Text, nullable=False)

    category = db.Column(
        db.String(50),
        nullable=False,
        default="General"
    )

    likes = db.Column(db.Integer, default=0)

    copies = db.Column(db.Integer, default=0)

    view_count = db.Column(db.Integer, default=0)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    favorites = db.relationship(
        "Favorite",
        backref="prompt",
        lazy=True,
        cascade="all, delete-orphan"
    )

    liked_by = db.relationship(
        "PromptLike",
        backref="prompt",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<Prompt {self.title}>"

class PromptLike(db.Model):
    """Database model representing a user like on a prompt."""
    __tablename__ = "user_likes"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("prompts.id"),
        nullable=False,
        index=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "prompt_id",
            name="unique_user_like"
        ),
    )
    
    
class PromptCollection(db.Model):
    """Database model representing a collection of prompts."""
    __tablename__ = "prompt_collections"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), unique=True)

    slug = db.Column(db.String(100), unique=True)

    description = db.Column(db.Text)

    prompts = db.relationship(
        "PromptCollectionItem",
        backref="collection",
        lazy=True,
        cascade="all, delete-orphan"
    )
    
class PromptCollectionItem(db.Model):
    """Association model representing prompts inside collections."""
    __tablename__ = "prompt_collection_items"

    id = db.Column(db.Integer, primary_key=True)

    collection_id = db.Column(
        db.Integer,
        db.ForeignKey("prompt_collections.id"),
        nullable=False
    )

    prompt_id = db.Column(
        db.Integer,
        db.ForeignKey("prompts.id"),
        nullable=False
    )

    prompt = db.relationship(
        "Prompt",
        backref="collection_items"
    )

    __table_args__ = (
        db.UniqueConstraint(
            "collection_id",
            "prompt_id",
            name="unique_collection_prompt"
        ),
    )    
    

class Favorite(db.Model):
    """Database model representing a user favorited prompt."""
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "prompt_id", name="unique_favorite"),)

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<Favorite user={self.user_id} prompt={self.prompt_id}>"



# ==========================================

class Course(db.Model):
    """Database model for a course."""
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    slug = db.Column(db.String(200), unique=True, nullable=False)

    description = db.Column(db.Text, nullable=True)

    thumbnail = db.Column(db.String(300), nullable=True)

    difficulty = db.Column(db.String(50), default="Beginner")

    is_published = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    days = db.relationship(
        "CourseDay",
        backref="course",
        lazy=True,
        cascade="all, delete-orphan"
    )


class CourseDay(db.Model):
    """Database model for a single day/lesson in a course."""
    __tablename__ = "course_days"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False,
        index=True
    )

    day_number = db.Column(db.Integer, nullable=False)

    title = db.Column(db.String(200), nullable=False)

    slug = db.Column(db.String(200), nullable=False)

    short_description = db.Column(db.Text, nullable=True)
    
    image = db.Column(db.String(300), nullable=True)

    content = db.Column(db.Text, nullable=True)

    xp_reward = db.Column(db.Integer, default=50)

    estimated_minutes = db.Column(db.Integer, default=10)

    is_published = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    lesson_data = db.Column(
    db.JSON,
    nullable=True
)


class UserCourseProgress(db.Model):
    """Database model tracking a user's progress through a course."""
    __tablename__ = "user_course_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False,
        index=True
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_user_course_progress"),
    )

    current_day = db.Column(db.Integer, default=1)

    completed_days = db.Column(db.Integer, default=0)

    total_xp = db.Column(db.Integer, default=0)

    last_completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship(
        "User",
        backref=db.backref("course_progresses", cascade="all, delete-orphan")
    )
    course = db.relationship(
        "Course",
        backref=db.backref("user_progresses", cascade="all, delete-orphan")
    )


class CourseEnrollment(db.Model):
    """Database model representing a user's enrollment in a course."""
    __tablename__ = "course_enrollments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False,
        index=True
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_id", name="uq_course_enrollment"),
    )

    enrolled_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    course = db.relationship(
        "Course",
        backref=db.backref("enrollments", cascade="all, delete-orphan")
    )

    user = db.relationship(
        "User",
        backref=db.backref("enrollments", cascade="all, delete-orphan")
    )
    
    
class LessonProgress(db.Model):
    """Database model tracking if a user completed a specific lesson."""
    __tablename__ = "lesson_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    course_day_id = db.Column(
        db.Integer,
        db.ForeignKey("course_days.id"),
        nullable=False,
        index=True
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_day_id", name="uq_lesson_progress"),
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    completed_at = db.Column(
        db.DateTime
    )

    course_day = db.relationship(
        "CourseDay",
        backref=db.backref("lesson_progress", cascade="all, delete-orphan")
    )

    user = db.relationship(
        "User",
        backref=db.backref("lesson_progress", cascade="all, delete-orphan")
    )


class LessonReview(db.Model):
    """Database model representing a user review/rating for a lesson."""
    __tablename__ = "lesson_reviews"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    course_day_id = db.Column(
        db.Integer,
        db.ForeignKey("course_days.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    __table_args__ = (
        db.UniqueConstraint("user_id", "course_day_id", name="uq_lesson_review"),
    )

    rating = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    course_day = db.relationship(
        "CourseDay",
        backref=db.backref("reviews", cascade="all, delete-orphan", lazy=True)
    )
    user = db.relationship(
        "User",
        backref=db.backref("reviews", cascade="all, delete-orphan", lazy=True)
    )


class Job(db.Model):
    """Database model representing a job posting."""
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    logo_url = db.Column(db.String(300), nullable=True)
    location = db.Column(db.String(200), nullable=False)
    job_type = db.Column(db.String(50), nullable=False, default="Job")  # e.g., Job, Internship
    category = db.Column(db.String(100), nullable=False, default="Python")  # e.g., Python, Backend, AI / LLM
    experience_level = db.Column(db.String(100), nullable=False, default="Freshers")  # e.g., Freshers, 0-2 years
    salary = db.Column(db.String(100), nullable=True)  # e.g., "₹5,00,000 - ₹8,00,000 / year"
    skills = db.Column(db.String(300), nullable=False)  # Comma-separated, e.g., "Python, Flask, Groq"
    description = db.Column(db.Text, nullable=False)
    course_match = db.Column(db.String(300), nullable=True)  # e.g., "7-Day AI Agent course"
    apply_url = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    clicks = db.Column(db.Integer, default=0)
    target_batch = db.Column(db.String(100), nullable=False, default="2025, 2026")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<Job {self.title} at {self.company}>"


class JobApplication(db.Model):
    """Database model representing a user's application to a job."""
    __tablename__ = "job_applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Unique constraint so a user can only apply once to a job
    __table_args__ = (
        db.UniqueConstraint("user_id", "job_id", name="uq_user_job_application"),
    )

    user = db.relationship("User", backref=db.backref("job_applications", lazy="dynamic"))
    job = db.relationship("Job", backref=db.backref("applications", lazy="dynamic"))

    def __repr__(self) -> str:
        """Return a string representation of the model."""
        return f"<JobApplication User:{self.user_id} Job:{self.job_id}>"


class UserAgentConfig(db.Model):
    """Database model representing the user's AI job agent configuration."""
    __tablename__ = "user_agent_configs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    resume_text = db.Column(db.Text, nullable=True)
    resume_filename = db.Column(db.String(255), nullable=True)
    target_roles = db.Column(db.String(300), nullable=True, default="Software Engineer, Backend Engineer, Frontend Engineer, Fullstack Engineer")
    target_locations = db.Column(db.String(300), nullable=True, default="Remote, India, Bengaluru")
    min_salary = db.Column(db.String(100), nullable=True, default="")
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("agent_config", uselist=False, cascade="all, delete-orphan"))


class AgentJobOpportunity(db.Model):
    """Database model representing a job opportunity fetched by the agent."""
    __tablename__ = "agent_job_opportunities"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    company = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    apply_url = db.Column(db.String(500), unique=True, nullable=False)
    recruiter_email = db.Column(db.String(120), nullable=True)
    source = db.Column(db.String(100), nullable=True, default="Lever/Greenhouse")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AgentApplicationLog(db.Model):
    """Database model representing the match logs for the AI job agent."""
    __tablename__ = "agent_application_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    job_opportunity_id = db.Column(db.Integer, db.ForeignKey("agent_job_opportunities.id", ondelete="CASCADE"), nullable=False)
    fit_score = db.Column(db.Integer, default=0)
    match_explanation = db.Column(db.Text, nullable=True)
    drafted_subject = db.Column(db.String(300), nullable=True)
    drafted_body = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="Matched")
    applied_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "job_opportunity_id", name="uq_user_job_opportunity"),
    )

    user = db.relationship("User", backref=db.backref("agent_logs", lazy="dynamic", cascade="all, delete-orphan"))
    job_opportunity = db.relationship("AgentJobOpportunity", backref=db.backref("logs", lazy="dynamic", cascade="all, delete-orphan"))


class PortfolioGrade(db.Model):
    """Database model to cache portfolio grades and share scores."""
    __tablename__ = "portfolio_grades"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False)
    punchline = db.Column(db.String(500), nullable=False)
    bullet_points = db.Column(db.JSON, nullable=False)  # List of strings cached as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_expired(self) -> bool:
        """Check if cached grade is older than 4 hours."""
        from datetime import datetime, timedelta
        return datetime.utcnow() - self.created_at > timedelta(hours=4)