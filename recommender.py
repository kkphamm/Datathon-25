import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import numpy as np
from sklearn.impute import SimpleImputer
from sklearn.metrics import euclidean_distances  


merged = pd.read_csv("processed_data/merged_dataset.csv")
df = merged.copy()  # your merged dataset

# ================================
# 2. FEATURES
# ================================
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

binary_features = [
    "HSI",
    "PBI",
    "AANAPII",
    "ANNHI",
    "HBCU",
    "TRIBAL",
    "NANTI",
]

categorical_features = [
    "State Abbreviation",
    "Region",
    "Institution Size Category Name",
    "Sector Name",
    "Highest Degree Offered Name",
]

# ================================
# 3. PREP DATAFRAME FOR KNN
# ================================

# Define the *key* features that are essential.
key_features = [
    "Net Price",
    "First-Time, Full-Time Retention Rate",
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"
] + binary_features + categorical_features

# Use .dropna(subset=...) to avoid catastrophic data loss
df_model = df[numeric_features + binary_features + categorical_features].dropna(subset=key_features)

# Impute NaNs for the *remaining* numeric features (e.g., "Median Earnings...")
imputer = SimpleImputer(strategy='mean')
df_model[numeric_features] = imputer.fit_transform(df_model[numeric_features])

# Store the index for later mapping
index_map = df_model.index

# One-hot encode categorical features
df_encoded = pd.get_dummies(df_model, columns=categorical_features, drop_first=True)

# Scale all numeric features
scaler = StandardScaler()
df_encoded[numeric_features] = scaler.fit_transform(df_encoded[numeric_features])

# Fit KNN model
knn = NearestNeighbors(metric="euclidean")
knn.fit(df_encoded)

# ================================
# 4. CONVERT USER INPUTS TO WEIGHTS
# ================================
def convert_preferences_to_weights(user_input):
    """
    Convert user-friendly inputs into weights for scoring model.
    🎯 NOW INCLUDES: Pell focus & Affordability Gap weighting!
    """
    weights = {}

    # numeric weights
    weights["Net Price"] = -1.0  # lower is better
    weights["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] = 1.0
    weights["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"] = 1.0  # 🎯 Pell grad rate
    weights["First-Time, Full-Time Retention Rate"] = 1.0
    weights["Affordability Gap"] = -0.3  # 🎯 Lower gap is better (negative weight)

    # store user thresholds
    weights["_max_net_price"] = user_input.get("max_net_price", np.inf)
    weights["_min_grad_rate"] = user_input.get("min_grad_rate", 0)
    weights["_min_retention"] = user_input.get("min_retention", 0)

    # MSI and state preferences
    weights["MSI_preferences"] = user_input.get("MSI_preferences", [])
    weights["preferred_state"] = user_input.get("preferred_state", None)
    
    # 🎯 MISSION-ALIGNED: Focus on Pell Grant students?
    weights["focus_pell"] = user_input.get("focus_pell", False)

    return weights

# ================================
# 5. WEIGHTED SCORING FUNCTION
# ================================
def compute_weighted_scores(df_clean, weights):
    """
    Computes a score based on user preferences.
    Operates on the unscaled, imputed data (df_model).
    🎯 NOW INCLUDES: Affordability Gap & Pell-focused graduation rates!
    """
    score = pd.Series(0.0, index=df_clean.index)

    # ## FIX: Define large bonus values on the same scale as 'Net Price'
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

    # Penalize exceeding max net price
    if "_max_net_price" in weights:
        penalty = df_clean["Net Price"] - weights["_max_net_price"]
        penalty = penalty.apply(lambda x: x if x > 0 else 0)
        # This penalty is already in "dollars", so its scale is correct
        score -= penalty * 1.0 # Make penalty 1:1

    # Bonus for exceeding min grad rate
    # 🎯 MISSION-ALIGNED: Use Pell-specific grad rate if focus_pell is enabled
    if "_min_grad_rate" in weights:
        if weights.get("focus_pell", False) and "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years" in df_clean.columns:
            grad_col = "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"
        else:
            grad_col = "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"
        
        bonus = df_clean[grad_col] - weights["_min_grad_rate"]
        bonus = bonus.apply(lambda x: x if x > 0 else 0)
        score += bonus * 10.0 # Boost this bonus slightly

    # Bonus for exceeding min retention
    if "_min_retention" in weights:
        bonus = df_clean["First-Time, Full-Time Retention Rate"] - weights["_min_retention"]
        bonus = bonus.apply(lambda x: x if x > 0 else 0)
        score += bonus * 10.0 # Boost this bonus slightly

    # ## FIX: Apply the new, powerful MSI bonus
    for msi in weights["MSI_preferences"]:
        if msi in df_clean.columns:
            # Add bonus for *each* preferred MSI
            score += df_clean[msi] * MSI_PREFERENCE_BONUS

    # ## FIX: Apply the new, powerful state bonus
    if weights["preferred_state"] and "State Abbreviation" in df_clean.columns:
        is_preferred_state = (df_clean["State Abbreviation"] == weights["preferred_state"]).astype(float)
        score += is_preferred_state * STATE_PREFERENCE_BONUS

    return score

# ================================
# 6. KNN SIMILARITY
# ================================
def knn_similarity(user_input):
    """
    Computes a dense similarity score for ALL colleges against the user input.
    NOW INCLUDES: Pell Grant Rate & Affordability Gap for mission alignment!
    """
    # Create the query vector with all columns from the encoded DataFrame
    vec = pd.DataFrame(0, index=[0], columns=df_encoded.columns)

    # --- Numeric Features ---
    numeric_input = pd.Series(index=numeric_features, dtype=float)
    numeric_input["Net Price"] = user_input.get("max_net_price", df_model["Net Price"].mean())
    numeric_input["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] = user_input.get("min_grad_rate", df_model["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"].mean())
    numeric_input["First-Time, Full-Time Retention Rate"] = user_input.get("min_retention", df_model["First-Time, Full-Time Retention Rate"].mean())
    
    # 🎯 MISSION-ALIGNED: Add Pell Grant & Affordability Gap to KNN
    numeric_input["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"] = user_input.get("min_grad_rate", df_model["Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years"].mean())
    numeric_input["Affordability Gap (net price minus income earned working 10 hrs at min wage)"] = user_input.get("max_net_price", df_model["Affordability Gap (net price minus income earned working 10 hrs at min wage)"].mean())
    
    numeric_input = numeric_input.fillna(df_model[numeric_features].mean())
    vec[numeric_features] = scaler.transform(numeric_input.to_frame().T)

    # --- Binary MSI Features ---
    for feat in binary_features:
        if feat in user_input.get("MSI_preferences", []):
            vec[feat] = 1

    # --- Categorical Features ---
    if user_input.get("preferred_state"):
        col = f"State Abbreviation_{user_input['preferred_state']}"
        if col in vec.columns:
            vec[col] = 1

    # --- Compute Dense Similarity ---
    # Get the data the KNN was fitted on (all encoded colleges)
    all_data = knn._fit_X
    
    # Compute Euclidean distance from our user vector 'vec' to ALL other colleges
    # This returns a (1, N) array
    distances = euclidean_distances(vec.values, all_data)
    
    # Invert the distance to get a similarity score (0 to 1)
    # 1 / (1 + distance) is a common way to do this
    sim = 1 / (1 + distances.flatten())
    
    # Return a dense Series mapped to the correct df_model index
    return pd.Series(sim, index=index_map)

# ================================
# 7. HYBRID RECOMMENDER
# ================================
ALPHA = 0.6  # weighted score
BETA = 0.4   # KNN similarity

def recommend_colleges(user_input, k=20, top_n=10):
    weights = convert_preferences_to_weights(user_input)
    
    # Compute weighted scores on df_model (the clean, unscaled data)
    weighted_scores = compute_weighted_scores(df_model, weights)
    
    # --- FIX 1 ---
    # Get KNN scores (now a DENSE Series)
    # Remove 'k' from the call
    knn_scores = knn_similarity(user_input) 
    
    # --- FIX 2 ---
    # This alignment is no longer needed, but harmless.
    # We can just rename the variable for clarity.
    knn_scores_aligned = knn_scores.reindex(df_model.index).fillna(0) 

    # Scale both scores (0-1) before combining them
    score_scaler = StandardScaler()
    scaled_weights = score_scaler.fit_transform(weighted_scores.values.reshape(-1, 1)).flatten()
    scaled_knn = score_scaler.fit_transform(knn_scores_aligned.values.reshape(-1, 1)).flatten()
    # Combine the scaled scores
    final_score = pd.Series(
        (ALPHA * scaled_weights + BETA * scaled_knn),
        index=df_model.index  # The index for both scores is df_model.index
    )
    
    # Get the original index (from `df`) of the top N scores
    top_idx = final_score.nlargest(top_n).index

    # Retrieve results from the *original* df with ALL columns
    results = df.loc[top_idx].copy()
    
    # Add the scores
    results['HybridScore'] = final_score[top_idx]
    results['WeightedScore_Scaled'] = scaled_weights[df_model.index.get_indexer(top_idx)]
    results['KnnScore_Scaled'] = scaled_knn[df_model.index.get_indexer(top_idx)]

    return results.sort_values("HybridScore", ascending=False)

# ================================
# 8. EXAMPLE USAGE
# ================================
student_input = {
    "max_net_price": 22000,
    "min_grad_rate": 40,
    "min_retention": 75,
    "MSI_preferences": ["HSI", "HBCU"],
    "preferred_state": "CA"
}

print("Running recommender with the following input:")
print(student_input)
print("---")

top_colleges = recommend_colleges(student_input, k=20, top_n=10)

# Set display options to show full output
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None) # This is the key one for 'Institution Name'

# Display a summary view (key columns only)
summary_cols = [
    "Institution Name",
    "State Abbreviation",
    "Net Price",
    "MSI Status",
    "First-Time, Full-Time Retention Rate",
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
    "Region",
    "HybridScore"
]
print(top_colleges[summary_cols].to_string())
print(f"\n(Full dataset with {len(top_colleges.columns)} columns will be exported to files)")

# ================================
# 9. EXPORT FOR TABLEAU (CSV)
# ================================
from sklearn.preprocessing import MinMaxScaler 

print("\n" + "="*30)
print("GENERATING FILES FOR TABLEAU...")
print("="*30)

# --- Re-calculate scores for all colleges ---
weights = convert_preferences_to_weights(student_input)
weighted_scores = compute_weighted_scores(df_model, weights)
knn_scores = knn_similarity(student_input)
knn_scores_aligned = knn_scores.reindex(df_model.index).fillna(0)

# Use MinMaxScaler to get a 0-1 scale
scaler = MinMaxScaler()
scaled_weights = scaler.fit_transform(weighted_scores.values.reshape(-1, 1)).flatten()
scaled_knn = scaler.fit_transform(knn_scores_aligned.values.reshape(-1, 1)).flatten()

final_score_all = pd.Series(
    (ALPHA * scaled_weights + BETA * scaled_knn),
    index=df_model.index,
    name="HybridScore"
)

# --- Create the "all_scores" DataFrame ---
all_scores_df = pd.DataFrame({
    'HybridScore': final_score_all,
    'WeightedScore_Scaled': scaled_weights,
    'KnnScore_Scaled': scaled_knn
})

# --- Join scores with the *original* 'df' ---
full_scored_df = df.join(all_scores_df)
full_scored_df = full_scored_df.dropna(subset=['HybridScore'])

# --- Get Top 10 DataFrame ---
# (This re-uses the 'top_colleges' variable from your section 8)
top_10_df = top_colleges 

# --- Save the CSV files ---
# Create outputs directory if it doesn't exist
import os
os.makedirs("outputs", exist_ok=True)

print("Writing CSV files to 'outputs' folder...")
top_10_df.to_csv("outputs/top_10_recommendations.csv", index=False)
full_scored_df.to_csv("outputs/all_colleges_scored.csv", index=False)

print("\nSUCCESS!")
print("Saved 'outputs/top_10_recommendations.csv'")
print("Saved 'outputs/all_colleges_scored.csv'")
print("\nYou can now use these CSV files in Tableau or other tools.")