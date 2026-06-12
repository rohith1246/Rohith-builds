from flask import render_template
from . import home_bp

from models import Prompt, CourseDay, User, Job

@home_bp.route("/")
def home():
    total_jobs = Job.query.filter_by(is_active=True).count()
    total_prompts = Prompt.query.count()
    total_lessons = CourseDay.query.count()
    total_users = User.query.count()
    
    recent_jobs = Job.query.filter_by(is_active=True).order_by(Job.created_at.desc()).limit(3).all()
    popular_prompts = Prompt.query.order_by(Prompt.view_count.desc()).limit(3).all()

    return render_template(
        "home.html",
        total_jobs=total_jobs,
        total_prompts=total_prompts,
        total_lessons=total_lessons,
        total_users=total_users,
        recent_jobs=recent_jobs,
        popular_prompts=popular_prompts
    )

