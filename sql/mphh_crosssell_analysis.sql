-- ============================================================
-- mphh_crosssell_analysis.sql
-- Project : MPHH Cross-Sell Propensity and Revenue Expansion
-- Author  : Luciano Casillas
-- Version : 1.0
-- Dialect : ANSI SQL (PostgreSQL / Snowflake compatible)
-- Table   : mphh_crosssell
-- ============================================================
-- PURPOSE: These queries support Agency Operations Analytics
-- reporting on Multiproduct Household conversion rates, segment
-- drivers, financial impact, and intervention candidate selection.
-- Each query answers a specific business question asked by sales
-- leadership, product teams, or control/BI partners.
-- ============================================================


-- ============================================================
-- Section 1: Data Quality and Overview
-- ============================================================

-- Q1: Row counts, target distribution, and basic data quality check
-- Answers: How many households are in scope? What is the baseline
-- conversion rate? Are there null values in key columns?
-- Business use: First slide in any briefing -- sets the stage.
SELECT
    COUNT(*)                                          AS total_households,
    SUM(converted_mphh)                               AS total_converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2) AS conversion_rate_pct,
    COUNT(*) - SUM(CASE WHEN household_id           IS NOT NULL THEN 1 ELSE 0 END) AS null_household_id,
    COUNT(*) - SUM(CASE WHEN agency_channel         IS NOT NULL THEN 1 ELSE 0 END) AS null_agency_channel,
    COUNT(*) - SUM(CASE WHEN anchor_product         IS NOT NULL THEN 1 ELSE 0 END) AS null_anchor_product,
    COUNT(*) - SUM(CASE WHEN policy_tier            IS NOT NULL THEN 1 ELSE 0 END) AS null_policy_tier,
    COUNT(*) - SUM(CASE WHEN tenure_months          IS NOT NULL THEN 1 ELSE 0 END) AS null_tenure_months,
    COUNT(*) - SUM(CASE WHEN annual_premium_anchor  IS NOT NULL THEN 1 ELSE 0 END) AS null_annual_premium,
    COUNT(*) - SUM(CASE WHEN projected_mphh_cltv    IS NOT NULL THEN 1 ELSE 0 END) AS null_projected_cltv,
    MIN(tenure_months)    AS min_tenure_months,
    MAX(tenure_months)    AS max_tenure_months,
    ROUND(AVG(tenure_months), 1) AS avg_tenure_months,
    ROUND(AVG(annual_premium_anchor), 2) AS avg_annual_premium
FROM mphh_crosssell;


-- Q2: Value distribution across key categorical dimensions
-- Answers: How is the population distributed across channels,
-- tiers, and products? Are segments balanced enough for analysis?
-- Business use: Data profiling; informs which segments have
-- enough volume to act on.
SELECT
    agency_channel,
    anchor_product,
    policy_tier,
    COUNT(*)                                              AS household_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)   AS pct_of_total,
    SUM(converted_mphh)                                   AS converted_count,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct
FROM mphh_crosssell
GROUP BY agency_channel, anchor_product, policy_tier
ORDER BY household_count DESC
LIMIT 30;


-- ============================================================
-- Section 2: Segmentation Analysis
-- ============================================================

-- Q3: Conversion rate by agency channel -- primary strategic driver
-- Answers: Which acquisition channel produces the most MPHH
-- conversions? Where should agency operations focus sales support?
-- Business use: Informs channel-specific outreach strategy and
-- agent incentive program design.
SELECT
    agency_channel,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct,
    ROUND(AVG(annual_premium_anchor), 2)                  AS avg_anchor_premium,
    ROUND(AVG(projected_mphh_cltv), 2)                    AS avg_mphh_cltv,
    RANK() OVER (ORDER BY SUM(converted_mphh) * 1.0 / COUNT(*) DESC) AS rank_by_rate
FROM mphh_crosssell
GROUP BY agency_channel
ORDER BY conversion_rate_pct DESC;


-- Q4: Conversion rate by policy tier -- reveals value concentration
-- Answers: Do higher-tier customers convert to MPHH at higher rates?
-- What is the revenue concentration by tier?
-- Business use: Elite/Plus segments may warrant dedicated cross-sell
-- programs; Basic customers may need product education first.
SELECT
    policy_tier,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct,
    ROUND(AVG(annual_premium_anchor), 2)                  AS avg_anchor_premium,
    ROUND(SUM(annual_premium_anchor) / 1000000.0, 3)      AS total_anchor_premium_M,
    ROUND(SUM(projected_mphh_cltv) / 1000000.0, 3)        AS total_mphh_cltv_M,
    RANK() OVER (ORDER BY SUM(converted_mphh) * 1.0 / COUNT(*) DESC) AS rank_by_rate
FROM mphh_crosssell
GROUP BY policy_tier
ORDER BY conversion_rate_pct DESC;


-- Q5: Top combined segments ranked by conversion rate (min 500 households)
-- Answers: Which specific channel + tier + product combinations have
-- the highest and lowest conversion rates?
-- Business use: Identifies "sweet spots" for targeted programs and
-- segments that may need intervention or product redesign.
WITH segment_stats AS (
    SELECT
        agency_channel,
        policy_tier,
        anchor_product,
        COUNT(*)                                          AS household_count,
        SUM(converted_mphh)                               AS converted,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2) AS conversion_rate_pct,
        ROUND(AVG(projected_mphh_cltv), 2)                AS avg_mphh_cltv
    FROM mphh_crosssell
    GROUP BY agency_channel, policy_tier, anchor_product
    HAVING COUNT(*) >= 500
)
SELECT
    agency_channel,
    policy_tier,
    anchor_product,
    household_count,
    converted,
    conversion_rate_pct,
    avg_mphh_cltv,
    RANK() OVER (ORDER BY conversion_rate_pct DESC)  AS rank_high,
    RANK() OVER (ORDER BY conversion_rate_pct ASC)   AS rank_low
FROM segment_stats
ORDER BY conversion_rate_pct DESC
LIMIT 20;


-- ============================================================
-- Section 3: Financial Impact Quantification
-- ============================================================

-- Q6: Total projected revenue at risk and opportunity by channel
-- Answers: What is the total MPHH CLTV opportunity remaining
-- in the unconverted population? Where is the largest dollar
-- opportunity by channel?
-- Business use: Builds the executive business case for MPHH investment.
-- "Unconverted CLTV" is revenue sitting on the table.
WITH channel_impact AS (
    SELECT
        agency_channel,
        COUNT(*)                                              AS total_households,
        SUM(CASE WHEN converted_mphh = 1 THEN 1 ELSE 0 END)  AS already_converted,
        SUM(CASE WHEN converted_mphh = 0 THEN 1 ELSE 0 END)  AS not_yet_converted,
        ROUND(SUM(CASE WHEN converted_mphh = 1
            THEN projected_mphh_cltv ELSE 0 END) / 1000000.0, 2) AS realized_cltv_M,
        ROUND(SUM(CASE WHEN converted_mphh = 0
            THEN projected_mphh_cltv ELSE 0 END) / 1000000.0, 2) AS unrealized_cltv_M,
        ROUND(AVG(CASE WHEN converted_mphh = 0
            THEN projected_mphh_cltv END), 2)                AS avg_cltv_per_unconverted
    FROM mphh_crosssell
    GROUP BY agency_channel
)
SELECT
    *,
    ROUND(unrealized_cltv_M / (realized_cltv_M + unrealized_cltv_M) * 100, 1) AS pct_unrealized
FROM channel_impact
ORDER BY unrealized_cltv_M DESC;


-- Q7: Financial impact by home ownership -- quantifies the property opportunity
-- Answers: What is the projected CLTV of homeowner households that
-- have not yet converted? This is the core property cross-sell population.
-- Business use: Homeowners are the primary target for Robinson Strategy
-- property attachment. Quantifies the premium-bearing population.
SELECT
    home_ownership,
    COUNT(*)                                                    AS total_households,
    SUM(CASE WHEN converted_mphh = 0 THEN 1 ELSE 0 END)        AS unconverted,
    ROUND(AVG(CASE WHEN converted_mphh = 0
        THEN projected_mphh_cltv END), 2)                      AS avg_cltv_unconverted,
    ROUND(SUM(CASE WHEN converted_mphh = 0
        THEN projected_mphh_cltv ELSE 0 END) / 1000000.0, 2)  AS total_opportunity_M,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)           AS conversion_rate_pct
FROM mphh_crosssell
GROUP BY home_ownership
ORDER BY total_opportunity_M DESC;


-- ============================================================
-- Section 4: Cohort and Behavioral Analysis
-- ============================================================

-- Q8: Conversion rate and CLTV by tenure bucket
-- Answers: At which tenure stage do households convert most readily?
-- Are there tenure "dead zones" where outreach is ineffective?
-- Business use: Optimizes the timing of cross-sell outreach programs
-- relative to when a household joined.
WITH tenure_buckets AS (
    SELECT
        CASE
            WHEN tenure_months < 6   THEN '1: 0-5 months'
            WHEN tenure_months < 12  THEN '2: 6-11 months'
            WHEN tenure_months < 24  THEN '3: 12-23 months'
            WHEN tenure_months < 36  THEN '4: 24-35 months'
            WHEN tenure_months < 60  THEN '5: 36-59 months'
            ELSE                          '6: 60+ months'
        END AS tenure_bucket,
        converted_mphh,
        annual_premium_anchor,
        projected_mphh_cltv
    FROM mphh_crosssell
)
SELECT
    tenure_bucket,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct,
    ROUND(AVG(annual_premium_anchor), 2)                  AS avg_anchor_premium,
    ROUND(AVG(projected_mphh_cltv), 2)                    AS avg_mphh_cltv
FROM tenure_buckets
GROUP BY tenure_bucket
ORDER BY tenure_bucket;


-- Q9: Outreach contact frequency impact on conversion (the behavioral signal)
-- Answers: How does the number of proactive outreach contacts affect
-- conversion rate? Is there a "sweet spot" contact frequency?
-- Business use: Directly informs how many touches the outreach program
-- should target per household per year. Shows ROI of outreach investment.
SELECT
    outreach_contacts_12m,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct,
    ROUND(AVG(digital_engagement_score), 2)               AS avg_digital_score,
    ROUND(AVG(projected_mphh_cltv), 2)                    AS avg_mphh_cltv,
    -- Index vs. baseline (0 contacts)
    ROUND(
        100.0 * SUM(converted_mphh) / COUNT(*) /
        FIRST_VALUE(SUM(converted_mphh) * 1.0 / COUNT(*))
            OVER (ORDER BY outreach_contacts_12m
                  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),
        1
    ) AS index_vs_zero_contact
FROM mphh_crosssell
GROUP BY outreach_contacts_12m
ORDER BY outreach_contacts_12m;


-- Q10: Property quote abandonment analysis -- the early friction signal
-- Answers: What share of households started a property quote but did
-- not convert? What are their characteristics vs. converters?
-- Business use: Quote abandonments are the highest-priority intervention
-- population. They raised their hand but did not close.
SELECT
    property_quote_started,
    converted_mphh,
    COUNT(*)                                              AS household_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)   AS pct_of_total,
    ROUND(AVG(annual_premium_anchor), 2)                  AS avg_anchor_premium,
    ROUND(AVG(projected_mphh_cltv), 2)                    AS avg_mphh_cltv,
    ROUND(AVG(digital_engagement_score), 2)               AS avg_digital_score,
    ROUND(AVG(outreach_contacts_12m * 1.0), 2)            AS avg_outreach_contacts
FROM mphh_crosssell
GROUP BY property_quote_started, converted_mphh
ORDER BY property_quote_started DESC, converted_mphh DESC;


-- ============================================================
-- Section 5: Model Support Queries
-- ============================================================

-- Q11: Feature engineering foundations -- propensity score decile distribution
-- Answers: How are households distributed across propensity score deciles?
-- Does higher decile correlate cleanly with conversion rate (lift check)?
-- Business use: Validates that the model separates well before deployment.
-- This is the "lift curve in SQL" that data scientists present to stakeholders.
WITH scored AS (
    SELECT
        household_id,
        converted_mphh,
        propensity_score,
        annual_premium_anchor,
        projected_mphh_cltv,
        NTILE(10) OVER (ORDER BY propensity_score DESC) AS propensity_decile
    FROM mphh_crosssell
),
decile_stats AS (
    SELECT
        propensity_decile,
        COUNT(*)                                              AS households,
        SUM(converted_mphh)                                   AS converted,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct,
        ROUND(AVG(propensity_score), 1)                       AS avg_score,
        ROUND(SUM(projected_mphh_cltv) / 1000000.0, 2)       AS total_cltv_M
    FROM scored
    GROUP BY propensity_decile
)
SELECT
    propensity_decile,
    households,
    converted,
    conversion_rate_pct,
    avg_score,
    total_cltv_M,
    -- Lift vs. random (overall conversion rate)
    ROUND(conversion_rate_pct /
        (SUM(converted) OVER () * 100.0 / SUM(households) OVER ()), 2) AS lift_vs_random,
    -- Cumulative gain
    ROUND(100.0 * SUM(converted) OVER (ORDER BY propensity_decile
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) /
        SUM(converted) OVER (), 2) AS cumulative_gain_pct
FROM decile_stats
ORDER BY propensity_decile;


-- Q12: Intervention candidate identification -- the at-risk cross-sell list
-- Answers: Which specific households should be prioritized for the next
-- outreach campaign? Ranked by propensity score, filtered for warm leads.
-- Business use: This query produces the campaign list for agency operations.
-- Feeds directly into the dashboard's "At-Risk Customer Profile" section.
-- In production, this would be scheduled as a weekly refresh.
WITH candidates AS (
    SELECT
        household_id,
        snapshot_date,
        state,
        agency_channel,
        anchor_product,
        policy_tier,
        tenure_months,
        home_ownership,
        income_band,
        outreach_contacts_12m,
        property_quote_started,
        digital_engagement_score,
        claims_24m,
        annual_premium_anchor,
        projected_mphh_cltv,
        propensity_score,
        propensity_tier,
        -- Priority segment classification
        CASE
            WHEN property_quote_started = 1
             AND converted_mphh = 0 THEN 'Warm Lead: Quote Abandoned'
            WHEN propensity_score >= 65
             AND outreach_contacts_12m = 0 THEN 'Warm Lead: High Score, No Outreach'
            WHEN propensity_score >= 50
             AND outreach_contacts_12m BETWEEN 1 AND 3 THEN 'Active Nurture'
            WHEN home_ownership = 'Homeowner'
             AND propensity_score >= 55 THEN 'Property Target: Homeowner'
            ELSE 'Standard Pipeline'
        END AS intervention_segment,
        -- Urgency rank for campaign scheduling
        ROW_NUMBER() OVER (
            PARTITION BY agency_channel
            ORDER BY propensity_score DESC, projected_mphh_cltv DESC
        ) AS rank_within_channel
    FROM mphh_crosssell
    WHERE
        converted_mphh = 0                   -- Not yet converted
        AND propensity_score >= 40            -- Minimum propensity threshold
        AND claims_24m <= 1                   -- Exclude high-friction households
)
SELECT
    household_id,
    snapshot_date,
    state,
    agency_channel,
    anchor_product,
    policy_tier,
    tenure_months,
    home_ownership,
    income_band,
    outreach_contacts_12m,
    property_quote_started,
    digital_engagement_score,
    annual_premium_anchor,
    projected_mphh_cltv,
    propensity_score,
    propensity_tier,
    intervention_segment,
    rank_within_channel
FROM candidates
WHERE rank_within_channel <= 500       -- Top 500 per channel for campaign sizing
ORDER BY agency_channel, rank_within_channel;
