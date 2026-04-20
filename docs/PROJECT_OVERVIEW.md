# MPHH Cross-Sell Propensity and Revenue Expansion

## Project Summary

This project analyzes which single-product AutoShield Insurance households are most likely to add a second product (becoming a Multiproduct Household, or MPHH) within 12 months. Using 150,000 synthetic agency households, the analysis identifies that property quote abandonment and proactive outreach contact frequency are the two strongest behavioral signals for cross-sell conversion. A Gradient Boosting model achieves AUC 0.69 on holdout data, with the top two propensity deciles capturing 36% of all conversions -- enabling highly targeted, low-waste outreach campaigns. The projected unconverted CLTV opportunity across the full dataset exceeds $280M.

---

## Business Problem

**Question:** Which of AutoShield's single-product households should receive cross-sell outreach, and in what priority order, to maximize Multiproduct Household growth and CLTV?

**Stakeholders:** Agency Operations leadership, Sales Strategy team, BI/Control partners, Product teams driving the Robertson Strategy.

The Robertson Strategy targets a specific high-value customer demographic known internally as the Robertsons. These are long-tenured households who have been with AutoShield Insurance for several years, hold multiple product policies across vehicles, motorcycle, boat, and home, are more likely to be married, pay their premiums reliably either in a single annual payment or through auto-pay, and demonstrate strong brand loyalty over time. The strategy is focused on deepening engagement with this demographic by expanding their product portfolio and ensuring they remain within the AutoShield household.

**Why it matters:** Multiproduct Households retain at significantly higher rates and generate 40-60% more lifetime premium than single-product customers. Each household that adds a property product represents not just incremental premium but a structural improvement in retention -- making MPHH growth a top strategic priority.

---

## Dataset

- **Source:** Synthetic (fully reproducible, seed=42)
- **Rows:** 150,000 (one row per household at a snapshot date)
- **Time Window:** January 2023 -- December 2025
- **Key Columns:** agency_channel, anchor_product, policy_tier, tenure_months, outreach_contacts_12m, property_quote_started, digital_engagement_score, claims_24m, annual_premium_anchor, projected_mphh_cltv
- **Target Variable:** `converted_mphh` (binary 0/1) -- household added a second product within 12 months
- **Conversion Rate:** ~26.1% (elevated to reflect an outreach-active population)
- **Full data dictionary:** See `data/data_dictionary.md`

---

## Methodology

**1. Data Generation**
Synthetic data was designed with realistic cross-sell dynamics. Outreach contact frequency and property quote initiation were explicitly wired as the two strongest behavioral signals, matching known industry patterns in P&C insurance cross-sell programs. All probabilities were drawn from a logistic function with calibrated coefficients to produce a ~26% conversion rate.

**2. EDA Approach**
Segmentation analysis across all categorical dimensions (channel, tier, product, ownership, tenure cohort). Behavioral signal impact analysis (outreach contacts, quote starts, digital engagement). Financial impact quantification by segment and ownership type.

**3. Modeling Approach**
Gradient Boosting Classifier (scikit-learn GradientBoostingClassifier) trained on 8 behavioral and demographic features. Leakage-prone columns (propensity_score, propensity_tier, projected_mphh_cltv) explicitly excluded from the feature set. 80/20 train/test split with stratification on the target variable.

**4. Financial Impact Framework**
CLTV = (anchor_premium + estimated_property_premium) x projected_tenure_years x 0.18 margin factor. Revenue simulator allows save rate and cost per contact adjustments to model campaign ROI across scenarios. Unconverted CLTV is the primary opportunity metric.

**5. Dashboard Design**
Six-tab Streamlit dashboard organized from overview to actionable recommendations. Persistent KPI header above all tabs. Sidebar filters drive all views. Financial simulator quantifies the business case interactively. Healthcare cross-industry tab demonstrates framework portability for non-insurance audiences.

---

## Key Findings

1. **Property quote abandonment is the single strongest conversion signal.** Households that started a property quote but did not complete it convert at 2.4x the baseline rate. This population (~28,000 households) represents the highest-ROI intervention target.

2. **Independent Agent channel drives the highest conversion rate at ~31%.** Despite lower volume than Direct Online, Independent Agent households convert at 6-8 percentage points above the overall average, reflecting the relationship-selling advantage of the agent channel.

3. **Outreach contact sweet spot is 1-3 contacts in 12 months.** Conversion rate climbs sharply from 0 contacts to 2-3 contacts, then flattens or declines above 4 contacts. This directly informs campaign contact cap design.

4. **Elite and Plus tier homeowners are the highest-value cross-sell segment.** Independent Agent / Elite / Auto households convert at over 38% with an average projected CLTV above $1,800 -- 1.5x the portfolio average.

5. **The 24-60 month tenure cohort is the volume-and-conversion sweet spot.** Established customers who have been with AutoShield 2-5 years have the trust and engagement profile most receptive to cross-sell, and they represent a large share of the unconverted opportunity.

6. **Top 20% of model-scored households capture 36% of all conversions. A campaign targeting only the top two propensity deciles achieves 2.05x the conversion rate of untargeted outreach, at a fraction of the contact cost.

7. **Total unconverted MPHH CLTV opportunity exceeds $280M across the dataset.** Even at a conservative 10% save rate, a targeted outreach program generates an estimated $28M in net CLTV -- well above any realistic campaign cost.

---

## Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3.11 |
| Data Generation | NumPy, Pandas |
| Machine Learning | scikit-learn (GradientBoostingClassifier) |
| Visualization | Plotly |
| Dashboard | Streamlit 1.35+ |
| SQL Dialect | ANSI SQL (PostgreSQL / Snowflake) |
| Version Control | Git / GitHub |

---

## File Structure

```
mphh_portfolio/
  app.py                          # Streamlit dashboard (single file)
  requirements.txt                # Python dependencies
  .streamlit/
    config.toml                   # Streamlit theme configuration
  data/
    mphh_crosssell.csv            # 150,000-row synthetic dataset
    mphh_crosssell_metadata.json  # Dataset metadata and generation params
    data_dictionary.md            # Column reference with leakage notes
  scripts/
    01_generate_data.py           # Reproducible data generation script
  sql/
    mphh_crosssell_analysis.sql   # 12 analysis queries (5 sections)
  docs/
    PROJECT_OVERVIEW.md           # This file
    INTERVIEW_PREP.md             # Interview preparation guide
```

---

## How to Run

```bash
# 1. Clone or download the project
git clone https://github.com/yourusername/mphh-portfolio.git
cd mphh-portfolio

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Regenerate the dataset (optional -- CSV is included)
python scripts/01_generate_data.py

# 5. Launch the dashboard
streamlit run app.py
```

The dashboard opens at `http://localhost:8501`.

---

## How to Deploy (Streamlit Community Cloud)

1. Push the repository to GitHub (ensure `data/mphh_crosssell.csv` is committed).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repository, branch `main`, and main file `app.py`.
4. Click **Deploy**. The app will be live at `https://share.streamlit.io/yourusername/mphh-portfolio`.
5. No secrets or environment variables required -- the app reads from the local `data/` directory.
