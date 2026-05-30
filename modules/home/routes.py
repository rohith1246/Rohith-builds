from flask import render_template
from . import home_bp

from models import Prompt, CourseDay

@home_bp.route("/")
def home():

    prompt_count = Prompt.query.count()
    lesson_count = CourseDay.query.count()

    return render_template(
        "home.html",
        prompt_count=prompt_count,
        lesson_count=lesson_count
    )
