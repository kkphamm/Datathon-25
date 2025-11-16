import pandas as pd
import numpy as np

# importing datasets
affordability = pd.read_csv('affordability.csv')
collegeresults = pd.read_csv('collegeresults.csv')


# note that affordability has more rows than collegeresults so merged column has dropped some rows

# cleaning data

college_results_cols = [

    #ID
    "UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION",
    
    
    # Identifiers
    "Institution Name",
    "City of Institution",
    "State of Institution",
    "Institution Type",
    "Sector of Institution",

    # Cost & Net Price (from College Results)
    "Average Net Price After Grants, 2020-21",
    "Average Net Price After Grants, 2019-20",
    "Average Net Price After Grants, 2018-19",

    # Pell Indicators
    "Percent of First-Time, Full-Time Undergraduates Awarded Pell Grants",
    "Percent Full-time, First-time, Pell Grant Recipients Receiving an Award - 6 Years",
    "Percent Full-time, First-time, Pell Grant Recipients Still Enrolled at Same Institution - 8 Years",

    # Graduation Rates
    "Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total",
    "Bachelor's Degree Graduation Rate Within 4 Years - Total",
    "Bachelor's Degree Graduation Rate Within 5 Years - Total",

    # Retention / Success Metrics
    "First-Time, Full-Time Retention Rate",
    "Percent of Full-time, First-time Degree-Seeking Undergraduates",

    # Grant Aid (Institutional + Federal)
    "Average Amount of Institutional Grant Aid Awarded to First-Time, Full-Time Undergraduates",
    "Average Amount of Federal, State, Local, or Institutional Grant Aid Awarded",
    "Percent of First-Time, Full-Time Undergraduates Awarded Federal, State, Local or Institutional Grant Aid",

    # School Size
    "Number of Undergraduates Enrolled",
    "Institution Size Category",

    # Instructional Spending / Financial Health
    "Instructional Expenses Per FTE",
    "Instructional Expenses FASB per FTE",
    "Endowment Assets FASB per Student",

    # MSI Tags (in this dataset)
    "Hispanic-serving Institution (HSI)",
    "Predominantly Black Institution (PBI)",
    "Asian American or Native American Pacific Islander-Serving Institution (AANAPISI)",
    "Native American Non-Tribal Institution (NANTI)",
    "Historically Black College or University (HBCU)",
    "Tribal College or University (TCU)",

    # Earnings (Optional but strong ROI features)
    "Median Earnings of Students Working and Not Enrolled 10 Years After Entry",
    "Median Earnings of Dependent Students Working and Not Enrolled 10 Years After Entry",
    "Median Earnings of Independent Students Working and Not Enrolled 10 Years After Entry",

    # Geo fields
    "LATITUDE",
    "LONGITUDE",
]

affordability_cols = [
    #ID
    "Unit ID",

    # Identifiers
    "Institution Name",
    "City",
    "State Abbreviation",
    "Sector Name",
    "Sector",

    # MSI Flags
    "MSI Status",
    "MSI Type",
    "HBCU",
    "PBI",
    "ANNHI",
    "TRIBAL",
    "AANAPII",
    "HSI",
    "NANTI",

    # Cost Data
    "Net Price",
    "Cost of Attendance: In State, On Campus",
    "Cost of Attendance: In State",
    "Cost of Attendance: Out of State",
    "Cost of Attendance: In District",

    # Affordability Gap
    "Affordability Gap (net price minus income earned working 10 hrs at min wage)",
    "Weekly Hours to Close Gap",

    # Income-related data
    "State Minimum Wage",
    "Income Earned from Working 10 Hours a Week at State's Minimum Wage",

    # Childcare cost (optional for parent students)
    "Monthly Center-Based Child Care Cost",
    "Annual Center-Based Child Care Cost",
    "Adjusted Monthly Center-Based Child Care Cost",
    "Monthly Home-Based Child Care Cost",
    "Adjusted Monthly Home-Based Child Care Cost",
    "Annual Home-Based Child Care Cost",

    # Location
    "Latitude",
    "Longitude",
    "County Name",
    "Zip Code",
    "Region",
    "Region #",

    # Academic classification
    "Highest Degree Offered Name",
    "Highest Level Offered Name",
    "Institution Size Category Name",
]

collegeresults = collegeresults[college_results_cols]
affordability = affordability[affordability_cols]

# collegeresults.head()

numeric_cols = affordability.select_dtypes(include='number').columns.drop('Unit ID')
non_numeric_cols = affordability.select_dtypes(exclude='number').columns

affordability = affordability.groupby('Unit ID').agg(
    {**{col: 'mean' for col in numeric_cols},
     **{col: 'first' for col in non_numeric_cols}}
).reset_index()


# Merging the datasets
merged = affordability.merge(collegeresults, left_on='Unit ID', right_on='UNIQUE_IDENTIFICATION_NUMBER_OF_THE_INSTITUTION')

# Display the merged DataFrame
merged.drop('Institution Name_y', axis=1, inplace=True)
merged.drop('State of Institution', axis=1, inplace=True)
merged.rename(columns={'Institution Name_x': 'Institution Name'}, inplace=True)

# merged.head()

#merged.to_csv("merged_dataset.csv", index=False)
merged.to_excel("merged_dataset.xlsx", index=False)

def compute_student_success_scores(df,
        selected_state=None,
        max_net_price=50000,
        max_afford_gap=50000,
        msi_preference=False,
        max_work_hours=40,
        student_parent=False):
    """
    df = processed affordability + outcomes dataframe
    If selected_state is None or '', state matching is disabled.
    """

    # -------------------------------------------------------------
    # 1. AFFORDABILITY SCORE
    # -------------------------------------------------------------
    affordability_score = (
        0.5 * (1 - df['Net Price'] / max_net_price) +
        0.5 * (1 - df['Affordability Gap (net price minus income earned working 10 hrs at min wage)'] / max_afford_gap)
    ).clip(lower=0, upper=1)

    # -------------------------------------------------------------
    # 2. STATE FIT SCORE
    # -------------------------------------------------------------
    if selected_state is None or selected_state == "":
        # no state selected → treat all states as equally valid
        fit_score = np.ones(len(df))
    else:
        fit_score = np.where(df['State Abbreviation'] == selected_state, 1.0, 0.3)

    # -------------------------------------------------------------
    # 3. MSI SCORE
    # -------------------------------------------------------------
    has_msi = (
        (df['MSI Status'] == "Yes") |
        (df[['HBCU', 'PBI', 'AANAPII', 'ANNHI', 'TRIBAL', 'HSI', 'NANTI']].sum(axis=1) > 0)
    )

    if msi_preference:
        msi_score = has_msi.astype(float)
    else:
        msi_score = np.full(len(df), 0.5)

    # -------------------------------------------------------------
    # 4. OUTCOME SCORE
    # -------------------------------------------------------------
    retention = df['First-Time, Full-Time Retention Rate'] / 100
    grad6 = df["Bachelor's Degree Graduation Rate Bachelor Degree Within 6 Years - Total"] / 100

    earnings = df['Median Earnings of Students Working and Not Enrolled 10 Years After Entry']
    earnings_norm = earnings / earnings.max()

    outcomes_score = (
        0.4 * retention +
        0.4 * grad6 +
        0.2 * earnings_norm
    ).clip(lower=0, upper=1)

    # -------------------------------------------------------------
    # 5. WORKLOAD SCORE
    # -------------------------------------------------------------
    workload_score = (1 - df['Weekly Hours to Close Gap'] / max_work_hours).clip(0, 1)

    # -------------------------------------------------------------
    # 6. PARENT SUPPORT SCORE
    # -------------------------------------------------------------
    childcare = df['Adjusted Monthly Center-Based Child Care Cost'].fillna(0)
    childcare_norm = (1 - (childcare / (childcare.max() if childcare.max() > 0 else 1))).clip(0, 1)

    if student_parent:
        parent_support_score = childcare_norm
    else:
        parent_support_score = np.full(len(df), 0.5)

    # -------------------------------------------------------------
    # 7. FINAL SCORE
    # -------------------------------------------------------------
    final_score = (
        0.30 * affordability_score +
        0.10 * fit_score +
        0.10 * msi_score +
        0.30 * outcomes_score +
        0.15 * workload_score +
        0.05 * parent_support_score
    ).clip(0, 1)

    df = df.copy()
    df['StudentSuccessScore'] = final_score

    return df
