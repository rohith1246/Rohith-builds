# Render Deployment Setup for RohithBuilds

## 1. Keep secrets out of Git

Add the following to `.gitignore` so your local `.env` and build artifacts are never committed:

```gitignore
# Environment variables
.env
*.env

# Python
*.pyc
__pycache__/
venv/
.venv/

# SQLite
*.db
*.sqlite3

# Flask instance folder
instance/
```

Do not commit `.env` to your repository.

## 2. Required render environment variables

Set these as secrets in Render under your service's **Environment** section:

```text
SECRET_KEY=your-strong-secret-key
ADMIN_EMAIL=admin@rohithbuilds.com
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=RohithBuilds <your-email@gmail.com>
PORT=10000
FLASK_DEBUG=false
```

> Note: Render provides its own `PORT` value. You can leave `PORT` blank in Render if you use the default Render port setting, but it is safe to include it.

## 3. Render build & start commands

For a Python Flask app, use this Render service configuration:

- **Build Command:**
  ```bash
  pip install -r requirements.txt
  ```

- **Start Command:**
  ```bash
  python app.py
  ```

If you prefer a production server, use:

```bash
gunicorn app:app
```

## 4. `runtime.txt`

Make sure `runtime.txt` is present and contains the Python version you want, for example:

```text
python-3.11.0
```

Render will use this to install the matching Python runtime.

## 5. Database note

Your app currently uses SQLite (`sqlite:///prompts.db`). For production on Render, SQLite is okay for small apps, but keep in mind:

- the filesystem is ephemeral for deploys
- database changes will not persist across service restarts if stored outside a persistent disk

If you want production durability, use a managed Postgres or MySQL database and update `SQLALCHEMY_DATABASE_URI` accordingly.

## 6. Confirm email verification works in production

After deployment, test these steps:

1. Sign up with a real email
2. Check your inbox for the verification link
3. Click the link and confirm the account is activated
4. Log in and verify you can create prompts, like, and favorite

## 7. If you want to keep using local `.env`

For local development, continue using:

```bash
pip install python-dotenv
```

Then add this to the top of `app.py` if it is not already there:

```python
from dotenv import load_dotenv
load_dotenv()
```

Also make sure `python-dotenv` is included in `requirements.txt` so Render can install it during deployment.

## 8. Quick production push checklist

- [x] `.gitignore` contains `.env` and `venv/`
- [x] Render environment variables are set
- [x] `requirements.txt` is up to date
- [x] `runtime.txt` specifies Python version
- [x] `FLASK_DEBUG=false`
- [x] Email verification tested against SMTP
- [x] App starts with `python app.py` or `gunicorn app:app`

## 9. Recommended Render service type

Use a **Web Service** on Render. It can run your Flask app and expose the website publicly.

If you want, I can also create a `render.yaml` file for automated Render deployments. 