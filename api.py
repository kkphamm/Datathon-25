from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.neighbors import NearestNeighbors
from sklearn.impute import SimpleImputer
from sklearn.metrics import euclidean_distances
import numpy as np
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # Enable CORS for React frontend

# Load and prepare data (same as claude_rag_recommender.py)
merged = pd.read_csv("processed_data/merged_dataset.csv")
df = merged.copy()

# Feature definitions
numeric_features = [
    "Net Price",
    "Average Net Price After Grants, 2020-21",
    "Average Net Price After Grants, 2019-20",
    "Average Net Price After Grants, 2018-19",
    "Affordability Gap (net price minus income earned working 10 hrs at min wage)",
    "Weekly Hours to Close Gap",
    "State Minimum Wage",
    "Income Earned from Working 10 Hours a Week at State's Minimum Wage",
    "Monthly Center-Based Child Care Cost",
    "Adjusted Monthly Center-Based Child Care Cost",
    "Annual Center-Based Child Care Cost",
    "Monthly Home-Based Child Care Cost",
    "Adjusted Monthly Home-Based Child Care Cost",
    "Annual Home-Based Child Care Cost",
    "First-Time, Full-Time Retention Rate",
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
    "Bachelor's Degree Graduation Rate Within 4 Years - Total",
    "Bachelor's Degree Graduation Rate Within 5 Years - Total",
    "Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants",
    "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years",
    "Median Earnings of Students Working and Not Enrolled 10 Years After Entry",
    "Median Earnings of Dependent Students Working and Not Enrolled 10 Years After Entry",
    "Median Earnings of Independent Students Working and Not Enrolled 10 Years After Entry",
    "Instructional Expenses Per FTE",
    "Instructional Expenses FASB per FTE",
    "Endowment Assets FASB per Student",
]

binary_features = ["HSI", "PBI", "AANAPII", "ANNHI", "HBCU", "TRIBAL", "NANTI"]
categorical_features = ["State Abbreviation", "Region", "Institution Size Category Name", "Sector Name", "Highest Degree Offered Name"]

# Prepare model
key_features = [
    "Net Price",
    "First-Time, Full-Time Retention Rate",
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"
] + binary_features + categorical_features

df_model = df[numeric_features + binary_features + categorical_features].dropna(subset=key_features)
imputer = SimpleImputer(strategy='mean')
df_model[numeric_features] = imputer.fit_transform(df_model[numeric_features])
index_map = df_model.index

df_encoded = pd.get_dummies(df_model, columns=categorical_features, drop_first=True)
scaler = StandardScaler()
df_encoded[numeric_features] = scaler.fit_transform(df_encoded[numeric_features])

knn = NearestNeighbors(metric="euclidean")
knn.fit(df_encoded)

# Helper functions
def convert_preferences_to_weights(user_input):
    """🎯 MISSION-ALIGNED: Includes Pell focus & Affordability Gap weighting!"""
    weights = {}
    weights["Net Price"] = -1.0
    weights["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] = 1.0
    weights["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"] = 1.0  # 🎯 Pell grad rate
    weights["First-Time, Full-Time Retention Rate"] = 1.0
    weights["Affordability Gap"] = -0.3  # 🎯 Lower gap is better (negative weight)
    weights["_max_net_price"] = user_input.get("max_net_price", np.inf)
    weights["_min_grad_rate"] = user_input.get("min_grad_rate", 0)
    weights["_min_retention"] = user_input.get("min_retention", 0)
    weights["MSI_preferences"] = user_input.get("MSI_preferences", [])
    weights["preferred_state"] = user_input.get("preferred_state", None)
    weights["focus_pell"] = user_input.get("focus_pell", False)  # 🎯 Focus on Pell students
    return weights

def compute_weighted_scores(df_clean, weights):
    """🎯 MISSION-ALIGNED: Includes Affordability Gap & Pell-focused graduation rates!"""
    score = pd.Series(0.0, index=df_clean.index)
    STATE_PREFERENCE_BONUS = 15000.0
    MSI_PREFERENCE_BONUS = 5000.0

    # Apply base weights
    base_features = ["Net Price", "First-Time, Full-Time Retention Rate"]
    
    # 🎯 MISSION-ALIGNED: Use Pell-specific grad rate if requested
    if weights.get("focus_pell", False):
        base_features.append("Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years")
    else:
        base_features.append("Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total")
    
    for feat in base_features:
        if feat in df_clean.columns and feat in weights:
            score += weights[feat] * df_clean[feat]
    
    # 🎯 MISSION-ALIGNED: Penalize high Affordability Gap (lower gap is better)
    if "Affordability Gap (net price minus income earned working 10 hrs at min wage)" in df_clean.columns:
        score += weights.get("Affordability Gap", -0.3) * df_clean["Affordability Gap (net price minus income earned working 10 hrs at min wage)"]

    if "_max_net_price" in weights:
        penalty = df_clean["Net Price"] - weights["_max_net_price"]
        penalty = penalty.apply(lambda x: x if x > 0 else 0)
        score -= penalty * 1.0

    # Bonus for exceeding min grad rate - 🎯 Use Pell-specific grad rate if focus_pell is enabled
    if "_min_grad_rate" in weights:
        if weights.get("focus_pell", False) and "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years" in df_clean.columns:
            grad_col = "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"
        else:
            grad_col = "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"
        
        bonus = df_clean[grad_col] - weights["_min_grad_rate"]
        bonus = bonus.apply(lambda x: x if x > 0 else 0)
        score += bonus * 10.0

    if "_min_retention" in weights:
        bonus = df_clean["First-Time, Full-Time Retention Rate"] - weights["_min_retention"]
        bonus = bonus.apply(lambda x: x if x > 0 else 0)
        score += bonus * 10.0

    for msi in weights["MSI_preferences"]:
        if msi in df_clean.columns:
            score += df_clean[msi] * MSI_PREFERENCE_BONUS

    if weights["preferred_state"] and "State Abbreviation" in df_clean.columns:
        is_preferred_state = (df_clean["State Abbreviation"] == weights["preferred_state"]).astype(float)
        score += is_preferred_state * STATE_PREFERENCE_BONUS

    return score

def knn_similarity(user_input):
    """🎯 MISSION-ALIGNED: Includes Pell Grant Rate & Affordability Gap in KNN!"""
    vec = pd.DataFrame(0, index=[0], columns=df_encoded.columns)
    
    numeric_input = pd.Series(index=numeric_features, dtype=float)
    numeric_input["Net Price"] = user_input.get("max_net_price", df_model["Net Price"].mean())
    numeric_input["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] = user_input.get("min_grad_rate", df_model["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"].mean())
    numeric_input["First-Time, Full-Time Retention Rate"] = user_input.get("min_retention", df_model["First-Time, Full-Time Retention Rate"].mean())
    
    # 🎯 MISSION-ALIGNED: Add Pell Grant & Affordability Gap to KNN
    numeric_input["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"] = user_input.get("min_grad_rate", df_model["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"].mean())
    numeric_input["Affordability Gap (net price minus income earned working 10 hrs at min wage)"] = user_input.get("max_net_price", df_model["Affordability Gap (net price minus income earned working 10 hrs at min wage)"].mean())
    
    numeric_input = numeric_input.fillna(df_model[numeric_features].mean())
    vec[numeric_features] = scaler.transform(numeric_input.to_frame().T)

    for feat in binary_features:
        if feat in user_input.get("MSI_preferences", []):
            vec[feat] = 1

    if user_input.get("preferred_state"):
        col = f"State Abbreviation_{user_input['preferred_state']}"
        if col in vec.columns:
            vec[col] = 1

    all_data = knn._fit_X
    distances = euclidean_distances(vec.values, all_data)
    sim = 1 / (1 + distances.flatten())
    
    return pd.Series(sim, index=index_map)

ALPHA = 0.6
BETA = 0.4

def recommend_colleges(user_input, top_n=10):
    weights = convert_preferences_to_weights(user_input)
    weighted_scores = compute_weighted_scores(df_model, weights)
    knn_scores = knn_similarity(user_input)
    knn_scores_aligned = knn_scores.reindex(df_model.index).fillna(0)

    score_scaler = StandardScaler()
    scaled_weights = score_scaler.fit_transform(weighted_scores.values.reshape(-1, 1)).flatten()
    scaled_knn = score_scaler.fit_transform(knn_scores_aligned.values.reshape(-1, 1)).flatten()
    
    final_score = pd.Series(
        (ALPHA * scaled_weights + BETA * scaled_knn),
        index=df_model.index
    )
    
    top_idx = final_score.nlargest(top_n).index
    results = df.loc[top_idx].copy()
    
    results['HybridScore'] = final_score[top_idx]
    results['WeightedScore_Scaled'] = scaled_weights[df_model.index.get_indexer(top_idx)]
    results['KnnScore_Scaled'] = scaled_knn[df_model.index.get_indexer(top_idx)]

    return results.sort_values("HybridScore", ascending=False)

# Serve static files
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/about.html')
def serve_about():
    return send_from_directory('.', 'about.html')

@app.route('/<path:path>')
def serve_static(path):
    # Serve CSS, JS, and other static files
    if path.endswith(('.css', '.js', '.html')):
        return send_from_directory('.', path)
    # If not a static file, return 404
    return "Not found", 404

# API Endpoints
@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    try:
        data = request.json
        user_input = {
            "max_net_price": data.get("maxNetPrice", 25000),
            "min_grad_rate": data.get("minGradRate", 40),
            "min_retention": data.get("minRetention", 70),
            "MSI_preferences": data.get("msiPreferences", []),
            "preferred_state": data.get("preferredState", None),
            "focus_pell": data.get("focusPell", False)  # 🎯 MISSION-ALIGNED: Pell focus option
        }
        
        top_n = data.get("topN", 10)
        results = recommend_colleges(user_input, top_n)
        
        # 🎯 MISSION-ALIGNED: Include Pell & Affordability data in response
        results_subset = results[[
            "Institution Name",
            "State Abbreviation",
            "Net Price",
            "MSI Status",
            "First-Time, Full-Time Retention Rate",
            "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
            "Region",
            "HybridScore",
            "City",
            "Affordability Gap (net price minus income earned working 10 hrs at min wage)",
            "Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants",
            "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"
        ]].copy()
        
        # Replace NaN values with None (becomes null in JSON) to ensure valid JSON
        results_subset = results_subset.fillna(0)  # Replace NaN with 0 for numeric fields
        
        results_dict = results_subset.to_dict(orient='records')
        
        return jsonify({
            "success": True,
            "results": results_dict
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400

@app.route('/api/states', methods=['GET'])
def get_states():
    states = sorted(df['State Abbreviation'].dropna().unique().tolist())
    return jsonify(states)

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

