"""
01_generate_data.py
-------------------
Generates a synthetic 150,000-row Multiproduct Household (MPHH) dataset
for Progressive Insurance Agency Operations Analytics portfolio project.

Each row represents one insured household at a point-in-time snapshot.
The target variable is `converted_mphh` (0/1) -- whether the household
added a second Progressive product within 12 months of the snapshot date.

Author : Luciano Casillas
Version: 1.0
"""

# ============================================================
# CONFIGURATION BLOCK -- edit only these values
# ============================================================
N_ROWS   = 150_000
SEED     = 42
VERSION  = "1.0"
OUT_DIR  = "data"
FILENAME = "mphh_crosssell"

import json
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

os.makedirs(OUT_DIR, exist_ok=True)
rng = np.random.default_rng(SEED)

# ============================================================
# SECTION 1: Household demographics and account attributes
# ============================================================
household_ids = [f"HH-{str(i).zfill(7)}" for i in range(1, N_ROWS + 1)]

states = ["OH", "TX", "FL", "CA", "PA", "IL", "GA", "NC", "MI", "AZ"]
state_weights = [0.18, 0.14, 0.12, 0.11, 0.09, 0.08, 0.07, 0.07, 0.07, 0.07]
state = rng.choice(states, size=N_ROWS, p=state_weights)

age_of_primary = rng.integers(22, 78, size=N_ROWS)

home_ownership = np.where(
    age_of_primary >= 35,
    rng.choice(["Homeowner", "Renter", "Condo"], size=N_ROWS, p=[0.62, 0.28, 0.10]),
    rng.choice(["Homeowner", "Renter", "Condo"], size=N_ROWS, p=[0.38, 0.52, 0.10])
)

household_size = rng.choice([1, 2, 3, 4, 5], size=N_ROWS, p=[0.25, 0.35, 0.20, 0.15, 0.05])

income_band = rng.choice(
    ["<$50k", "$50k-$75k", "$75k-$100k", "$100k-$150k", "$150k+"],
    size=N_ROWS,
    p=[0.18, 0.24, 0.22, 0.22, 0.14]
)

# ============================================================
# SECTION 2: Agency and product channel attributes
# ============================================================
agency_channel = rng.choice(
    ["Independent Agent", "Direct Online", "Call Center", "Captive Agent"],
    size=N_ROWS,
    p=[0.42, 0.28, 0.18, 0.12]
)

anchor_product = rng.choice(
    ["Auto", "Motorcycle", "Boat", "Commercial Auto"],
    size=N_ROWS,
    p=[0.72, 0.12, 0.08, 0.08]
)

policy_tier = rng.choice(
    ["Basic", "Standard", "Plus", "Elite"],
    size=N_ROWS,
    p=[0.22, 0.38, 0.28, 0.12]
)

# ============================================================
# SECTION 3: Tenure and engagement signals
# ============================================================
tenure_months = rng.integers(1, 121, size=N_ROWS).astype(float)

# Proactive outreach contacts -- a key behavioral signal
# Households that received 1-3 outreach contacts convert at higher rates
outreach_contacts_12m = rng.choice(
    [0, 1, 2, 3, 4, 5],
    size=N_ROWS,
    p=[0.38, 0.22, 0.18, 0.12, 0.06, 0.04]
)

# Claims filed in past 24 months -- friction signal
claims_24m = rng.choice(
    [0, 1, 2, 3],
    size=N_ROWS,
    p=[0.58, 0.28, 0.10, 0.04]
)

# Digital engagement score (1-10): app logins, policy views, quote starts
digital_engagement_score = rng.integers(1, 11, size=N_ROWS).astype(float)
# Boost engagement for younger, direct-online customers
direct_online_mask = agency_channel == "Direct Online"
age_young_mask = age_of_primary < 40
digital_engagement_score = np.where(
    direct_online_mask & age_young_mask,
    np.clip(digital_engagement_score + rng.integers(1, 4, size=N_ROWS), 1, 10),
    digital_engagement_score
)

# Quote started for property product in past 6 months (early signal)
property_quote_started = rng.choice([0, 1], size=N_ROWS, p=[0.72, 0.28])

# ============================================================
# SECTION 4: Financial value columns
# ============================================================
# Annual premium on anchor product (base by tier, with noise)
base_premium_map = {"Basic": 680, "Standard": 920, "Plus": 1250, "Elite": 1750}
base_premium = np.array([base_premium_map[t] for t in policy_tier], dtype=float)
annual_premium_anchor = np.round(
    base_premium * rng.uniform(0.85, 1.20, size=N_ROWS), 2
)

# Projected CLTV if household converts to MPHH (anchor + property premium * retention factor)
# CLTV = (anchor_premium + property_premium_estimate) * projected_tenure_years * margin_factor
property_premium_est = np.where(
    home_ownership == "Homeowner",
    rng.uniform(900, 1800, size=N_ROWS),
    rng.uniform(400, 900, size=N_ROWS)
)
projected_tenure_years = np.clip(
    (tenure_months + rng.uniform(12, 60, size=N_ROWS)) / 12, 1, 8
)
margin_factor = 0.18
projected_mphh_cltv = np.round(
    (annual_premium_anchor + property_premium_est) * projected_tenure_years * margin_factor
    * rng.uniform(0.90, 1.10, size=N_ROWS),
    2
)

# ============================================================
# SECTION 5: Target variable construction (converted_mphh)
# Build a realistic conversion signal with multiple drivers.
# ============================================================
log_odds = (
    -2.80                                                          # intercept (base ~5.7% rate)
    + 0.65  * (outreach_contacts_12m >= 1).astype(float)          # any outreach
    + 0.45  * (outreach_contacts_12m >= 2).astype(float)          # 2+ outreach
    + 0.90  * property_quote_started                               # started a quote
    + 0.40  * (digital_engagement_score >= 7).astype(float)       # high digital use
    + 0.35  * (home_ownership == "Homeowner").astype(float)       # homeowner
    + 0.20  * (tenure_months >= 24).astype(float)                 # established customer
    + 0.30  * (income_band.isin(["$100k-$150k", "$150k+"]) if hasattr(income_band, 'isin')
               else np.isin(income_band, ["$100k-$150k", "$150k+"])).astype(float)
    + 0.25  * (policy_tier.isin(["Plus", "Elite"]) if hasattr(policy_tier, 'isin')
               else np.isin(policy_tier, ["Plus", "Elite"])).astype(float)
    + 0.30  * (agency_channel == "Independent Agent").astype(float)
    - 0.20  * (agency_channel == "Direct Online").astype(float)   # slightly lower IA influence
    - 0.35  * (claims_24m >= 2).astype(float)                     # friction from claims
    + 0.10  * (household_size >= 3).astype(float)                 # larger households
    - 0.15  * (tenure_months < 6).astype(float)                   # too new
)

prob_convert = 1 / (1 + np.exp(-log_odds))
# Add calibrated noise
prob_convert = np.clip(prob_convert + rng.normal(0, 0.03, size=N_ROWS), 0.01, 0.98)

converted_mphh = (rng.uniform(size=N_ROWS) < prob_convert).astype(int)

# ============================================================
# SECTION 6: Derived risk / propensity score (dashboard only)
# NOTE: Exclude from ML training features -- leakage-adjacent
# This is a business-facing score, not a model input.
# ============================================================
propensity_score = np.round(np.clip(prob_convert * 100, 1, 99), 1)

# Risk tier from score
def score_to_tier(score):
    if score >= 65:
        return "High Propensity"
    elif score >= 40:
        return "Medium Propensity"
    else:
        return "Low Propensity"

propensity_tier = np.array([score_to_tier(s) for s in propensity_score])

# ============================================================
# SECTION 7: Snapshot date (for cohort analysis)
# ============================================================
base_date = datetime(2023, 1, 1)
snapshot_offsets = rng.integers(0, 1095, size=N_ROWS)  # 3-year window
snapshot_date = [
    (base_date + timedelta(days=int(d))).strftime("%Y-%m-%d")
    for d in snapshot_offsets
]

# ============================================================
# SECTION 8: Assemble DataFrame and export
# ============================================================
df = pd.DataFrame({
    "household_id"             : household_ids,
    "snapshot_date"            : snapshot_date,
    "state"                    : state,
    "age_of_primary"           : age_of_primary,
    "home_ownership"           : home_ownership,
    "household_size"           : household_size,
    "income_band"              : income_band,
    "agency_channel"           : agency_channel,
    "anchor_product"           : anchor_product,
    "policy_tier"              : policy_tier,
    "tenure_months"            : tenure_months.astype(int),
    "outreach_contacts_12m"    : outreach_contacts_12m,
    "claims_24m"               : claims_24m,
    "digital_engagement_score" : digital_engagement_score.astype(int),
    "property_quote_started"   : property_quote_started,
    "annual_premium_anchor"    : annual_premium_anchor,
    "projected_mphh_cltv"      : projected_mphh_cltv,
    "propensity_score"         : propensity_score,       # DASHBOARD ONLY -- do not train on
    "propensity_tier"          : propensity_tier,        # DASHBOARD ONLY -- do not train on
    "converted_mphh"           : converted_mphh,         # TARGET VARIABLE
})

csv_path = os.path.join(OUT_DIR, f"{FILENAME}.csv")
df.to_csv(csv_path, index=False)
print(f"Dataset saved: {csv_path}  |  Rows: {len(df):,}  |  Conversion rate: {df['converted_mphh'].mean():.3%}")

# ============================================================
# SECTION 9: Metadata JSON export
# ============================================================
meta = {
    "project"           : "MPHH Cross-Sell Propensity",
    "version"           : VERSION,
    "seed"              : SEED,
    "n_rows"            : N_ROWS,
    "generated_at"      : datetime.now().isoformat(),
    "target_variable"   : "converted_mphh",
    "conversion_rate"   : round(float(df["converted_mphh"].mean()), 4),
    "columns"           : list(df.columns),
    "leakage_columns"   : ["propensity_score", "propensity_tier"],
    "financial_columns" : ["annual_premium_anchor", "projected_mphh_cltv"],
}
meta_path = os.path.join(OUT_DIR, f"{FILENAME}_metadata.json")
with open(meta_path, "w") as f:
    json.dump(meta, f, indent=2)
print(f"Metadata saved: {meta_path}")
