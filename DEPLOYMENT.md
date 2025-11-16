# 🚀 Deployment Guide

## Deployment Options

This app can be deployed on several platforms. Here are the easiest options:

---

## Option 1: Render (Recommended - FREE)

### Why Render?
- ✅ Free tier available
- ✅ Easy setup (connects directly to GitHub)
- ✅ Automatic deployments on push
- ✅ Great for Python web apps

### Steps:

1. **Push your code to GitHub** (make sure `processed_data/merged_dataset.csv` is included!)

2. **Go to [Render.com](https://render.com)** and sign up

3. **Create New Web Service**
   - Connect your GitHub repository
   - Select the repo: `Datathon-25`

4. **Configure Build Settings**:
   ```
   Name: college-recommender
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn api:app
   ```

5. **Add Environment Variables** (if needed):
   - `PYTHON_VERSION`: 3.11.0

6. **Deploy!** 
   - Click "Create Web Service"
   - Wait 5-10 minutes for first build
   - Your app will be live at: `https://college-recommender.onrender.com`

---

## Option 2: Heroku (Requires Credit Card for Free Tier)

### Steps:

1. **Install Heroku CLI**: [Download here](https://devcenter.heroku.com/articles/heroku-cli)

2. **Login**:
   ```bash
   heroku login
   ```

3. **Create app**:
   ```bash
   cd "C:\Users\Man Pham\Berkeley\Datathon25"
   heroku create college-recommender-app
   ```

4. **Deploy**:
   ```bash
   git push heroku main
   ```

5. **Open app**:
   ```bash
   heroku open
   ```

**Note**: The `Procfile` and `runtime.txt` files tell Heroku how to run your app.

---

## Option 3: PythonAnywhere (Easy, Free)

### Steps:

1. **Sign up** at [PythonAnywhere.com](https://www.pythonanywhere.com)

2. **Upload files** via their web interface or use git:
   ```bash
   git clone https://github.com/kkphamm/Datathon-25.git
   ```

3. **Install dependencies**:
   ```bash
   pip install --user -r requirements.txt
   ```

4. **Create Web App**:
   - Go to "Web" tab
   - Add new web app
   - Choose Flask
   - Point to your `api.py` file

5. **Configure WSGI file** to import your app:
   ```python
   import sys
   path = '/home/yourusername/Datathon-25'
   if path not in sys.path:
       sys.path.append(path)
   
   from api import app as application
   ```

6. **Reload** and your app is live!

---

## Option 4: Google Cloud Run (More Advanced)

### Steps:

1. **Install Google Cloud CLI**

2. **Create Dockerfile**:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   CMD gunicorn -b :$PORT api:app
   ```

3. **Deploy**:
   ```bash
   gcloud run deploy college-recommender --source .
   ```

---

## Option 5: Vercel (Frontend + Serverless Functions)

Vercel is great for static sites but requires adapting your Flask app to serverless functions.

**Note**: This requires restructuring your app - not recommended unless you're familiar with serverless architecture.

---

## 📝 Pre-Deployment Checklist

Before deploying, make sure:

- [x] `.gitignore` is updated to INCLUDE `processed_data/merged_dataset.csv`
- [x] `Procfile` exists (tells platform how to run app)
- [x] `runtime.txt` exists (specifies Python version)
- [x] `requirements.txt` includes `gunicorn`
- [x] `processed_data/merged_dataset.csv` is committed to git
- [x] All code is pushed to GitHub
- [ ] Test locally first: `gunicorn api:app`

---

## 🧪 Test Production Build Locally

Before deploying, test with Gunicorn (production server):

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (like production)
gunicorn api:app

# Open browser to http://localhost:8000
```

If this works, your deployment should work too!

---

## 🐛 Common Deployment Issues

### Issue: "Module not found"
**Solution**: Make sure `requirements.txt` includes all dependencies

### Issue: "Application failed to start"
**Solution**: Check that `api.py` has `if __name__ == '__main__'` block at the end

### Issue: "CSV file not found"
**Solution**: 
1. Check that `processed_data/merged_dataset.csv` is in your repo
2. Update `.gitignore` to NOT exclude it
3. Run: `git add processed_data/merged_dataset.csv`
4. Commit and push

### Issue: "Port binding error"
**Solution**: Update `api.py` to use environment port:
```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
```

---

## 🔒 Environment Variables (Optional)

If you need secrets (API keys, database URLs), add them as environment variables:

**In Render/Heroku:**
- Go to Settings → Environment Variables
- Add key-value pairs

**In code:**
```python
import os
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-key')
```

---

## 📊 Database Considerations

**Current Setup**: Uses CSV files (works fine for small datasets)

**For larger scale**:
- Consider PostgreSQL (Render/Heroku offer free tiers)
- Migrate CSV data to database tables
- Update queries to use SQLAlchemy

**But for a datathon project, CSV is perfectly fine!**

---

## ✅ Recommended: Render

For your use case, **Render** is the best choice:
- Free
- Easy setup
- Automatic deployments
- Good for Python/Flask
- No credit card required

Just make sure `processed_data/merged_dataset.csv` is in your repo first!

---

## 🎉 After Deployment

Once deployed, you'll get a URL like:
- `https://college-recommender.onrender.com`

Share this URL with anyone, and they can use your app!

No need to run `python api.py` anymore - it's live on the internet! 🌐

