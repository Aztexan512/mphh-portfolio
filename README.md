# 🏠 MPHH Cross-Sell Propensity and Revenue Expansion

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-GradientBoosting-F7931E?logo=scikit-learn&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-PostgreSQL%20%2F%20Snowflake-4169E1?logo=postgresql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

Using 150,000 synthetic agency households across a 3-year window (2023–2025), this project identifies **$280M** in unconverted Multiproduct Household (MPHH) revenue and builds a Gradient Boosting model (AUC 0.69) that concentrates 36% of all conversions into the top two propensity deciles.

---

## 📋 Table of Contents

- [Project Background](#-project-background)
- [Executive Summary](#-executive-summary)
- [Insights Deep Dive](#-insights-deep-dive)
- [Recommendations](#-recommendations)
- [Data Structure](#️-data-structure)
- [Setup](#️-setup)
- [Live Dashboards](#-live-dashboards)
- [File Structure](#-file-structure)
- [Assumptions and Caveats](#️-assumptions-and-caveats)
- [Author](#-author)

---

## 🏢 Project Background

AutoShield Insurance is a mid-size personal lines carrier operating across 10 states through four distribution channels: Independent Agent, Direct Online, Captive Agent, and Employer Sponsored. Despite strong retention among long-tenured customers, a large share of AutoShield's book remains single-product households, representing a significant untapped revenue opportunity.

The Robertson Strategy is AutoShield's internal initiative to deepen engagement with its highest-value customer demographic: long-tenured households holding multiple product policies across auto, motorcycle, boat, and home. These customers pay reliably, demonstrate strong brand loyalty, and are the most likely candidates to expand their policy portfolio. The strategy targets converting single-product households in this demographic into Multiproduct Households (MPHH) through structured outreach campaigns.

The central business question is which single-product households should receive cross-sell outreach, and in what priority order, to maximize MPHH growth and customer lifetime value. Multiproduct Households retain at significantly higher rates and generate 40–60% more lifetime premium than single-product customers. Each household that adds a property product represents not just incremental premium but a structural improvement in retention, making MPHH growth a top strategic priority for AutoShield leadership.

---

## 📊 Executive Summary

- Property quote abandonment is the single strongest conversion signal. Households that started a property quote but did not complete it convert at **2.4x the baseline rate**, representing the highest-ROI intervention target across the portfolio.
- The Independent Agent channel drives the highest conversion rate at **~31%**, outperforming the overall average by 6–8 percentage points and reflecting the relationship-selling advantage of the agent channel.
- Outreach contact frequency peaks at 1–3 contacts per 12-month window. Conversion rate climbs sharply from 0 to 2–3 contacts, then flattens or declines above 4, directly informing campaign contact cap design.
- Elite and Plus tier homeowners are the highest-value cross-sell segment, with Independent Agent / Elite / Auto households converting at **over 38%** and an average projected CLTV above **$1,800**, approximately 1.5x the portfolio average.
- The 24–60 month tenure cohort is the volume-and-conversion sweet spot. Established customers 2–5 years into their relationship with AutoShield have the trust and engagement profile most receptive to cross-sell.
- The top 20% of model-scored households capture **36% of all conversions**, achieving 2.05x the conversion rate of untargeted outreach at a fraction of the contact cost. Total unconverted MPHH CLTV opportunity exceeds **$280M**.

---

## 🔍 Insights Deep Dive

### 1. Property Quote Abandonment Drives Highest Conversion Lift

Households that initiated a property quote but did not complete it convert at **2.4x the baseline rate**, making this behavioral signal the single most predictive feature in the model. This population of approximately 28,000 households represents the clearest self-identified demand signal in the book.

<!-- SCREENSHOT REQUIRED: Cross-Sell Drivers tab -- quote abandonment chart showing conversion rate lift -->
![Quote Abandonment Conversion Lift](screenshots/cross_sell_drivers.png)

### 2. Independent Agent Channel Outperforms All Others

The Independent Agent channel converts at **~31%**, 6–8 percentage points above the portfolio average, reflecting the trust and consultation dynamic inherent in agent-led relationships. Captive Agent follows, while Direct Online trails significantly, highlighting channel as a critical stratification variable for campaign targeting.

<!-- SCREENSHOT REQUIRED: Overview tab -- channel conversion rate breakdown chart -->
![Channel Conversion Rate](screenshots/overview.png)

### 3. Propensity Model Concentrates Conversions into Top Deciles

The Gradient Boosting model achieves **AUC 0.69** on holdout data, with the top two propensity deciles capturing **36% of all conversions** and delivering a 2.05x lift over random targeting. The lift chart confirms the model's ability to rank-order households by conversion likelihood, enabling precise, low-waste outreach.

<!-- SCREENSHOT REQUIRED: Model + Risk tab -- propensity decile lift chart and score distribution -->
![Model Lift Chart](screenshots/model_risk.png)

### 4. Financial Simulator Quantifies Campaign ROI

The financial impact tab allows campaign planners to model outreach scenarios against the **$280M** unconverted CLTV opportunity. At a conservative 10% save rate on targeted households, a campaign focused on the top two deciles generates an estimated **$28M** in net CLTV, well above any realistic contact cost.

<!-- SCREENSHOT REQUIRED: Financial Impact tab -- CLTV simulator with results card and scenario bar chart -->
![Financial Impact Simulator](screenshots/financial_impact.png)

---

## 💡 Recommendations

### Immediate Actions (0–30 Days)

**Launch a Quote Abandonment Re-Engagement Campaign**
Approximately 28,000 households with incomplete property quotes convert at 2.4x the baseline rate. A targeted outreach sequence for this segment requires no model scoring and can begin immediately.

**Apply a 3-Contact Cap to All Outreach Campaigns**
Conversion rate peaks at 2–3 contacts and flattens or declines above 4. Implementing a contact cap reduces wasted outreach and improves the household experience at negligible cost.

### Short-Term Actions (30–90 Days)

**Deploy the Propensity Model to Rank the Full Single-Product Book**
The top two propensity deciles capture 36% of all conversions at 2.05x the untargeted rate. Routing campaign lists through the model score before each outreach cycle maximizes conversion per dollar spent.

**Prioritize Elite and Plus Tier Independent Agent Households**
This sub-segment converts at over 38% with an average CLTV above $1,800. Dedicating Independent Agent capacity to this cohort generates the highest per-contact revenue return in the book.

### Strategic Investments (90+ Days)

**Build a Robertson Strategy Performance Dashboard for Executive Reporting**
The Robertson Strategy is currently behind target in 6 of 8 tracked quarters. A structured reporting cadence with quarterly MPHH rate vs. target, agent leaderboard, and YoY growth visibility enables leadership to diagnose underperformance and reallocate resources.

**Develop a Tenure-Segmented Outreach Playbook for the 24–60 Month Cohort**
The 2–5 year tenure cohort represents the volume-and-conversion sweet spot across the book. A dedicated playbook with channel-specific messaging for this cohort, informed by behavioral signals and propensity scores, provides a scalable framework for MPHH growth beyond the immediate campaign cycle.

---

## 🗂️ Data Structure

All data in this project is synthetic. The analysis-ready dataset (`data/mphh_crosssell.csv`) was generated from source tables that reflect how this data actually lives in a real insurance system.

Dataset: 150,000 rows | Seed: 42 | Time window: January 2023 to December 2025

| Column | Type | Description |
|---|---|---|
| household_id | string | Unique household identifier |
| snapshot_date | date | Date of household snapshot |
| tenure_months | integer | Months since first policy effective date |
| channel | string | Distribution channel (Independent Agent, Direct Online, Captive Agent, Employer Sponsored) |
| tier | string | Customer tier (Elite, Plus, Standard) |
| primary_product | string | Current primary product (Auto, Motorcycle, Boat) |
| outreach_contacts_12m | integer | Number of outreach contacts in prior 12 months |
| quote_abandoned | boolean | Whether household started but did not complete a property quote |
| propensity_score | float | Model-assigned conversion probability (0–1) |
| projected_cltv | float | Estimated customer lifetime value if converted |
| converted | boolean | Target variable: converted to MPHH within 12 months |

Leakage-prone columns (excluded from model training):

| Column | Risk | Reason |
|---|---|---|
| projected_cltv | HIGH | Computed from conversion outcome; including it would leak the target |
| propensity_score | HIGH | Is the model output; cannot be used as a training feature |

Source table schema: See [data/schema/erd.md](data/schema/erd.md) for the entity-relationship diagram and [data/schema/table_definitions.md](data/schema/table_definitions.md) for source table grain and join logic.

---

## ⚙️ Setup

```bash
# 1. Clone the repo
git clone https://github.com/Aztexan512/Multiproduct-Household-Propensity-Model.git
cd Multiproduct-Household-Propensity-Model

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the primary dashboard
streamlit run app.py

# 4. Run the benchmarking dashboard (separate terminal)
streamlit run benchmarking_app.py
```

> Note: The analysis-ready dataset is committed to this repo at `data/mphh_crosssell.csv`. No data generation step is required to run the dashboard or notebook.

---

## 🚀 Live Dashboards

| Dashboard | Link |
|---|---|
| MPHH Cross-Sell Propensity Explorer | [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://qf7zyjwemc2duqnbkhbhgh.streamlit.app/) |
| MPHH Benchmarking & Reporting Tracker | [![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://benchmarkingapppy-vjccagmtcwt2fdtbrzrjtx.streamlit.app/) |

---

## 📁 File Structure

```
mphh_portfolio/
|-- README.md                          # This file
|-- app.py                             # Cross-sell propensity dashboard
|-- benchmarking_app.py                # Benchmarking & reporting dashboard
|-- requirements.txt                   # Python dependencies
|-- portfolio_page.html                # Standalone shareable project page
|-- .streamlit/
|   |-- config.toml                    # Dashboard theme configuration
|-- data/
|   |-- mphh_crosssell.csv             # Analysis-ready dataset (150,000 rows)
|   |-- mphh_crosssell_metadata.json   # Generation parameters and dataset summary
|   |-- mphh_benchmarking.csv          # Benchmarking dataset (adds agent_id, region, quarter)
|   |-- data_dictionary.md             # Column reference with leakage documentation
|   |-- schema/
|       |-- erd.md                     # Entity-relationship diagram (Mermaid)
|       |-- table_definitions.md       # Source table grain and join logic
|-- sql/
|   |-- mphh_crosssell_analysis.sql    # 12 queries: EDA, segmentation, model support
|   |-- mphh_benchmarking_analysis.sql # 19 queries: Robertson tracker, agent, YoY, cohort
|-- docs/
|   |-- PROJECT_OVERVIEW.md            # Methodology, key findings, how to run
|-- screenshots/                       # Dashboard screenshots for this README
```

---

## ⚠️ Assumptions and Caveats

**Synthetic data:** All data in this project is synthetic. The dataset was generated using NumPy with seed 42 for reproducibility. It is designed to produce realistic analytical patterns but does not represent any real company, customer, or transaction.

**Modeling assumptions:**
- CLTV definition: annual premium multiplied by projected retention months, discounted at 8%
- Leakage prevention: `projected_cltv` and `propensity_score` excluded from model training
- Target variable: `converted` flag represents MPHH conversion within a 12-month forward window
- Model algorithm: GradientBoostingClassifier (scikit-learn) with default hyperparameters tuned via cross-validation

**Business assumptions:**
- Outreach cost per contact: $150 default in financial simulator
- Save rate baseline: 10% conservative estimate applied to top-decile opportunity sizing
- MPHH conversion rate baseline: ~26.1%, computed across the full 150,000-row dataset
- Channel performance: Independent Agent conversion advantage reflects relationship-selling dynamics, not volume

---

## 👤 Author

Luciano Casillas

Independent Analytics Consultant | Austin, TX

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://linkedin.com/in/luciano-casillas)
[![GitHub](https://img.shields.io/badge/GitHub-Aztexan512-lightgrey)](https://github.com/Aztexan512)

luciano.casillasjr@outlook.com
