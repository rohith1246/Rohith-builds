# RohithBuilds — AI-Powered Learning Platform

> Learn AI by Building Real Things. Not theory. Not fluff. Just practical skills.

[![Live Demo](https://img.shields.io/badge/Live-rohith--builds.onrender.com-brightgreen)](https://rohith-builds-g79e.onrender.com)
[![Flask](https://img.shields.io/badge/Flask-Python-blue)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791)](https://www.postgresql.org/)
[![Groq API](https://img.shields.io/badge/AI-Groq%20API-orange)](https://groq.com/)
[![Deployed on Render](https://img.shields.io/badge/Deployed-Render-46E3B7)](https://render.com/)

---

## What Is RohithBuilds?

RohithBuilds is a full-stack AI-powered learning platform built for students and developers who want to learn AI, Python, and prompt engineering through practical, project-based education.

Built solo. Zero funding. No team. Just execution.

**Live Platform:** [rohith-builds-g79e.onrender.com](https://rohith-builds-g79e.onrender.com)

---

## Platform Modules & Features

### 1. Structured Learning Courses
- **Python + AI Course:** 100 days of structured, sketchnote-based python lessons.
- **7-Day AI Agent Course:** Real-world AI agents built with Python and Groq.
- **XP & Progress Tracking:** Users earn XP upon completing lessons, tracked persistently in the database.
- **Reviews:** Students can submit reviews/ratings for each course day.

### 2. Prompt Vault & Collections
- **220+ Curated Prompts:** Curated AI prompts for developers spanning coding, debugging, system design, career, and productivity.
- **Likes & Favorites:** Interactive copying, liking, and favoriting prompts.
- **Outcome-Based Collections:** Grouped prompt packages (e.g. AI Beginner, Python Starter) to guide learning paths.

### 3. Rohi — AI Tutor
- **Lesson-Aware Context:** Rohi knows which course day you are currently reading and adapts answers to the lesson.
- **Daily Message Limits:**
  - **Guests:** 3 messages per session with instant redirect to sign up on completion.
  - **Registered Users:** 20 messages per day (resets automatically at midnight).
- **Resilient Fallback Chain:** Powered by Groq API with automatic key & model rotation to prevent 429 rate limit issues. Shows clean error notices rather than raw API status codes.

### 4. Jobs Board (`/jobs`) & AI Agent
- **Curated Jobs List:** Junior developer jobs scraped and curated automatically.
- **AI Job Agent:** Matches your uploaded PDF resume with listed jobs, computes match fit scores, draft cover letters, and logs applications.

### 5. Admin Dashboard (`admin_dashboard/`)
- **Metrics Dashboard:** Overview of user signups, course enrollments, lesson completion history, and prompt metrics.
- **AI Daily Report:** Automatically compiles today's signup/completion logs and drafts an AI daily narrative, compiling it into a PDF and emailing it to the admin.
- **Reddit Marketing Harvester:** Background harvester that polls target subreddits, processes new help queries, drafts helpful responses mentoring like a senior Indian developer, and caches drafts for the admin.
- **User & Review Moderation:** Reset student progress, approve user-submitted prompts, delete spam reviews, and download SQL backups.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask (Python 3.11 with full type hints & logging) |
| **Database** | PostgreSQL / Neon DB |
| **ORM & Migrations** | SQLAlchemy + Flask-Migrate (Alembic) |
| **Connection Pooling** | Neon-optimized SQLAlchemy pool with pre-ping validation |
| **AI Integration** | Groq (llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768) |
| **PDF Generation** | ReportLab |
| **E-mail Mailer** | SMTP / SendGrid |
| **Frontend** | Vanilla HTML5, Vanilla CSS3 (custom dark/glass themes), Vanilla JS |
| **Deployment** | Render / Gunicorn |

---

## Database Schema

```
users
├── id (PK), username, email, password_hash
├── is_admin, bio, created_at, is_verified
├── rohi_messages_today (int)
└── rohi_last_reset_date (date)

prompts
├── id (PK), title, content, category, likes, copies
├── user_id (FK), created_at
└── approved (boolean)

courses
├── id (PK), title, slug, description, difficulty
├── thumbnail, is_published, created_at
└── slug (unique)

course_days (lessons)
├── id (PK), course_id (FK), day_number, title, slug
├── short_description, image, xp_reward, estimated_minutes
└── content, is_published, created_at

lesson_progress
├── id (PK), user_id (FK), course_day_id (FK)
├── completed, completed_at, completion_email_sent
└── xp_earned

jobs
└── id (PK), title, company, location, category, description,
    skills, url, is_active, clicks, created_at
```

---

## Project Structure

```
RohithBuilds/
├── app.py                  # Main flask application factory
├── models.py               # SQLAlchemy models
├── extensions.py           # Shared DB and CSRF instances
├── forms.py                # Flask WTForms definitions
├── gemini_helper.py        # Groq Fallback / AI core helper
├── requirements.txt        # Backend dependencies
├── migrations/             # Database migration history
├── static/                 # Static assets (CSS, images, JS)
│   ├── css/                # Style directories
│   ├── js/                 # Widget modules (rohi.js, etc.)
│   └── uploads/            # Resumes & Thumbnails uploads
├── modules/                # Application blueprints
│   ├── auth/               # User Authentication & Verification
│   ├── home/               # Landing pages and navigation
│   ├── improve/            # AI Prompt Improver
│   ├── learn/              # Courses, lessons, and progress
│   ├── prompts/            # Prompt Vault and collections
│   └── jobs/               # Jobs Board and AI Resume Agent
└── admin_dashboard/        # Internal administrative dashboard app
    ├── app.py              # Harvester, reporting mailer, and admin routes
    └── templates/          # Admin-facing layouts
```

---

## Local Setup & Run

### Prerequisites
- Python 3.11+
- PostgreSQL
- Git

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/rohith1246/rohithbuilds.git
   cd rohithbuilds
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   # Main Platform
   FLASK_ENV=development
   SECRET_KEY=your-random-super-secret-key
   DATABASE_URL=postgresql://postgres:password@localhost:5432/rohithbuilds
   GROQ_API_KEY=your-primary-groq-api-key
   GROQ_API_KEY_SECONDARY=your-backup-groq-api-key
   ADMIN_EMAIL=admin@rohithbuilds.com
   SMTP_EMAIL=your-gmail@gmail.com
   SMTP_PASSWORD=your-gmail-app-password
   
   # Admin Dashboard credentials
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=strong-admin-password
   ```

5. **Run Database Migrations:**
   ```bash
   flask db upgrade
   ```

6. **Start the applications:**
   * **Main Student Application:**
     ```bash
     flask run --port=5000
     ```
     Access at [http://127.0.0.1:5000](http://127.0.0.1:5000)

   * **Admin Dashboard:**
     ```bash
     python admin_dashboard/app.py
     ```
     Access at [http://127.0.0.1:5000](http://127.0.0.1:5000) (if run on a different port, make sure to configure properly).

---

## License

MIT License. Feel free to use, modify, and build upon this codebase.

*Built with Flask, PostgreSQL, Groq API, and a dedication to project-based learning.*
