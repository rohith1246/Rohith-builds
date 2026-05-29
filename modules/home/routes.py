from flask import render_template
from . import home_bp

@home_bp.route("/")
def home():
    """New Clean Landing Page"""
    return render_template("home.html")
