"""
02_generate_benchmarking_data.py
---------------------------------
Generates data/mphh_benchmarking.csv from the existing data/mphh_crosssell.csv.
Adds agent_id, region, and robinson_target_pct columns required by benchmarking_app.py.

Run once before launching benchmarking_app.py:
    python scripts/02_generate_benchmarking_data.py

Requirements: pandas, numpy (already in requirements.txt)
Author : Luciano Casillas
Version: 1.0
"""

# ============================================================
# CONFIGURATION
# ============================================================
SEED       = 42
INPUT_CSV  = "data/mphh_crosssell.csv"
OUTPUT_CSV = "data/mphh_benchmarking.csv"

import os
import json
import numpy as np
import pandas as pd
from datetime import datetime

# ============================================================
# SECTION 1: Load base dataset
# ============================================================
print(f"Loading {INPUT_CSV} ...")
df = pd.read_csv(INPUT_CSV)
print(f"  {len(df):,} rows loaded")

assert "household_id"    in df.columns, "Missing household_id — is this the right CSV?"
assert "agency_channel"  in df.columns, "Missing agency_channel"
assert "converted_mphh"  in df.columns, "Missing converted_mphh"

# ============================================================
# SECTION 2: Assign synthetic agent IDs
# Pool sizes mirror realistic agency structures:
#   Independent Agent: 200 agents (largest channel by count)
#   Call Center:       120 agents
#   Captive Agent:      80 agents
#   Direct Online:      50 agents (pooled queue, not individual agents)
# ============================================================
rng = np.random.default_rng(SEED)

agent_pool = {
    "Independent Agent": [f"IA-{str(i).zfill(4)}" for i in range(1, 201)],
    "Captive Agent":     [f"CA-{str(i).zfill(4)}" for i in range(1, 81)],
    "Call Center":       [f"CC-{str(i).zfill(4)}" for i in range(1, 121)],
    "Direct Online":     [f"DO-{str(i).zfill(4)}" for i in range(1, 51)],
}

def assign_agents(group):
    channel = group.name
    pool    = agent_pool[channel]
    return pd.Series(
        rng.choice(pool, size=len(group)),
        index=group.index
    )

print("Assigning agent IDs ...")
df["agent_id"] = df.groupby("agency_channel")["agency_channel"].transform(
    lambda g: rng.choice(agent_pool[g.name], size=len(g))
)
print(f"  {df['agent_id'].nunique()} unique agents assigned across {df['agency_channel'].nunique()} channels")

# ============================================================
# SECTION 3: Assign region from state
# ============================================================
STATE_REGION = {
    "OH": "Midwest",   "MI": "Midwest",   "IL": "Midwest",
    "TX": "South",     "FL": "South",     "GA": "South",    "NC": "South",
    "CA": "West",      "AZ": "West",
    "PA": "Northeast",
}

df["region"] = df["state"].map(STATE_REGION)

missing_states = df[df["region"].isna()]["state"].unique()
if len(missing_states) > 0:
    print(f"  WARNING: {len(missing_states)} states not mapped to a region: {missing_states}")
    df["region"] = df["region"].fillna("Other")

print(f"  Regions assigned: {sorted(df['region'].unique().tolist())}")

# ============================================================
# SECTION 4: Add Robinson Strategy quarterly targets
# Targets represent the MPHH conversion rate (%) that the
# Robinson Strategy sets as the growth goal for each quarter.
# ============================================================
df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
df["quarter"]       = df["snapshot_date"].dt.to_period("Q").astype(str)

ROBINSON_TARGETS = {
    "2023Q1": 25.0,
    "2023Q2": 25.5,
    "2023Q3": 26.0,
    "2023Q4": 26.5,
    "2024Q1": 27.0,
    "2024Q2": 27.5,
    "2024Q3": 28.0,
    "2024Q4": 28.5,
    "2025Q1": 29.0,
    "2025Q2": 29.5,
    "2025Q3": 30.0,
    "2025Q4": 30.5,
}

df["robinson_target_pct"] = df["quarter"].map(ROBINSON_TARGETS)

unmapped = df[df["robinson_target_pct"].isna()]["quarter"].unique()
if len(unmapped) > 0:
    print(f"  WARNING: {len(unmapped)} quarters not in target map: {unmapped}")

print(f"  Robinson targets mapped for {df['robinson_target_pct'].notna().sum():,} rows")

# ============================================================
# SECTION 5: Validate output schema
# benchmarking_app.py expects all of these columns
# ============================================================
REQUIRED_COLS = [
    "household_id", "snapshot_date", "state", "age_of_primary",
    "home_ownership", "household_size", "income_band",
    "agency_channel", "anchor_product", "policy_tier",
    "tenure_months", "outreach_contacts_12m", "claims_24m",
    "digital_engagement_score", "property_quote_started",
    "annual_premium_anchor", "projected_mphh_cltv",
    "propensity_score", "propensity_tier", "converted_mphh",
    "agent_id", "region", "quarter", "robinson_target_pct",
]

missing_cols = [c for c in REQUIRED_COLS if c not in df.columns]
if missing_cols:
    raise ValueError(f"Output is missing required columns: {missing_cols}")

print(f"\nSchema check: all {len(REQUIRED_COLS)} required columns present")

# ============================================================
# SECTION 6: Save output
# ============================================================
os.makedirs("data", exist_ok=True)
df.to_csv(OUTPUT_CSV, index=False)

print(f"\nSaved: {OUTPUT_CSV}")
print(f"  Rows    : {len(df):,}")
print(f"  Columns : {len(df.columns)}")
print(f"  Agents  : {df['agent_id'].nunique()}")
print(f"  Regions : {sorted(df['region'].unique().tolist())}")
print(f"  Quarters: {sorted(df['quarter'].unique().tolist())}")

# ============================================================
# SECTION 7: Quick sanity checks
# ============================================================
print("\nSanity checks:")

rate = df["converted_mphh"].mean()
print(f"  Conversion rate       : {rate:.3%}  (expected ~26%)")
assert 0.20 < rate < 0.35, f"Unexpected conversion rate: {rate:.3%}"

q_counts = df["quarter"].value_counts().sort_index()
assert len(q_counts) == 12, f"Expected 12 quarters, got {len(q_counts)}"
print(f"  Quarters              : {len(q_counts)}  (expected 12)")

agent_counts = df.groupby("agency_channel")["agent_id"].nunique()
print(f"  Agents per channel    :")
for ch, n in agent_counts.items():
    print(f"    {ch:<22}: {n}")

null_check = df[REQUIRED_COLS].isnull().sum()
null_cols  = null_check[null_check > 0]
if len(null_cols) > 0:
    print(f"  WARNING: Nulls found in: {null_cols.to_dict()}")
else:
    print(f"  Null values           : none")

print("\nAll checks passed. benchmarking_app.py is ready to run.")
print(f"Launch with: streamlit run benchmarking_app.py")
