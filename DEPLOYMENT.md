# Deployment Guide

## Prerequisites

Ensure these files are in your repository:
- `Procfile` (contains: `web: gunicorn api:app`)
- `runtime.txt` (contains: `python-3.11.0`)
- `requirements.txt` (includes `gunicorn`)
- `processed_data/merged_dataset.csv` (required data file)

## Option 1: Render (Recommended)

**Free tier available, easiest setup**

1. Sign up at [render.com](https://render.com)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn api:app`
5. Click "Create Web Service"

First build takes 5-10 minutes. Your app will be live at `https://your-app.onrender.com`

## Option 2: Heroku

**Requires credit card for free tier**

```bash
# Install Heroku CLI
# Download from: https://devcenter.heroku.com/articles/heroku-cli

# Login and deploy
heroku login
heroku create your-app-name
git push heroku main
heroku open
```

## Option 3: PythonAnywhere

1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Clone your repository in their console
3. Install dependencies: `pip install --user -r requirements.txt`
4. Create web app pointing to your `api.py`
5. Configure WSGI file to import your Flask app

## Local Testing with Gunicorn

Before deploying, test locally:

```bash
pip install gunicorn
gunicorn api:app
# Visit http://localhost:8000
```

## Common Issues

**"Module not found: app"**
- Check that Start Command is `gunicorn api:app` (not `gunicorn app:app`)

**"CSV file not found"**
- Ensure `processed_data/merged_dataset.csv` is committed to git
- Check that `.gitignore` doesn't exclude it

**Port binding errors**
- The app already uses `os.environ.get('PORT', 5000)` for dynamic ports

## Environment Variables

If needed, add these in your platform's settings:
- `PORT` (auto-set by most platforms)
- `PYTHON_VERSION` (optional, defaults to `runtime.txt`)

## After Deployment

- Test all features work
- Check Tableau dashboards load correctly
- Verify API endpoints respond
- Test on mobile devices

Your app should be fully functional at the provided URL. No further configuration needed.
