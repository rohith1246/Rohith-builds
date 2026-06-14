from flask import render_template

from models import CourseDay, Job, Prompt, User
from . import home_bp


@home_bp.route("/")
def home() -> str:
    """Render the home page with platform statistics and highlights."""
    total_jobs: int = Job.query.filter_by(is_active=True).count()
    total_prompts: int = Prompt.query.count()
    total_lessons: int = CourseDay.query.count()
    total_users: int = User.query.count()
    
    recent_jobs: list[Job] = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(3).all()
    popular_prompts: list[Prompt] = Prompt.query.order_by(Prompt.view_count.desc()).limit(3).all()

    return render_template(
        "home.html",
        total_jobs=total_jobs,
        total_prompts=total_prompts,
        total_lessons=total_lessons,
        total_users=total_users,
        recent_jobs=recent_jobs,
        popular_prompts=popular_prompts
    )


