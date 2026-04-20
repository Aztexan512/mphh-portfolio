# MPHH Cross-Sell Propensity and Revenue Expansion

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-GradientBoosting-F7931E?logo=scikit-learn&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL%20%2F%20Snowflake-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Live Dashboards

| Dashboard | Description |
|---|---|
| [MPHH Cross-Sell Propensity](https://your-username.streamlit.app/mphh-propensity) | Campaign targeting: which households to outreach, why, and what it's worth |
| [MPHH Benchmarking & Reporting](https://your-username.streamlit.app/mphh-benchmarking) | Executive reporting: Robinson Strategy tracker, agent leaderboard, YoY growth |

> Replace placeholder URLs with your deployed Streamlit Community Cloud links.

---

## Project Summary

This project analyzes which single-product Progressive Insurance households are most likely to add a second product (becoming a Multiproduct Household, or MPHH) within 12 months. Using 150,000 synthetic agency households across a 3-year window (2023–2025), the analysis identifies that **property quote abandonment** and **proactive outreach contact frequency** are the two strongest behavioral signals for cross-sell conversion.

A Gradient Boosting model achieves AUC 0.69 on holdout data, with the top two propensity deciles capturing 36% of all conversions — enabling highly targeted, low-waste outreach campaigns. The projected unconverted CLTV opportunity across the full dataset exceeds **$280M**.

---

## Business Problem

**Question:** Which of Progressive's single-product households should receive cross-sell outreach, and in what priority order, to maximize Multiproduct Household growth and CLTV?

**Stakeholders:** Agency Operations leadership, Sales Strategy team, BI/Control partners, Product teams driving the Robinson Strategy.

**Why it matters:** Multiproduct Households retain at significantly higher rates and generate 40–60% more lifetime premium than single-product customers. Each household that adds a property product represents not just incremental premium but a structural improvement in retention — making MPHH growth a top strategic priority.

---

## Key Findings

1. **Property quote abandonment is the single strongest conversion signal.** Households that started a property quote but did not complete it convert at 2.4x the baseline rate. This population (~28,000 households) represents the highest-ROI intervention target.

2. **Independent Agent channel drives the highest conversion rate at ~31%.** Despite lower volume than Direct Online, Independent Agent households convert 6–8 percentage points above the overall average, reflecting the relationship-selling advantage of the agent channel.

3. **Outreach contact sweet spot is 1–3 contacts in 12 months.** Conversion rate climbs sharply from 0 contacts to 2–3 contacts, then flattens or declines above 4. This directly informs campaign contact cap design.

4. **Elite and Plus tier homeowners are the highest-value cross-sell segment.** Independent Agent / Elite / Auto households convert at over 38% with an average projected CLTV above $1,800 — 1.5x the portfolio average.

5. **The 24–60 month tenure cohort is the volume-and-conversion sweet spot.** Established customers who have been with Progressive 2–5 years have the trust and engagement profile most receptive to cross-sell.

6. **Top 20% of model-scored households capture 36% of all conversions.** A campaign targeting only the top two propensity deciles achieves 2.05x the conversion rate of untargeted outreach, at a fraction of the contact cost.

7. **Total unconverted MPHH CLTV opportunity exceeds $280M.** Even at a conservative 10% save rate, a targeted outreach program generates an estimated $28M in net CLTV — well above any realistic campaign cost.

---

## Dashboards

### `app.py` — MPHH Cross-Sell Propensity Dashboard
Six tabs designed for campaign teams and analysts:
- **Overview** — conversion rate summary, segment breakdown
- **Cross-Sell Drivers** — outreach contact impact, quote abandonment analysis, behavioral signals
- **Model + Risk** — propensity decile lift chart, score distribution, intervention candidates
- **Financial Impact** — CLTV opportunity by segment, revenue simulator
- **Healthcare Application** — framework portability demonstration
- **Recommendations** — prioritized action items with supporting evidence

### `benchmarking_app.py` — MPHH Benchmarking & Reporting Dashboard
Six tabs designed for executive and operations reporting:
- **Robinson Strategy Tracker** — quarterly MPHH rate vs. target (12 quarters, 2023–2025)
- **YoY Growth** — year-over-year rate and delta charts across all 3 years
- **Cohort Retention** — acquisition cohort comparison (2023 Early / 2024 Mid / 2025 Recent)
- **Agent Leaderboard** — ranked agent performance across 450 agents and 4 channels
- **State Performance** — conversion rate and CLTV heatmap across 10 states
- **Pipeline Health** — propensity tier funnel, outreach gap, intervention queue

---

## Tech Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Data Generation | NumPy, Pandas |
| Machine Learning | scikit-learn (GradientBoostingClassifier) |
| Visualization | Plotly |
| Dashboard | Streamlit 1.35+ |
| SQL Dialect | ANSI SQL (PostgreSQL / Snowflake compatible) |
| Version Control | Git / GitHub |

---

## File Structure

```
mphh_portfolio/
  app.py                              # Cross-sell propensity dashboard
  benchmarking_app.py                 # Benchmarking & reporting dashboard
  requirements.txt                    # Python dependencies
  .streamlit/
    config.toml                       # Streamlit theme configuration
  data/
    mphh_crosssell.csv                # 150,000-row synthetic dataset (2023–2025)
    mphh_crosssell_metadata.json      # Dataset metadata and generation params
    mphh_benchmarking.csv             # Benchmarking dataset (adds agent_id, region, quarter)
    data_dictionary.md                # Column reference with leakage notes
  scripts/
    01_generate_data.py               # Generates mphh_crosssell.csv
    02_generate_benchmarking_data.py  # Generates mphh_benchmarking.csv
  sql/
    mphh_crosssell_analysis.sql       # 12 queries: EDA, segmentation, model support
    mphh_benchmarking_analysis.sql    # 19 queries: Robinson tracker, agent, YoY, cohort
  docs/
    PROJECT_OVERVIEW.md               # Full project narrative
    INTERVIEW_PREP.md                 # Interview preparation guide
```

---

## Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/your-username/mphh-portfolio.git
cd mphh-portfolio

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate the datasets (CSVs are included; run only if regenerating)
python scripts/01_generate_data.py
python scripts/02_generate_benchmarking_data.py

# 5. Launch the dashboards (run in separate terminals)
streamlit run app.py
streamlit run benchmarking_app.py
```

Both dashboards open at `http://localhost:8501` (second gets `http://localhost:8502`).

---

## Deploy to Streamlit Community Cloud

1. Push the repository to GitHub (ensure `data/*.csv` files are committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repository, branch `main`.
4. For the propensity dashboard, set main file to `app.py`. Deploy again with `benchmarking_app.py` for the second dashboard.
5. No secrets or environment variables required.

---

## Dataset

- **Source:** Synthetic (fully reproducible, seed=42)
- **Rows:** 150,000 (one row per household at a snapshot date)
- **Time Window:** January 2023 – December 2025
- **Conversion Rate:** ~26.1%
- **Full data dictionary:** `data/data_dictionary.md`
