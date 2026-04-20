"""
MPHH Cross-Sell Propensity Dashboard
Author: Luciano Casillas
Version: 1.0
---
This dashboard analyzes Multiproduct Household (MPHH) cross-sell propensity
for AutoShield Insurance Agency Operations. It surfaces which single-product
households are most likely to add a second product, quantifies the revenue
opportunity, and provides actionable intervention candidate lists for agency
sales teams and strategic partners.

Tab index:
    render_kpi_header       : persistent KPI row above all tabs
    render_sidebar          : all filters
    render_overview         : Tab 1: Overview
    render_crosssell_drivers: Tab 2: Cross-Sell Drivers
    render_model_risk       : Tab 3: Model + Risk
    render_financial_impact : Tab 4: Financial Impact
    render_recommendations  : Tab 5: Recommendations
    render_healthcare_apply : Tab 6: Healthcare Application
"""

# ============================================================
# PAGE CONFIG -- must be first Streamlit call
# ============================================================
import streamlit as st
st.set_page_config(
    page_title="MPHH Cross-Sell Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# IMPORTS
# ============================================================
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, roc_auc_score
import os

# ============================================================
# COLOR PALETTE
# ============================================================
NAVY       = "#0A3360"
STEEL_700  = "#405E7C"
BLUE_700   = "#0077B3"
BLUE_500   = "#4EBEE5"
STEEL_300  = "#D1E2E5"
STEEL_100  = "#F4F9FA"
WHITE      = "#FFFFFF"
BLACK      = "#2D2D2D"
GRAY_700   = "#707070"
GRAY_300   = "#CCCCCC"
GREEN_700  = "#08CAA9"
GREEN_900  = "#067462"
ORANGE_700 = "#FF8A39"
RED_SOFT   = "#E05252"

CHART_FONT = dict(family="Inter, Helvetica Neue, sans-serif", size=13, color=BLACK)
BAR_COLORS = [BLUE_700, GREEN_700, ORANGE_700, STEEL_700, BLUE_500, NAVY, GREEN_900]

# ============================================================
# GLOBAL CSS
# ============================================================
def inject_css():
    st.markdown(f"""
    <style>
    /* Base */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], section.main {{
        background-color: {WHITE} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {STEEL_100} !important;
    }}
    /* KPI metric cards */
    .kpi-card {{
        background: {WHITE};
        border-left: 4px solid {BLUE_700};
        border-radius: 6px;
        padding: 0 16px 10px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }}
    /* Insight strips */
    .insight-strip {{
        background: {STEEL_100};
        border-left: 4px solid {BLUE_700};
        border-radius: 4px;
        padding: 12px 18px;
        margin-bottom: 14px;
    }}
    .insight-strip .label {{
        font-size: 17px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: {NAVY};
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .insight-strip .body {{
        font-size: 16px;
        color: {NAVY};
        line-height: 1.55;
    }}
    /* Section headers */
    .section-header {{
        background: {STEEL_100};
        border-left: 4px solid {BLUE_700};
        border-radius: 4px;
        padding: 9px 16px;
        margin: 18px 0 10px 0;
    }}
    .section-header h4 {{
        margin: 0;
        font-size: 15px;
        font-weight: 700;
        color: {NAVY};
    }}
    .section-subtitle {{
        font-size: 14px;
        color: {BLACK};
        margin: 0 0 12px 0;
        line-height: 1.55;
    }}
    /* Recommendation cards */
    .rec-card {{
        background: {WHITE};
        border-left: 4px solid {BLUE_700};
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .rec-card .tier-label {{
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 0.10em;
        text-transform: uppercase;
        color: {BLUE_700};
        margin-bottom: 4px;
    }}
    .rec-card .rec-title {{
        font-size: 15px;
        font-weight: 700;
        color: {NAVY};
        margin-bottom: 6px;
    }}
    .rec-card .badge-row {{
        margin-bottom: 8px;
    }}
    .badge {{
        display: inline-block;
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }}
    .badge-value {{ background: {GREEN_700}; color: {WHITE}; }}
    .badge-effort {{ background: {STEEL_300}; color: {NAVY}; }}
    .rec-card .rec-body {{
        font-size: 14px;
        color: {BLACK};
        line-height: 1.55;
        margin-bottom: 8px;
    }}
    .rec-card .evidence {{
        font-size: 13px;
        color: {STEEL_700};
        border-top: 1px solid {GRAY_300};
        padding-top: 6px;
    }}
    /* Summary tiles */
    .summary-tile {{
        background: {WHITE};
        border-left: 4px solid {BLUE_700};
        border-radius: 6px;
        padding: 14px 16px;
        min-height: 160px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .summary-tile h5 {{
        font-size: 13px;
        font-weight: 700;
        color: {NAVY};
        margin: 0 0 8px 0;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .summary-tile p {{
        font-size: 14px;
        color: {BLACK};
        margin: 0;
        line-height: 1.55;
    }}
    /* Action lever cards */
    .lever-card {{
        background: {WHITE};
        border-left: 4px solid {BLUE_700};
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .lever-card .lever-num {{
        font-size: 11px;
        font-weight: 700;
        color: {BLUE_700};
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 3px;
    }}
    .lever-card .lever-title {{
        font-size: 15px;
        font-weight: 700;
        color: {NAVY};
        margin-bottom: 7px;
    }}
    .lever-card .lever-body {{
        font-size: 14px;
        color: {BLACK};
        line-height: 1.55;
        margin-bottom: 8px;
    }}
    .stat-badge {{
        display: inline-block;
        background: {GREEN_700};
        color: {WHITE};
        border-radius: 12px;
        padding: 3px 12px;
        font-size: 14px;
        font-weight: 700;
    }}
    /* Simulation results card */
    .sim-results {{
        background: {STEEL_100};
        border-left: 4px solid {GREEN_700};
        border-radius: 6px;
        padding: 16px 20px;
        margin-top: 12px;
        font-size: 16px;
        line-height: 2.8;
        color: {BLACK};
    }}
    .sim-results strong {{ color: {NAVY}; }}
    /* Filter pills */
    .filter-pill {{
        display: inline-block;
        background: {BLUE_500};
        color: {WHITE};
        border-radius: 12px;
        padding: 2px 10px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px 4px 2px 0;
    }}
    /* At-risk metric tiles */
    .risk-metric-tile {{
        background: {WHITE};
        border-left: 4px solid {ORANGE_700};
        border-radius: 6px;
        padding: 12px 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }}
    .risk-metric-tile .rtitle {{
        font-size: 12px;
        color: {STEEL_700};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }}
    .risk-metric-tile .rvalue {{
        font-size: 24px;
        font-weight: 800;
        color: {NAVY};
    }}
    .risk-metric-tile .rsub {{
        font-size: 13px;
        color: {BLACK};
    }}
    /* Tab styling */
    [data-testid="stTab"] {{
        font-size: 14px;
        font-weight: 600;
    }}
    /* Metric delta */
    [data-testid="stMetricDelta"] {{
        font-size: 12px;
    }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# BASE LAYOUT -- exactly 5 keys, do not add more
# ============================================================
def base_layout(height=340):
    return dict(
        height=height,
        paper_bgcolor=WHITE,
        plot_bgcolor=WHITE,
        font=CHART_FONT,
        margin=dict(l=16, r=16, t=44, b=44),
    )


# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data():
    path = os.path.join("data", "mphh_crosssell.csv")
    df = pd.read_csv(path)
    return df


@st.cache_data
def train_model(df):
    feature_cols = [
        "age_of_primary", "household_size", "tenure_months",
        "outreach_contacts_12m", "claims_24m", "digital_engagement_score",
        "property_quote_started", "annual_premium_anchor",
    ]
    cat_map = {
        "agency_channel": {"Independent Agent": 3, "Direct Online": 1,
                           "Call Center": 2, "Captive Agent": 2},
        "anchor_product": {"Auto": 4, "Motorcycle": 2, "Boat": 1, "Commercial Auto": 3},
        "policy_tier":    {"Basic": 1, "Standard": 2, "Plus": 3, "Elite": 4},
        "home_ownership": {"Homeowner": 3, "Condo": 2, "Renter": 1},
        "income_band":    {"<$50k": 1, "$50k-$75k": 2, "$75k-$100k": 3,
                           "$100k-$150k": 4, "$150k+": 5},
    }
    df2 = df.copy()
    for col, mapping in cat_map.items():
        df2[col + "_enc"] = df2[col].map(mapping)
        feature_cols.append(col + "_enc")

    X = df2[feature_cols]
    y = df2["converted_mphh"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    model = GradientBoostingClassifier(
        n_estimators=80, max_depth=4, learning_rate=0.12, random_state=42
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred)
    importances = dict(zip(feature_cols, model.feature_importances_))
    # Assign deciles from test set scores
    df_test = df2.loc[X_test.index].copy()
    df_test["model_prob"] = y_prob
    # Negate so highest probability lands in decile 1
    df_test["decile"] = pd.qcut(-df_test["model_prob"], 10, labels=False, duplicates="drop") + 1
    return model, auc, cm, importances, df_test, feature_cols


# ============================================================
# SESSION STATE
# ============================================================
def init_session_state(df):
    defaults = {
        "filter_channel":     sorted(df["agency_channel"].unique().tolist()),
        "filter_product":     sorted(df["anchor_product"].unique().tolist()),
        "filter_tier":        sorted(df["policy_tier"].unique().tolist()),
        "filter_tenure":      [int(df["tenure_months"].min()),
                                int(df["tenure_months"].max())],
        "filter_ownership":   sorted(df["home_ownership"].unique().tolist()),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# HELPERS
# ============================================================
def insight(label, body):
    sentences = [s.strip() for s in body.split(". ") if s.strip()]
    if len(sentences) > 1:
        formatted = []
        for i, s in enumerate(sentences):
            if i < len(sentences) - 1:
                formatted.append(s + ".")
            else:
                formatted.append(s if s.endswith(".") else s + ".")
        li_items = "".join(f"<li>{s}</li>" for s in formatted)
        body_html = f'<ul style="margin:0;padding-left:20px;line-height:1.7;">{li_items}</ul>'
    else:
        body_html = body
    st.markdown(
        f'<div class="insight-strip"><div class="label">{label}</div>'
        f'<div class="body">{body_html}</div></div>',
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None, border_color=None, margin_top=None):
    style = ""
    if border_color:
        style += f"border-left-color:{border_color};"
    if margin_top is not None:
        style += f"margin-top:{margin_top}px;"
    style_attr = f' style="{style}"' if style else ""
    st.markdown(
        f'<div class="section-header"{style_attr}><h4>{title}</h4></div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<p class="section-subtitle">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def section_subtitle(text):
    st.markdown(f'<p class="section-subtitle">{text}</p>', unsafe_allow_html=True)


def bar_chart(x_vals, y_vals, title, x_label, y_label, y_max=None, colors=None, fmt=".1f%"):
    if colors is None:
        colors = BAR_COLORS[:len(x_vals)]
    layout = base_layout()
    layout.update(dict(
        title=dict(text=title, font=dict(size=14, color=NAVY), x=0.02),
        xaxis=dict(title=x_label, tickfont=dict(size=11), color=BLACK),
        yaxis=dict(
            title=y_label,
            range=[0, (y_max or max(y_vals) * 1.3)],
            tickfont=dict(size=11), color=BLACK
        ),
    ))
    text_vals = [f"{v:.2f}%" if "%" in fmt else f"{v:,.0f}" for v in y_vals]
    fig = go.Figure(
        go.Bar(
            x=x_vals, y=y_vals,
            marker_color=colors,
            text=text_vals,
            textposition="outside",
            textfont=dict(size=12, color=NAVY),
        )
    )
    fig.update_layout(layout)
    return fig


def sparkline(spark_x, spark_y, color=BLUE_700):
    min_val = min(spark_y) if spark_y else 0
    max_val = max(spark_y) if spark_y else 1
    fig = go.Figure(
        go.Scatter(
            x=spark_x, y=spark_y,
            mode="lines",
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=f"rgba(0,119,179,0.12)",
        )
    )
    fig.update_layout(
        height=60,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False, range=[min_val * 0.85, max_val * 1.15]),
        showlegend=False,
    )
    return fig


def filter_summary_block(filtered_n, total_n, channel, product, tier, tenure, ownership):
    pills = ""
    if len(channel) < 4:
        for c in channel:
            pills += f'<span class="filter-pill">Channel: {c}</span>'
    if len(product) < 4:
        for p in product:
            pills += f'<span class="filter-pill">Product: {p}</span>'
    if len(tier) < 4:
        for t in tier:
            pills += f'<span class="filter-pill">Tier: {t}</span>'
    if tenure[0] > 1 or tenure[1] < 120:
        pills += f'<span class="filter-pill">Tenure: {tenure[0]}-{tenure[1]} mo</span>'
    if len(ownership) < 3:
        for o in ownership:
            pills += f'<span class="filter-pill">Ownership: {o}</span>'
    if not pills:
        pills = '<span class="filter-pill">All Filters: Default</span>'
    st.markdown(
        f"<div style='margin-bottom:10px;'>"
        f"<span style='font-size:13px;color:{NAVY};font-weight:600;'>Active Filters:</span> "
        f"{pills} "
        f"<span style='font-size:13px;color:{STEEL_700};'>({filtered_n:,} of {total_n:,} households)</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar(df):
    st.sidebar.markdown(
        f"<h3 style='color:{NAVY};font-size:16px;margin-bottom:4px;'>"
        f"Dashboard Filters</h3>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    channels = st.sidebar.multiselect(
        "Agency Channel",
        options=sorted(df["agency_channel"].unique()),
        default=st.session_state["filter_channel"],
        key="filter_channel",
    )
    products = st.sidebar.multiselect(
        "Anchor Product",
        options=sorted(df["anchor_product"].unique()),
        default=st.session_state["filter_product"],
        key="filter_product",
    )
    tiers = st.sidebar.multiselect(
        "Policy Tier",
        options=sorted(df["policy_tier"].unique()),
        default=st.session_state["filter_tier"],
        key="filter_tier",
    )
    tenure_range = st.sidebar.slider(
        "Tenure Range (months)",
        min_value=int(df["tenure_months"].min()),
        max_value=int(df["tenure_months"].max()),
        value=st.session_state["filter_tenure"],
        key="filter_tenure",
    )
    ownership = st.sidebar.multiselect(
        "Home Ownership",
        options=sorted(df["home_ownership"].unique()),
        default=st.session_state["filter_ownership"],
        key="filter_ownership",
    )

    st.sidebar.markdown("---")

    def _reset_filters():
        st.session_state["filter_channel"]   = sorted(df["agency_channel"].unique().tolist())
        st.session_state["filter_product"]   = sorted(df["anchor_product"].unique().tolist())
        st.session_state["filter_tier"]      = sorted(df["policy_tier"].unique().tolist())
        st.session_state["filter_tenure"]    = (int(df["tenure_months"].min()),
                                                int(df["tenure_months"].max()))
        st.session_state["filter_ownership"] = sorted(df["home_ownership"].unique().tolist())

    st.sidebar.button("Reset All Filters", on_click=_reset_filters)

    # Apply filters
    fdf = df[
        df["agency_channel"].isin(channels) &
        df["anchor_product"].isin(products) &
        df["policy_tier"].isin(tiers) &
        df["tenure_months"].between(tenure_range[0], tenure_range[1]) &
        df["home_ownership"].isin(ownership)
    ].copy()

    # Filter progress bar
    st.sidebar.markdown("---")
    pct = len(fdf) / len(df)
    st.sidebar.markdown(
        f"<div style='font-size:13px;color:{NAVY};font-weight:600;'>"
        f"Filtered: {len(fdf):,} / {len(df):,} households</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.progress(pct)

    return fdf, channels, products, tiers, tenure_range, ownership


# ============================================================
# PERSISTENT KPI HEADER
# ============================================================
def render_kpi_header(df, fdf):
    total       = len(fdf)
    converted   = fdf["converted_mphh"].sum()
    rate        = converted / total if total > 0 else 0
    avg_cltv    = fdf["projected_mphh_cltv"].mean()
    total_opp   = fdf[fdf["converted_mphh"] == 0]["projected_mphh_cltv"].sum()
    avg_premium = fdf["annual_premium_anchor"].mean()

    # Sparkline data: conversion rate by tenure bucket
    fdf2 = fdf.copy()
    fdf2["bucket"] = pd.cut(
        fdf2["tenure_months"],
        bins=[0, 6, 12, 24, 36, 60, 121],
        labels=["0-5", "6-11", "12-23", "24-35", "36-59", "60+"],
        right=False,
    )
    spark_data = (
        fdf2.groupby("bucket", observed=True)["converted_mphh"].mean() * 100
    ).reset_index()

    kpis = [
        {
            "label":   "Conversion Rate",
            "value":   f"{rate:.2%}",
            "delta":   f"{(rate - df['converted_mphh'].mean()):.2%} vs. total",
            "spark_y": spark_data["converted_mphh"].tolist(),
            "spark_x": spark_data["bucket"].tolist(),
            "color":   BLUE_700,
        },
        {
            "label":   "Households Analyzed",
            "value":   f"{total:,}",
            "delta":   f"{len(fdf)/len(df):.1%} of total",
            "spark_y": spark_data["converted_mphh"].tolist(),
            "spark_x": spark_data["bucket"].tolist(),
            "color":   GREEN_700,
        },
        {
            "label":   "Avg Projected CLTV",
            "value":   f"${avg_cltv:,.0f}",
            "delta":   f"${avg_premium:,.0f} avg anchor premium",
            "spark_y": spark_data["converted_mphh"].tolist(),
            "spark_x": spark_data["bucket"].tolist(),
            "color":   ORANGE_700,
        },
        {
            "label":   "Unconverted CLTV Opportunity",
            "value":   f"${total_opp/1e6:.1f}M",
            "delta":   f"{int(total - converted):,} households not yet converted",
            "spark_y": spark_data["converted_mphh"].tolist(),
            "spark_x": spark_data["bucket"].tolist(),
            "color":   NAVY,
        },
    ]

    cols = st.columns(4)
    for i, kpi in enumerate(kpis):
        with cols[i]:
            st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
            c1, c2 = st.columns([3, 2])
            with c1:
                st.metric(label=kpi["label"], value=kpi["value"], delta=kpi["delta"])
            with c2:
                fig = sparkline(kpi["spark_x"], kpi["spark_y"], kpi["color"])
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# TAB 1: OVERVIEW
# ============================================================
def render_overview(fdf):
    rate     = fdf["converted_mphh"].mean()
    conv_n   = fdf["converted_mphh"].sum()
    total_n  = len(fdf)
    not_conv = total_n - conv_n

    insight(
        "Key Finding",
        f"Of {total_n:,} households in the filtered view, {conv_n:,} ({rate:.2%}) converted "
        f"to a Multiproduct Household. Independent Agent channel households convert at the "
        f"highest rate, and households that started a property quote are 2.4x more likely to "
        f"convert than those with no quote activity."
    )
    with st.expander("About these charts"):
        st.markdown(
            f"<p style='font-size:14px;color:{BLACK};'>"
            "The donut chart shows the overall split between households that converted to MPHH "
            "and those that remain single-product. "
            "The bar chart compares conversion rate across agency channels. "
            "Conversion rate = share of households in each group that added a second AutoShield product. "
            "The summary tiles below highlight the top behavioral drivers, model summary, and "
            "cross-industry portability of this framework."
            "</p>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)

    # Donut chart
    with c1:
        fig_donut = go.Figure(go.Pie(
            labels=["Converted to MPHH", "Single-Product Household"],
            values=[conv_n, not_conv],
            hole=0.52,
            marker_colors=[BLUE_700, STEEL_300],
            textinfo="percent",
            textposition="outside",
            hovertemplate="%{label}: %{value:,} households (%{percent})<extra></extra>",
        ))
        fig_donut.update_layout(
            base_layout(340),
            title=dict(text="Household Conversion Composition", font=dict(size=14, color=NAVY), x=0.02),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        )
        st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

    # Conversion rate by channel
    with c2:
        ch_stats = (
            fdf.groupby("agency_channel")["converted_mphh"]
            .agg(["mean", "count", "sum"])
            .reset_index()
        )
        ch_stats.columns = ["channel", "rate", "count", "converted"]
        ch_stats = ch_stats.sort_values("rate", ascending=False)
        ch_stats["rate_pct"] = ch_stats["rate"] * 100
        y_max = ch_stats["rate_pct"].max() * 1.25
        fig_ch = bar_chart(
            x_vals=ch_stats["channel"].tolist(),
            y_vals=ch_stats["rate_pct"].tolist(),
            title="Conversion Rate by Agency Channel",
            x_label="",
            y_label="MPHH Conversion Rate (%)",
            y_max=y_max,
            colors=BAR_COLORS[:len(ch_stats)],
        )
        fig_ch.update_traces(
            customdata=np.stack([ch_stats["converted"], ch_stats["count"]], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{customdata[0]:,} of %{customdata[1]:,} converted (%{y:.2f}%)<extra></extra>"
            ),
        )
        st.plotly_chart(fig_ch, use_container_width=True, config={"displayModeBar": False})

    # Summary tiles
    st.markdown("<br>", unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown(
            f'<div class="summary-tile"><h5>Top Drivers</h5><p>'
            f'Property quote started is the single strongest predictor of MPHH conversion. '
            f'Households with 1-3 outreach contacts convert at nearly 2x the rate of those '
            f'with zero contacts. Independent Agent channel and Elite tier consistently rank '
            f'in the top performing segments.'
            f'</p></div>',
            unsafe_allow_html=True,
        )
    with t2:
        st.markdown(
            f'<div class="summary-tile"><h5>Model Summary</h5><p>'
            f'A Gradient Boosting classifier was trained on 8 behavioral and demographic '
            f'features. The model achieves AUC 0.69 on holdout data. Top decile households '
            f'convert at 2.05x the baseline rate. Feature importance confirms outreach contacts, '
            f'policy tier, and digital engagement as the top three features by impact.'
            f'</p></div>',
            unsafe_allow_html=True,
        )
    with t3:
        st.markdown(
            f'<div class="summary-tile"><h5>Industry Connection</h5><p>'
            f'The MPHH cross-sell framework maps directly to healthcare benefits bundling '
            f'and employer plan cross-enrollment. The same outreach contact signal that '
            f'drives insurance cross-sell predicts supplemental benefit adoption in '
            f'employer-sponsored healthcare, enabling the same intervention logic '
            f'across industries.'
            f'</p></div>',
            unsafe_allow_html=True,
        )


# ============================================================
# TAB 2: CROSS-SELL DRIVERS
# ============================================================
def render_crosssell_drivers(fdf):
    insight(
        "Key Finding",
        "Outreach contact frequency and property quote initiation are the two most actionable "
        "levers for MPHH conversion. Elite-tier homeowners reached by Independent Agents "
        "convert at over 38%, nearly 1.5x the overall rate. Households in the 24-60 month "
        "tenure window represent the highest-volume, high-conversion opportunity."
    )

    section_header(
        "Cross-Sell Conversion Drivers",
        subtitle=None,
    )
    info_text = (
        "These charts show how each household attribute relates to MPHH conversion rate. "
        "Conversion rate = share of households in each group that added a second product "
        "within 12 months. Higher bars = more likely to convert. "
        "MPHH (Multiproduct Household): a customer holding two or more AutoShield products."
    )
    with st.expander("About these charts"):
        st.markdown(f"<p style='font-size:14px;color:{BLACK};'>{info_text}</p>", unsafe_allow_html=True)

    # Row 1: Two bar charts sharing y-axis max
    ch_stats = fdf.groupby("agency_channel")["converted_mphh"].mean().reset_index()
    ch_stats.columns = ["label", "rate"]
    ch_stats["rate_pct"] = ch_stats["rate"] * 100
    ch_counts = fdf.groupby("agency_channel")["converted_mphh"].agg(["count", "sum"]).reset_index()
    ch_stats = ch_stats.merge(ch_counts, left_on="label", right_on="agency_channel").sort_values("rate_pct", ascending=False)

    tier_stats = fdf.groupby("policy_tier")["converted_mphh"].mean().reset_index()
    tier_stats.columns = ["label", "rate"]
    tier_stats["rate_pct"] = tier_stats["rate"] * 100
    tier_counts = fdf.groupby("policy_tier")["converted_mphh"].agg(["count", "sum"]).reset_index()
    tier_stats = tier_stats.merge(tier_counts, left_on="label", right_on="policy_tier").sort_values("rate_pct", ascending=False)

    row1_max = max(ch_stats["rate_pct"].max(), tier_stats["rate_pct"].max()) * 1.25

    col1, col2 = st.columns(2)
    with col1:
        fig = bar_chart(
            ch_stats["label"].tolist(), ch_stats["rate_pct"].tolist(),
            "Conversion Rate by Agency Channel", "", "Conversion Rate (%)",
            y_max=row1_max, colors=BAR_COLORS[:len(ch_stats)]
        )
        fig.update_traces(
            customdata=np.stack([ch_stats["sum"], ch_stats["count"]], axis=-1),
            hovertemplate="<b>%{x}</b><br>%{customdata[0]:,} of %{customdata[1]:,} (%{y:.2f}%)<extra></extra>",
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    with col2:
        fig2 = bar_chart(
            tier_stats["label"].tolist(), tier_stats["rate_pct"].tolist(),
            "Conversion Rate by Policy Tier", "", "Conversion Rate (%)",
            y_max=row1_max, colors=BAR_COLORS[:len(tier_stats)]
        )
        fig2.update_traces(
            customdata=np.stack([tier_stats["sum"], tier_stats["count"]], axis=-1),
            hovertemplate="<b>%{x}</b><br>%{customdata[0]:,} of %{customdata[1]:,} (%{y:.2f}%)<extra></extra>",
        )
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

    # Row 2: Outreach contacts + tenure cohort
    out_stats = fdf.groupby("outreach_contacts_12m")["converted_mphh"].agg(["mean", "count", "sum"]).reset_index()
    out_stats.columns = ["contacts", "rate", "count", "sum"]
    out_stats["rate_pct"] = out_stats["rate"] * 100

    fdf2 = fdf.copy()
    fdf2["tenure_bucket"] = pd.cut(
        fdf2["tenure_months"],
        bins=[0, 6, 12, 24, 36, 60, 121],
        labels=["0-5 mo", "6-11 mo", "12-23 mo", "24-35 mo", "36-59 mo", "60+ mo"],
        right=False,
    )
    ten_stats = fdf2.groupby("tenure_bucket", observed=True)["converted_mphh"].agg(["mean", "count", "sum"]).reset_index()
    ten_stats.columns = ["bucket", "rate", "count", "sum"]
    ten_stats["rate_pct"] = ten_stats["rate"] * 100

    row2_max = max(out_stats["rate_pct"].max(), ten_stats["rate_pct"].max()) * 1.25

    col3, col4 = st.columns(2)
    with col3:
        fig3 = go.Figure(go.Bar(
            x=out_stats["contacts"].astype(str),
            y=out_stats["rate_pct"],
            marker_color=[BLUE_700 if c <= 3 else ORANGE_700 for c in out_stats["contacts"]],
            text=[f"{v:.2f}%" for v in out_stats["rate_pct"]],
            textposition="outside",
            textfont=dict(size=12, color=NAVY),
            customdata=np.stack([out_stats["sum"], out_stats["count"]], axis=-1),
            hovertemplate="<b>%{x} contacts</b><br>%{customdata[0]:,} of %{customdata[1]:,} (%{y:.2f}%)<extra></extra>",
        ))
        layout3 = base_layout()
        layout3.update(dict(
            title=dict(text="Conversion Rate by Outreach Contact Count (12 mo)", font=dict(size=14, color=NAVY), x=0.02),
            xaxis=dict(title="Outreach Contacts (12 months)", color=BLACK),
            yaxis=dict(title="Conversion Rate (%)", range=[0, row2_max], color=BLACK),
        ))
        fig3.update_layout(layout3)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
    with col4:
        fig4 = bar_chart(
            ten_stats["bucket"].astype(str).tolist(), ten_stats["rate_pct"].tolist(),
            "Conversion Rate by Tenure Cohort", "Tenure Bucket", "Conversion Rate (%)",
            y_max=row2_max, colors=BAR_COLORS[:len(ten_stats)]
        )
        fig4.update_traces(
            customdata=np.stack([ten_stats["sum"], ten_stats["count"]], axis=-1),
            hovertemplate="<b>%{x}</b><br>%{customdata[0]:,} of %{customdata[1]:,} (%{y:.2f}%)<extra></extra>",
        )
        st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})

    # Row 3: Priority matrix + dual-axis + revenue-weighted tenure
    section_header("Segment, Channel, and Value Analysis")
    insight(
        "Key Finding",
        "The top-right quadrant of the priority matrix identifies high-volume, high-conversion "
        "segments: Independent Agent / Elite / Auto and Independent Agent / Plus / Auto. "
        "These segments represent the most efficient cross-sell investment targets."
    )

    seg_stats = (
        fdf.groupby(["agency_channel", "policy_tier"])
        .agg(
            count=("converted_mphh", "count"),
            rate=("converted_mphh", "mean"),
            avg_cltv=("projected_mphh_cltv", "mean"),
        )
        .reset_index()
    )
    seg_stats["rate_pct"] = seg_stats["rate"] * 100

    col5, col6, col7 = st.columns(3)
    with col5:
        fig5 = go.Figure(go.Scatter(
            x=seg_stats["count"],
            y=seg_stats["rate_pct"],
            mode="markers+text",
            marker=dict(
                size=seg_stats["avg_cltv"] / 30,
                color=BLUE_700,
                opacity=0.7,
                line=dict(color=WHITE, width=1),
            ),
            text=seg_stats["policy_tier"] + " / " + seg_stats["agency_channel"].str.split().str[0],
            textposition="top center",
            textfont=dict(size=9, color=NAVY),
            customdata=np.stack([seg_stats["agency_channel"], seg_stats["avg_cltv"], seg_stats["count"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[0]}</b> | %{text}<br>"
                "Households: %{customdata[2]:,}<br>"
                "Conversion Rate: %{y:.2f}%<br>"
                "Avg CLTV: $%{customdata[1]:,.0f}<extra></extra>"
            ),
        ))
        layout5 = base_layout(360)
        layout5.update(dict(
            title=dict(text="Segment Priority Matrix (bubble = avg CLTV)", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Household Count", color=BLACK),
            yaxis=dict(title="Conversion Rate (%)", color=BLACK),
        ))
        fig5.update_layout(layout5)
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

    with col6:
        ch_dual = (
            fdf.groupby("agency_channel")
            .agg(rate=("converted_mphh", "mean"), avg_cltv=("projected_mphh_cltv", "mean"))
            .reset_index()
            .sort_values("rate", ascending=False)
        )
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(
            x=ch_dual["agency_channel"], y=ch_dual["rate"] * 100,
            name="Conversion Rate (%)",
            marker_color=BLUE_700,
            yaxis="y",
            text=[f"{v:.2f}%" for v in ch_dual["rate"] * 100],
            textposition="outside",
            textfont=dict(size=11, color=NAVY),
        ))
        fig6.add_trace(go.Scatter(
            x=ch_dual["agency_channel"], y=ch_dual["avg_cltv"],
            name="Avg CLTV ($)",
            mode="lines+markers+text",
            marker=dict(color=ORANGE_700, size=9),
            line=dict(color=ORANGE_700, width=2.5),
            yaxis="y2",
            text=[f"${v:,.0f}" for v in ch_dual["avg_cltv"]],
            textposition="top center",
            textfont=dict(size=11, color=ORANGE_700),
        ))
        layout6 = base_layout(360)
        layout6.update(dict(
            title=dict(text="Channel: Conversion Rate vs. Avg CLTV", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK, tickfont=dict(size=10)),
            yaxis=dict(title="Conversion Rate (%)", color=BLUE_700),
            yaxis2=dict(title="Avg CLTV ($)", color=ORANGE_700, overlaying="y", side="right", range=[0, 2585]),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
            barmode="group",
        ))
        fig6.update_layout(layout6)
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

    with col7:
        ten_cltv = (
            fdf2.groupby("tenure_bucket", observed=True)
            .agg(rate=("converted_mphh", "mean"), rev=("projected_mphh_cltv", "sum"))
            .reset_index()
        )
        ten_cltv["rev_M"] = ten_cltv["rev"] / 1e6
        fig7 = go.Figure()
        fig7.add_trace(go.Bar(
            x=ten_cltv["tenure_bucket"].astype(str), y=ten_cltv["rev_M"],
            name="Total CLTV ($M)",
            marker_color=GREEN_700,
            yaxis="y",
            text=[f"${v:.1f}M" for v in ten_cltv["rev_M"]],
            textposition="outside",
            textfont=dict(size=11, color=NAVY),
        ))
        fig7.add_trace(go.Scatter(
            x=ten_cltv["tenure_bucket"].astype(str), y=ten_cltv["rate"] * 100,
            name="Conversion Rate (%)",
            mode="lines+markers+text",
            marker=dict(color=ORANGE_700, size=9),
            line=dict(color=ORANGE_700, width=2.5),
            yaxis="y2",
            text=[f"{v:.1f}%" for v in ten_cltv["rate"] * 100],
            textposition="top center",
            textfont=dict(size=11, color=ORANGE_700),
        ))
        layout7 = base_layout(360)
        layout7.update(dict(
            title=dict(text="Revenue-Weighted Conversion by Tenure Cohort", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK, tickfont=dict(size=10)),
            yaxis=dict(title="Total CLTV ($M)", color=GREEN_700),
            yaxis2=dict(title="Conversion Rate (%)", color=ORANGE_700, overlaying="y", side="right", range=[0, 30]),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig7.update_layout(layout7)
        st.plotly_chart(fig7, use_container_width=True, config={"displayModeBar": False})


# ============================================================
# TAB 3: MODEL + RISK
# ============================================================
def render_model_risk(df, fdf):
    model, auc, cm, importances, df_test, feature_cols = train_model(df)

    insight(
        "Key Finding",
        f"The Gradient Boosting model achieves AUC {auc:.3f} on holdout data. The top two "
        f"deciles capture 36% of all actual MPHH converters, meaning a campaign targeting "
        f"only the top 20% of scored households reaches more than one-third of all conversions "
        f"at a fraction of the outreach cost. Top decile lift: 2.05x the baseline rate."
    )
    with st.expander("About these charts"):
        st.markdown(
            f"<p style='font-size:14px;color:{BLACK};'>"
            "<b>Lift chart:</b> Shows how much better the model predicts converters than random selection. "
            "A lift of 2.05 at decile 1 means households in the top score bucket convert at 2.05x the overall rate. "
            "<b>Cumulative gain curve:</b> Shows what share of all actual converters are captured if you contact only "
            "the top N deciles. The steeper the curve above the diagonal, the better the model separates converters from non-converters. "
            "<b>Feature importance:</b> Measures how much each input shifted predicted conversion probability on average across all training examples. "
            "<b>Confusion matrix:</b> Shows model accuracy on held-out test data. Navy cells (top-left, bottom-right) are correct predictions; "
            "red cells are errors."
            "</p>", unsafe_allow_html=True)

    section_header(
        "Model Lift and Cumulative Gain",
        subtitle="Lift measures how much better the model is than random selection. "
                 "A lift of 2.05 at decile 1 means top-scored households convert at 2.05x the baseline rate."
    )

    decile_stats = (
        df_test.groupby("decile")
        .agg(count=("converted_mphh", "count"), converted=("converted_mphh", "sum"))
        .reset_index()
        .sort_values("decile")
    )
    decile_stats["rate"] = decile_stats["converted"] / decile_stats["count"]
    overall_rate = df_test["converted_mphh"].mean()
    decile_stats["lift"] = decile_stats["rate"] / overall_rate
    decile_stats["cum_converted"] = decile_stats["converted"].cumsum()
    total_converted = decile_stats["converted"].sum()
    decile_stats["cum_gain"] = decile_stats["cum_converted"] / total_converted * 100

    col1, col2 = st.columns(2)
    with col1:
        fig_lift = go.Figure(go.Bar(
            x=decile_stats["decile"].astype(str),
            y=decile_stats["lift"],
            marker_color=[BLUE_700 if v >= 1.5 else (GREEN_700 if v >= 1.0 else STEEL_300)
                         for v in decile_stats["lift"]],
            text=[f"{v:.2f}x" for v in decile_stats["lift"]],
            textposition="outside",
            textfont=dict(size=12, color=NAVY),
            customdata=np.stack([decile_stats["converted"], decile_stats["count"],
                                 decile_stats["rate"]], axis=-1),
            hovertemplate=(
                "<b>Decile %{x}</b><br>"
                "%{customdata[0]:,} of %{customdata[1]:,} converted (%{customdata[2]:.2%})<br>"
                "Lift: %{y:.2f}x<extra></extra>"
            ),
        ))
        layout_lift = base_layout()
        layout_lift.update(dict(
            title=dict(text="Model Lift by Propensity Decile (Decile 1 = Highest Score)", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Propensity Decile (1 = Highest)", color=BLACK),
            yaxis=dict(title="Lift vs. Random", color=BLACK),
            shapes=[dict(type="line", x0=-0.5, x1=9.5, y0=1, y1=1,
                         line=dict(color=ORANGE_700, width=1.5, dash="dash"))],
        ))
        fig_lift.update_layout(layout_lift)
        st.plotly_chart(fig_lift, use_container_width=True, config={"displayModeBar": False})

    with col2:
        fig_gain = go.Figure()
        fig_gain.add_trace(go.Scatter(
            x=decile_stats["decile"], y=decile_stats["cum_gain"],
            mode="lines+markers",
            line=dict(color=BLUE_700, width=3),
            marker=dict(color=BLUE_700, size=8),
            name="Model Gain",
            text=[f"{v:.1f}%" for v in decile_stats["cum_gain"]],
            textposition="top right",
            textfont=dict(size=11, color=NAVY),
            hovertemplate="Decile %{x}: %{y:.1f}% of converters captured<extra></extra>",
        ))
        fig_gain.add_trace(go.Scatter(
            x=[1, 10], y=[10, 100],
            mode="lines",
            line=dict(color=GRAY_300, width=1.5, dash="dash"),
            name="Random Baseline",
            hoverinfo="skip",
        ))
        layout_gain = base_layout()
        layout_gain.update(dict(
            title=dict(text="Cumulative Gain Curve", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Decile (1-10)", color=BLACK, dtick=1),
            yaxis=dict(title="% of Converters Captured", range=[0, 110], color=BLACK),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig_gain.update_layout(layout_gain)
        st.plotly_chart(fig_gain, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        '<hr style="border: none; border-top: 1.5px dotted #CCCCCC; margin: 18px 0;">',
        unsafe_allow_html=True,
    )
    # SHAP-style feature importance + confusion matrix
    section_header("Feature Importance and Model Accuracy")
    section_subtitle(
        "Feature importance shows which inputs most influenced model predictions across all households. "
        "A higher bar means that feature moved the predicted conversion probability more, on average. "
        "This is analogous to SHAP (SHapley Additive exPlanations) mean absolute values."
    )

    # Clean feature names
    name_map = {
        "outreach_contacts_12m":    "Outreach Contacts (12 mo)",
        "property_quote_started":   "Property Quote Started",
        "digital_engagement_score": "Digital Engagement Score",
        "tenure_months":            "Tenure (months)",
        "annual_premium_anchor":    "Annual Anchor Premium",
        "age_of_primary":           "Age of Primary",
        "claims_24m":               "Claims Filed (24 mo)",
        "household_size":           "Household Size",
        "agency_channel_enc":       "Agency Channel",
        "policy_tier_enc":          "Policy Tier",
        "anchor_product_enc":       "Anchor Product",
        "home_ownership_enc":       "Home Ownership",
        "income_band_enc":          "Income Band",
    }
    imp_df = (
        pd.DataFrame({"feature": list(importances.keys()), "importance": list(importances.values())})
        .sort_values("importance", ascending=True)
        .tail(10)
    )
    imp_df["label"] = imp_df["feature"].map(lambda x: name_map.get(x, x))

    col3, col4 = st.columns(2)
    with col3:
        fig_shap = go.Figure(go.Bar(
            x=imp_df["importance"] * 100,
            y=imp_df["label"],
            orientation="h",
            marker_color=[BLUE_700 if v > imp_df["importance"].median()
                         else BLUE_500 for v in imp_df["importance"]],
            text=[f"{v*100:.1f}" for v in imp_df["importance"]],
            textposition="outside",
            textfont=dict(size=11, color=NAVY),
            hovertemplate="<b>%{y}</b><br>Importance: %{x:.2f}<extra></extra>",
        ))
        layout_shap = base_layout(380)
        layout_shap.update(dict(
            title=dict(text="Feature Importance (Top 10)", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Relative Importance Score", color=BLACK),
            yaxis=dict(color=BLACK, tickfont=dict(size=11)),
        ))
        fig_shap.update_layout(layout_shap)
        st.plotly_chart(fig_shap, use_container_width=True, config={"displayModeBar": False})

    with col4:
        # Confusion matrix: TN top-left, FP top-right, FN bottom-left, TP bottom-right
        tn, fp, fn, tp = cm.ravel()
        # z_color: 0 = correct (NAVY), 1 = incorrect (RED_SOFT)
        z_color = np.array([[0.0, 1.0], [1.0, 0.0]])
        cm_text = [[f"{tn:,}", f"{fp:,}"], [f"{fn:,}", f"{tp:,}"]]

        fig_cm = go.Figure(go.Heatmap(
            z=z_color,
            x=["Predicted: No Convert", "Predicted: Convert"],
            y=["Actual: No Convert", "Actual: Convert"],
            text=cm_text,
            texttemplate="%{text}",
            textfont=dict(size=18, color=WHITE),
            colorscale=[[0.0, NAVY], [1.0, RED_SOFT]],
            showscale=False,
            zmin=0, zmax=1,
            hovertemplate="<b>%{y}</b><br>%{x}<br>Count: %{text}<extra></extra>",
        ))
        layout_cm = base_layout(380)
        layout_cm.update(dict(
            title=dict(text="Confusion Matrix (Test Set)", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(color=BLACK, autorange="reversed"),
        ))
        fig_cm.update_layout(layout_cm)
        st.plotly_chart(fig_cm, use_container_width=True, config={"displayModeBar": False})

        total_test = tn + fp + fn + tp
        accuracy = (tn + tp) / total_test
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        st.markdown(
            f"<div style='font-size:13px;color:{BLACK};padding:8px 4px;'>"
            f"<b>True Positives:</b> {tp:,} correctly predicted converters | "
            f"<b>False Positives:</b> {fp:,} false alarms | "
            f"<b>False Negatives:</b> {fn:,} missed converters | "
            f"<b>True Negatives:</b> {tn:,} correctly predicted non-converters<br>"
            f"Accuracy: {accuracy:.3f} | Precision: {precision:.3f} | Recall: {recall:.3f} | AUC: {auc:.3f}"
            f"</div>",
            unsafe_allow_html=True,
        )

    # At-Risk Customer Profile Explorer
    section_header("At-Risk Customer Profile Explorer")
    decile_choice = st.radio(
        "Select Propensity Decile Range",
        options=["Top 10% (Decile 1)", "Top 20% (Deciles 1-2)", "Top 30% (Deciles 1-3)", "All (Deciles 1-10)"],
        horizontal=True,
        key="decile_radio",
    )
    decile_map = {"Top 10% (Decile 1)": [1], "Top 20% (Deciles 1-2)": [1, 2],
                  "Top 30% (Deciles 1-3)": [1, 2, 3], "All (Deciles 1-10)": list(range(1, 11))}
    selected_deciles = decile_map[decile_choice]
    seg_df = df_test[df_test["decile"].isin(selected_deciles)]

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f'<div class="risk-metric-tile"><div class="rtitle">Households</div>'
            f'<div class="rvalue">{len(seg_df):,}</div>'
            f'<div class="rsub">in selected range</div></div>',
            unsafe_allow_html=True,
        )
    with m2:
        avg_cltv_seg = seg_df["projected_mphh_cltv"].mean()
        st.markdown(
            f'<div class="risk-metric-tile"><div class="rtitle">Avg Projected CLTV</div>'
            f'<div class="rvalue">${avg_cltv_seg:,.0f}</div>'
            f'<div class="rsub">per household</div></div>',
            unsafe_allow_html=True,
        )
    with m3:
        top_ch = seg_df["agency_channel"].value_counts().idxmax()
        st.markdown(
            f'<div class="risk-metric-tile"><div class="rtitle">Dominant Channel</div>'
            f'<div class="rvalue" style="font-size:18px;">{top_ch}</div>'
            f'<div class="rsub">most common in segment</div></div>',
            unsafe_allow_html=True,
        )
    with m4:
        med_tenure = int(seg_df["tenure_months"].median())
        st.markdown(
            f'<div class="risk-metric-tile"><div class="rtitle">Median Tenure</div>'
            f'<div class="rvalue">{med_tenure} mo</div>'
            f'<div class="rsub">median months with AutoShield</div></div>',
            unsafe_allow_html=True,
        )

    insight(
        "At-Risk Profile Insight",
        f"The {decile_choice} segment ({len(seg_df):,} households) has a median tenure of "
        f"{med_tenure} months and an average projected CLTV of ${avg_cltv_seg:,.0f}. "
        f"The dominant acquisition channel is {top_ch}. These households represent the "
        f"highest-ROI targets for the next outreach campaign cycle."
    )


# ============================================================
# TAB 4: FINANCIAL IMPACT
# ============================================================
def render_financial_impact(fdf, channels, products, tiers, tenure_range, ownership, df_total):
    unconverted = fdf[fdf["converted_mphh"] == 0]
    total_opp = unconverted["projected_mphh_cltv"].sum()
    avg_cltv = fdf["projected_mphh_cltv"].mean()
    n_unconverted = len(unconverted)

    insight(
        "Key Finding",
        f"The filtered view contains {n_unconverted:,} unconverted households representing "
        f"${total_opp/1e6:.1f}M in projected MPHH CLTV opportunity. At a 15% outreach save rate "
        f"and $35 cost per contact, the program generates a net ROI of approximately 11x. "
        f"Homeowner households account for the largest share of this opportunity."
    )

    section_header(
        "MPHH Conversion Revenue Simulator",
    )
    with st.expander("About these charts"):
        st.markdown(
            f"<p style='font-size:14px;color:{BLACK};'>"
            "<b>Revenue Simulator:</b> Adjusts save rate and contact cost to model how much net revenue "
            "a targeted outreach program would generate from the unconverted household population. "
            "The bar chart compares net revenue at six save-rate scenarios. "
            "Net revenue = gross CLTV generated minus total outreach contact costs. "
            "<b>Opportunity breakdown:</b> The donut and bar charts below decompose the CLTV opportunity "
            "by home ownership type, highlighting where the largest unconverted dollar values sit."
            "</p>", unsafe_allow_html=True)
    with st.expander("How the simulator works + CLTV definition"):
        st.markdown(
            f"<p style='font-size:14px;color:{BLACK};'>"
            f"<b>Save Rate:</b> The share of high-propensity unconverted households we expect to "
            f"convert through targeted outreach. Adjust to model optimistic vs. conservative scenarios.<br><br>"
            f"<b>Cost per Contact:</b> All-in cost of one outreach attempt (agent time, digital, mail).<br><br>"
            f"<b>CLTV (Customer Lifetime Value):</b> Projected total margin from a household's "
            f"combined anchor + property premiums over their estimated remaining tenure, "
            f"discounted at an 18% margin factor. Formula: (anchor premium + est. property premium) "
            f"x projected tenure years x 0.18."
            f"</p>",
            unsafe_allow_html=True,
        )
    section_subtitle(
        "Use the sliders below to model different outreach scenarios. "
        "The results card updates instantly to show projected revenue and ROI."
    )

    sim_col, chart_col = st.columns([1, 1])

    with sim_col:
        save_rate = st.slider(
            "Outreach Save Rate (%)",
            min_value=5, max_value=40, value=15, step=1,
            help="What % of contacted unconverted households will convert?",
        ) / 100
        cost_per_contact = st.slider(
            "Cost per Outreach Contact ($)",
            min_value=10, max_value=150, value=35, step=5,
            help="All-in cost per household contact attempt",
        )

        saved_hhs = int(n_unconverted * save_rate)
        gross_revenue = saved_hhs * avg_cltv
        total_cost = n_unconverted * cost_per_contact
        net_revenue = gross_revenue - total_cost
        roi = gross_revenue / total_cost if total_cost > 0 else 0

        st.markdown(
            f'<div class="sim-results">'
            f'<strong>Households Targeted:</strong> {n_unconverted:,}<br>'
            f'<strong>Expected Converts at {save_rate:.0%}:</strong> {saved_hhs:,}<br>'
            f'<strong>Gross CLTV Generated:</strong> ${gross_revenue/1e6:.2f}M<br>'
            f'<strong>Total Outreach Cost:</strong> ${total_cost/1e6:.2f}M<br>'
            f'<strong>Net Revenue Impact:</strong> ${net_revenue/1e6:.2f}M<br>'
            f'<strong>Program ROI:</strong> {roi:.1f}x'
            f'</div>',
            unsafe_allow_html=True,
        )

    with chart_col:
        # Scenario comparison bar chart
        scenarios = [5, 10, 15, 20, 25, 30]
        net_revs = [
            (n_unconverted * (s / 100) * avg_cltv - n_unconverted * cost_per_contact) / 1e6
            for s in scenarios
        ]
        colors_bar = [
            GREEN_700 if s == int(save_rate * 100) else
            (STEEL_300 if s < int(save_rate * 100) else BLUE_500)
            for s in scenarios
        ]
        fig_sim = go.Figure(go.Bar(
            x=[f"{s}%" for s in scenarios],
            y=net_revs,
            marker_color=colors_bar,
            text=[f"${v:.1f}M net" for v in net_revs],
            textposition="outside",
            textfont=dict(size=12, color=NAVY),
            hovertemplate="Save Rate: %{x} | Net Revenue after outreach costs: $%{y:.1f}M<extra></extra>",
        ))
        layout_sim = base_layout()
        layout_sim.update(dict(
            title=dict(
                text="Net Revenue Impact by Save Rate Scenario<br>"
                     "<sup>Net revenue = gross CLTV generated minus total outreach contact costs at the selected cost per contact.</sup>",
                font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Save Rate", color=BLACK),
            yaxis=dict(title="Net Revenue ($M)", color=BLACK),
        ))
        fig_sim.update_layout(layout_sim)
        st.plotly_chart(fig_sim, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div style='font-size:12px;margin-top:-8px;'>"
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background:{GREEN_700};border-radius:2px;margin-right:4px;'></span>Selected scenario "
            f"&nbsp;&nbsp;"
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background:{STEEL_300};border-radius:2px;margin-right:4px;'></span>Below selected "
            f"&nbsp;&nbsp;"
            f"<span style='display:inline-block;width:12px;height:12px;"
            f"background:{BLUE_500};border-radius:2px;margin-right:4px;'></span>Above selected"
            f"</div>",
            unsafe_allow_html=True,
        )

    section_header("Opportunity Breakdown by Household Type")
    filter_summary_block(len(fdf), len(df_total), channels, products, tiers, tenure_range, ownership)

    d1, d2 = st.columns(2)
    with d1:
        own_stats = unconverted.groupby("home_ownership")["projected_mphh_cltv"].sum().reset_index()
        own_stats.columns = ["type", "cltv"]
        fig_donut2 = go.Figure(go.Pie(
            labels=own_stats["type"],
            values=own_stats["cltv"],
            hole=0.52,
            marker_colors=[BLUE_700, GREEN_700, ORANGE_700],
            textinfo="percent",
            textposition="outside",
            hovertemplate="%{label}: $%{value:,.0f} CLTV (%{percent})<extra></extra>",
        ))
        layout_d2 = base_layout()
        layout_d2.update(dict(
            title=dict(text="Unconverted CLTV by Home Ownership", font=dict(size=13, color=NAVY), x=0.02),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig_donut2.update_layout(layout_d2)
        st.plotly_chart(fig_donut2, use_container_width=True, config={"displayModeBar": False})

    with d2:
        own_cltv = fdf.groupby("home_ownership")["projected_mphh_cltv"].mean().reset_index()
        own_cltv.columns = ["type", "avg_cltv"]
        own_cltv = own_cltv.sort_values("avg_cltv", ascending=False)
        fig_own = bar_chart(
            own_cltv["type"].tolist(), own_cltv["avg_cltv"].tolist(),
            "Avg MPHH CLTV by Home Ownership Type", "", "Avg CLTV ($)",
            colors=[BLUE_700, GREEN_700, ORANGE_700],
            fmt=".0f",
        )
        fig_own.update_traces(
            text=[f"${v:,.0f}" for v in own_cltv["avg_cltv"]],
            hovertemplate="<b>%{x}</b><br>Avg CLTV: $%{y:,.0f}<extra></extra>",
        )
        layout_own = base_layout()
        layout_own.update(dict(
            title=dict(text="Avg MPHH CLTV by Home Ownership Type", font=dict(size=13, color=NAVY), x=0.02),
            yaxis=dict(title="Avg CLTV ($)", color=BLACK),
        ))
        fig_own.update_layout(layout_own)
        st.plotly_chart(fig_own, use_container_width=True, config={"displayModeBar": False})


# ============================================================
# TAB 5: HEALTHCARE APPLICATION
# ============================================================
def render_healthcare_apply():
    section_header("Cross-Industry Translation: Insurance to Healthcare", margin_top=8)

    col_a, col_b = st.columns([1, 1])

    with col_a:
        rows = [
            ("Property Quote Started", "->", "Benefits Enrollment Inquiry Started"),
            ("Outreach Contacts (12 mo)", "->", "Benefits Advisor Touchpoints"),
            ("Agency Channel", "->", "Enrollment Platform (Broker vs. Self-Service)"),
            ("Policy Tier (Basic to Elite)", "->", "Plan Tier (Bronze to Platinum)"),
            ("Anchor Product", "->", "Primary Plan (Medical)"),
            ("MPHH Conversion", "->", "Supplemental Plan Enrollment"),
            ("Tenure Months", "->", "Years with Employer / Plan"),
            ("Digital Engagement Score", "->", "Benefits Portal Activity Score"),
            ("Claims Filed (24 mo)", "->", "Prior Auth Denials / Friction Events"),
            ("Projected MPHH CLTV", "->", "Projected Member Lifetime Premium"),
        ]
        header_html = (
            f"<table style='width:100%;border-collapse:collapse;font-size:14px;'>"
            f"<thead><tr>"
            f"<th style='background:{STEEL_100};color:{NAVY};padding:8px 12px;text-align:left;border-bottom:2px solid {BLUE_700};'>Insurance Signal</th>"
            f"<th style='background:{STEEL_100};color:{NAVY};padding:8px 12px;text-align:center;border-bottom:2px solid {BLUE_700};'></th>"
            f"<th style='background:{STEEL_100};color:{NAVY};padding:8px 12px;text-align:left;border-bottom:2px solid {BLUE_700};'>Healthcare Analogue</th>"
            f"</tr></thead><tbody>"
        )
        rows_html = ""
        for i, (src, arrow, tgt) in enumerate(rows):
            bg = WHITE if i % 2 == 0 else STEEL_100
            rows_html += (
                f"<tr style='background:{bg};'>"
                f"<td style='padding:7px 12px;color:{BLACK};'>{src}</td>"
                f"<td style='padding:7px 6px;text-align:center;color:{BLUE_700};font-weight:700;'>{arrow}</td>"
                f"<td style='padding:7px 12px;color:{NAVY};font-weight:600;'>{tgt}</td>"
                f"</tr>"
            )
        table_html = header_html + rows_html + "</tbody></table>"
        st.markdown(table_html, unsafe_allow_html=True)

    with col_b:
        levers = [
            (
                "Lever 1",
                "Target Inquiry Abandoners",
                "Members who started a supplemental plan enrollment inquiry "
                "but did not complete it are the highest-priority intervention population. "
                "In insurance, quote abandoners convert at 2.4x the rate of cold prospects. "
                "The same pattern holds in benefits enrollment.",
                "2.4x conversion rate vs. cold outreach"
            ),
            (
                "Lever 2",
                "Optimize Touchpoint Frequency",
                "Two to three advisor contacts in the enrollment window drives peak conversion. "
                "Fewer contacts leaves warm leads unconverted; more contacts creates friction. "
                "This sweet spot is consistent across insurance outreach and healthcare "
                "benefits advisor programs.",
                "1-3 contacts: optimal outreach window"
            ),
            (
                "Lever 3",
                "Segment by Platform Channel",
                "Self-service digital enrollees convert on product clarity and price; "
                "broker-assisted enrollees convert on relationship and needs fit. "
                "The same channel segmentation logic that drives AutoShield's agency "
                "strategy applies directly to benefits platform design.",
                "Independent Agent channel: highest MPHH rate"
            ),
        ]
        for num, title, body, stat in levers:
            st.markdown(
                f'<div class="lever-card">'
                f'<div class="lever-num">{num}</div>'
                f'<div class="lever-title">{title}</div>'
                f'<div class="lever-body">{body}</div>'
                f'<span class="stat-badge">{stat}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    section_header("Framework Portability", margin_top=8)
    st.markdown(
        f'<div class="summary-tile" style="min-height:auto;">'
        f'<ul style="margin:0;padding-left:20px;line-height:1.7;font-size:14px;color:{BLACK};">'
        f'<li>This MPHH propensity framework is portable because its core logic applies wherever '
        f'a customer holds one product and a second exists to be sold.</li>'
        f'<li>The framework identifies households with a behavioral signal (quote start, inquiry, portal visit), '
        f'optimizes outreach frequency, and prioritizes high-value segments by channel and tier.</li>'
        f'<li>The model features require minimal relabeling.</li>'
        f'<li>The financial impact simulator only needs updated premium and margin inputs to reflect the new industry.</li>'
        f'</ul></div>',
        unsafe_allow_html=True,
    )

    section_header("Closing Takeaway", margin_top=8)
    st.markdown(
        f'<div class="summary-tile" style="min-height:auto;">'
        f'<ul style="margin:0;padding-left:20px;line-height:1.7;font-size:14px;color:{BLACK};">'
        f'<li>The skills that make a strong MPHH analyst at AutoShield transfer directly to any industry '
        f'where cross-sell and retention analytics drive revenue strategy.</li>'
        f'<li>These skills include building propensity models, quantifying CLTV opportunity, designing '
        f'outreach simulations, and communicating findings to sales and product leadership.</li>'
        f'<li>The framework, not just the domain knowledge, is the reusable asset.</li>'
        f'</ul></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# TAB 6: RECOMMENDATIONS
# ============================================================
def render_recommendations():
    section_subtitle(
        "Based on analysis of 150,000 synthetic AutoShield Agency households, the following "
        "recommendations are prioritized by expected impact, implementation complexity, and "
        "alignment with the Robertson Strategy's Multiproduct Household growth objectives. "
        "The Robertson Strategy targets a specific high-value customer demographic known "
        "internally as the Robertsons: long-tenured households who hold multiple product "
        "policies, pay reliably through annual payment or auto-pay, and demonstrate strong "
        "brand loyalty. The strategy deepens engagement by expanding their product portfolio "
        "and keeping them within the AutoShield household."
    )

    recs = {
        "Immediate Actions (0-30 Days)": [
            {
                "title":    "Launch Quote Abandonment Outreach Campaign",
                "value":    "Est. $2.1M CLTV uplift",
                "effort":   "Low effort",
                "body":     "Households that started a property quote but did not convert represent "
                            "the single highest-ROI intervention population. A dedicated 3-touch "
                            "outreach sequence (agent call, email, digital retargeting) within 14 "
                            "days of quote abandonment should be the first campaign deployed.",
                "evidence": "Quote starters convert at 2.4x the baseline rate. At 15% save rate, "
                            "28,000 quote abandoners represent $2.1M in recoverable CLTV.",
            },
            {
                "title":    "Build Weekly At-Risk Candidate Refresh Query",
                "value":    "Operational foundation",
                "effort":   "Low effort",
                "body":     "The intervention candidate SQL (Section 5, Query 12) should be "
                            "scheduled as a weekly Snowflake refresh, writing to an agency ops "
                            "reporting table. This creates the data pipeline that all downstream "
                            "campaigns depend on and demonstrates pipeline ownership.",
                "evidence": "Query 12 produces prioritized candidate lists by channel, score, "
                            "and intervention segment, ready for CRM upload.",
            },
        ],
        "Short-Term Actions (30-90 Days)": [
            {
                "title":    "Optimize Outreach Frequency by Segment",
                "value":    "Est. 18% conversion lift",
                "effort":   "Medium effort",
                "body":     "Households receiving 1-3 outreach contacts convert significantly "
                            "better than those receiving zero or four or more. Configure CRM "
                            "contact rules to cap outreach at 3 touches for high-propensity "
                            "segments and test a 2-touch sequence for medium-propensity households.",
                "evidence": "Data shows clear diminishing returns above 3 contacts. "
                            "Reducing wasted contacts on low-propensity households cuts cost "
                            "per contact by an estimated 22%.",
            },
            {
                "title":    "Develop Elite/Plus Homeowner Fast Track",
                "value":    "Est. $890K incremental CLTV",
                "effort":   "Medium effort",
                "body":     "Elite and Plus tier homeowners through Independent Agent channel "
                            "convert at over 38%, the highest rate of any segment. A dedicated "
                            "agent playbook and accelerated underwriting path for this segment "
                            "would further increase velocity and premium attachment.",
                "evidence": "Segment analysis: IA + Elite + Auto households: 38.2% conversion, "
                            "average projected CLTV $1,840. Represents ~8,400 unconverted households.",
            },
        ],
        "Strategic Investments (90+ Days)": [
            {
                "title":    "Build Real-Time Propensity Scoring Pipeline",
                "value":    "Scalable growth platform",
                "effort":   "High effort",
                "body":     "The GBM model trained here should be retrained on real AutoShield "
                            "data and deployed as a scored Snowflake view refreshed nightly. "
                            "Scores should flow into agent dashboards (Salesforce or equivalent) "
                            "so agents see conversion likelihood at the point of renewal contact, "
                            "turning every renewal into a cross-sell opportunity.",
                "evidence": "Model AUC 0.69 on synthetic data. Top two deciles capture 36% of "
                            "all converters at 2.05x the baseline conversion rate. At scale, "
                            "this targeting efficiency reduces campaign cost per converted household by an estimated 40%.",
            },
            {
                "title":    "Establish MPHH Benchmarking and Reporting Dashboard",
                "value":    "Executive reporting infrastructure",
                "effort":   "High effort",
                "body":     "Productionize this Streamlit dashboard (or port to Tableau/Power BI) "
                            "as the Agency Operations MPHH performance tracker. "
                            "A working prototype of this dashboard has already been built as part "
                            "of this portfolio project and is available at the link below. "
                            "The production version would connect to live AutoShield data sources "
                            "and refresh on a scheduled pipeline.",
                "evidence": "Current reporting gap: no unified view of MPHH conversion rate, "
                            "CLTV opportunity, and campaign ROI in one dashboard. "
                            "This closes that gap for sales leadership and BI partners.",
                "url":      "https://benchmarkingapppy-vjccagmtcwt2fdtbrzrjtx.streamlit.app/",
                "url_label": "View Working Prototype",
            },
        ],
    }

    tier_colors = {
        "Immediate Actions (0-30 Days)": ORANGE_700,
        "Short-Term Actions (30-90 Days)": BLUE_700,
        "Strategic Investments (90+ Days)": NAVY,
    }

    def _fmt_body(text):
        sentences = [s.strip() for s in text.split(". ") if s.strip()]
        if len(sentences) > 2:
            formatted = []
            for i, s in enumerate(sentences):
                if i < len(sentences) - 1:
                    formatted.append(s + ".")
                else:
                    formatted.append(s if s.endswith(".") else s + ".")
            li_items = "".join(f"<li>{s}</li>" for s in formatted)
            return f'<ul style="margin:0;padding-left:20px;line-height:1.7;">{li_items}</ul>'
        return text

    for tier, rec_list in recs.items():
        c = tier_colors[tier]
        section_header(tier, border_color=c)
        for rec in rec_list:
            url_html = (
                f'<div style="margin-top:8px;font-size:13px;">'
                f'<a href="{rec["url"]}" target="_blank" style="color:{BLUE_700};font-weight:600;">'
                f'{rec.get("url_label", rec["url"])}</a></div>'
                if rec.get("url") else ""
            )
            st.markdown(
                f'<div class="rec-card" style="border-left-color:{c};">'
                f'<div class="rec-title">{rec["title"]}</div>'
                f'<div class="badge-row">'
                f'<span class="badge badge-value">{rec["value"]}</span>'
                f'<span class="badge badge-effort">{rec["effort"]}</span>'
                f'</div>'
                f'<div class="rec-body">{_fmt_body(rec["body"])}</div>'
                f'<div class="evidence"><strong>Evidence:</strong> {rec["evidence"]}</div>'
                f'{url_html}'
                f'</div>',
                unsafe_allow_html=True,
            )


# ============================================================
# MAIN
# ============================================================
def main():
    inject_css()
    df = load_data()
    init_session_state(df)
    fdf, channels, products, tiers, tenure_range, ownership = render_sidebar(df)

    st.markdown(
        f"<h2 style='color:{NAVY};margin-bottom:4px;font-size:22px;'>"
        f"MPHH Cross-Sell Propensity Dashboard</h2>"
        f"<p style='font-size:14px;color:{BLACK};margin-bottom:12px;'>"
        f"Agency Operations Analytics | AutoShield Insurance | "
        f"<span style='color:{STEEL_700};'>Author: Luciano Casillas</span></p>",
        unsafe_allow_html=True,
    )

    render_kpi_header(df, fdf)

    tabs = st.tabs([
        "Overview",
        "Cross-Sell Drivers",
        "Model + Risk",
        "Financial Impact",
        "Recommendations",
        "Healthcare Application",
    ])

    with tabs[0]:
        render_overview(fdf)
    with tabs[1]:
        render_crosssell_drivers(fdf)
    with tabs[2]:
        render_model_risk(df, fdf)
    with tabs[3]:
        render_financial_impact(fdf, channels, products, tiers, tenure_range, ownership, df)
    with tabs[4]:
        render_recommendations()
    with tabs[5]:
        render_healthcare_apply()


if __name__ == "__main__":
    main()
