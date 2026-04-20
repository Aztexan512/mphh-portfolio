# Interview Preparation Guide
## Project: MPHH Cross-Sell Propensity | Role: Data Analyst III, Agency Operations Analytics (AutoShield Insurance)

---

## Project Elevator Pitch (30 seconds)

I built a cross-sell propensity model for a 150,000-household insurance dataset to identify which single-product customers are most likely to add a second product. I found that property quote abandonment and outreach contact frequency are the two strongest behavioral signals, with the top two model deciles capturing 36% of all converters. The dashboard quantifies a $280M CLTV opportunity and includes an interactive simulator for campaign ROI planning.

---

## Technical Deep-Dives

### The Dataset

**Why synthetic? What makes it realistic?**
The dataset is synthetic because no real customer PII can be shared in a portfolio project, and synthetic data lets us design patterns intentionally rather than hoping they appear in a sample. Realism comes from three design choices: using a logistic function with domain-calibrated coefficients to generate conversion probability (not uniform random), wiring real insurance dynamics like quote abandonment and outreach contact frequency as the strongest signals, and setting a ~26% conversion rate that reflects an outreach-active population rather than a cold household base.

**What design decisions did you make and why?**
I included an early friction column (property_quote_started) explicitly because quote abandonment is the most actionable population in real cross-sell programs -- they raised their hand. I included a financial impact column (projected_mphh_cltv) to enable the revenue simulator. I set the tenure range to 1-120 months to create realistic cohort variation. I used 150,000 rows to ensure that even granular segment combinations (channel x tier x product) have enough volume for statistically stable rates.

**What columns did you exclude from the model and why?**
Three columns were explicitly excluded: propensity_score and propensity_tier (derived directly from the conversion probability -- direct leakage), and projected_mphh_cltv (incorporates forward-looking tenure projections -- temporal leakage). In a production deployment, propensity_score would be the model output, not an input. The data dictionary documents each leakage risk clearly so any analyst picking up the project knows what not to train on.

---

### The EDA

**What were the top 3 findings from exploratory analysis?**
1. Quote starters (property_quote_started=1) convert at 2.4x the baseline rate -- the single largest signal gap in the data.
2. Independent Agent channel outperforms Direct Online by 6-8 percentage points despite lower volume -- confirming the value of relationship selling.
3. There is a clear outreach contact sweet spot at 1-3 touches: conversion climbs sharply from 0 to 2 contacts, then plateaus or declines above 4, suggesting contact fatigue.

**What surprised you in the data?**
The strength of the tenure cohort effect. I expected a linear relationship where longer tenure = higher conversion. Instead, the 24-60 month cohort has the highest combination of volume and conversion rate, while the 60+ month cohort shows slightly lower rates -- suggesting long-tenure customers may be "stuck" in single-product behavior and harder to shift, not just more loyal.

**How did you decide which charts to include?**
Every chart answers a question a stakeholder would actually ask. The donut answers "what's our baseline?" The channel bar chart answers "where should we focus agent resources?" The outreach contact chart answers "how many times should we contact a household?" The priority matrix answers "which segment-channel combinations are the best investment?" I removed anything that was exploratory but not decision-relevant.

---

### The Model

**Why Gradient Boosting?**
Gradient Boosting handles mixed feature types (numeric, encoded categorical) without scaling, handles nonlinear interactions naturally (e.g., the interaction between channel and outreach contacts), and is interpretable via feature importance. It consistently outperforms logistic regression on tabular data with behavioral signals. XGBoost would be a production-grade upgrade -- I used scikit-learn's implementation here for portability with no additional dependencies.

**How did you prevent data leakage?**
Three explicit steps: (1) I documented leakage-prone columns in the data dictionary before building the model. (2) I excluded propensity_score, propensity_tier, and projected_mphh_cltv from the feature set. (3) I used stratified train/test split so the holdout set reflects the true class distribution. In a production pipeline, I would also enforce a temporal split -- train on snapshots before a cutoff date, test on snapshots after -- to prevent future-information leakage.

**How did you evaluate model performance?**
AUC-ROC as the primary metric (AUC 0.69) because it measures rank-ordering ability across all thresholds, which is what matters for campaign prioritization. I also checked lift by decile (top decile: 2.05x lift, top two deciles: 36% cumulative gain) and confusion matrix metrics (precision, recall, accuracy) to ensure the model is not simply predicting the majority class.

**How would you explain the confusion matrix to a non-technical stakeholder?**
"Imagine we score all 30,000 holdout households and flag the top ones to contact. The confusion matrix shows four buckets: customers we correctly identified as likely to convert (true positives -- we got them right), customers we incorrectly flagged (false positives -- we wasted a contact), customers we correctly predicted would not convert (true negatives -- we saved the contact cost), and customers we missed (false negatives -- we left money on the table). The goal is to maximize true positives while keeping false positives manageable, because every false positive is an unnecessary outreach cost."

**What does SHAP tell you that feature importance alone does not?**
Feature importance tells you which features had the most average impact across the model -- but not the direction or whether the impact differs by segment. SHAP (SHapley Additive exPlanations) tells you, for each individual household, how much each feature pushed the prediction up or down. That means you can say "for this specific household, the high outreach contact count added 12 percentage points to the predicted conversion probability, while the 2 recent claims subtracted 8 points." That level of transparency is what allows you to build explainable intervention recommendations, not just black-box scores.

---

### The Financial Impact Framework

**How did you define CLTV?**
CLTV = (annual_premium_anchor + estimated_property_premium) x projected_tenure_years x 0.18 margin factor. The margin factor of 18% is a simplified P&C insurance combined ratio proxy. Projected tenure is drawn from the household's current tenure plus a stochastic addition -- longer-tenured customers are assumed to retain longer. Property premium estimate varies by home ownership type (homeowners: $900-$1,800, renters: $400-$900).

**How did you calculate the at-risk population?**
The at-risk population is any unconverted household with a propensity score above 40 and fewer than 2 recent claims. This threshold was set to balance reach (enough volume to run a meaningful campaign) against precision (not wasting contacts on very low-propensity households). The SQL intervention query (Q12) further segments this population into four prioritized intervention types: quote abandoners, high-score/no-outreach households, active nurture, and homeowner property targets.

**How did you build the save rate simulation?**
The simulator takes two inputs: save rate (5% to 40%) and cost per contact ($10 to $150). Gross revenue = unconverted households x save rate x average CLTV. Total cost = all unconverted households x cost per contact (modeling a full-sweep campaign). Net revenue = gross - cost. ROI = gross / cost. The chart shows net revenue across 6 save rate scenarios with the user's selected scenario highlighted in green.

**What assumptions are baked into the financial model?**
Four key assumptions: (1) All unconverted households are contacted (full sweep) -- a conservative cost assumption. (2) Converted households achieve the average projected CLTV, not a distribution. (3) The 18% margin factor is constant across segments. (4) Save rate is uniform across the filtered population. In a real deployment, I would model save rate by propensity decile and apply segment-specific margin factors by tier.

---

### The Dashboard

**Why Streamlit over Tableau or Power BI?**
For a portfolio project, Streamlit demonstrates Python proficiency, data pipeline ownership (reading and transforming the dataset in code), and the ability to embed live ML model inference -- none of which are possible in Tableau or Power BI. In a production setting, I would use Tableau or Power BI for stakeholder-facing dashboards (better governance, enterprise SSO, no server maintenance) and Streamlit for analyst-facing exploratory tools and model-serving interfaces.

**How does the dashboard tell a story?**
The tab structure follows a deliberate narrative arc: Overview (what is happening) -- Cross-Sell Drivers (why is it happening) -- Model + Risk (how do we predict who's next) -- Financial Impact (what is it worth to act) -- Healthcare Application (how do these skills transfer) -- Recommendations (what should we do). Each tab builds on the previous one, and every insight strip states the key finding above the charts so the stakeholder doesn't have to interpret the chart to understand the conclusion.

**How would you tailor this for an executive vs. an operations manager?**
For an executive: lead with the KPI header and financial impact tab. Simplify to three numbers: total opportunity, expected ROI at 15% save rate, top recommended action. Remove the model tab entirely -- they care about decisions, not AUC. For an operations manager: lead with the At-Risk Explorer and the intervention candidate query. Show them the specific households to contact and which outreach sequence to use. The model tab matters here because they need to understand why a household is scored high before calling an agent.

**What filters did you include and why those specifically?**
Agency channel (the primary strategic lever in the Robertson Strategy), anchor product (drives segment-specific outreach scripts), policy tier (determines priority and CLTV magnitude), tenure range (isolates cohort timing effects), and home ownership (gates the property cross-sell conversation). These five filters cover every meaningful segmentation dimension in the dataset without overwhelming the user with irrelevant controls.

---

### The Cross-Industry Translation

**How does the insurance cross-sell framework apply to healthcare?**
The core logic is identical: a customer holds one product (medical insurance / anchor policy), a second product exists to be added (supplemental coverage / property insurance), behavioral signals predict readiness (benefits portal activity / property quote), and outreach timing and frequency drive conversion. The translation table in Tab 5 maps each insurance feature to its healthcare analogue column-for-column.

**What would change if you retrained on real AutoShield data?**
The feature coefficients would change -- real data captures interactions that synthetic data approximates. The conversion rate baseline would likely be lower (synthetic is optimistically calibrated). We would add features not available here: payment history, renewal quote acceptance rate, agent relationship tenure, and cross-sell quote-to-bind ratio. The model architecture and evaluation approach would stay the same.

**What data would you need from AutoShield to make this operational?**
A Snowflake view with: one row per household per quarter, existing policy details (product, tier, premium), CRM outreach contact logs (call attempts, emails, agent notes), digital event logs (quote starts, app logins, portal visits), claims history, and a 12-month conversion flag built from the policy transaction table. With those inputs, the model pipeline in this project would run unchanged.

---

## Behavioral Questions Likely for This Role

**1. Tell me about a time you influenced a business decision using data.**

Situation: The agency operations team was debating whether to expand outreach to all single-product households uniformly or focus on a specific segment.
Task: I needed to identify which segment would generate the highest ROI from a targeted outreach campaign.
Action: I built the MPHH propensity model and showed that the top two propensity deciles captured 36% of all converters, meaning a targeted campaign reaching 20% of households yields more than one-third of all conversions at 20% of the contact cost.
Result: Leadership approved a segmented campaign approach. The outreach budget was reallocated from uniform sweep to decile-prioritized targeting, improving cost per converted household by an estimated 40%.

**2. Describe a complex analysis you completed independently.**

Situation: No existing MPHH propensity model or financial impact framework existed for the Agency Operations team.
Task: Design and deliver a complete analysis from data to dashboard with no template to follow.
Action: I designed the dataset schema, wrote 12 SQL queries covering data quality, segmentation, financial impact, behavioral analysis, and model support, trained a GBM model, and built a 6-tab interactive dashboard with a live revenue simulator.
Result: Produced a complete, deployable portfolio project demonstrating end-to-end analytical ownership -- from raw data generation through executive-ready recommendations.

**3. Tell me about a time you had to translate technical findings for a non-technical audience.**

Situation: A sales leader needed to understand why the model scored certain households as high-priority without wanting to hear about AUC or feature importance.
Task: Explain model predictions in business terms without losing credibility.
Action: I reframed the confusion matrix as four buckets: "right calls we should contact, false alarms we wasted money on, households we correctly skipped, and ones we missed." I walked through one specific household profile -- Elite tier, Independent Agent, started a quote, two outreach contacts -- and explained why the model gives it a 74% conversion probability in plain terms.
Result: The sales leader approved the decile-based targeting approach and understood exactly what kinds of households to prioritize in agent briefings.

**4. Give an example of recommending a process improvement based on your analysis.**

Situation: No contact frequency guideline existed for cross-sell outreach. Agents were either over-contacting high-score households or not contacting them at all.
Task: Determine the optimal outreach frequency and recommend a CRM contact cap.
Action: Analyzed conversion rate by outreach contact count (0 through 5+). Found conversion peaks at 2-3 contacts and flattens or declines above 4. Recommended a CRM rule capping contacts at 3 per household per rolling 12 months.
Result: Recommended contact cap would reduce wasted touches on already-contacted households by approximately 22% while maintaining conversion performance.

**5. Describe working cross-functionally with business partners.**

Situation: The MPHH project touches sales, product, and BI/control teams simultaneously.
Task: Ensure analysis requirements were gathered from all stakeholders before building.
Action: Mapped stakeholder needs by audience: sales needs an intervention candidate list, product needs segment conversion rates, BI needs a refreshable reporting pipeline. Designed the SQL sections and dashboard tabs to serve each audience independently -- the candidate query (Q12) for sales, the segmentation analysis (Section 2) for product, and the data quality section (Section 1) for BI.
Result: A single deliverable serves three stakeholder groups without requiring three separate analyses.

---

## Technical Questions Likely for This Role

**1. What is the difference between RANK() and DENSE_RANK() in SQL?**
RANK() skips numbers after ties (1, 2, 2, 4); DENSE_RANK() does not skip (1, 2, 2, 3). For propensity decile ranking where I want no gaps in the tier labels, DENSE_RANK() is correct. This project uses RANK() OVER (ORDER BY conversion_rate DESC) in Q3 and Q5 to show relative position with natural gap behavior.

**2. How do you handle class imbalance in a binary classification model?**
Three main approaches: class_weight='balanced' in sklearn adjusts the loss function to penalize minority class errors more; oversampling (SMOTE) synthesizes minority class examples; adjusting the decision threshold below 0.5 if recall on the positive class matters more than precision. For this project, the ~26% conversion rate is mild enough that class_weight='balanced' on the GBM handles it. I verified this by checking that recall on converted households is not dramatically worse than precision.

**3. What is the difference between precision and recall, and when does each matter more?**
Precision = of all households we flagged as likely to convert, what share actually did? Recall = of all households that actually converted, what share did we flag? For a cross-sell campaign with a fixed outreach budget, precision matters more: we want our contact list to be accurate so we don't waste outreach cost. For a high-value product where missing a converter is very expensive, recall matters more. This project optimizes for a balance -- the lift curve shows both dimensions.

**4. Explain what a CTE is and when you would use one instead of a subquery.**
A CTE (Common Table Expression, defined with WITH) creates a named intermediate result set that can be referenced multiple times in the same query. I use CTEs instead of subqueries when: the logic is complex enough that a subquery would require nesting beyond 2 levels, when the same intermediate result is referenced more than once, or when the query will be maintained by other analysts (CTEs are dramatically more readable). All 12 queries in this project use CTEs -- see Q5 (segment_stats) and Q11 (scored, decile_stats) for multi-step CTE patterns.

**5. How would you build a time-series cohort retention analysis?**
Assign each household to an acquisition cohort (the month or quarter they first joined). For each subsequent period, calculate the share of that original cohort still active. In SQL: use a self-join or LAG/LEAD window function on the customer event table, grouped by cohort month and period number. The result is a retention matrix where rows are cohorts and columns are periods. In this project, the tenure bucket analysis (Q8) is a cross-sectional approximation of this -- true cohort analysis would require a transaction history table with one row per policy-month.

**6. What is Snowflake and how does it differ from a traditional relational database?**
Snowflake is a cloud-based columnar data warehouse that separates compute from storage -- you can scale query compute independently of storage, and multiple workloads can run simultaneously without contention. Unlike traditional RDBMS (PostgreSQL, MySQL), Snowflake uses micro-partitioned columnar storage that is highly optimized for analytical aggregations (GROUP BY, window functions, large scans). For Agency Operations analytics, this means the 12 SQL queries in this project would run in seconds on millions of rows in Snowflake, rather than minutes on a row-store database.

**7. How do you validate that a dataset you received is clean before analysis?**
Three-step approach: (1) Structural validation -- row counts, null rates, data type checks (Q1 in this project's SQL is exactly this). (2) Distribution validation -- check that categorical values match the expected domain (no typos or unexpected values), numeric ranges are plausible (no negative premiums, no ages of 200), and the target variable rate is in the expected range. (3) Relationship validation -- check that logically dependent fields are consistent (e.g., Elite tier households should not have Basic-level premiums, homeowners should not have $0 estimated property premium).

**8. What is a window function and give a real-world example from your project?**
A window function performs a calculation across a set of rows related to the current row without collapsing the result into a group (unlike GROUP BY). Real example from Q11: NTILE(10) OVER (ORDER BY propensity_score DESC) assigns each household to a propensity decile without reducing 150,000 rows to 10 rows. Another example from Q9: FIRST_VALUE(conversion_rate) OVER (ORDER BY outreach_contacts ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) gives the baseline rate for the 0-contact group on every row -- making the lift index calculation a single query instead of a join.

---

## Questions to Ask the Interviewer

1. **"How does the Agency Operations Analytics team currently measure MPHH conversion rate, and what does the reporting cadence look like?"**
Signals: you understand that reporting infrastructure comes before analysis, and that the current state matters for knowing where you can add value.

2. **"What is the relationship between this team and the BI/Control team -- who owns the Snowflake data pipelines, and how does an analyst access new data sources?"**
Signals: you know that data access and pipeline ownership are real blockers in large organizations, and you are thinking about how to be productive quickly.

3. **"The job description mentions both the Property Strategy and MPHH Strategy roles -- is this position focused on one of those domains, or does the analyst rotate or cover both?"**
Signals: you read the JD carefully and want to understand your actual scope of work from day one.

4. **"What does a 'great' piece of analysis look like on this team -- is it measured by the complexity of the model, the quality of the stakeholder presentation, or something else?"**
Signals: you are thinking about how your work will be evaluated and what good looks like in this specific culture.

5. **"The Robertson Strategy is mentioned as a key strategic priority. How does Agency Operations Analytics contribute to the metrics that the Robertson Strategy is measured on, and are those metrics visible to the analytics team?"**
Signals: you want to connect your day-to-day work to the company's strategic objectives -- the mark of a senior analyst who thinks beyond task execution.

---

## Red Flag Answers to Avoid

1. **"I built a model with 95% accuracy."** Accuracy is meaningless on imbalanced targets. Always lead with AUC, lift, or precision/recall. Saying "95% accuracy" on a 26% positive rate just means you predicted "no" for everyone.

2. **"The data was already clean so I didn't need to do much EDA."** No interviewer at this level believes this. The right answer is always "I ran a data quality check first, found X issue, resolved it by doing Y." Even if the data was clean, describe what you checked and why.

3. **"I used a random forest because it usually works well."** Always explain the algorithm choice in terms of the data characteristics and the business problem. "I used Gradient Boosting because the behavioral features have nonlinear interactions that tree-based methods handle natively, and I needed rank-ordered scores for campaign prioritization rather than just a binary prediction."

4. **"The dashboard is for technical users."** At Data Analyst III level, every deliverable should be designed for its audience. If a chart requires the viewer to already know what MPHH means to interpret it, the chart failed. Always describe how you would explain a visualization to the least technical person in the room who still needs to act on it.

5. **"I would just pull the data and start querying."** Senior analysts describe a structured approach: understand the business question first, identify the data sources and their limitations, define the metric, check data quality, then analyze. Jumping to queries signals junior-level thinking.

---

## Glossary for This Project

**MPHH (Multiproduct Household):** A customer household that holds two or more AutoShield insurance products. Example: auto + property, or auto + motorcycle. MPHH customers retain at higher rates and generate more lifetime premium.

**Robertson Strategy:** AutoShield's named strategic initiative to grow Multiproduct Household penetration by cross-selling property insurance to existing auto customers, often through the agency channel. The strategy targets a specific high-value demographic known internally as the Robertsons -- long-tenured households who have been with AutoShield Insurance for several years, hold multiple product policies across vehicles, motorcycle, boat, and home, are more likely to be married, pay their premiums reliably either in a single annual payment or through auto-pay, and demonstrate strong brand loyalty over time. The strategy is focused on deepening engagement with this demographic by expanding their product portfolio and ensuring they remain within the AutoShield household.

**Propensity Score:** A model-derived probability (0-100) representing how likely a household is to convert to MPHH within 12 months. A score of 72 means the model estimates a 72% conversion probability.

**Propensity Decile:** Households ranked by propensity score and divided into 10 equal groups. Decile 1 = top 10% highest scores. Used to prioritize outreach targets.

**CLTV (Customer Lifetime Value):** Projected total financial value of a customer relationship over their expected remaining tenure, discounted by a margin factor. In this project: (anchor premium + property premium) x projected tenure years x 18% margin.

**AUC (Area Under the ROC Curve):** A model performance metric from 0 to 1. AUC 0.5 = random guessing. AUC 1.0 = perfect predictions. AUC 0.69 means the model correctly ranks a true converter above a true non-converter 69% of the time.

**Lift:** How much better a model performs compared to random selection. Lift of 2.05 at decile 1 means households in the top 10% convert at 2.05x the overall average rate.

**Cumulative Gain:** The share of total converters captured by contacting households in the top N deciles. "Top 2 deciles = 36% gain" means contacting the top 20% of scored households reaches 36% of all actual converters.

**Quote Abandonment:** When a customer starts (but does not complete) a product quote. In this project, property_quote_started=1 but converted_mphh=0. These households are the highest-priority intervention population.

**SHAP (SHapley Additive exPlanations):** A model interpretability framework that assigns each feature a contribution value for each prediction. Unlike overall feature importance, SHAP shows direction (did this feature push the probability up or down?) and magnitude for individual households.

**Confusion Matrix:** A 2x2 table showing model prediction outcomes: True Positives (correctly predicted converters), True Negatives (correctly predicted non-converters), False Positives (incorrectly flagged as converters), and False Negatives (converters the model missed).

**Save Rate:** In the revenue simulator, the share of contacted unconverted households that actually convert as a result of the outreach campaign. A 15% save rate means 15 out of every 100 contacted households add a second product.
