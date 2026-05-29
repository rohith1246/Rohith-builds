from flask import Blueprint

prompts_bp = Blueprint("prompts", __name__)

from . import routes
