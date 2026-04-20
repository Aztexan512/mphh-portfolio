-- ============================================================
-- mphh_benchmarking_analysis.sql
-- Project : MPHH Cross-Sell Propensity and Revenue Expansion
-- Author  : Luciano Casillas
-- Version : 1.0
-- Dialect : ANSI SQL (PostgreSQL / Snowflake compatible)
-- Table   : mphh_benchmarking
-- ============================================================
-- PURPOSE: These queries back the MPHH Benchmarking and Reporting
-- Dashboard (benchmarking_app.py). Each query corresponds to a
-- specific chart or table in one of the six dashboard tabs:
--   Tab 1 -- Robertson Strategy Tracker
--   Tab 2 -- YoY Growth
--   Tab 3 -- Cohort Retention
--   Tab 4 -- Agent Leaderboard
--   Tab 5 -- State Performance
--   Tab 6 -- Pipeline Health
--
-- mphh_benchmarking extends mphh_crosssell with four columns:
--   agent_id            : assigned agent per household
--   region              : Midwest / South / West / Northeast
--   quarter             : snapshot quarter label (e.g. 2023Q1)
--   robinson_target_pct : Robertson Strategy target for that quarter
--
-- Robertson Strategy: AutoShield's initiative to grow Multiproduct Household
-- penetration by deepening engagement with the Robertsons -- long-tenured
-- households holding multiple policies who pay reliably and demonstrate strong
-- brand loyalty. Targets represent the quarterly MPHH conversion rate (%) the
-- strategy sets as the portfolio growth goal.
--
-- Robertson Strategy targets by quarter:
--   2023Q1=25.0  2023Q2=25.5  2023Q3=26.0  2023Q4=26.5
--   2024Q1=27.0  2024Q2=27.5  2024Q3=28.0  2024Q4=28.5
--   2025Q1=29.0  2025Q2=29.5  2025Q3=30.0  2025Q4=30.5
-- ============================================================


-- ============================================================
-- Section 1: Robertson Strategy Tracker (Tab 1)
-- ============================================================

-- Q1: Quarterly MPHH rate vs. Robertson Strategy target
-- Answers: Is the portfolio on track or behind the Robertson
-- Strategy target each quarter? What is the gap?
-- Dashboard: "Quarterly MPHH Rate vs. Robertson Strategy Target"
-- and "Quarterly Status Summary" panel.
SELECT
    quarter,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS actual_rate_pct,
    MIN(robinson_target_pct)                              AS target_pct,
    ROUND(
        100.0 * SUM(converted_mphh) / COUNT(*)
        - MIN(robinson_target_pct),
        2
    )                                                     AS vs_target_pp,
    CASE
        WHEN 100.0 * SUM(converted_mphh) / COUNT(*) >= MIN(robinson_target_pct)
        THEN 'On Track'
        ELSE 'Behind'
    END                                                   AS status,
    ROUND(AVG(projected_mphh_cltv), 2)                   AS avg_cltv,
    ROUND(SUM(projected_mphh_cltv) / 1000000.0, 2)       AS total_cltv_M,
    ROUND(AVG(annual_premium_anchor), 2)                  AS avg_premium
FROM mphh_benchmarking
GROUP BY quarter
ORDER BY quarter;


-- Q2: Gap vs. Robertson target summary
-- Answers: In how many quarters did the portfolio miss its target?
-- What is the average shortfall across all quarters?
-- Dashboard: "Gap vs. Robertson Target by Quarter" bar chart.
WITH quarterly_perf AS (
    SELECT
        quarter,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2) AS actual_rate_pct,
        MIN(robinson_target_pct)                          AS target_pct
    FROM mphh_benchmarking
    GROUP BY quarter
)
SELECT
    COUNT(*)                                                 AS total_quarters,
    SUM(CASE WHEN actual_rate_pct < target_pct THEN 1 ELSE 0 END) AS quarters_behind,
    SUM(CASE WHEN actual_rate_pct >= target_pct THEN 1 ELSE 0 END) AS quarters_on_track,
    ROUND(AVG(actual_rate_pct - target_pct), 2)              AS avg_gap_pp,
    ROUND(MIN(actual_rate_pct - target_pct), 2)              AS worst_gap_pp,
    ROUND(MAX(actual_rate_pct - target_pct), 2)              AS best_gap_pp
FROM quarterly_perf;


-- Q3: Channel contribution to quarterly conversion volume
-- Answers: Which channels drive converted household volume each quarter?
-- Is one channel disproportionately responsible for on-track quarters?
-- Dashboard: "Channel Contribution to Quarterly MPHH Rate" stacked bar.
SELECT
    quarter,
    agency_channel,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS channel_rate_pct,
    ROUND(
        100.0 * SUM(converted_mphh) /
        SUM(SUM(converted_mphh)) OVER (PARTITION BY quarter),
        1
    )                                                     AS pct_of_quarter_conversions
FROM mphh_benchmarking
GROUP BY quarter, agency_channel
ORDER BY quarter, converted DESC;


-- ============================================================
-- Section 2: YoY Growth Analysis (Tab 2)
-- ============================================================

-- Q4: Year-over-year MPHH rate by matched quarter (all three years)
-- Answers: How did each quarter evolve from 2023 → 2024 → 2025?
-- Dashboard: "MPHH Rate: 2023 / 2024 / 2025 (Same Quarter)" and
-- "YoY Delta by Quarter" charts.
WITH quarterly_rates AS (
    SELECT
        quarter,
        LEFT(quarter, 4)                                  AS year,
        RIGHT(quarter, 2)                                 AS qtr_label,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2) AS rate_pct
    FROM mphh_benchmarking
    GROUP BY quarter
)
SELECT
    q23.qtr_label                                         AS quarter_label,
    q23.rate_pct                                          AS rate_2023,
    q24.rate_pct                                          AS rate_2024,
    q25.rate_pct                                          AS rate_2025,
    ROUND(q24.rate_pct - q23.rate_pct, 2)                AS delta_23_24_pp,
    ROUND(q25.rate_pct - q24.rate_pct, 2)                AS delta_24_25_pp,
    CASE
        WHEN q24.rate_pct > q23.rate_pct THEN 'Improved'
        WHEN q24.rate_pct < q23.rate_pct THEN 'Declined'
        ELSE 'Flat'
    END                                                   AS direction_23_24,
    CASE
        WHEN q25.rate_pct > q24.rate_pct THEN 'Improved'
        WHEN q25.rate_pct < q24.rate_pct THEN 'Declined'
        ELSE 'Flat'
    END                                                   AS direction_24_25
FROM quarterly_rates q23
JOIN quarterly_rates q24
    ON  q23.qtr_label = q24.qtr_label
    AND q23.year      = '2023'
    AND q24.year      = '2024'
LEFT JOIN quarterly_rates q25
    ON  q23.qtr_label = q25.qtr_label
    AND q25.year      = '2025'
ORDER BY q23.qtr_label;


-- Q5: Year-over-year channel performance (all three years)
-- Answers: Which channels improved or regressed across 2023, 2024, and 2025?
-- Dashboard: "Channel Rate: 2023 / 2024 / 2025" and "Channel YoY Delta" charts.
WITH channel_year AS (
    SELECT
        CASE
            WHEN quarter LIKE '2023%' THEN '2023'
            WHEN quarter LIKE '2024%' THEN '2024'
            WHEN quarter LIKE '2025%' THEN '2025'
        END                                                           AS year,
        agency_channel,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)             AS rate_pct
    FROM mphh_benchmarking
    GROUP BY year, agency_channel
)
SELECT
    y23.agency_channel,
    y23.rate_pct                                          AS rate_2023,
    y24.rate_pct                                          AS rate_2024,
    y25.rate_pct                                          AS rate_2025,
    ROUND(y24.rate_pct - y23.rate_pct, 2)                AS delta_23_24_pp,
    ROUND(y25.rate_pct - y24.rate_pct, 2)                AS delta_24_25_pp,
    CASE
        WHEN y25.rate_pct > y24.rate_pct THEN 'Improved'
        WHEN y25.rate_pct < y24.rate_pct THEN 'Declined'
        ELSE 'Flat'
    END                                                   AS direction_24_25
FROM channel_year y23
JOIN channel_year y24
    ON  y23.agency_channel = y24.agency_channel
    AND y23.year = '2023'
    AND y24.year = '2024'
LEFT JOIN channel_year y25
    ON  y23.agency_channel = y25.agency_channel
    AND y25.year = '2025'
ORDER BY delta_24_25_pp DESC;


-- Q6: Year-over-year CLTV growth (all three years)
-- Answers: Did average and total projected CLTV grow across 2023, 2024, and 2025?
-- Dashboard: "Avg Projected MPHH CLTV by Year" and
-- "Total Portfolio CLTV by Year" charts.
SELECT
    CASE
        WHEN quarter LIKE '2023%' THEN '2023'
        WHEN quarter LIKE '2024%' THEN '2024'
        WHEN quarter LIKE '2025%' THEN '2025'
    END                                                         AS year,
    COUNT(*)                                                    AS total_households,
    ROUND(AVG(projected_mphh_cltv), 2)                         AS avg_cltv,
    ROUND(SUM(projected_mphh_cltv) / 1000000.0, 2)             AS total_cltv_M,
    ROUND(AVG(annual_premium_anchor), 2)                        AS avg_anchor_premium
FROM mphh_benchmarking
GROUP BY year
ORDER BY year;


-- ============================================================
-- Section 3: Cohort Retention (Tab 3)
-- ============================================================

-- Q7: Cohort retention matrix -- acquisition quarter x tenure bucket
-- Answers: At which tenure stage do households acquired in each quarter
-- convert at the highest rate? What is the optimal outreach timing window?
-- Dashboard: "MPHH Conversion Rate Heatmap -- Quarter x Tenure Bucket".
-- Tenure buckets match build_cohort_matrix() in benchmarking_app.py:
--   [0,6) = 0-5mo, [6,12) = 6-11mo, [12,24) = 12-23mo,
--   [24,36) = 24-35mo, [36,60) = 36-59mo, [60,121) = 60+mo
SELECT
    quarter                                                    AS acquisition_quarter,
    CASE
        WHEN tenure_months < 6   THEN '0-5mo'
        WHEN tenure_months < 12  THEN '6-11mo'
        WHEN tenure_months < 24  THEN '12-23mo'
        WHEN tenure_months < 36  THEN '24-35mo'
        WHEN tenure_months < 60  THEN '36-59mo'
        ELSE                          '60+mo'
    END                                                        AS tenure_bucket,
    COUNT(*)                                                   AS total_households,
    SUM(converted_mphh)                                        AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)          AS conversion_rate_pct
FROM mphh_benchmarking
GROUP BY acquisition_quarter, tenure_bucket
ORDER BY acquisition_quarter, tenure_bucket;


-- Q8: Average conversion rate by tenure bucket across all cohorts
-- Answers: Which single tenure window has the highest average conversion
-- rate across all acquisition quarters? Where should outreach be timed?
-- Dashboard: "Average Conversion Rate by Tenure Bucket (All Cohorts)" bar.
SELECT
    CASE
        WHEN tenure_months < 6   THEN '0-5mo'
        WHEN tenure_months < 12  THEN '6-11mo'
        WHEN tenure_months < 24  THEN '12-23mo'
        WHEN tenure_months < 36  THEN '24-35mo'
        WHEN tenure_months < 60  THEN '36-59mo'
        ELSE                          '60+mo'
    END                                                        AS tenure_bucket,
    COUNT(*)                                                   AS total_households,
    SUM(converted_mphh)                                        AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)          AS avg_conversion_rate_pct,
    RANK() OVER (
        ORDER BY SUM(converted_mphh) * 1.0 / COUNT(*) DESC
    )                                                          AS rank_by_rate
FROM mphh_benchmarking
GROUP BY tenure_bucket
ORDER BY avg_conversion_rate_pct DESC;


-- Q9: Long-tenure (60+ month) conversion rate by acquisition quarter
-- Answers: How do the most tenured households in each cohort perform?
-- Is long-tenure conversion improving in more recently acquired cohorts?
-- Dashboard: "Cohort Maturity Trend -- 60+ Month Retention Rate".
SELECT
    quarter                                                    AS acquisition_quarter,
    COUNT(*)                                                   AS households_60plus_months,
    SUM(converted_mphh)                                        AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)          AS conversion_rate_pct
FROM mphh_benchmarking
WHERE tenure_months >= 60
GROUP BY acquisition_quarter
ORDER BY acquisition_quarter;


-- Q10: Early / mid / recent cohort comparison by tenure bucket (3-year span)
-- Answers: How do 2023 early, 2024 mid, and 2025 recent cohorts compare
-- at the same tenure stage? Is conversion improving across cohort vintages?
-- Dashboard: "2023 vs. 2024 vs. 2025 Cohort Conversion Rate by Tenure Bucket".
SELECT
    CASE
        WHEN tenure_months < 6   THEN '0-5mo'
        WHEN tenure_months < 12  THEN '6-11mo'
        WHEN tenure_months < 24  THEN '12-23mo'
        WHEN tenure_months < 36  THEN '24-35mo'
        WHEN tenure_months < 60  THEN '36-59mo'
        ELSE                          '60+mo'
    END                                                        AS tenure_bucket,
    CASE
        WHEN quarter IN ('2023Q1', '2023Q2') THEN '2023 (Early)'
        WHEN quarter IN ('2024Q1', '2024Q2') THEN '2024 (Mid)'
        WHEN quarter IN ('2025Q3', '2025Q4') THEN '2025 (Recent)'
    END                                                        AS cohort_group,
    COUNT(*)                                                   AS total_households,
    SUM(converted_mphh)                                        AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)          AS conversion_rate_pct
FROM mphh_benchmarking
WHERE quarter IN ('2023Q1', '2023Q2', '2024Q1', '2024Q2', '2025Q3', '2025Q4')
GROUP BY tenure_bucket, cohort_group
ORDER BY tenure_bucket, cohort_group;


-- ============================================================
-- Section 4: Agent Leaderboard (Tab 4)
-- ============================================================

-- Q11: Full agent leaderboard with multi-dimensional rankings
-- Answers: Who are the top agents by conversion rate, total conversions,
-- and total CLTV generated? Which agents need coaching?
-- Dashboard: "Agent Performance Rankings" leaderboard and distribution.
-- Note: Minimum 50 households required (matches build_agent_leaderboard()).
WITH agent_stats AS (
    SELECT
        agent_id,
        agency_channel,
        region,
        state,
        COUNT(*)                                              AS households,
        SUM(converted_mphh)                                   AS converted,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS rate_pct,
        ROUND(AVG(projected_mphh_cltv), 2)                    AS avg_cltv,
        ROUND(SUM(projected_mphh_cltv) / 1000.0, 1)          AS total_cltv_k,
        ROUND(AVG(outreach_contacts_12m * 1.0), 2)            AS avg_outreach,
        ROUND(AVG(digital_engagement_score * 1.0), 2)         AS avg_digital_score
    FROM mphh_benchmarking
    GROUP BY agent_id, agency_channel, region, state
    HAVING COUNT(*) >= 50
)
SELECT
    agent_id,
    agency_channel,
    region,
    state,
    households,
    converted,
    rate_pct,
    avg_cltv,
    total_cltv_k,
    avg_outreach,
    avg_digital_score,
    RANK() OVER (ORDER BY rate_pct DESC)    AS rank_by_rate,
    RANK() OVER (ORDER BY converted DESC)   AS rank_by_conversions,
    RANK() OVER (ORDER BY total_cltv_k DESC) AS rank_by_cltv
FROM agent_stats
ORDER BY converted DESC;


-- Q12: Top 10 vs. bottom 10 vs. median agent performance gap
-- Answers: How wide is the performance spread between the best and worst
-- agents? What is the coaching opportunity if bottom agents reach median?
-- Dashboard: "Performance Gap: Top 10 vs. Bottom 10 Agents" bar.
WITH agent_rates AS (
    SELECT
        agent_id,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2) AS rate_pct
    FROM mphh_benchmarking
    GROUP BY agent_id
    HAVING COUNT(*) >= 50
),
ranked AS (
    SELECT
        rate_pct,
        ROW_NUMBER() OVER (ORDER BY rate_pct DESC) AS rank_desc,
        ROW_NUMBER() OVER (ORDER BY rate_pct ASC)  AS rank_asc,
        COUNT(*) OVER ()                            AS total_agents
    FROM agent_rates
)
SELECT
    ROUND(AVG(CASE WHEN rank_desc <= 10 THEN rate_pct END), 2)  AS top_10_avg_rate,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY rate_pct)
          OVER (), 2)                                            AS median_rate,
    ROUND(AVG(CASE WHEN rank_asc  <= 10 THEN rate_pct END), 2)  AS bottom_10_avg_rate,
    ROUND(
        AVG(CASE WHEN rank_desc <= 10 THEN rate_pct END)
        - AVG(CASE WHEN rank_asc  <= 10 THEN rate_pct END),
        2
    )                                                            AS top_bottom_gap_pp
FROM ranked
LIMIT 1;


-- Q13: Regional agent performance summary
-- Answers: Which regions have the highest average agent conversion rate?
-- Which regions have the widest spread (coaching opportunity)?
-- Dashboard: "Avg Agent Conversion Rate by Region" bar.
WITH agent_stats AS (
    SELECT
        agent_id,
        region,
        ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS rate_pct,
        ROUND(SUM(projected_mphh_cltv) / 1000.0, 1)          AS total_cltv_k
    FROM mphh_benchmarking
    GROUP BY agent_id, region
    HAVING COUNT(*) >= 50
)
SELECT
    region,
    COUNT(*)                                                   AS agent_count,
    ROUND(AVG(rate_pct), 2)                                    AS avg_rate_pct,
    ROUND(MIN(rate_pct), 2)                                    AS min_rate_pct,
    ROUND(MAX(rate_pct), 2)                                    AS max_rate_pct,
    ROUND(MAX(rate_pct) - MIN(rate_pct), 2)                    AS rate_spread_pp,
    ROUND(AVG(total_cltv_k), 1)                                AS avg_cltv_k
FROM agent_stats
GROUP BY region
ORDER BY avg_rate_pct DESC;


-- ============================================================
-- Section 5: State Performance (Tab 5)
-- ============================================================

-- Q14: State-level MPHH conversion metrics
-- Answers: Which states lead and lag the portfolio average?
-- Where is the largest unconverted CLTV opportunity by state?
-- Dashboard: "MPHH Conversion Rate by State" and
-- "Total CLTV Opportunity by State" charts and detail table.
WITH portfolio_avg AS (
    SELECT ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2) AS overall_rate
    FROM mphh_benchmarking
)
SELECT
    b.state,
    COUNT(*)                                                    AS total_households,
    SUM(converted_mphh)                                         AS converted,
    COUNT(*) - SUM(converted_mphh)                              AS unconverted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)           AS rate_pct,
    ROUND(
        100.0 * SUM(converted_mphh) / COUNT(*) - p.overall_rate,
        2
    )                                                           AS vs_portfolio_avg_pp,
    CASE
        WHEN 100.0 * SUM(converted_mphh) / COUNT(*) >= p.overall_rate
        THEN 'Above Avg' ELSE 'Below Avg'
    END                                                         AS vs_avg_status,
    ROUND(AVG(projected_mphh_cltv), 2)                         AS avg_cltv,
    ROUND(SUM(projected_mphh_cltv) / 1000000.0, 2)             AS total_cltv_M,
    ROUND(AVG(annual_premium_anchor), 2)                        AS avg_anchor_premium,
    ROUND(AVG(outreach_contacts_12m * 1.0), 2)                 AS avg_outreach_contacts,
    ROUND(AVG(digital_engagement_score * 1.0), 2)              AS avg_digital_score
FROM mphh_benchmarking b
CROSS JOIN portfolio_avg p
GROUP BY b.state, p.overall_rate
ORDER BY rate_pct DESC;


-- Q15: State x channel conversion rate heatmap
-- Answers: Which channel performs best in each state?
-- Where should channel investment be redirected by geography?
-- Dashboard: "State x Channel Conversion Rate Heatmap".
SELECT
    state,
    agency_channel,
    COUNT(*)                                              AS total_households,
    SUM(converted_mphh)                                   AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)     AS conversion_rate_pct,
    RANK() OVER (
        PARTITION BY state
        ORDER BY SUM(converted_mphh) * 1.0 / COUNT(*) DESC
    )                                                     AS rank_within_state
FROM mphh_benchmarking
GROUP BY state, agency_channel
ORDER BY state, conversion_rate_pct DESC;


-- ============================================================
-- Section 6: Pipeline Health (Tab 6)
-- ============================================================

-- Q16: Property quote conversion funnel
-- Answers: What share of households started a quote? Of those,
-- how many converted vs. abandoned? What is the abandonment rate?
-- Dashboard: "Conversion Funnel" and "Quote Outcome Breakdown".
SELECT
    COUNT(*)                                                      AS total_households,
    SUM(property_quote_started)                                   AS quote_started,
    ROUND(100.0 * SUM(property_quote_started) / COUNT(*), 2)     AS quote_start_rate_pct,
    SUM(CASE WHEN property_quote_started = 1 AND converted_mphh = 1 THEN 1 ELSE 0 END) AS converted_with_quote,
    SUM(CASE WHEN property_quote_started = 1 AND converted_mphh = 0 THEN 1 ELSE 0 END) AS abandoned,
    SUM(CASE WHEN property_quote_started = 0 AND converted_mphh = 1 THEN 1 ELSE 0 END) AS converted_no_quote,
    SUM(CASE WHEN property_quote_started = 0 AND converted_mphh = 0 THEN 1 ELSE 0 END) AS never_started_not_converted,
    ROUND(
        100.0 * SUM(CASE WHEN property_quote_started = 1 AND converted_mphh = 1 THEN 1 ELSE 0 END)
        / NULLIF(SUM(property_quote_started), 0),
        2
    )                                                             AS quote_conversion_rate_pct,
    ROUND(
        100.0 * SUM(CASE WHEN property_quote_started = 1 AND converted_mphh = 0 THEN 1 ELSE 0 END)
        / NULLIF(SUM(property_quote_started), 0),
        2
    )                                                             AS abandonment_rate_pct,
    -- Quote starters convert at X times the rate of non-starters
    ROUND(
        (SUM(CASE WHEN property_quote_started = 1 AND converted_mphh = 1 THEN 1.0 ELSE 0 END)
         / NULLIF(SUM(property_quote_started), 0))
        /
        NULLIF(
            SUM(CASE WHEN property_quote_started = 0 AND converted_mphh = 1 THEN 1.0 ELSE 0 END)
            / NULLIF(COUNT(*) - SUM(property_quote_started), 0),
            0
        ),
        2
    )                                                             AS quote_starter_lift_vs_non_starter
FROM mphh_benchmarking;


-- Q17: Outreach contact frequency vs. conversion rate
-- Answers: How does increasing outreach contact count affect conversion?
-- What is the optimal contact band? Where do diminishing returns set in?
-- Dashboard: "Conversion Rate by Outreach Contact Count" bar.
SELECT
    outreach_contacts_12m                                         AS contacts,
    COUNT(*)                                                      AS total_households,
    SUM(converted_mphh)                                           AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)             AS conversion_rate_pct,
    ROUND(AVG(digital_engagement_score * 1.0), 2)                AS avg_digital_score,
    ROUND(AVG(projected_mphh_cltv), 2)                           AS avg_cltv,
    -- Index conversion rate vs. zero-contact baseline
    ROUND(
        100.0 * SUM(converted_mphh) / COUNT(*) /
        FIRST_VALUE(SUM(converted_mphh) * 1.0 / COUNT(*))
            OVER (ORDER BY outreach_contacts_12m
                  ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING),
        1
    )                                                             AS index_vs_zero_contact,
    CASE
        WHEN outreach_contacts_12m BETWEEN 1 AND 3 THEN 'Sweet Spot'
        WHEN outreach_contacts_12m > 3             THEN 'Diminishing Returns'
        ELSE                                            'No Outreach'
    END                                                           AS outreach_band
FROM mphh_benchmarking
GROUP BY contacts
ORDER BY contacts;


-- Q18: Propensity tier x outreach interaction
-- Answers: Are high-propensity households receiving adequate outreach?
-- Does outreach lift conversion equally across all propensity tiers?
-- Dashboard: "Conversion Rate by Outreach Count and Propensity Tier".
SELECT
    propensity_tier,
    outreach_contacts_12m                                         AS contacts,
    COUNT(*)                                                      AS total_households,
    SUM(converted_mphh)                                           AS converted,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)             AS conversion_rate_pct
FROM mphh_benchmarking
GROUP BY propensity_tier, contacts
ORDER BY
    CASE propensity_tier
        WHEN 'High Propensity'   THEN 1
        WHEN 'Medium Propensity' THEN 2
        WHEN 'Low Propensity'    THEN 3
    END,
    contacts;


-- Q19: Leading indicators -- digital engagement and propensity by quarter
-- Answers: Are digital engagement and propensity scores trending up or down?
-- Do rising scores precede conversion rate improvements in subsequent quarters?
-- Dashboard: "Leading Indicators: Digital Engagement and Propensity by Quarter".
SELECT
    quarter,
    COUNT(*)                                                       AS total_households,
    ROUND(AVG(digital_engagement_score * 1.0), 2)                 AS avg_digital_score,
    ROUND(AVG(propensity_score), 2)                                AS avg_propensity_score,
    ROUND(AVG(outreach_contacts_12m * 1.0), 2)                    AS avg_outreach_contacts,
    ROUND(100.0 * SUM(converted_mphh) / COUNT(*), 2)              AS actual_conversion_rate_pct,
    MIN(robinson_target_pct)                                       AS robinson_target_pct
FROM mphh_benchmarking
GROUP BY quarter
ORDER BY quarter;
