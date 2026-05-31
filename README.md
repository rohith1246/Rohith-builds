# RohithBuilds — AI-Powered Learning Platform

> Learn AI by Building Real Things. Not theory. Not fluff. Just practical skills.

[![Live Demo](https://img.shields.io/badge/Live-rohith--builds.onrender.com-brightgreen)](https://rohith-builds.onrender.com)
[![Flask](https://img.shields.io/badge/Flask-Python-blue)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791)](https://www.postgresql.org/)
[![Groq API](https://img.shields.io/badge/AI-Groq%20API-orange)](https://groq.com/)
[![Deployed on Render](https://img.shields.io/badge/Deployed-Render-46E3B7)](https://render.com/)

---

## What Is RohithBuilds?

RohithBuilds is a full-stack AI-powered learning platform built for students and developers who want to learn AI, Python, and prompt engineering through practical, project-based education.

Built solo. Zero funding. No team. Just execution.

**Live Platform:** [rohith-builds.onrender.com](https://rohith-builds.onrender.com)

---

## Platform Modules

### 1. Structured Learning Courses
- Python + AI course (100 days, visual sketchnote-based lessons)
- AI Agent Bootcamp (7-day practical course)
- XP rewards and progress tracking per lesson
- Enrollment system with completion tracking

### 2. Prompt Vault
- 166+ curated prompts organized by category
- Full-text search and category filtering
- Pagination, favorites, and likes system
- User-contributed prompts with admin moderation

### 3. Collections System
- 12 curated learning packs (AI Beginner, Python Starter, Coding Mastery, etc.)
- Featured collections on vault homepage
- Complete discovery flow: Learn → Collections → Vault → Prompt
- Outcome-based organization (not random categories)

### 4. Rohi — AI Tutor
- Lesson-aware AI tutor powered by Groq API
- Answers questions based on current lesson context
- Available globally across all pages
- Guest usage limit (3 free questions) → signup conversion flow
- Custom branded chat widget

### 5. AI Prompt Improver
- Transforms weak prompts into structured, high-performance AI instructions
- Before/after demonstration
- Instant results, no signup required

### 6. Authentication System
- User registration and login
- Forgot password with SendGrid email integration
- Secure reset token with 1-hour expiry
- Email enumeration protection
- Password strength meter

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python) |
| Database | PostgreSQL |
| ORM | SQLAlchemy + Alembic |
| AI Tutor | Groq API |
| Email | SendGrid |
| Auth | Flask-Login + Session Management |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| Deployment | Render |

---

## Database Schema (Key Tables)

```
users
├── id, username, email, password_hash
├── is_admin, bio
└── created_at

prompts
├── id, title, content, category
├── user_id (FK), likes_count
└── created_at

prompt_collections
├── id, name, slug, description
└── created_at

prompt_collection_items
├── id, collection_id (FK), prompt_id (FK)
└── unique_collection_prompt constraint

courses
├── id, title, slug, description
└── is_published

lessons
├── id, course_id (FK), title, slug
├── content, order, xp_reward
└── is_published

user_progress
├── id, user_id (FK), lesson_id (FK)
├── completed, xp_earned
└── completed_at

favorites
└── user_id (FK), prompt_id (FK)
```

---

## Project Structure

```
rohithbuilds/
├── app.py                  # App factory and config
├── models.py               # SQLAlchemy models
├── requirements.txt
├── .env                    # Environment variables (not committed)
├── blueprints/
│   ├── auth/               # Login, register, forgot password
│   ├── prompts/            # Vault, collections, prompt detail
│   ├── learn/              # Courses, lessons, progress
│   ├── improve/            # Prompt improver
│   └── home/               # Homepage
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── vault.html
│   ├── collections.html
│   ├── learn.html
│   └── ...
└── static/
    ├── css/
    ├── js/
    │   ├── rohi.js         # AI tutor widget
    │   └── main.js
    └── images/
```

---

## Local Setup

### Prerequisites
- Python 3.10+
- PostgreSQL
- Git

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/rohith1246/rohithbuilds.git
cd rohithbuilds

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Fill in your values (see below)

# 5. Set up database
flask db upgrade

# 6. Run the app
flask run
```

### Environment Variables

```env
FLASK_ENV=development
SECRET_KEY=your_secret_key
DATABASE_URL=postgresql://user:password@localhost/rohithbuilds
GROQ_API_KEY=your_groq_api_key
SENDGRID_API_KEY=your_sendgrid_api_key
MAIL_DEFAULT_SENDER=your_email@domain.com
```

---

## Key Features in Detail

### Guest Limit → Conversion Funnel
Rohi gives guests 3 free questions. After the limit, a branded modal prompts signup. This is a deliberate conversion flow — not a bug.

### Lesson-Aware AI Tutor
Rohi reads `window.COURSE_SLUG` and `window.LESSON_SLUG` injected by Flask into each lesson page. This gives Groq the exact lesson context so answers are relevant, not generic.

### Collections Before Prompts
The vault shows featured collections (AI Beginner, Coding Mastery, Student Productivity) before the raw prompt grid. This prevents information overload and creates a structured onboarding path.

### Alembic Migration Safety
All schema changes go through Alembic migrations. Before any destructive migration, a backup table (`prompts_backup_YYYYMMDD`) is created. Never run blind migrations on production.

---

## Deployment

Deployed on **Render** (free tier).

```
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Environment:   Set all .env variables in Render dashboard
Database:      Render PostgreSQL (or external)
```

Note: Free tier has cold starts (30–60 seconds on first load after inactivity).

---

## Roadmap

- [ ] Conversation memory for Rohi
- [ ] Quiz mode per lesson
- [ ] Daily Rohi usage counter for logged-in users
- [ ] Rohi learning analytics dashboard
- [ ] Email digest — weekly new prompts
- [ ] Monetization — premium collections

---

## About the Builder

**Rohith Vuppula** — SQL Developer at Lionix LLP, solo founder of RohithBuilds.

Building in public at [@Rohith_Builds](https://twitter.com/Rohith_Builds)

Portfolio: [rohith-vuppula-portfolio.vercel.app](https://rohith-vuppula-portfolio.vercel.app)

---

## License

MIT License — use it, learn from it, build on it.

---

*Built with Flask, PostgreSQL, Groq API, and a lot of execution.*
