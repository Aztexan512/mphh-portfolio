# Data Dictionary: MPHH Cross-Sell Propensity Dataset

**File:** `data/mphh_crosssell.csv`
**Rows:** 150,000
**Seed:** 42 (fully reproducible)
**Target Variable:** `converted_mphh`
**Conversion Rate:** ~26.1%

Each row represents one insured household at a point-in-time snapshot. A household
is the unit of analysis -- one or more policies tied to the same address and primary
policyholder. The goal is to predict which single-product households will add a
second AutoShield product within 12 months.

---

## Column Reference

| Column | Type | Description | Business Meaning | Notes |
|---|---|---|---|---|
| `household_id` | string | Unique household identifier (HH-0000001 format) | Primary key for joining across systems | Not a model feature |
| `snapshot_date` | date (YYYY-MM-DD) | Date of the household record snapshot | Used for cohort analysis and time-based segmentation | Ranges 2023-01-01 to 2024-12-31 |
| `state` | string | State where household is located | Geographic segmentation; agent density and property rates vary significantly by state | 10 states weighted by AutoShield market presence |
| `age_of_primary` | integer | Age of primary policyholder in years | Older homeowners have higher property attachment rates | Range: 22-77 |
| `home_ownership` | string | Homeowner / Renter / Condo | Homeowners are prime targets for property cross-sell; renters map to renters insurance | Drives property premium estimate |
| `household_size` | integer | Number of people in household | Larger households often have bundling motivation (multi-driver, multi-asset) | Range: 1-5 |
| `income_band` | string | Estimated household income band | Higher income bands show greater propensity for Plus/Elite tiers and property products | Five bands from under $50k to $150k+ |
| `agency_channel` | string | How the household acquired their policy | Independent Agents drive more cross-sell due to relationship selling; Direct Online is higher volume, lower relationship | Four channels: Independent Agent, Direct Online, Call Center, Captive Agent |
| `anchor_product` | string | First (existing) AutoShield product the household holds | Auto is dominant; Motorcycle and Boat represent niche segments with different property needs | Four products: Auto, Motorcycle, Boat, Commercial Auto |
| `policy_tier` | string | Coverage tier of the anchor product | Higher tiers correlate with more engaged, higher-value customers; Elite customers have strongest cross-sell conversion | Four tiers: Basic, Standard, Plus, Elite |
| `tenure_months` | integer | Months since household's first policy with AutoShield | Established customers (24+ months) show stronger trust and conversion; very new customers (under 6 months) convert poorly | Range: 1-120 |
| `outreach_contacts_12m` | integer | Number of proactive outreach contacts (calls, emails, agent touchpoints) in the past 12 months | STRONGEST BEHAVIORAL SIGNAL: 1-3 contacts significantly increases conversion; 4+ shows diminishing returns or annoyance effect | Range: 0-5 |
| `claims_24m` | integer | Number of claims filed in the past 24 months | Claims create friction; 2+ claims reduces conversion propensity; also flags higher-risk households | Range: 0-3 |
| `digital_engagement_score` | integer | Composite score (1-10) of app logins, policy views, and quote starts in past 6 months | High digital engagement (7+) signals receptivity and self-service behavior; correlates with Direct Online channel | Synthetic composite; not a single system field |
| `property_quote_started` | integer (0/1) | Whether household started (but did not complete) a property product quote in the past 6 months | EARLY FRICTION SIGNAL: Quote starts with no conversion represent warm leads and the highest-priority intervention population | Binary; 1 = started quote, 0 = no quote started |
| `annual_premium_anchor` | float | Annual premium on the anchor product (USD) | Directly represents revenue at stake; higher-premium customers contribute more to MPHH revenue expansion | Range: approximately $578-$2,100 depending on tier |
| `projected_mphh_cltv` | float | Projected Customer Lifetime Value if household converts to MPHH (USD) | Financial impact metric: sum of anchor + property premiums times projected tenure years times margin factor (18%) | **FINANCIAL COLUMN -- use for ROI simulation, not model training** |

---

## Dashboard-Only Columns (EXCLUDE FROM ML TRAINING)

The following columns are derived from the true probability used to generate `converted_mphh`.
Including them as model features would constitute **data leakage** -- they encode the outcome
signal directly.

| Column | Type | Leakage Risk | Use |
|---|---|---|---|
| `propensity_score` | float (1-99) | **HIGH -- direct leakage** | Dashboard display, At-Risk Explorer, intervention prioritization |
| `propensity_tier` | string | **HIGH -- direct leakage** | Segment filter labels in dashboard sidebar |

**Rule:** In any real deployment, the propensity score would be the model OUTPUT, not an input.
It is included in the dataset here for dashboard demonstration purposes only.

---

## Leakage Documentation Summary

| Column | Use in Model | Reason |
|---|---|---|
| `propensity_score` | EXCLUDE | Directly derived from conversion probability |
| `propensity_tier` | EXCLUDE | Directly derived from propensity_score |
| `projected_mphh_cltv` | EXCLUDE | Incorporates future projected tenure -- forward-looking leakage |
| `household_id` | EXCLUDE | Identifier only |
| `snapshot_date` | EXCLUDE as raw date | Use only to derive cohort/quarter features |

---

## Target Variable Definition

**`converted_mphh`** (integer, 0 or 1)

- **1** = The household added a second AutoShield product (property, renters, condo, umbrella)
  within 12 months following the snapshot date.
- **0** = No second product was added within the 12-month window.

A conversion rate of approximately 26% reflects a realistic cross-sell environment for
a large P&C insurer with active outreach programs. Untargeted baseline conversion
for cold households is approximately 8-10%; the elevated overall rate reflects that
the dataset intentionally oversamples higher-engagement households to create an
actionable story.
