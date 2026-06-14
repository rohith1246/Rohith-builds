from datetime import datetime

from flask import flash, jsonify, redirect, render_template, request, Response, url_for
from flask_login import current_user, login_required

from extensions import csrf
from forms import PromptForm
from models import Favorite, Prompt, PromptCollection, PromptCollectionItem, PromptLike, db
from . import prompts_bp
from .helpers import build_prompt_feed_context



@prompts_bp.route("/vault")
def vault() -> str:
    """Render the prompt vault page."""
    page: int = request.args.get("page", 1, type=int)

    feed = build_prompt_feed_context(
        category=request.args.get("category", "").strip(),
        search=request.args.get("search", "").strip(),
        page=page,
    )

    feed["featured_collections"] = (
        PromptCollection.query
        .filter(
            PromptCollection.slug.in_([
                "ai-beginner-pack",
                "coding-mastery-pack",
                "student-productivity-pack",
            ])
        )
        .all()
    )

    return render_template(
        "vault.html",
        **feed
    )


@prompts_bp.route("/collections")
def collections() -> str:
    """Render the list of prompt collections."""
    collections = PromptCollection.query.all()
    return render_template(
        "collections.html",
        collections=collections
    )


@prompts_bp.route("/collections/<slug>")
def collection_detail(slug: str) -> str:
    """Render the details and prompts for a specific collection."""
    collection = PromptCollection.query.filter_by(
        slug=slug
    ).first_or_404()

    prompt_ids = db.session.query(
        PromptCollectionItem.prompt_id
    ).filter(
        PromptCollectionItem.collection_id == collection.id
    )

    prompts = Prompt.query.filter(
        Prompt.id.in_(prompt_ids)
    ).all()

    return render_template(
        "collection_detail.html",
        collection=collection,
        prompts=prompts
    )


@prompts_bp.route("/api/prompts")
def api_prompts() -> Response:
    """Handle API request for paginated prompt results."""
    page: int = request.args.get("page", 1, type=int)

    feed = build_prompt_feed_context(
        category=request.args.get("category", "").strip(),
        search=request.args.get("search", "").strip(),
        page=page,
    )

    html = render_template(
        "partials/prompt_results.html",
        **feed
    )

    return jsonify({
        "html": html,
        "prompt_count": feed["prompt_count"],
        "total_prompts": feed["total_prompts"],
        "active_category": feed["active_category"],
        "search": feed["search"],
    })


@prompts_bp.route("/prompt/<int:prompt_id>")
def prompt_detail(prompt_id: int) -> str:
    """Render details of a single prompt."""
    prompt = Prompt.query.get_or_404(prompt_id)

    is_favorite: bool = False

    if current_user.is_authenticated:
        is_favorite = (
            Favorite.query.filter_by(
                user_id=current_user.id,
                prompt_id=prompt_id
            ).first()
            is not None
        )

    return render_template(
        "prompt_detail.html",
        prompt=prompt,
        is_favorite=is_favorite
    )


@prompts_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_prompt() -> Response | str:
    """Render prompt creation page and process new prompt submission."""
    if not current_user.is_verified:
        flash(
            "Please verify your email before creating prompts.",
            "warning"
        )
        return redirect(url_for("auth.dashboard"))

    form: PromptForm = PromptForm()

    if form.validate_on_submit():
        prompt: Prompt = Prompt(
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            user_id=current_user.id
        )

        db.session.add(prompt)
        db.session.commit()

        flash("Prompt published! 🚀", "success")

        return redirect(
            url_for(
                "prompts.prompt_detail",
                prompt_id=prompt.id
            )
        )

    return render_template(
        "create_prompt.html",
        form=form,
        edit_mode=False
    )


@prompts_bp.route("/edit/<int:prompt_id>", methods=["GET", "POST"])
@login_required
def edit_prompt(prompt_id: int) -> Response | str:
    """Render prompt edit page and process prompt updates."""
    prompt: Prompt = Prompt.query.get_or_404(prompt_id)

    if prompt.user_id != current_user.id:
        flash(
            "You can only edit your own prompts.",
            "danger"
        )
        return redirect(url_for("home.home"))

    if not current_user.is_verified:
        flash(
            "Please verify your email before editing prompts.",
            "warning"
        )
        return redirect(url_for("auth.dashboard"))

    form: PromptForm = PromptForm(obj=prompt)

    if form.validate_on_submit():
        prompt.title = form.title.data
        prompt.content = form.content.data
        prompt.category = form.category.data

        db.session.commit()

        flash("Prompt updated! ✅", "success")

        return redirect(
            url_for(
                "prompts.prompt_detail",
                prompt_id=prompt.id
            )
        )

    return render_template(
        "create_prompt.html",
        form=form,
        edit_mode=True,
        prompt=prompt
    )


@prompts_bp.route("/delete/<int:prompt_id>", methods=["POST"])
@login_required
def delete_prompt(prompt_id: int) -> Response:
    """Delete a prompt owned by the current user."""
    prompt: Prompt = Prompt.query.get_or_404(prompt_id)

    if prompt.user_id != current_user.id:
        flash(
            "You can only delete your own prompts.",
            "danger"
        )
        return redirect(url_for("home.home"))

    db.session.delete(prompt)
    db.session.commit()

    flash("Prompt deleted.", "info")

    return redirect(url_for("auth.dashboard"))


@prompts_bp.route("/favorites")
@login_required
def favorites() -> str:
    """Render the user's favorited prompts."""
    fav_records: list[Favorite] = Favorite.query.filter_by(
        user_id=current_user.id
    ).all()

    fav_prompts: list[Prompt] = Prompt.query.filter(
        Prompt.id.in_([f.prompt_id for f in fav_records])
    ).all()

    return render_template(
        "favorites.html",
        prompts=fav_prompts
    )


@prompts_bp.route("/api/like/<int:prompt_id>", methods=["POST"])
@csrf.exempt
@login_required
def like_prompt(prompt_id: int) -> Response:
    """API endpoint to toggle liking a prompt."""
    if not current_user.is_verified:
        return jsonify({
            "error": "Please verify your email to like prompts."
        }), 403

    prompt: Prompt = Prompt.query.get_or_404(prompt_id)

    existing: PromptLike | None = PromptLike.query.filter_by(
        user_id=current_user.id,
        prompt_id=prompt_id
    ).first()

    if existing:
        db.session.delete(existing)
        if prompt.likes > 0:
            prompt.likes -= 1
        liked: bool = False
    else:
        db.session.add(
            PromptLike(
                user_id=current_user.id,
                prompt_id=prompt_id
            )
        )
        prompt.likes += 1
        liked: bool = True

    db.session.commit()

    return jsonify({
        "success": True,
        "liked": liked,
        "likes": prompt.likes
    })


@prompts_bp.route("/api/copy/<int:prompt_id>", methods=["POST"])
@csrf.exempt
def record_copy(prompt_id: int) -> Response:
    """API endpoint to increment copy count of a prompt."""
    prompt: Prompt = Prompt.query.get_or_404(prompt_id)
    prompt.copies = (prompt.copies or 0) + 1
    db.session.commit()

    return jsonify({
        "copies": prompt.copies
    })


@prompts_bp.route("/api/favorite/<int:prompt_id>", methods=["POST"])
@csrf.exempt
@login_required
def toggle_favorite(prompt_id: int) -> Response:
    """API endpoint to toggle favoriting a prompt."""
    if not current_user.is_verified:
        return jsonify({
            "error": "Please verify your email to save favorites."
        }), 403

    prompt: Prompt = Prompt.query.get_or_404(prompt_id)

    existing: Favorite | None = Favorite.query.filter_by(
        user_id=current_user.id,
        prompt_id=prompt_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()

        return jsonify({
            "status": "removed"
        })

    db.session.add(
        Favorite(
            user_id=current_user.id,
            prompt_id=prompt_id,
            created_at=datetime.utcnow()
        )
    )

    db.session.commit()

    return jsonify({
        "status": "added"
    })