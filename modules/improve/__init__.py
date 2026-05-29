from flask import Blueprint

improve_bp = Blueprint("improve", __name__)

from . import routes
