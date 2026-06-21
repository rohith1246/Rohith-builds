from flask import Blueprint

portfolio_grader_bp = Blueprint("portfolio_grader", __name__)

from . import routes
