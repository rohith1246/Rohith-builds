from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    prompts = db.relationship("Prompt", backref="author", lazy=True, cascade="all, delete-orphan")
    favorites = db.relationship("Favorite", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class Prompt(db.Model):
    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False, default="General")
    likes = db.Column(db.Integer, default=0)
    copies = db.Column(db.Integer, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    favorites = db.relationship("Favorite", backref="prompt", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Prompt {self.title}>"


class Favorite(db.Model):
    __tablename__ = "favorites"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    prompt_id = db.Column(db.Integer, db.ForeignKey("prompts.id"), nullable=False)

    __table_args__ = (db.UniqueConstraint("user_id", "prompt_id", name="unique_favorite"),)

    def __repr__(self):
        return f"<Favorite user={self.user_id} prompt={self.prompt_id}>"



# ==========================================

class Course(db.Model):
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
    __tablename__ = "course_days"

    id = db.Column(db.Integer, primary_key=True)

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
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


class UserCourseProgress(db.Model):
    __tablename__ = "user_course_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    current_day = db.Column(db.Integer, default=1)

    completed_days = db.Column(db.Integer, default=0)

    total_xp = db.Column(db.Integer, default=0)

    last_completed_at = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
    
class CourseEnrollment(db.Model):
    __tablename__ = "course_enrollments"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    course_id = db.Column(
        db.Integer,
        db.ForeignKey("courses.id"),
        nullable=False
    )

    enrolled_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )
    course = db.relationship(
    "Course",
    backref="enrollments"
)

user = db.relationship(
    "User",
    backref="enrollments"
)
    
    
class LessonProgress(db.Model):
    __tablename__ = "lesson_progress"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    course_day_id = db.Column(
        db.Integer,
        db.ForeignKey("course_days.id"),
        nullable=False
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
    backref="lesson_progress"
)

user = db.relationship(
    "User",
    backref="lesson_progress"
)