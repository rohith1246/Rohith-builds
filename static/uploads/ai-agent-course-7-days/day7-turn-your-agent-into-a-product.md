# 📦 Day 7 — Turn Your Agent Into a Product

### AI Agent Course — RohithBuilds

Deploy your Flask app live to the internet using Render so anyone can visit it.

## Step 1 — Create Deployment Config Files

Run the following command in your terminal to create and open a new file named `Procfile` (without any file extension) in VS Code:

```cmd
code Procfile
```

Paste the startup command instruction inside:
```
# Tells Render to run a Gunicorn WSGI server pointing to app.py's app instance
web: gunicorn app:app
```

Run the following command in your terminal to create and open a new file named `requirements.txt` inside VS Code:

```cmd
code requirements.txt
```

Paste the list of required libraries inside:
```
# Listing the packages Render needs to install for the application to run
groq
python-dotenv
ddgs
flask
requests
gunicorn
```

## Step 2 — Commit and Push to GitHub

Initialize your git repository, commit all files, and push to GitHub. Create a new repository on [GitHub](https://github.com/new), then run the commands below in your terminal:

```cmd
# Initialize a new local Git repository
git init
git add .
git commit -m "Build: AI Research Agent Dashboard"
# Link and push to your remote GitHub repository
```

## Step 3 — Deploy Live on Render

1. Log in to the [Render Dashboard](https://dashboard.render.com/) and click **New + → Web Service**.
2. Connect your GitHub repository.
3. Use the configurations below:
   * **Runtime:** Python 3
   * **Build Command:** `pip install -r requirements.txt`
   * **Start Command:** `gunicorn app:app`
4. Add your environment variable under the **Environment** tab:
   * **Key:** `GROQ_API_KEY`
   * **Value:** *(your actual Groq API key)*
5. Click **Deploy Web Service**.

Once deployed, copy your generated public URL and share your AI Agent with the world!