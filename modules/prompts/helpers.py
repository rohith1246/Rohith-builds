from typing import Any

from flask import url_for
from flask_login import current_user

from forms import CATEGORIES
from models import Favorite, Prompt, db

PER_PAGE: int = 20


def build_prompt_feed_context(category: str = "", search: str = "", page: int = 1) -> dict[str, Any]:
    """Build the dictionary context for prompt vault feed presentation."""
    query = Prompt.query

    # Category filter
    if category:
        query = query.filter_by(category=category)

    # Search filter
    if search:
        search_term: str = f"%{search}%"
        query = query.filter(
            db.or_(
                Prompt.title.ilike(search_term),
                Prompt.content.ilike(search_term)
            )
        )

    # Pagination (20 prompts per page)
    pagination = query.order_by(
        Prompt.created_at.desc(),
        Prompt.id.desc()
    ).paginate(
        page=page,
        per_page=PER_PAGE,
        error_out=False
    )

    prompts: list[Prompt] = pagination.items

    # User favorites
    user_favorites: set[int] = set()

    if current_user.is_authenticated:
        user_favorites = {
            favorite.prompt_id
            for favorite in Favorite.query.filter_by(
                user_id=current_user.id
            ).all()
        }

    # Preserve filters while paginating
    query_params: dict[str, str] = {}

    if category:
        query_params["category"] = category

    if search:
        query_params["search"] = search

    clear_search_params: dict[str, str] = {}

    if category:
        clear_search_params["category"] = category

    return {
        "prompts": prompts,
        "pagination": pagination,
        "categories": [c[0] for c in CATEGORIES],
        "active_category": category,
        "search": search,
        "page": page,
        "user_favorites": user_favorites,
        "prompt_count": pagination.total,
        "total_prompts": Prompt.query.count(),
        "clear_search_url": url_for(
            "prompts.vault",
            **clear_search_params
        ),
        "query_params": query_params,
    }