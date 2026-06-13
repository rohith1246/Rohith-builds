import os
import resend
import threading
from flask import Flask, render_template, request, jsonify
from flask_login import current_user
from flask_wtf.csrf import generate_csrf
from dotenv import load_dotenv

# Shared extensions and models
from extensions import db, csrf, login_manager, migrate
from models import db, User, Prompt, Favorite, Job
from werkzeug.security import generate_password_hash

# Blueprints
from modules.home import home_bp
from modules.learn import learn_bp
from modules.prompts import prompts_bp
from modules.improve import improve_bp
from modules.auth import auth_bp
from modules.admin import admin_bp
from modules.jobs import jobs_bp

load_dotenv(override=True)

app = Flask(__name__)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "fallback-dev-key")
app.config["GOOGLE_CLIENT_ID"] = os.environ.get("GOOGLE_CLIENT_ID")
app.config["GOOGLE_CLIENT_SECRET"] = os.environ.get("GOOGLE_CLIENT_SECRET")
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
app.register_blueprint(jobs_bp)

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

# DB Setup & Seeding is now deferred to a safe startup hook so imports don't
# attempt to connect to Neon/Postgres during module import (which can crash
# the process if the database is unreachable). Initialization will run once
# on the first incoming request; failures are handled gracefully and a
# friendly error page is shown instead of letting the server crash.

def _initialize_database():
    from sqlalchemy import inspect, text
    from sqlalchemy.exc import OperationalError, SQLAlchemyError

    try:
        # create tables and apply lightweight, idempotent migration SQL
        with app.app_context():
            db.create_all()

            inspector = inspect(db.engine)
            table_names = inspector.get_table_names()

            # PROMPTS TABLE
            if "prompts" in table_names:
                columns = [col["name"] for col in inspector.get_columns("prompts")]
                if "copies" not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE prompts ADD COLUMN copies INTEGER DEFAULT 0"))
                        conn.commit()
                if "view_count" not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE prompts ADD COLUMN view_count INTEGER DEFAULT 0"))
                        conn.commit()

            # USERS TABLE
            if "users" in table_names:
                if "is_verified" not in [col["name"] for col in inspector.get_columns("users")]:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
                        conn.commit()

            # COURSE DAYS TABLE
            if "course_days" in table_names:
                if "image" not in [col["name"] for col in inspector.get_columns("course_days")]:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE course_days ADD COLUMN image VARCHAR(300)"))
                        conn.commit()

            # JOBS TABLE
            if "jobs" in table_names:
                columns = [col["name"] for col in inspector.get_columns("jobs")]
                if "clicks" not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE jobs ADD COLUMN clicks INTEGER DEFAULT 0"))
                        conn.commit()
                if "target_batch" not in columns:
                    with db.engine.connect() as conn:
                        conn.execute(text("ALTER TABLE jobs ADD COLUMN target_batch VARCHAR(100) DEFAULT '2025, 2026'"))
                        conn.commit()

            # seed only when tables exist
            seed_database()

            app.config["DB_AVAILABLE"] = True
            app.config.pop("DB_INIT_ERROR", None)

    except OperationalError as e:
        app.logger.error("Database initialization failed: %s", e)
        app.config["DB_AVAILABLE"] = False
        app.config["DB_INIT_ERROR"] = str(e)

    except SQLAlchemyError as e:
        app.logger.exception("Database error during initialization: %s", e)
        app.config["DB_AVAILABLE"] = False
        app.config["DB_INIT_ERROR"] = str(e)

    except Exception as e:
        app.logger.exception("Unexpected error during DB initialization: %s", e)
        app.config["DB_AVAILABLE"] = False
        app.config["DB_INIT_ERROR"] = str(e)


@app.before_request
def _block_if_db_unavailable():
    # Allow static assets, robots.txt, sitemap.xml and simple health paths to load even when DB is down
    path = request.path or ""
    if path.startswith("/static") or path.startswith("/health") or path == "/favicon.ico" or path == "/robots.txt" or path == "/sitemap.xml":
        return None

    # Initialize DB on first real request (some Flask installs don't expose
    # `before_first_request` as an attribute). Use a lock to avoid races.
    if app.config.get("DB_AVAILABLE") is None:
        init_lock = app.config.setdefault("_db_init_lock", threading.Lock())
        # Mark that init has started so concurrent requests don't all try.
        if not app.config.get("DB_INIT_STARTED"):
            app.config["DB_INIT_STARTED"] = True
            with init_lock:
                # Double-check after acquiring lock
                if app.config.get("DB_AVAILABLE") is None:
                    _initialize_database()

    # If initialization previously failed, show a friendly error page
    if app.config.get("DB_AVAILABLE") is False:
        error_message = app.config.get("DB_INIT_ERROR", "Cannot connect to the database.")
        try:
            return render_template("db_unavailable.html", admin_email=app.config.get("ADMIN_EMAIL"), error_message=error_message), 503
        except Exception:
            # Fallback plain-text response if template rendering itself fails
            return f"Database unavailable: {error_message}", 503

@app.route("/blog")
def blog_hub():
    return render_template("blog/index.html")

@app.route("/blog/how-to-learn-python-free-india")
def how_to_learn_python_free_india():
    return render_template("blog/how-to-learn-python-free-india.html")

@app.route("/blog/best-python-projects-freshers-resume-india")
def best_python_projects_freshers_resume_india():
    return render_template("blog/best-python-projects-freshers-resume-india.html")

@app.route("/blog/how-to-get-ai-internship-india")
def how_to_get_ai_internship_india():
    return render_template("blog/how-to-get-ai-internship-india.html")

@app.route("/blog/top-python-interview-questions-freshers")
def top_python_interview_questions_freshers():
    return render_template("blog/top-python-interview-questions-freshers.html")

@app.route("/blog/python-roadmap-beginners-2026")
def python_roadmap_beginners_2026():
    return render_template("blog/python-roadmap-beginners-2026.html")

@app.route("/blog/ai-engineer-roadmap-freshers")
def ai_engineer_roadmap_freshers():
    return render_template("blog/ai-engineer-roadmap-freshers.html")

@app.route("/blog/best-ai-projects-students")
def best_ai_projects_students():
    return render_template("blog/best-ai-projects-students.html")

@app.route("/blog/backend-developer-roadmap-india")
def backend_developer_roadmap_india():
    return render_template("blog/backend-developer-roadmap-india.html")

@app.route("/blog/python-developer-salary-india")
def python_developer_salary_india():
    return render_template("blog/python-developer-salary-india.html")

@app.route("/blog/backend-developer-salary-india")
def backend_developer_salary_india():
    return render_template("blog/backend-developer-salary-india.html")


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"}), 200

@app.route("/robots.txt")
def robots_txt():
    content = "User-agent: *\nAllow: /\nSitemap: https://rohith-builds.onrender.com/sitemap.xml\n"
    response = app.make_response(content)
    response.headers["Content-Type"] = "text/plain"
    return response

@app.route("/sitemap.xml")
def sitemap_xml():
    from datetime import datetime, timezone
    
    # Base URL of the site
    base_url = "https://rohith-builds.onrender.com"
    
    # We will build sitemap.xml dynamically
    urls = []
    
    # 1. Static/Public Main Pages
    # format: (url_path, changefreq, priority)
    static_pages = [
        ("/", "daily", "1.0"),
        ("/learn", "weekly", "0.9"),
        ("/jobs", "daily", "0.9"),
        ("/prompts", "daily", "0.8"),
        ("/prompts/collections", "weekly", "0.7"),
        ("/improve", "monthly", "0.6"),
        ("/blog", "weekly", "0.8"),
        ("/blog/how-to-learn-python-free-india", "weekly", "0.8"),
        ("/blog/best-python-projects-freshers-resume-india", "weekly", "0.8"),
        ("/blog/how-to-get-ai-internship-india", "weekly", "0.8"),
        ("/blog/top-python-interview-questions-freshers", "weekly", "0.8"),
        ("/blog/python-roadmap-beginners-2026", "weekly", "0.8"),
        ("/blog/ai-engineer-roadmap-freshers", "weekly", "0.8"),
        ("/blog/best-ai-projects-students", "weekly", "0.8"),
        ("/blog/backend-developer-roadmap-india", "weekly", "0.8"),
        ("/blog/python-developer-salary-india", "weekly", "0.8"),
        ("/blog/backend-developer-salary-india", "weekly", "0.8"),
    ]
    
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for path, changefreq, priority in static_pages:
        urls.append({
            "loc": f"{base_url}{path}",
            "lastmod": now_str,
            "changefreq": changefreq,
            "priority": priority
        })
        
    # 2. Dynamic Course Pages
    try:
        from models import Course, CourseDay
        courses = Course.query.filter_by(is_published=True).all()
        for course in courses:
            urls.append({
                "loc": f"{base_url}/learn/course/{course.slug}",
                "lastmod": now_str,
                "changefreq": "weekly",
                "priority": "0.8"
            })
            
            # Dynamic Lesson Pages for this course
            lessons = CourseDay.query.filter_by(course_id=course.id, is_published=True).all()
            for lesson in lessons:
                urls.append({
                    "loc": f"{base_url}/learn/{course.slug}/{lesson.slug}",
                    "lastmod": now_str,
                    "changefreq": "weekly",
                    "priority": "0.7"
                })
    except Exception as e:
        app.logger.error("Error generating sitemap courses: %s", e)
        
    # 3. Dynamic Prompt Pages
    try:
        from models import Prompt
        prompts = Prompt.query.all()
        for prompt in prompts:
            urls.append({
                "loc": f"{base_url}/prompt/{prompt.id}",
                "lastmod": now_str,
                "changefreq": "weekly",
                "priority": "0.6"
            })
    except Exception as e:
        app.logger.error("Error generating sitemap prompts: %s", e)
        
    # 4. Dynamic Collection Pages
    try:
        from models import PromptCollection
        collections = PromptCollection.query.all()
        for col in collections:
            urls.append({
                "loc": f"{base_url}/collections/{col.slug}",
                "lastmod": now_str,
                "changefreq": "weekly",
                "priority": "0.7"
            })
    except Exception as e:
        app.logger.error("Error generating sitemap collections: %s", e)
        
    # Build XML
    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    ]
    for url in urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{url['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{url['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{url['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{url['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")
    
    xml_content = "\n".join(xml_lines)
    response = app.make_response(xml_content)
    response.headers["Content-Type"] = "application/xml; charset=utf-8"
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG", "false").lower() == "true")