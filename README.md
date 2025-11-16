# College Recommender

A data-driven college search tool designed to help first-generation and Pell Grant students find affordable schools where they can succeed.

## Quick Start

**Requirements:** Python 3.11+

```bash
# Install dependencies
pip install -r requirements.txt

# Start the server
python api.py
```

Open your browser to `http://localhost:5000`

## What It Does

This tool helps students find colleges based on:
- Net price (actual cost after financial aid)
- Graduation and retention rates
- Affordability gap (cost relative to minimum wage work)
- Pell Grant student outcomes
- Minority-Serving Institution status
- Geographic preferences

The recommendation engine uses a hybrid machine learning approach combining weighted preferences with K-nearest neighbors similarity matching.

## Features

- Real-time recommendations based on your budget and priorities
- Focus mode for Pell Grant student outcomes
- Interactive Tableau dashboards with automatic filtering
- Clean, minimal interface
- No ads, no sponsored results

## Tech Stack

- **Backend:** Flask, Pandas, Scikit-learn
- **Frontend:** Vanilla JavaScript, CSS
- **Data:** 1,500+ U.S. colleges with 80+ data points each
- **Visualization:** Tableau Public (embedded)

## Deployment

See `DEPLOYMENT.md` for instructions on deploying to Render, Heroku, or other platforms.

## Project Structure

```
├── api.py                  # Flask backend
├── index.html              # Main page
├── about.html              # About page
├── script.js               # Frontend logic
├── style.css               # Styling
├── requirements.txt        # Python dependencies
└── processed_data/
    └── merged_dataset.csv  # College data
```

## License

Created for Berkeley Datathon 2025
