from flask import render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, User, Prompt
from . import admin_bp
from flask import render_template, redirect, url_for, flash
from forms import CourseDayForm
from models import db, Course, CourseDay
import os
from werkzeug.utils import secure_filename
from flask import current_app
from flask import (
    render_template,
    redirect,
    url_for,
    flash,
    abort,
    current_app
)


@admin_bp.route("/admin", endpoint="admin")
@login_required
def admin():
    if current_user.email != current_app.config["ADMIN_EMAIL"]:
        flash("Admin access only.", "danger")
        return redirect(url_for("auth.dashboard"))
    user_count = User.query.count()
    prompt_count = Prompt.query.count()
    total_likes = db.session.query(func.coalesce(func.sum(Prompt.likes), 0)).scalar() or 0
    total_copies = db.session.query(func.coalesce(func.sum(Prompt.copies), 0)).scalar() or 0
    top_prompts = Prompt.query.order_by(Prompt.likes.desc(), Prompt.copies.desc()).limit(10).all()
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin.html",
        user_count=user_count, prompt_count=prompt_count,
        total_likes=total_likes, total_copies=total_copies,
        top_prompts=top_prompts, users=users, config=current_app.config)

@admin_bp.route("/admin/verify-user/<int:user_id>", methods=["POST"])
@login_required
def admin_verify_user(user_id):
    if current_user.email != current_app.config["ADMIN_EMAIL"]:
        flash("Admin access only.", "danger")
        return redirect(url_for("auth.dashboard"))
    user = db.session.get(User, user_id)
    if user:
        user.is_verified = True
        db.session.commit()
        flash(f"✅ {user.username} verified successfully.", "success")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@login_required
def admin_delete_user(user_id):
    if current_user.email != current_app.config["ADMIN_EMAIL"]:
        flash("Admin access only.", "danger")
        return redirect(url_for("auth.dashboard"))
    user = db.session.get(User, user_id)
    if user and user.email != current_app.config["ADMIN_EMAIL"]:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted.", "info")
    return redirect(url_for("admin.admin"))

@admin_bp.route("/admin/delete-prompt/<int:prompt_id>", methods=["POST"])
@login_required
def admin_delete_prompt(prompt_id):
    if current_user.email != current_app.config["ADMIN_EMAIL"]:
        flash("Admin access only.", "danger")
        return redirect(url_for("auth.dashboard"))
    prompt = Prompt.query.get_or_404(prompt_id)
    db.session.delete(prompt)
    db.session.commit()
    flash("Prompt deleted.", "info")
    return redirect(url_for("admin.admin"))



@admin_bp.route("/admin/course-days/add", methods=["GET", "POST"])
def add_course_day():

    form = CourseDayForm()

    courses = Course.query.all()

    form.course_id.choices = [
    (c.id, c.title)
    for c in courses
    ]

    if form.validate_on_submit():

        image_path = ""

        if form.image.data:

            image_file = form.image.data

            filename = secure_filename(
                image_file.filename
            )

            upload_folder = os.path.join(
                current_app.root_path,
                "static/uploads/course_days"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            save_path = os.path.join(
                upload_folder,
                filename
            )

            image_file.save(save_path)

            image_path = (
                f"uploads/course_days/{filename}"
            )

        day = CourseDay(
            course_id=form.course_id.data,
            day_number=form.day_number.data,
            title=form.title.data,
            slug=form.slug.data,
            short_description=form.short_description.data,
            image=image_path,
            estimated_minutes=form.estimated_minutes.data,
            xp_reward=form.xp_reward.data,
            content=form.content.data
        )

        db.session.add(day)
        db.session.commit()

        flash(
            "Course day added successfully!",
            "success"
        )

        return redirect(
            url_for("admin.add_course_day")
        )

    return render_template(
        "admin/add_course_day.html",
        form=form
    )
    
    
@admin_bp.route("/course-days/<int:day_id>/edit", methods=["GET", "POST"])


@login_required
def edit_course_day(day_id):

    if current_user.email != current_app.config["ADMIN_EMAIL"]:
        abort(403)

    day = CourseDay.query.get_or_404(day_id)

    form = CourseDayForm(obj=day)

    if form.validate_on_submit():

        day.day_number = form.day_number.data
        day.title = form.title.data
        day.slug = form.slug.data
        day.short_description = form.short_description.data
        day.content = form.content.data
        day.estimated_minutes = form.estimated_minutes.data
        day.xp_reward = form.xp_reward.data

        if form.image.data:

            image_file = form.image.data

            filename = secure_filename(image_file.filename)

            upload_folder = os.path.join(
                current_app.root_path,
                "static/uploads/course_days"
            )

            os.makedirs(upload_folder, exist_ok=True)

            save_path = os.path.join(upload_folder, filename)

            image_file.save(save_path)

            day.image = f"uploads/course_days/{filename}"

        db.session.commit()

        flash("Lesson updated successfully!", "success")

        return redirect(
            url_for(
                "learn.python_course_day",
                slug=day.slug
            )
        )

    return render_template(
        "admin/edit_course_day.html",
        form=form,
        day=day
    )    
    