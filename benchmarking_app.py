"""
MPHH Benchmarking and Reporting Dashboard
Author: Luciano Casillas
Version: 1.0
---
Agency Operations MPHH performance tracker supporting the Robinson Strategy
reporting cadence. Tracks quarterly MPHH conversion rate vs. target, YoY growth,
cohort retention views, agent leaderboards, and state-level performance.

Tab index:
    render_kpi_header           -- persistent KPI row above all tabs
    render_sidebar              -- all filters
    render_robinson_tracker     -- Tab 1: Robinson Strategy Tracker
    render_yoy_growth           -- Tab 2: YoY Growth
    render_cohort_retention     -- Tab 3: Cohort Retention
    render_agent_leaderboard    -- Tab 4: Agent Leaderboard
    render_state_performance    -- Tab 5: State Performance
    render_pipeline_health      -- Tab 6: Pipeline Health
"""

# ============================================================
# PAGE CONFIG -- must be first Streamlit call
# ============================================================
import streamlit as st
st.set_page_config(
    page_title="MPHH Benchmarking Dashboard",
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

QUARTERS_ORDERED = [
    "2023Q1","2023Q2","2023Q3","2023Q4",
    "2024Q1","2024Q2","2024Q3","2024Q4",
    "2025Q1","2025Q2","2025Q3","2025Q4",
]
TARGET_MAP = {
    "2023Q1": 25.0, "2023Q2": 25.5, "2023Q3": 26.0, "2023Q4": 26.5,
    "2024Q1": 27.0, "2024Q2": 27.5, "2024Q3": 28.0, "2024Q4": 28.5,
    "2025Q1": 29.0, "2025Q2": 29.5, "2025Q3": 30.0, "2025Q4": 30.5,
}

# ============================================================
# GLOBAL CSS
# ============================================================
def inject_css():
    st.markdown(f"""
    <style>
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], section.main {{
        background-color: {WHITE} !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {STEEL_100} !important;
    }}
    .kpi-card {{
        background: {WHITE};
        border-left: 4px solid {BLUE_700};
        border-radius: 6px;
        padding: 12px 16px 10px 16px;
        margin-bottom: 8px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    }}
    .insight-strip {{
        background: {STEEL_100};
        border-left: 4px solid {BLUE_700};
        border-radius: 4px;
        padding: 12px 18px;
        margin-bottom: 14px;
    }}
    .insight-strip .label {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.08em;
        color: {NAVY};
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    .insight-strip .body {{
        font-size: 14px;
        color: {NAVY};
        line-height: 1.55;
    }}
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
    /* Status badges */
    .badge-on-track {{
        display: inline-block;
        background: {GREEN_700};
        color: {WHITE};
        border-radius: 12px;
        padding: 2px 12px;
        font-size: 12px;
        font-weight: 700;
    }}
    .badge-behind {{
        display: inline-block;
        background: {RED_SOFT};
        color: {WHITE};
        border-radius: 12px;
        padding: 2px 12px;
        font-size: 12px;
        font-weight: 700;
    }}
    .badge-neutral {{
        display: inline-block;
        background: {STEEL_300};
        color: {NAVY};
        border-radius: 12px;
        padding: 2px 12px;
        font-size: 12px;
        font-weight: 700;
    }}
    /* Leaderboard rows */
    .lb-row {{
        display: flex;
        align-items: center;
        padding: 9px 14px;
        border-radius: 4px;
        margin-bottom: 5px;
        font-size: 14px;
        color: {BLACK};
    }}
    .lb-row-1 {{ background: #FFF8E7; border-left: 4px solid #F5A623; }}
    .lb-row-2 {{ background: #F5F5F5; border-left: 4px solid {STEEL_700}; }}
    .lb-row-3 {{ background: #FFF3F0; border-left: 4px solid #C97A5A; }}
    .lb-row-n {{ background: {STEEL_100}; border-left: 4px solid {STEEL_300}; }}
    .lb-rank  {{ font-weight: 800; color: {NAVY}; width: 32px; }}
    .lb-name  {{ flex: 1; font-weight: 600; }}
    .lb-stat  {{ width: 90px; text-align: right; color: {STEEL_700}; }}
    .lb-rate  {{ width: 80px; text-align: right; font-weight: 700; color: {NAVY}; }}
    /* Status tiles */
    .status-tile {{
        background: {WHITE};
        border-radius: 6px;
        padding: 14px 18px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.07);
        margin-bottom: 10px;
    }}
    .status-tile .st-title {{
        font-size: 12px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.07em;
        color: {STEEL_700};
        margin-bottom: 4px;
    }}
    .status-tile .st-value {{
        font-size: 26px;
        font-weight: 800;
        color: {NAVY};
        line-height: 1.2;
    }}
    .status-tile .st-sub {{
        font-size: 13px;
        color: {BLACK};
        margin-top: 2px;
    }}
    /* Cohort heatmap label */
    .cohort-note {{
        font-size: 12px;
        color: {STEEL_700};
        margin-top: -6px;
        margin-bottom: 10px;
    }}
    /* Table styles */
    .perf-table {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }}
    .perf-table th {{
        background: {STEEL_100};
        color: {NAVY};
        padding: 8px 12px;
        text-align: left;
        border-bottom: 2px solid {BLUE_700};
        font-weight: 700;
    }}
    .perf-table td {{
        padding: 7px 12px;
        color: {BLACK};
        border-bottom: 1px solid {GRAY_300};
    }}
    .perf-table tr:hover td {{ background: {STEEL_100}; }}
    </style>
    """, unsafe_allow_html=True)


# ============================================================
# BASE LAYOUT
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
    path = os.path.join("data", "mphh_benchmarking.csv")
    df = pd.read_csv(path)
    df["snapshot_date"] = pd.to_datetime(df["snapshot_date"])
    df["quarter"] = df["snapshot_date"].dt.to_period("Q").astype(str)
    df["year"] = df["snapshot_date"].dt.year.astype(str)
    df["robinson_target_pct"] = df["quarter"].map(TARGET_MAP)
    return df


@st.cache_data
def build_quarterly_summary(df):
    qs = (
        df.groupby("quarter")
        .agg(
            total=("converted_mphh", "count"),
            converted=("converted_mphh", "sum"),
            rate=("converted_mphh", "mean"),
            avg_cltv=("projected_mphh_cltv", "mean"),
            total_cltv=("projected_mphh_cltv", "sum"),
            avg_premium=("annual_premium_anchor", "mean"),
        )
        .reset_index()
    )
    qs["rate_pct"] = qs["rate"] * 100
    qs["target_pct"] = qs["quarter"].map(TARGET_MAP)
    qs["vs_target"] = qs["rate_pct"] - qs["target_pct"]
    qs["status"] = qs["vs_target"].apply(
        lambda x: "On Track" if x >= 0 else "Behind"
    )
    qs = qs.set_index("quarter").reindex(QUARTERS_ORDERED).reset_index()
    return qs


@st.cache_data
def build_agent_leaderboard(df):
    lb = (
        df.groupby(["agent_id", "agency_channel", "region", "state"])
        .agg(
            households=("converted_mphh", "count"),
            converted=("converted_mphh", "sum"),
            rate=("converted_mphh", "mean"),
            avg_cltv=("projected_mphh_cltv", "mean"),
            total_cltv=("projected_mphh_cltv", "sum"),
            avg_outreach=("outreach_contacts_12m", "mean"),
            avg_digital=("digital_engagement_score", "mean"),
        )
        .reset_index()
    )
    lb["rate_pct"] = (lb["rate"] * 100).round(2)
    lb["total_cltv_k"] = (lb["total_cltv"] / 1000).round(1)
    lb = lb[lb["households"] >= 50].copy()
    lb["rank_converted"] = lb["converted"].rank(ascending=False, method="min").astype(int)
    lb["rank_rate"] = lb["rate"].rank(ascending=False, method="min").astype(int)
    lb["rank_cltv"] = lb["total_cltv"].rank(ascending=False, method="min").astype(int)
    return lb.sort_values("converted", ascending=False)


@st.cache_data
def build_cohort_matrix(df):
    tenure_order = ["0-5mo", "6-11mo", "12-23mo", "24-35mo", "36-59mo", "60+mo"]
    df2 = df.copy()
    df2["tenure_bucket"] = pd.cut(
        df2["tenure_months"],
        bins=[0, 6, 12, 24, 36, 60, 121],
        labels=tenure_order,
        right=False,
    )
    matrix = (
        df2.groupby(["quarter", "tenure_bucket"], observed=True)["converted_mphh"]
        .mean()
        .unstack()
        .reindex(QUARTERS_ORDERED)
        * 100
    )
    return matrix


# ============================================================
# SESSION STATE
# ============================================================
def init_session_state(df):
    defaults = {
        "b_channel":  sorted(df["agency_channel"].unique().tolist()),
        "b_region":   sorted(df["region"].unique().tolist()),
        "b_state":    sorted(df["state"].unique().tolist()),
        "b_year":     sorted(df["year"].unique().tolist()),
        "b_tier":     sorted(df["policy_tier"].unique().tolist()),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ============================================================
# HELPERS
# ============================================================
def insight(label, body):
    st.markdown(
        f'<div class="insight-strip"><div class="label">{label}</div>'
        f'<div class="body">{body}</div></div>',
        unsafe_allow_html=True,
    )


def section_header(title, subtitle=None):
    st.markdown(
        f'<div class="section-header"><h4>{title}</h4></div>',
        unsafe_allow_html=True,
    )
    if subtitle:
        st.markdown(
            f'<p class="section-subtitle">{subtitle}</p>',
            unsafe_allow_html=True,
        )


def section_subtitle(text):
    st.markdown(f'<p class="section-subtitle">{text}</p>', unsafe_allow_html=True)


def status_tile(title, value, sub, border_color=BLUE_700):
    st.markdown(
        f'<div class="status-tile" style="border-left:4px solid {border_color};">'
        f'<div class="st-title">{title}</div>'
        f'<div class="st-value">{value}</div>'
        f'<div class="st-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def sparkline_mini(values, color=BLUE_700):
    fig = go.Figure(go.Scatter(
        x=list(range(len(values))), y=values,
        mode="lines",
        line=dict(color=color, width=2),
        fill="tozeroy",
        fillcolor=f"rgba(0,119,179,0.10)",
    ))
    fig.update_layout(
        height=55,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )
    return fig


# ============================================================
# SIDEBAR
# ============================================================
def render_sidebar(df):
    st.sidebar.markdown(
        f"<h3 style='color:{NAVY};font-size:16px;margin-bottom:4px;'>"
        f"Report Filters</h3>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("---")

    channel = st.sidebar.multiselect(
        "Agency Channel",
        options=sorted(df["agency_channel"].unique()),
        default=st.session_state["b_channel"],
        key="b_channel",
    )
    region = st.sidebar.multiselect(
        "Region",
        options=sorted(df["region"].unique()),
        default=st.session_state["b_region"],
        key="b_region",
    )
    state = st.sidebar.multiselect(
        "State",
        options=sorted(df["state"].unique()),
        default=st.session_state["b_state"],
        key="b_state",
    )
    year = st.sidebar.multiselect(
        "Year",
        options=sorted(df["year"].unique()),
        default=st.session_state["b_year"],
        key="b_year",
    )
    tier = st.sidebar.multiselect(
        "Policy Tier",
        options=sorted(df["policy_tier"].unique()),
        default=st.session_state["b_tier"],
        key="b_tier",
    )

    st.sidebar.markdown("---")

    def _reset_filters():
        st.session_state["b_channel"] = sorted(df["agency_channel"].unique().tolist())
        st.session_state["b_region"]  = sorted(df["region"].unique().tolist())
        st.session_state["b_state"]   = sorted(df["state"].unique().tolist())
        st.session_state["b_year"]    = sorted(df["year"].unique().tolist())
        st.session_state["b_tier"]    = sorted(df["policy_tier"].unique().tolist())

    st.sidebar.button("Reset All Filters", on_click=_reset_filters)

    fdf = df[
        df["agency_channel"].isin(channel) &
        df["region"].isin(region) &
        df["state"].isin(state) &
        df["year"].isin(year) &
        df["policy_tier"].isin(tier)
    ].copy()

    pct = len(fdf) / len(df)
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<div style='font-size:13px;color:{NAVY};font-weight:600;'>"
        f"Filtered: {len(fdf):,} / {len(df):,}</div>",
        unsafe_allow_html=True,
    )
    st.sidebar.progress(pct)

    return fdf


# ============================================================
# PERSISTENT KPI HEADER
# ============================================================
def render_kpi_header(df, fdf):
    qs_full = build_quarterly_summary(df)
    qs_filt = build_quarterly_summary(fdf) if len(fdf) > 0 else qs_full

    current_q = QUARTERS_ORDERED[-1]
    prev_q    = QUARTERS_ORDERED[-2]

    def safe_get(qs, q, col):
        row = qs[qs["quarter"] == q]
        if len(row) == 0:
            return None
        return row.iloc[0][col]

    cur_rate  = safe_get(qs_full, current_q, "rate_pct") or 0
    prev_rate = safe_get(qs_full, prev_q, "rate_pct") or 0
    cur_tgt   = TARGET_MAP.get(current_q, 28.5)
    vs_tgt    = cur_rate - cur_tgt

    total_converted = fdf["converted_mphh"].sum()
    total_hh        = len(fdf)
    filt_rate       = (total_converted / total_hh * 100) if total_hh > 0 else 0

    unconverted_opp = fdf[fdf["converted_mphh"] == 0]["projected_mphh_cltv"].sum()

    yoy_2025 = safe_get(qs_full, "2025Q4", "rate_pct") or 0
    yoy_2024 = safe_get(qs_full, "2024Q4", "rate_pct") or 0
    yoy_delta = yoy_2025 - yoy_2024

    spark_y = [safe_get(qs_full, q, "rate_pct") or 0 for q in QUARTERS_ORDERED]

    kpis = [
        {
            "label":  "Current Quarter MPHH Rate",
            "value":  f"{cur_rate:.2f}%",
            "delta":  f"{vs_tgt:+.2f}% vs. Robinson target",
            "color":  GREEN_700 if vs_tgt >= 0 else RED_SOFT,
        },
        {
            "label":  "Filtered Conversion Rate",
            "value":  f"{filt_rate:.2f}%",
            "delta":  f"{total_converted:,} of {total_hh:,} households",
            "color":  BLUE_700,
        },
        {
            "label":  "YoY Rate Change (Q4)",
            "value":  f"{yoy_delta:+.2f}%",
            "delta":  f"2025Q4 {yoy_2025:.2f}% vs. 2024Q4 {yoy_2024:.2f}%",
            "color":  GREEN_700 if yoy_delta >= 0 else RED_SOFT,
        },
        {
            "label":  "Unconverted CLTV Opportunity",
            "value":  f"${unconverted_opp/1e6:.1f}M",
            "delta":  f"{int(total_hh - total_converted):,} unconverted households",
            "color":  ORANGE_700,
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
                st.plotly_chart(
                    sparkline_mini(spark_y, kpi["color"]),
                    use_container_width=True,
                    config={"displayModeBar": False},
                    key=f"kpi_sparkline_{i}",
                )
            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


# ============================================================
# TAB 1: ROBINSON STRATEGY TRACKER
# ============================================================
def render_robinson_tracker(fdf):
    qs = build_quarterly_summary(fdf)

    behind_qtrs = qs[qs["status"] == "Behind"]["quarter"].tolist()
    on_track    = qs[qs["status"] == "On Track"]["quarter"].tolist()
    latest_q    = qs.dropna(subset=["rate_pct"]).iloc[-1]
    gap         = latest_q["vs_target"]
    gap_str     = f"{gap:+.2f}%"

    insight(
        "Robinson Strategy Status",
        f"The most recent quarter ({latest_q['quarter']}) shows an MPHH rate of "
        f"{latest_q['rate_pct']:.2f}% against a Robinson Strategy target of "
        f"{latest_q['target_pct']:.1f}% ({gap_str}). "
        f"The portfolio has been behind target in {len(behind_qtrs)} of "
        f"{len(qs.dropna(subset=['rate_pct']))} quarters tracked. "
        f"Immediate focus on outreach program optimization is required to close the trajectory."
    )

    # --- Row 1: Actual vs Target trend + quarterly delta bar ---
    col1, col2 = st.columns([3, 2])

    with col1:
        section_header("Quarterly MPHH Rate vs. Robinson Strategy Target")
        fig = go.Figure()

        # Target area fill
        fig.add_trace(go.Scatter(
            x=qs["quarter"], y=qs["target_pct"],
            mode="lines",
            line=dict(color=ORANGE_700, width=2, dash="dash"),
            name="Robinson Target",
            hovertemplate="Target: %{y:.1f}%<extra></extra>",
        ))

        # Color actual line by on/behind status
        for _, row in qs.iterrows():
            color = GREEN_700 if row["status"] == "On Track" else RED_SOFT
            fig.add_trace(go.Scatter(
                x=[row["quarter"]], y=[row["rate_pct"]],
                mode="markers",
                marker=dict(color=color, size=10, line=dict(color=WHITE, width=2)),
                showlegend=False,
                hovertemplate=(
                    f"<b>{row['quarter']}</b><br>"
                    f"Rate: {row['rate_pct']:.2f}%<br>"
                    f"Target: {row['target_pct']:.1f}%<br>"
                    f"Gap: {row['vs_target']:+.2f}%<br>"
                    f"Status: {row['status']}<extra></extra>"
                ),
            ))

        fig.add_trace(go.Scatter(
            x=qs["quarter"], y=qs["rate_pct"],
            mode="lines",
            line=dict(color=BLUE_700, width=3),
            name="Actual MPHH Rate",
            hoverinfo="skip",
        ))

        layout = base_layout(340)
        layout.update(dict(
            title=dict(text="", font=dict(size=14, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK, tickangle=-30),
            yaxis=dict(
                title="MPHH Conversion Rate (%)",
                color=BLACK,
                range=[23, 31],
            ),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig.update_layout(layout)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False}, key="chart_robinson_trend")

    with col2:
        section_header("Quarterly Status Summary")
        st.markdown("<br>", unsafe_allow_html=True)
        for _, row in qs.dropna(subset=["rate_pct"]).iterrows():
            badge_cls = "badge-on-track" if row["status"] == "On Track" else "badge-behind"
            gap_color = GREEN_900 if row["vs_target"] >= 0 else RED_SOFT
            st.markdown(
                f"<div style='display:flex;align-items:center;padding:7px 0;"
                f"border-bottom:1px solid {GRAY_300};'>"
                f"<span style='font-weight:700;color:{NAVY};width:72px;font-size:13px;'>"
                f"{row['quarter']}</span>"
                f"<span style='flex:1;font-size:14px;color:{BLACK};'>"
                f"{row['rate_pct']:.2f}% / {row['target_pct']:.1f}%</span>"
                f"<span style='font-size:13px;font-weight:700;color:{gap_color};width:60px;text-align:right;'>"
                f"{row['vs_target']:+.2f}%</span>"
                f"&nbsp;&nbsp;<span class='{badge_cls}'>{row['status']}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    # --- Row 2: Gap vs target bar + quarterly volume ---
    st.markdown("<br>", unsafe_allow_html=True)
    section_header(
        "Gap Analysis and Conversion Volume",
        subtitle="Gap = actual MPHH rate minus Robinson target. Green bars are on-track quarters; red bars show the shortfall."
    )

    col3, col4 = st.columns(2)

    with col3:
        bar_colors = [GREEN_700 if v >= 0 else RED_SOFT for v in qs["vs_target"]]
        fig_gap = go.Figure(go.Bar(
            x=qs["quarter"],
            y=qs["vs_target"],
            marker_color=bar_colors,
            text=[f"{v:+.2f}%" for v in qs["vs_target"]],
            textposition="outside",
            textfont=dict(size=12, color=NAVY),
            customdata=np.stack([qs["rate_pct"], qs["target_pct"]], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Actual: %{customdata[0]:.2f}%<br>"
                "Target: %{customdata[1]:.1f}%<br>"
                "Gap: %{y:+.2f}%<extra></extra>"
            ),
        ))
        layout_gap = base_layout()
        layout_gap.update(dict(
            title=dict(text="Gap vs. Robinson Target by Quarter", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK, tickangle=-30),
            yaxis=dict(title="Gap (percentage points)", color=BLACK, zeroline=True,
                       zerolinecolor=GRAY_300, zerolinewidth=1.5),
        ))
        fig_gap.update_layout(layout_gap)
        st.plotly_chart(fig_gap, use_container_width=True, config={"displayModeBar": False}, key="chart_gap")

    with col4:
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=qs["quarter"], y=qs["converted"],
            name="Converted",
            marker_color=BLUE_700,
            text=[f"{v:,}" for v in qs["converted"]],
            textposition="outside",
            textfont=dict(size=11, color=NAVY),
            hovertemplate="<b>%{x}</b><br>Converted: %{y:,}<extra></extra>",
        ))
        fig_vol.add_trace(go.Scatter(
            x=qs["quarter"], y=qs["rate_pct"],
            name="MPHH Rate (%)",
            mode="lines+markers",
            line=dict(color=ORANGE_700, width=2.5),
            marker=dict(color=ORANGE_700, size=8),
            yaxis="y2",
            text=[f"{v:.1f}%" for v in qs["rate_pct"]],
            textposition="top center",
            textfont=dict(size=11, color=ORANGE_700),
            hovertemplate="Rate: %{y:.2f}%<extra></extra>",
        ))
        layout_vol = base_layout()
        layout_vol.update(dict(
            title=dict(text="Quarterly Conversion Volume and Rate", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK, tickangle=-30),
            yaxis=dict(title="Converted Households", color=BLUE_700),
            yaxis2=dict(title="MPHH Rate (%)", color=ORANGE_700, overlaying="y", side="right"),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
            barmode="group",
        ))
        fig_vol.update_layout(layout_vol)
        st.plotly_chart(fig_vol, use_container_width=True, config={"displayModeBar": False}, key="chart_vol")

    # --- Row 3: Channel contribution to quarterly rate ---
    section_header("Channel Contribution to Quarterly MPHH Rate")
    section_subtitle(
        "Each bar segment shows how many converted households came from each channel in that quarter. "
        "Independent Agent consistently drives the largest share of conversions."
    )

    ch_q = (
        fdf.groupby(["quarter", "agency_channel"])
        .agg(converted=("converted_mphh", "sum"), total=("converted_mphh", "count"))
        .reset_index()
    )
    ch_q = ch_q[ch_q["quarter"].isin(QUARTERS_ORDERED)].copy()

    fig_stacked = go.Figure()
    channels = sorted(fdf["agency_channel"].unique())
    ch_colors = {
        "Independent Agent": BLUE_700,
        "Direct Online":     GREEN_700,
        "Call Center":       ORANGE_700,
        "Captive Agent":     STEEL_700,
    }
    for ch in channels:
        subset = ch_q[ch_q["agency_channel"] == ch].set_index("quarter").reindex(QUARTERS_ORDERED).reset_index()
        fig_stacked.add_trace(go.Bar(
            x=subset["quarter"],
            y=subset["converted"].fillna(0),
            name=ch,
            marker_color=ch_colors.get(ch, BLUE_500),
            hovertemplate=f"<b>{ch}</b><br>%{{x}}: %{{y:,}} converted<extra></extra>",
        ))

    layout_stk = base_layout(320)
    layout_stk.update(dict(
        title=dict(text="", x=0.02),
        xaxis=dict(color=BLACK, tickangle=-30),
        yaxis=dict(title="Converted Households", color=BLACK),
        barmode="stack",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
    ))
    fig_stacked.update_layout(layout_stk)
    st.plotly_chart(fig_stacked, use_container_width=True, config={"displayModeBar": False}, key="chart_stacked")


# ============================================================
# TAB 2: YOY GROWTH
# ============================================================
def render_yoy_growth(fdf):
    qs = build_quarterly_summary(fdf)

    def get_rate(q):
        row = qs[qs["quarter"] == q]
        return row.iloc[0]["rate_pct"] if len(row) > 0 else None

    # Build per-quarter-label rate table for all three years
    qlabels = ["Q1", "Q2", "Q3", "Q4"]
    yoy_rows = []
    for ql in qlabels:
        r23 = get_rate(f"2023{ql}")
        r24 = get_rate(f"2024{ql}")
        r25 = get_rate(f"2025{ql}")
        yoy_rows.append({
            "label":      ql,
            "rate_2023":  r23,
            "rate_2024":  r24,
            "rate_2025":  r25,
            "delta_23_24": (r24 - r23) if r23 is not None and r24 is not None else None,
            "delta_24_25": (r25 - r24) if r24 is not None and r25 is not None else None,
        })
    yoy_df = pd.DataFrame(yoy_rows)

    d2324 = yoy_df["delta_23_24"].dropna()
    d2425 = yoy_df["delta_24_25"].dropna()
    avg_2324 = d2324.mean() if len(d2324) else 0
    avg_2425 = d2425.mean() if len(d2425) else 0
    pos_2324 = (d2324 > 0).sum()
    pos_2425 = (d2425 > 0).sum()

    insight(
        "YoY Growth",
        f"2024 vs 2023: average delta {avg_2324:+.2f}pp across matched quarters "
        f"({pos_2324} of {len(d2324)} improved). "
        f"2025 vs 2024: average delta {avg_2425:+.2f}pp "
        f"({pos_2425} of {len(d2425)} improved)."
    )

    col1, col2 = st.columns(2)

    with col1:
        section_header("MPHH Rate: 2023 / 2024 / 2025 (Same Quarter)")
        fig_yoy = go.Figure()
        for yr, col_name, color in [
            ("2023", "rate_2023", STEEL_300),
            ("2024", "rate_2024", BLUE_700),
            ("2025", "rate_2025", GREEN_700),
        ]:
            vals = yoy_df[col_name]
            mask = vals.notna()
            if mask.any():
                fig_yoy.add_trace(go.Bar(
                    x=yoy_df.loc[mask, "label"], y=vals[mask],
                    name=yr, marker_color=color,
                    text=[f"{v:.2f}%" for v in vals[mask]],
                    textposition="outside", textfont=dict(size=11, color=NAVY),
                    hovertemplate=f"{yr} %{{x}}: %{{y:.2f}}%<extra></extra>",
                ))
        all_vals = pd.concat([yoy_df["rate_2023"], yoy_df["rate_2024"], yoy_df["rate_2025"]]).dropna()
        ymax = all_vals.max() * 1.20 if len(all_vals) else 35
        layout_yoy = base_layout()
        layout_yoy.update(dict(
            title=dict(text="", x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="MPHH Rate (%)", range=[0, ymax], color=BLACK),
            barmode="group",
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig_yoy.update_layout(layout_yoy)
        st.plotly_chart(fig_yoy, use_container_width=True, config={"displayModeBar": False}, key="chart_yoy")

    with col2:
        section_header("YoY Delta by Quarter (percentage points)")
        fig_delta = go.Figure()
        for delta_col, label, color_pos, color_neg in [
            ("delta_23_24", "2023→2024", BLUE_700, STEEL_300),
            ("delta_24_25", "2024→2025", GREEN_700, RED_SOFT),
        ]:
            vals = yoy_df[delta_col]
            mask = vals.notna()
            if mask.any():
                bar_colors = [color_pos if v >= 0 else color_neg for v in vals[mask]]
                fig_delta.add_trace(go.Bar(
                    x=yoy_df.loc[mask, "label"], y=vals[mask],
                    name=label, marker_color=bar_colors,
                    text=[f"{v:+.2f}pp" for v in vals[mask]],
                    textposition="outside", textfont=dict(size=11, color=NAVY),
                    hovertemplate=f"<b>{label} %{{x}}</b><br>Delta: %{{y:+.2f}}pp<extra></extra>",
                ))
        layout_delta = base_layout()
        layout_delta.update(dict(
            title=dict(text="", x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(
                title="Rate Change (pp)", color=BLACK,
                zeroline=True, zerolinecolor=GRAY_300, zerolinewidth=1.5,
            ),
            barmode="group",
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig_delta.update_layout(layout_delta)
        st.plotly_chart(fig_delta, use_container_width=True, config={"displayModeBar": False}, key="chart_delta")

    # YoY by channel — 3 years
    section_header(
        "YoY Rate Change by Channel",
        subtitle="Conversion rate per channel across all three years. Delta bars show 2023→2024 and 2024→2025 changes."
    )

    ch_year = (
        fdf.groupby(["year", "agency_channel"])["converted_mphh"]
        .mean()
        .reset_index()
    )
    ch_year.columns = ["year", "channel", "rate"]
    ch_year["rate_pct"] = ch_year["rate"] * 100

    ch_pivot = ch_year.pivot(index="channel", columns="year", values="rate_pct").reset_index()
    available_years = [y for y in ["2023", "2024", "2025"] if y in ch_pivot.columns]

    if len(available_years) >= 2:
        if "2024" in ch_pivot.columns and "2025" in ch_pivot.columns:
            ch_pivot["delta_24_25"] = ch_pivot["2025"] - ch_pivot["2024"]
            ch_pivot = ch_pivot.sort_values("delta_24_25", ascending=False)
        elif "2024" in ch_pivot.columns and "2023" in ch_pivot.columns:
            ch_pivot["delta_24_25"] = ch_pivot["2024"] - ch_pivot["2023"]
            ch_pivot = ch_pivot.sort_values("delta_24_25", ascending=False)

        col3, col4 = st.columns(2)
        with col3:
            fig_ch_bar = go.Figure()
            yr_colors = {"2023": STEEL_300, "2024": BLUE_700, "2025": GREEN_700}
            for yr in available_years:
                fig_ch_bar.add_trace(go.Bar(
                    x=ch_pivot["channel"], y=ch_pivot[yr],
                    name=yr, marker_color=yr_colors[yr],
                    text=[f"{v:.2f}%" for v in ch_pivot[yr]],
                    textposition="outside", textfont=dict(size=11, color=NAVY),
                    hovertemplate=f"{yr}: %{{y:.2f}}%<extra></extra>",
                ))
            all_ch_vals = pd.concat([ch_pivot[y] for y in available_years]).dropna()
            y_ch_max = all_ch_vals.max() * 1.20 if len(all_ch_vals) else 35
            layout_chb = base_layout()
            layout_chb.update(dict(
                title=dict(text=f"Channel Rate: {' / '.join(available_years)}",
                           font=dict(size=13, color=NAVY), x=0.02),
                xaxis=dict(color=BLACK, tickfont=dict(size=11)),
                yaxis=dict(title="MPHH Rate (%)", range=[0, y_ch_max], color=BLACK),
                barmode="group",
                legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
            ))
            fig_ch_bar.update_layout(layout_chb)
            st.plotly_chart(fig_ch_bar, use_container_width=True, config={"displayModeBar": False}, key="chart_ch_bar")

        with col4:
            fig_ch_d = go.Figure()
            delta_pairs = []
            if "2023" in ch_pivot.columns and "2024" in ch_pivot.columns:
                delta_pairs.append(("2023→2024", ch_pivot["2024"] - ch_pivot["2023"], BLUE_700, STEEL_300))
            if "2024" in ch_pivot.columns and "2025" in ch_pivot.columns:
                delta_pairs.append(("2024→2025", ch_pivot["2025"] - ch_pivot["2024"], GREEN_700, RED_SOFT))
            for d_label, d_vals, c_pos, c_neg in delta_pairs:
                d_colors = [c_pos if v >= 0 else c_neg for v in d_vals]
                fig_ch_d.add_trace(go.Bar(
                    x=ch_pivot["channel"], y=d_vals,
                    name=d_label, marker_color=d_colors,
                    text=[f"{v:+.2f}pp" for v in d_vals],
                    textposition="outside", textfont=dict(size=11, color=NAVY),
                    hovertemplate=f"<b>{d_label} %{{x}}</b><br>%{{y:+.2f}}pp<extra></extra>",
                ))
            layout_chd = base_layout()
            layout_chd.update(dict(
                title=dict(text="Channel YoY Delta", font=dict(size=13, color=NAVY), x=0.02),
                xaxis=dict(color=BLACK, tickfont=dict(size=11)),
                yaxis=dict(title="Rate Change (pp)", color=BLACK,
                           zeroline=True, zerolinecolor=GRAY_300, zerolinewidth=1.5),
                barmode="group",
                legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
            ))
            fig_ch_d.update_layout(layout_chd)
            st.plotly_chart(fig_ch_d, use_container_width=True, config={"displayModeBar": False}, key="chart_ch_d")

    # YoY CLTV
    section_header("YoY CLTV and Revenue Growth")
    cltv_year = (
        fdf.groupby("year")["projected_mphh_cltv"]
        .agg(["mean", "sum"])
        .reset_index()
    )
    cltv_year.columns = ["year", "avg_cltv", "total_cltv"]
    cltv_year["total_cltv_M"] = cltv_year["total_cltv"] / 1e6

    col5, col6 = st.columns(2)
    with col5:
        fig_cltv = go.Figure(go.Bar(
            x=cltv_year["year"], y=cltv_year["avg_cltv"],
            marker_color=[STEEL_300, BLUE_700][:len(cltv_year)],
            text=[f"${v:,.0f}" for v in cltv_year["avg_cltv"]],
            textposition="outside", textfont=dict(size=13, color=NAVY),
            hovertemplate="<b>%{x}</b><br>Avg CLTV: $%{y:,.0f}<extra></extra>",
        ))
        layout_cltv = base_layout()
        layout_cltv.update(dict(
            title=dict(text="Avg Projected MPHH CLTV by Year", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="Avg CLTV ($)", color=BLACK,
                       range=[0, cltv_year["avg_cltv"].max() * 1.25]),
        ))
        fig_cltv.update_layout(layout_cltv)
        st.plotly_chart(fig_cltv, use_container_width=True, config={"displayModeBar": False}, key="chart_cltv")

    with col6:
        fig_tcltv = go.Figure(go.Bar(
            x=cltv_year["year"], y=cltv_year["total_cltv_M"],
            marker_color=[STEEL_300, GREEN_700][:len(cltv_year)],
            text=[f"${v:.1f}M" for v in cltv_year["total_cltv_M"]],
            textposition="outside", textfont=dict(size=13, color=NAVY),
            hovertemplate="<b>%{x}</b><br>Total CLTV: $%{y:.1f}M<extra></extra>",
        ))
        layout_tcltv = base_layout()
        layout_tcltv.update(dict(
            title=dict(text="Total Portfolio CLTV by Year ($M)", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="Total CLTV ($M)", color=BLACK,
                       range=[0, cltv_year["total_cltv_M"].max() * 1.25]),
        ))
        fig_tcltv.update_layout(layout_tcltv)
        st.plotly_chart(fig_tcltv, use_container_width=True, config={"displayModeBar": False}, key="chart_tcltv")


# ============================================================
# TAB 3: COHORT RETENTION
# ============================================================
def render_cohort_retention(fdf):
    matrix = build_cohort_matrix(fdf)

    insight(
        "Cohort Retention View",
        "The heatmap shows MPHH conversion rate by acquisition quarter (rows) and household "
        "tenure bucket (columns). Darker cells indicate higher conversion rates. The 24-35 month "
        "tenure bucket consistently shows the strongest conversion lift across all cohorts -- "
        "this is the optimal window for cross-sell outreach."
    )

    section_header(
        "MPHH Conversion Rate Heatmap -- Quarter x Tenure Bucket",
        subtitle="Each cell = conversion rate for households acquired in that quarter at that tenure stage. "
                 "Darker blue = higher conversion. Use this to time outreach by cohort maturity."
    )

    z_vals = matrix.values
    x_labels = [str(c) for c in matrix.columns]
    y_labels = matrix.index.tolist()

    text_vals = [[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in z_vals]

    fig_heat = go.Figure(go.Heatmap(
        z=z_vals,
        x=x_labels,
        y=y_labels,
        text=text_vals,
        texttemplate="%{text}",
        textfont=dict(size=12, color=BLACK),
        colorscale=[[0, STEEL_100], [0.4, BLUE_500], [1.0, NAVY]],
        showscale=True,
        colorbar=dict(title="Rate (%)", tickfont=dict(size=11)),
        hovertemplate="<b>%{y}</b> | Tenure: %{x}<br>Conversion rate: %{z:.2f}%<extra></extra>",
        zmin=18, zmax=32,
    ))
    layout_heat = base_layout(420)
    layout_heat.update(dict(
        title=dict(text="", x=0.02),
        xaxis=dict(title="Tenure Bucket", color=BLACK, tickfont=dict(size=12)),
        yaxis=dict(title="Acquisition Quarter", color=BLACK, tickfont=dict(size=12), autorange="reversed"),
    ))
    fig_heat.update_layout(layout_heat)
    st.plotly_chart(fig_heat, use_container_width=True, config={"displayModeBar": False}, key="chart_heat")

    # Tenure bucket summary + cohort trend
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        section_header("Average Conversion Rate by Tenure Bucket (All Cohorts)")
        tenure_avg = matrix.mean(axis=0).reset_index()
        tenure_avg.columns = ["bucket", "avg_rate"]
        tenure_avg = tenure_avg.dropna()

        fig_tb = go.Figure(go.Bar(
            x=tenure_avg["bucket"].astype(str), y=tenure_avg["avg_rate"],
            marker_color=[
                BLUE_700 if v == tenure_avg["avg_rate"].max() else BLUE_500
                for v in tenure_avg["avg_rate"]
            ],
            text=[f"{v:.2f}%" for v in tenure_avg["avg_rate"]],
            textposition="outside", textfont=dict(size=12, color=NAVY),
            hovertemplate="<b>%{x}</b><br>Avg rate: %{y:.2f}%<extra></extra>",
        ))
        layout_tb = base_layout()
        layout_tb.update(dict(
            title=dict(text="", x=0.02),
            xaxis=dict(title="Tenure Bucket", color=BLACK),
            yaxis=dict(title="Avg Conversion Rate (%)", color=BLACK,
                       range=[0, tenure_avg["avg_rate"].max() * 1.25]),
        ))
        fig_tb.update_layout(layout_tb)
        st.plotly_chart(fig_tb, use_container_width=True, config={"displayModeBar": False}, key="chart_tb")

    with col2:
        section_header("Cohort Maturity Trend -- 60+ Month Retention Rate by Acquisition Quarter")
        section_subtitle("How do long-tenure (60+ month) households in each cohort convert over time?")
        if "60+mo" in matrix.columns:
            long_tenure = matrix["60+mo"].dropna().reset_index()
            long_tenure.columns = ["quarter", "rate"]

            fig_lt = go.Figure(go.Scatter(
                x=long_tenure["quarter"], y=long_tenure["rate"],
                mode="lines+markers+text",
                line=dict(color=NAVY, width=2.5),
                marker=dict(color=NAVY, size=9),
                text=[f"{v:.1f}%" for v in long_tenure["rate"]],
                textposition="top center",
                textfont=dict(size=11, color=NAVY),
                fill="tozeroy",
                fillcolor="rgba(10,51,96,0.08)",
                hovertemplate="<b>%{x}</b><br>60+ month rate: %{y:.2f}%<extra></extra>",
            ))
            layout_lt = base_layout()
            layout_lt.update(dict(
                title=dict(text="", x=0.02),
                xaxis=dict(color=BLACK, tickangle=-30),
                yaxis=dict(title="Conversion Rate (%)", color=BLACK,
                           range=[22, 32]),
            ))
            fig_lt.update_layout(layout_lt)
            st.plotly_chart(fig_lt, use_container_width=True, config={"displayModeBar": False}, key="chart_lt")

    # Cohort comparison: early / mid / recent across 3 years
    section_header(
        "Early vs. Mid vs. Recent Cohort Comparison",
        subtitle="Compare 2023 early cohorts, 2024 mid cohorts, and 2025 recent cohorts across the same tenure buckets."
    )
    cohort_defs = [
        (["2023Q1", "2023Q2"], "2023 (Early)",  STEEL_700),
        (["2024Q1", "2024Q2"], "2024 (Mid)",    BLUE_700),
        (["2025Q3", "2025Q4"], "2025 (Recent)", ORANGE_700),
    ]
    cohort_frames = []
    for quarters, label, _ in cohort_defs:
        available = [q for q in quarters if q in matrix.index]
        if available:
            grp = matrix[matrix.index.isin(available)].mean(axis=0).reset_index()
            grp.columns = ["bucket", "rate"]
            grp["cohort"] = label
            cohort_frames.append(grp)
    compare = pd.concat(cohort_frames).dropna() if cohort_frames else pd.DataFrame()

    fig_cmp = go.Figure()
    for _, cohort_name, color in cohort_defs:
        sub = compare[compare["cohort"] == cohort_name] if len(compare) else pd.DataFrame()
        if len(sub) > 0:
            fig_cmp.add_trace(go.Bar(
                x=sub["bucket"].astype(str), y=sub["rate"],
                name=cohort_name, marker_color=color,
                text=[f"{v:.1f}%" for v in sub["rate"]],
                textposition="outside", textfont=dict(size=11, color=NAVY),
                hovertemplate=f"<b>{cohort_name}</b><br>%{{x}}: %{{y:.2f}}%<extra></extra>",
            ))
    cmp_max = compare["rate"].max() * 1.25 if len(compare) else 35
    layout_cmp = base_layout()
    layout_cmp.update(dict(
        title=dict(text="2023 vs. 2024 vs. 2025 Cohort Conversion Rate by Tenure Bucket",
                   font=dict(size=13, color=NAVY), x=0.02),
        xaxis=dict(color=BLACK),
        yaxis=dict(title="Avg Conversion Rate (%)", range=[0, cmp_max], color=BLACK),
        barmode="group",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
    ))
    fig_cmp.update_layout(layout_cmp)
    st.plotly_chart(fig_cmp, use_container_width=True, config={"displayModeBar": False}, key="chart_cmp")


# ============================================================
# TAB 4: AGENT LEADERBOARD
# ============================================================
def render_agent_leaderboard(fdf):
    lb = build_agent_leaderboard(fdf)

    top_agent = lb.iloc[0] if len(lb) > 0 else None
    total_agents = len(lb)
    ia_lb = lb[lb["agency_channel"] == "Independent Agent"]
    top_by_rate = lb.sort_values("rate_pct", ascending=False).iloc[0]

    insight(
        "Leaderboard Insight",
        f"Rankings cover {total_agents:,} agents with 50+ household assignments. "
        f"When ranked by conversion rate, Independent Agents hold the top positions -- "
        f"the top IA agent converts at {lb[lb['agency_channel']=='Independent Agent'].sort_values('rate_pct',ascending=False).iloc[0]['rate_pct']:.1f}%. "
        f"Direct Online agents lead on total conversions due to higher household volume per agent. "
        f"Use the rank mode selector to compare coaching priorities across both dimensions."
    )

    # Rank mode selector
    section_header("Agent Performance Rankings")
    rank_by = st.radio(
        "Rank agents by",
        ["Conversion Rate", "Total Conversions", "Total CLTV Generated"],
        horizontal=True,
        key="lb_rank_mode",
    )

    rank_col_map = {
        "Conversion Rate":      ("rate_pct", "rank_rate"),
        "Total Conversions":    ("converted", "rank_converted"),
        "Total CLTV Generated": ("total_cltv", "rank_cltv"),
    }
    sort_col, rank_col = rank_col_map[rank_by]

    # Channel filter for leaderboard
    lb_channel = st.multiselect(
        "Filter leaderboard by channel",
        options=sorted(lb["agency_channel"].unique()),
        default=sorted(lb["agency_channel"].unique()),
        key="lb_channel_filter",
    )
    lb_view = lb[lb["agency_channel"].isin(lb_channel)].sort_values(sort_col, ascending=False)

    # Top 15 leaderboard list
    top15 = lb_view.head(15).reset_index(drop=True)

    col_lb, col_charts = st.columns([1, 2])

    with col_lb:
        st.markdown(f"<div style='font-size:13px;color:{STEEL_700};margin-bottom:8px;'>"
                    f"Top 15 agents ranked by <b>{rank_by}</b></div>", unsafe_allow_html=True)
        for i, row in top15.iterrows():
            rank = i + 1
            if rank == 1:
                row_cls = "lb-row-1"
                medal = "1st"
            elif rank == 2:
                row_cls = "lb-row-2"
                medal = "2nd"
            elif rank == 3:
                row_cls = "lb-row-3"
                medal = "3rd"
            else:
                row_cls = "lb-row-n"
                medal = f"{rank}th"

            if rank_by == "Total Conversions":
                stat_display = f"{int(row['converted']):,} converted"
                rate_display = f"{row['rate_pct']:.1f}%"
            elif rank_by == "Conversion Rate":
                stat_display = f"{int(row['converted']):,} converted"
                rate_display = f"{row['rate_pct']:.1f}%"
            else:
                stat_display = f"${row['total_cltv_k']:.0f}K CLTV"
                rate_display = f"{row['rate_pct']:.1f}%"

            st.markdown(
                f'<div class="lb-row {row_cls}">'
                f'<span class="lb-rank">{medal}</span>'
                f'<span class="lb-name">{row["agent_id"]}<br>'
                f'<span style="font-size:11px;color:{STEEL_700};font-weight:400;">'
                f'{row["agency_channel"]} | {row["state"]}</span></span>'
                f'<span class="lb-stat">{stat_display}</span>'
                f'<span class="lb-rate">{rate_display}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    with col_charts:
        # Conversion rate distribution
        fig_dist = go.Figure()
        for ch, color in [
            ("Independent Agent", BLUE_700), ("Direct Online", GREEN_700),
            ("Call Center", ORANGE_700), ("Captive Agent", STEEL_700)
        ]:
            sub = lb_view[lb_view["agency_channel"] == ch]["rate_pct"]
            if len(sub) > 0:
                fig_dist.add_trace(go.Box(
                    y=sub, name=ch,
                    marker_color=color,
                    boxmean=True,
                    hovertemplate=f"<b>{ch}</b><br>Rate: %{{y:.2f}}%<extra></extra>",
                ))
        layout_dist = base_layout(380)
        layout_dist.update(dict(
            title=dict(text="Agent Conversion Rate Distribution by Channel",
                       font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="Conversion Rate (%)", color=BLACK),
        ))
        fig_dist.update_layout(layout_dist)
        st.plotly_chart(fig_dist, use_container_width=True, config={"displayModeBar": False}, key="chart_dist")

    # Bottom row: regional breakdown + top/bottom comparison
    st.markdown("<br>", unsafe_allow_html=True)
    section_header(
        "Regional and Tier Performance",
        subtitle="Average agent metrics by region. Identify which regions have the highest performance ceiling and widest agent spread."
    )
    col3, col4 = st.columns(2)

    with col3:
        reg_stats = (
            lb_view.groupby("region")
            .agg(agents=("agent_id","count"), avg_rate=("rate_pct","mean"), avg_cltv_k=("total_cltv_k","mean"))
            .reset_index().sort_values("avg_rate", ascending=False)
        )
        fig_reg = go.Figure(go.Bar(
            x=reg_stats["region"], y=reg_stats["avg_rate"],
            marker_color=BAR_COLORS[:len(reg_stats)],
            text=[f"{v:.2f}%" for v in reg_stats["avg_rate"]],
            textposition="outside", textfont=dict(size=12, color=NAVY),
            customdata=np.stack([reg_stats["agents"], reg_stats["avg_cltv_k"]], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>Avg rate: %{y:.2f}%<br>"
                "Agents: %{customdata[0]}<br>Avg CLTV: $%{customdata[1]:.0f}K<extra></extra>"
            ),
        ))
        layout_reg = base_layout()
        layout_reg.update(dict(
            title=dict(text="Avg Agent Conversion Rate by Region", font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="Avg Conversion Rate (%)", color=BLACK,
                       range=[0, reg_stats["avg_rate"].max() * 1.25]),
        ))
        fig_reg.update_layout(layout_reg)
        st.plotly_chart(fig_reg, use_container_width=True, config={"displayModeBar": False}, key="chart_reg")

    with col4:
        # Top 10 vs bottom 10 agents: gap analysis
        top10 = lb_view.head(10)["rate_pct"].mean()
        bot10 = lb_view.tail(10)["rate_pct"].mean()
        median_rate = lb_view["rate_pct"].median()

        fig_gap_agents = go.Figure(go.Bar(
            x=["Bottom 10 Agents", "Median Agent", "Top 10 Agents"],
            y=[bot10, median_rate, top10],
            marker_color=[RED_SOFT, STEEL_300, GREEN_700],
            text=[f"{v:.2f}%" for v in [bot10, median_rate, top10]],
            textposition="outside", textfont=dict(size=13, color=NAVY),
            hovertemplate="<b>%{x}</b><br>Avg rate: %{y:.2f}%<extra></extra>",
        ))
        layout_gap_a = base_layout()
        layout_gap_a.update(dict(
            title=dict(text="Performance Gap: Top 10 vs. Bottom 10 Agents",
                       font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="Avg Conversion Rate (%)", color=BLACK,
                       range=[0, top10 * 1.25]),
        ))
        fig_gap_agents.update_layout(layout_gap_a)
        st.plotly_chart(fig_gap_agents, use_container_width=True, config={"displayModeBar": False}, key="chart_gap_agents")


# ============================================================
# TAB 5: STATE PERFORMANCE
# ============================================================
def render_state_performance(fdf):
    state_stats = (
        fdf.groupby("state")
        .agg(
            total=("converted_mphh", "count"),
            converted=("converted_mphh", "sum"),
            rate=("converted_mphh", "mean"),
            avg_cltv=("projected_mphh_cltv", "mean"),
            total_cltv=("projected_mphh_cltv", "sum"),
            avg_premium=("annual_premium_anchor", "mean"),
            avg_outreach=("outreach_contacts_12m", "mean"),
            avg_digital=("digital_engagement_score", "mean"),
        )
        .reset_index()
    )
    state_stats["rate_pct"] = (state_stats["rate"] * 100).round(2)
    state_stats["total_cltv_M"] = (state_stats["total_cltv"] / 1e6).round(2)
    state_stats["unconverted"] = state_stats["total"] - state_stats["converted"]
    state_stats = state_stats.sort_values("rate_pct", ascending=False)

    top_state = state_stats.iloc[0]
    bot_state = state_stats.iloc[-1]
    spread    = top_state["rate_pct"] - bot_state["rate_pct"]

    insight(
        "State Performance",
        f"MPHH conversion rates range from {bot_state['rate_pct']:.2f}% ({bot_state['state']}) "
        f"to {top_state['rate_pct']:.2f}% ({top_state['state']}) -- a {spread:.2f} percentage "
        f"point spread. OH, GA, and IL lead on conversion rate. CA underperforms the portfolio "
        f"average and warrants a channel-mix or outreach-program review."
    )

    col1, col2 = st.columns(2)

    with col1:
        section_header("MPHH Conversion Rate by State")
        fig_state = go.Figure(go.Bar(
            x=state_stats["state"], y=state_stats["rate_pct"],
            marker_color=[
                GREEN_700 if v >= state_stats["rate_pct"].mean() else BLUE_500
                for v in state_stats["rate_pct"]
            ],
            text=[f"{v:.2f}%" for v in state_stats["rate_pct"]],
            textposition="outside", textfont=dict(size=12, color=NAVY),
            customdata=np.stack([state_stats["converted"], state_stats["total"]], axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>Rate: %{y:.2f}%<br>"
                "Converted: %{customdata[0]:,} of %{customdata[1]:,}<extra></extra>"
            ),
        ))
        avg_line = state_stats["rate_pct"].mean()
        fig_state.add_hline(
            y=avg_line,
            line=dict(color=ORANGE_700, width=1.5, dash="dash"),
            annotation_text=f"Avg: {avg_line:.2f}%",
            annotation_font=dict(size=11, color=ORANGE_700),
        )
        layout_state = base_layout()
        layout_state.update(dict(
            title=dict(text="", x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="MPHH Rate (%)", color=BLACK,
                       range=[0, state_stats["rate_pct"].max() * 1.25]),
        ))
        fig_state.update_layout(layout_state)
        st.plotly_chart(fig_state, use_container_width=True, config={"displayModeBar": False}, key="chart_state")

    with col2:
        section_header("Total CLTV Opportunity by State ($M)")
        unc_stats = state_stats.sort_values("total_cltv_M", ascending=False)
        fig_cltv_s = go.Figure(go.Bar(
            x=unc_stats["state"], y=unc_stats["total_cltv_M"],
            marker_color=BLUE_700,
            text=[f"${v:.1f}M" for v in unc_stats["total_cltv_M"]],
            textposition="outside", textfont=dict(size=11, color=NAVY),
            hovertemplate="<b>%{x}</b><br>Total CLTV: $%{y:.1f}M<extra></extra>",
        ))
        layout_cltv_s = base_layout()
        layout_cltv_s.update(dict(
            title=dict(text="", x=0.02),
            xaxis=dict(color=BLACK),
            yaxis=dict(title="Total CLTV ($M)", color=BLACK,
                       range=[0, unc_stats["total_cltv_M"].max() * 1.25]),
        ))
        fig_cltv_s.update_layout(layout_cltv_s)
        st.plotly_chart(fig_cltv_s, use_container_width=True, config={"displayModeBar": False}, key="chart_cltv_s")

    # State detail table
    section_header("State Performance Detail Table")
    table_rows = ""
    for _, row in state_stats.iterrows():
        vs_avg = row["rate_pct"] - state_stats["rate_pct"].mean()
        badge = (
            f'<span class="badge-on-track">Above Avg</span>'
            if vs_avg >= 0 else
            f'<span class="badge-behind">Below Avg</span>'
        )
        table_rows += (
            f"<tr>"
            f"<td><strong>{row['state']}</strong></td>"
            f"<td>{row['total']:,}</td>"
            f"<td>{row['converted']:,}</td>"
            f"<td>{row['rate_pct']:.2f}%</td>"
            f"<td>{vs_avg:+.2f}pp</td>"
            f"<td>${row['avg_cltv']:,.0f}</td>"
            f"<td>${row['total_cltv_M']:.1f}M</td>"
            f"<td>{badge}</td>"
            f"</tr>"
        )
    st.markdown(
        f"<table class='perf-table'>"
        f"<thead><tr>"
        f"<th>State</th><th>Households</th><th>Converted</th>"
        f"<th>MPHH Rate</th><th>vs. Avg</th>"
        f"<th>Avg CLTV</th><th>Total CLTV</th><th>Status</th>"
        f"</tr></thead><tbody>{table_rows}</tbody></table>",
        unsafe_allow_html=True,
    )

    # State x channel heatmap
    st.markdown("<br>", unsafe_allow_html=True)
    section_header(
        "State x Channel Conversion Rate Heatmap",
        subtitle="Identifies which channel performs best in each state. "
                 "Use to guide state-level channel investment and agent recruitment."
    )
    sc_matrix = (
        fdf.groupby(["state", "agency_channel"])["converted_mphh"]
        .mean() * 100
    ).unstack().round(2)

    fig_sc = go.Figure(go.Heatmap(
        z=sc_matrix.values,
        x=sc_matrix.columns.tolist(),
        y=sc_matrix.index.tolist(),
        text=[[f"{v:.1f}%" if not np.isnan(v) else "" for v in row] for row in sc_matrix.values],
        texttemplate="%{text}",
        textfont=dict(size=12, color=BLACK),
        colorscale=[[0, STEEL_100], [0.5, BLUE_500], [1, NAVY]],
        showscale=True,
        colorbar=dict(title="Rate (%)", tickfont=dict(size=11)),
        hovertemplate="<b>%{y} | %{x}</b><br>Conversion rate: %{z:.2f}%<extra></extra>",
        zmin=15, zmax=35,
    ))
    layout_sc = base_layout(360)
    layout_sc.update(dict(
        title=dict(text="", x=0.02),
        xaxis=dict(color=BLACK, tickfont=dict(size=12)),
        yaxis=dict(color=BLACK, tickfont=dict(size=12)),
    ))
    fig_sc.update_layout(layout_sc)
    st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False}, key="chart_sc")


# ============================================================
# TAB 6: PIPELINE HEALTH
# ============================================================
def render_pipeline_health(fdf):
    # Quote abandonment funnel
    total        = len(fdf)
    quote_starts = fdf["property_quote_started"].sum()
    converted_w_quote = fdf[(fdf["property_quote_started"] == 1) & (fdf["converted_mphh"] == 1)].shape[0]
    abandoned    = fdf[(fdf["property_quote_started"] == 1) & (fdf["converted_mphh"] == 0)].shape[0]
    converted_no_quote = fdf[(fdf["property_quote_started"] == 0) & (fdf["converted_mphh"] == 1)].shape[0]
    abandon_rate = abandoned / quote_starts if quote_starts > 0 else 0
    quote_cvr    = converted_w_quote / quote_starts if quote_starts > 0 else 0
    overall_cvr  = fdf["converted_mphh"].mean()

    insight(
        "Pipeline Health",
        f"Of {total:,} households, {quote_starts:,} ({quote_starts/total:.1%}) started a property "
        f"quote. Of those, {converted_w_quote:,} converted ({quote_cvr:.1%}) and "
        f"{abandoned:,} abandoned ({abandon_rate:.1%}). Quote starters convert at "
        f"{quote_cvr/overall_cvr:.1f}x the rate of non-starters -- making abandonment "
        f"recovery the highest-leverage pipeline intervention available."
    )

    col1, col2 = st.columns(2)

    with col1:
        section_header("Conversion Funnel")
        funnel_stages = [
            "All Households",
            "Quote Started",
            "Converted (w/ Quote)",
        ]
        funnel_values = [total, int(quote_starts), int(converted_w_quote)]
        funnel_pcts   = [100.0, quote_starts/total*100, converted_w_quote/total*100]

        fig_funnel = go.Figure(go.Funnel(
            y=funnel_stages,
            x=funnel_values,
            textinfo="value+percent initial",
            textfont=dict(size=13, color=WHITE),
            marker=dict(color=[BLUE_700, BLUE_500, GREEN_700]),
            connector=dict(line=dict(color=GRAY_300, width=1)),
            hovertemplate="<b>%{y}</b><br>Count: %{x:,}<br>% of total: %{percentInitial:.2%}<extra></extra>",
        ))
        layout_funnel = base_layout(340)
        layout_funnel.update(dict(
            title=dict(text="MPHH Conversion Funnel", font=dict(size=13, color=NAVY), x=0.02),
        ))
        fig_funnel.update_layout(layout_funnel)
        st.plotly_chart(fig_funnel, use_container_width=True, config={"displayModeBar": False}, key="chart_funnel")

    with col2:
        section_header("Quote Outcome Breakdown")
        labels = ["Converted (started quote)", "Abandoned (started, not converted)", "Converted (no quote)", "Never started, not converted"]
        values = [converted_w_quote, abandoned, converted_no_quote,
                  total - quote_starts - converted_no_quote]
        fig_pie = go.Figure(go.Pie(
            labels=labels,
            values=values,
            hole=0.50,
            marker_colors=[GREEN_700, RED_SOFT, BLUE_500, STEEL_300],
            textinfo="percent",
            textposition="outside",
            hovertemplate="%{label}: %{value:,} (%{percent})<extra></extra>",
        ))
        layout_pie = base_layout(340)
        layout_pie.update(dict(
            title=dict(text="Quote Outcome Breakdown", font=dict(size=13, color=NAVY), x=0.02),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.30,
                        font=dict(size=11)),
        ))
        fig_pie.update_layout(layout_pie)
        st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False}, key="chart_pie")

    # Outreach effectiveness
    section_header(
        "Outreach Program Effectiveness",
        subtitle="Tracks contact frequency against conversion outcome. "
                 "The 1-3 contact band is the sweet spot -- above 3 contacts shows diminishing returns."
    )

    out_stats = (
        fdf.groupby("outreach_contacts_12m")["converted_mphh"]
        .agg(["mean", "count", "sum"])
        .reset_index()
    )
    out_stats.columns = ["contacts", "rate", "count", "converted"]
    out_stats["rate_pct"] = out_stats["rate"] * 100

    col3, col4 = st.columns(2)
    with col3:
        bar_cols = [
            GREEN_700 if 1 <= c <= 3 else (ORANGE_700 if c > 3 else STEEL_300)
            for c in out_stats["contacts"]
        ]
        fig_out = go.Figure(go.Bar(
            x=out_stats["contacts"].astype(str),
            y=out_stats["rate_pct"],
            marker_color=bar_cols,
            text=[f"{v:.2f}%" for v in out_stats["rate_pct"]],
            textposition="outside", textfont=dict(size=12, color=NAVY),
            customdata=np.stack([out_stats["converted"], out_stats["count"]], axis=-1),
            hovertemplate=(
                "<b>%{x} contacts</b><br>"
                "%{customdata[0]:,} of %{customdata[1]:,} converted (%{y:.2f}%)<extra></extra>"
            ),
        ))
        layout_out = base_layout()
        layout_out.update(dict(
            title=dict(text="Conversion Rate by Outreach Contact Count",
                       font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Contacts in 12 months", color=BLACK),
            yaxis=dict(title="Conversion Rate (%)", color=BLACK,
                       range=[0, out_stats["rate_pct"].max() * 1.25]),
        ))
        fig_out.update_layout(layout_out)
        st.plotly_chart(fig_out, use_container_width=True, config={"displayModeBar": False}, key="chart_out")

    with col4:
        # Propensity tier x outreach -- are we reaching high-propensity households?
        tier_out = (
            fdf.groupby(["propensity_tier", "outreach_contacts_12m"])["converted_mphh"]
            .mean() * 100
        ).reset_index()
        tier_out.columns = ["tier", "contacts", "rate"]
        tier_order = ["High Propensity", "Medium Propensity", "Low Propensity"]
        tier_colors_map = {
            "High Propensity":   NAVY,
            "Medium Propensity": BLUE_500,
            "Low Propensity":    STEEL_300,
        }
        fig_to = go.Figure()
        for tier_name in tier_order:
            sub = tier_out[tier_out["tier"] == tier_name]
            if len(sub) > 0:
                fig_to.add_trace(go.Scatter(
                    x=sub["contacts"].astype(str), y=sub["rate"],
                    mode="lines+markers",
                    name=tier_name,
                    line=dict(color=tier_colors_map[tier_name], width=2.5),
                    marker=dict(color=tier_colors_map[tier_name], size=8),
                    hovertemplate=f"<b>{tier_name}</b><br>%{{x}} contacts: %{{y:.2f}}%<extra></extra>",
                ))
        layout_to = base_layout()
        layout_to.update(dict(
            title=dict(text="Conversion Rate by Outreach Count and Propensity Tier",
                       font=dict(size=13, color=NAVY), x=0.02),
            xaxis=dict(title="Outreach Contacts", color=BLACK),
            yaxis=dict(title="Conversion Rate (%)", color=BLACK),
            legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
        ))
        fig_to.update_layout(layout_to)
        st.plotly_chart(fig_to, use_container_width=True, config={"displayModeBar": False}, key="chart_to")

    # Digital engagement trend by quarter
    section_header(
        "Digital Engagement and Propensity Trends",
        subtitle="Rising digital engagement scores indicate growing household receptivity. "
                 "Monitor this leading indicator alongside the conversion rate trend."
    )

    dq_stats = (
        fdf.groupby("quarter")
        .agg(
            avg_digital=("digital_engagement_score", "mean"),
            avg_propensity=("propensity_score", "mean"),
            avg_outreach=("outreach_contacts_12m", "mean"),
        )
        .reset_index()
    )
    dq_stats = dq_stats[dq_stats["quarter"].isin(QUARTERS_ORDERED)].set_index("quarter").reindex(QUARTERS_ORDERED).reset_index()

    fig_lead = go.Figure()
    fig_lead.add_trace(go.Scatter(
        x=dq_stats["quarter"], y=dq_stats["avg_digital"],
        name="Avg Digital Score",
        mode="lines+markers",
        line=dict(color=BLUE_700, width=2.5),
        marker=dict(size=8),
        yaxis="y",
        hovertemplate="<b>%{x}</b><br>Avg digital score: %{y:.2f}<extra></extra>",
    ))
    fig_lead.add_trace(go.Scatter(
        x=dq_stats["quarter"], y=dq_stats["avg_propensity"],
        name="Avg Propensity Score",
        mode="lines+markers",
        line=dict(color=GREEN_700, width=2.5),
        marker=dict(size=8),
        yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Avg propensity: %{y:.2f}<extra></extra>",
    ))
    layout_lead = base_layout(320)
    layout_lead.update(dict(
        title=dict(text="Leading Indicators: Digital Engagement and Propensity by Quarter",
                   font=dict(size=13, color=NAVY), x=0.02),
        xaxis=dict(color=BLACK, tickangle=-30),
        yaxis=dict(title="Avg Digital Score", color=BLUE_700),
        yaxis2=dict(title="Avg Propensity Score", color=GREEN_700, overlaying="y", side="right"),
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.22),
    ))
    fig_lead.update_layout(layout_lead)
    st.plotly_chart(fig_lead, use_container_width=True, config={"displayModeBar": False}, key="chart_lead")


# ============================================================
# MAIN
# ============================================================
def main():
    inject_css()
    df = load_data()
    init_session_state(df)
    fdf = render_sidebar(df)

    st.markdown(
        f"<h2 style='color:{NAVY};margin-bottom:2px;font-size:22px;'>"
        f"MPHH Benchmarking and Reporting Dashboard</h2>"
        f"<p style='font-size:14px;color:{BLACK};margin-bottom:12px;'>"
        f"Agency Operations Analytics | Robinson Strategy Reporting Cadence | "
        f"<span style='color:{STEEL_700};'>Author: Luciano Casillas</span></p>",
        unsafe_allow_html=True,
    )

    render_kpi_header(df, fdf)

    tabs = st.tabs([
        "Robinson Strategy Tracker",
        "YoY Growth",
        "Cohort Retention",
        "Agent Leaderboard",
        "State Performance",
        "Pipeline Health",
    ])

    with tabs[0]:
        render_robinson_tracker(fdf)
    with tabs[1]:
        render_yoy_growth(fdf)
    with tabs[2]:
        render_cohort_retention(fdf)
    with tabs[3]:
        render_agent_leaderboard(fdf)
    with tabs[4]:
        render_state_performance(fdf)
    with tabs[5]:
        render_pipeline_health(fdf)


if __name__ == "__main__":
    main()
