import os
import resend
from flask import Flask, render_template, request, jsonify
from flask_login import current_user
from flask_wtf.csrf import generate_csrf
from dotenv import load_dotenv

# Shared extensions and models
from extensions import db, csrf, login_manager, migrate
from models import db, User, Prompt, Favorite
from werkzeug.security import generate_password_hash

# Blueprints
from modules.home import home_bp
from modules.learn import learn_bp
from modules.prompts import prompts_bp
from modules.improve import improve_bp
from modules.auth import auth_bp
from modules.admin import admin_bp

load_dotenv(override=True)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-dev-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///prompts.db")
engine_options = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
if not app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
    engine_options["connect_args"] = {"connect_timeout": 10}
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["ADMIN_EMAIL"] = os.environ.get("ADMIN_EMAIL", "rohithbuildsofficial@gmail.com")

resend.api_key = os.environ.get("RESEND_API_KEY")

# Initialize Extensions
csrf.init_app(app)
db.init_app(app)
migrate.init_app(app, db)
login_manager.init_app(app)

# Configure Login Manager
login_manager.login_view = "auth.login"  # Namespaced
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.context_processor
def inject_csrf_token():
    is_admin = (current_user.is_authenticated and getattr(current_user, "email", None) == app.config["ADMIN_EMAIL"])
    return dict(csrf_token=generate_csrf, is_admin=is_admin)

# Register Blueprints
app.register_blueprint(home_bp)
app.register_blueprint(learn_bp)
app.register_blueprint(prompts_bp)
app.register_blueprint(improve_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

# Database Seeding
SEED_PROMPTS = [
    {"title": "Ultimate Code Reviewer", "content": "You are an expert senior software engineer conducting a thorough code review...", "category": "Coding"},
    {"title": "Viral Twitter Thread Generator", "content": "You are a viral social media strategist...", "category": "Marketing"},
    {"title": "Startup Idea Validator", "content": "Act as a seasoned startup mentor...", "category": "Business"},
    {"title": "Essay Writing Assistant", "content": "You are an expert academic writer...", "category": "Writing"},
    {"title": "Personal Tutor - Any Subject", "content": "You are a world-class tutor...", "category": "Education"},
]

def seed_database():
    if User.query.first():
        return
    seed_user = User(username="rohithbuilds", email="rohithbuildsofficial@gmail.com", password_hash=generate_password_hash("admin123"), is_verified=True)
    db.session.add(seed_user)
    db.session.flush()
    for p in SEED_PROMPTS:
        db.session.add(Prompt(title=p["title"], content=p["content"], category=p["category"], likes=0, user_id=seed_user.id))
    db.session.commit()
    print("[OK] Database seeded successfully.")

# DB Setup & Seeding
with app.app_context():

    db.create_all()

    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    table_names = inspector.get_table_names()

    # PROMPTS TABLE
    if "prompts" in table_names:

        if "copies" not in [
            col["name"] for col in inspector.get_columns("prompts")
        ]:

            with db.engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE prompts ADD COLUMN copies INTEGER DEFAULT 0"
                    )
                )

    # USERS TABLE
    if "users" in table_names:

        if "is_verified" not in [
            col["name"] for col in inspector.get_columns("users")
        ]:

            with db.engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT 0"
                    )
                )

    # COURSE DAYS TABLE
    if "course_days" in table_names:

        if "image" not in [
            col["name"] for col in inspector.get_columns("course_days")
        ]:

            with db.engine.connect() as conn:
                conn.execute(
                    text(
                        "ALTER TABLE course_days ADD COLUMN image VARCHAR(300)"
                    )
                )

    seed_database()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")