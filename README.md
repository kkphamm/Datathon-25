# 🎓 College Recommender System

A minimal, data-driven web application that empowers first-generation and Pell Grant students to find colleges where they can thrive, afford to stay, and successfully graduate.

## 🚀 Super Simple Setup (2 Steps!)

### Step 1: Start the Backend (Terminal 1)

```bash
python api.py
```

✅ Backend will run on http://localhost:5000

### Step 2: Open the Website

Simply **double-click** `index.html` or open it in your browser!

**Note:** All three files must be in the same folder:
- `index.html` - Main page
- `style.css` - Styling
- `script.js` - JavaScript logic

That's it! 🎉

---

## 📁 Project Files

**Important Files:**
- `index.html` - Main recommender page (minimal design)
- `about.html` - Mission and impact page for first-gen students
- `style.css` - Clean, minimal styling
- `script.js` - JavaScript logic (includes Tableau integration)
- `api.py` - Flask backend API
- `recommender.py` - ML recommender script
- `requirements.txt` - Python dependencies
- `TABLEAU_INTEGRATION.md` - Guide for dashboard integration

**Data:**
- `processed_data/merged_dataset.csv` - College dataset
- `outputs/` - Generated CSV files

---

## 🎯 How to Use

1. **Learn about the mission** - Visit the "About This Tool" page to understand why we built this for first-gen students
2. **Open `index.html` in your browser**
3. **Adjust your preferences** using clean, minimal sliders:
   - Maximum net price (actual cost after aid)
   - Minimum graduation rate (proven student success)
   - Minimum retention rate (ongoing support)
   - Number of results
4. **Optional filters:**
   - Select a preferred state
   - Check MSI institution types (HSI, HBCU, PBI, etc.)
5. **Click "Get Recommendations"**
6. **View your matches** - ranked colleges with detailed stats
7. **Dashboard updates automatically** with smart filtering:
   - **Heatmap**: Shows top 200 colleges for geographic density visualization
   - **Bar Chart**: Shows top 50 colleges for clear comparison
   - **Your cards**: Show the number you selected (5-20)

---

## 📊 Features

✅ **Minimal, Clean Design** - Professional aesthetic focused on usability  
✅ **First-Gen Focused** - Built specifically for first-generation and Pell Grant students  
✅ **About Page** - Explains social impact and why metrics matter  
✅ **Net Price Focus** - Uses actual net price, not misleading sticker prices  
✅ **Outcome-Driven** - Emphasizes graduation and retention rates  
✅ **MSI Discovery** - Easy filtering for Minority-Serving Institutions  
✅ **Real-time ML recommendations** via Flask API  
✅ **Dynamic Tableau dashboard** - updates automatically with your preferences!  
✅ **Smart filtering** - different limits for different visualizations:
   - Heatmap: Top 200 colleges for geographic patterns
   - Bar chart: Top 50 colleges for clarity
✅ **Optimized views** - Each chart shows the perfect amount of data  
✅ **Responsive design** - works on any device  
✅ **Auto-scroll** - smoothly scrolls to show the updated dashboard  

---

## 🛠️ Requirements

**Python Dependencies:**
```bash
pip install -r requirements.txt
```

Required:
- Flask
- Flask-CORS
- Pandas
- Scikit-learn
- NumPy

---

## 🔧 Technical Details

### Backend (Flask API)

**Endpoints:**
- `POST /api/recommend` - Get college recommendations
- `GET /api/states` - Get list of available states
- `GET /api/health` - Health check

### Frontend (Pure HTML/CSS/JS)

- No build process required
- No npm or Node.js needed
- Works directly in any modern browser
- Uses Fetch API for backend communication
- Tableau JavaScript API for dashboard

### ML Model

- **Hybrid recommender system:**
  - 60% weighted preference scoring
  - 40% KNN similarity matching
- **Features:** Net price, graduation rates, retention rates, MSI status, location
- **Dataset:** 6,000+ colleges with 76+ data points each

---

## 🐛 Troubleshooting

### "Error connecting to server"
**Solution:** Make sure Flask is running:
```bash
python api.py
```
You should see: `Running on http://127.0.0.1:5000`

### "Cannot GET /api/recommend"
**Solution:** The Flask backend needs to be started first.

### Tableau dashboard not showing
**Solutions:**
1. Make sure you have internet connection (loads from Tableau Public)
2. Wait a few seconds for it to load
3. Try refreshing the page (Ctrl+R or Cmd+R)

### "Module not found" error
**Solution:** Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Port 5000 already in use
**Solution:** Change the port in `api.py` line 228:
```python
app.run(debug=True, port=5001)  # Change to any available port
```

---

## 📂 Project Structure

```
.
├── index.html                      # Main HTML page
├── style.css                       # CSS styling
├── script.js                       # JavaScript logic
├── api.py                          # Flask backend
├── claude_rag_recommender.py       # ML recommender script
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── processed_data/
│   └── merged_dataset.csv          # College data
└── outputs/
    ├── top_10_recommendations.csv
    └── all_colleges_scored.csv
```

---

## 🎨 Design Philosophy

### Minimal & Purposeful
- **Clean white background** (#f9f9f9) - removes visual noise
- **Professional blue accent** (#007aff) - modern and trustworthy
- **Inter font** - clean, legible typography
- **Subtle borders** instead of heavy shadows
- **Ample whitespace** - focuses attention on what matters

### Built for First-Gen Students
Every design choice prioritizes clarity and accessibility. No confusing jargon, no overwhelming gradients—just clean, honest data that helps students make informed decisions.

## 🎨 Customization

### Change Accent Color
Edit `style.css` and search for `#007aff` to change the blue accent color throughout.

### Change Background
Edit `style.css` (line 8):
```css
background: #f9f9f9; /* Change to your preferred color */
```

### Modify Slider Ranges
Edit `index.html`:
```html
<input type="range" min="5000" max="50000" step="1000" value="25000">
```

### Adjust Tableau Dashboard Size
Edit `style.css` (lines 198-203):
```css
.tableauPlaceholder {
    width: 100%;
    min-height: 1400px;  /* Change this value */
}
```

### Update Tableau Dashboard
Replace the embed code in `index.html` (around line 93) with your new dashboard URL.

---

## 🚀 Production Deployment

### Backend
Use Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

### Frontend
Just upload these three files to any web host:
- `index.html`
- `style.css`
- `script.js`

Or use Python's built-in server:
```bash
python -m http.server 8000
```
Then visit: http://localhost:8000

---

## 📖 How It Works

1. **User adjusts preferences** in the HTML form
2. **JavaScript sends data** to Flask API via Fetch
3. **Flask processes** using ML model:
   - KNN finds similar colleges
   - Weighted scoring applies preferences
   - Hybrid score combines both
4. **Results returned** and displayed as cards
5. **Tableau filters intelligently**:
   - Fetches top 200 for heatmap (geographic density)
   - Shows top 50 in bar chart (clear comparison)
   - Displays your selected N in cards (5-20)
6. **Dashboard updates** - Each visualization optimized for its purpose

---

## 📝 License

Created for Berkeley Datathon 2025

---

## 🤝 Need Help?

1. Make sure `python api.py` is running
2. Open `index.html` in a modern browser (Chrome, Firefox, Edge, Safari)
3. Ensure all 3 files are in the same folder (`index.html`, `style.css`, `script.js`)
4. Check the browser console (F12) for any errors
5. Ensure `processed_data/merged_dataset.csv` exists

**That's all you need! Enjoy! 🎓**
