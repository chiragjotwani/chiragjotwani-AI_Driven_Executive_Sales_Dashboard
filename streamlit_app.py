from __future__ import annotations

from hashlib import md5

import plotly.express as px
import streamlit as st

from app.analytics import (
    build_insight_context,
    compute_overview_metrics,
    monthly_sales,
    sales_by_dimension,
    top_products,
)
from app.config import AppConfig
from app.data import apply_filters, load_sales_data
from app.llm import generate_executive_insight
from app.powerbi import render_powerbi_section


st.set_page_config(page_title="Executive Sales Dashboard", layout="wide")

config = AppConfig()


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Manrope', sans-serif;
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(15, 118, 110, 0.10), transparent 24%),
                radial-gradient(circle at top right, rgba(14, 116, 144, 0.12), transparent 22%),
                linear-gradient(180deg, #f8fcfb 0%, #f4f8fc 100%);
        }

        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #111827 100%);
            border-right: 1px solid rgba(255,255,255,0.06);
        }

        section[data-testid="stSidebar"] * {
            color: #e5eef6;
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        .hero-shell {
            background: linear-gradient(135deg, #0f172a 0%, #134e4a 50%, #155e75 100%);
            border-radius: 28px;
            padding: 2rem 2.2rem;
            color: #f8fafc;
            box-shadow: 0 24px 70px rgba(15, 23, 42, 0.16);
            margin-bottom: 1.25rem;
            overflow: hidden;
        }

        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.78rem;
            font-weight: 700;
            color: rgba(226, 232, 240, 0.76);
            margin-bottom: 0.7rem;
        }

        .hero-title {
            font-size: 2.3rem;
            line-height: 1.05;
            font-weight: 800;
            margin: 0;
        }

        .hero-copy {
            font-size: 1rem;
            line-height: 1.7;
            color: rgba(226, 232, 240, 0.88);
            margin-top: 0.9rem;
            max-width: 58rem;
        }

        .hero-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 1.2rem;
        }

        .hero-badge {
            padding: 0.55rem 0.85rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.12);
            border: 1px solid rgba(255, 255, 255, 0.14);
            font-size: 0.88rem;
        }

        .kpi-card {
            background: rgba(255, 255, 255, 0.88);
            border: 1px solid rgba(15, 23, 42, 0.06);
            border-radius: 22px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 14px 38px rgba(15, 23, 42, 0.06);
            min-height: 138px;
        }

        .kpi-label {
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: #0f766e;
            font-weight: 800;
        }

        .kpi-value {
            font-size: 2rem;
            line-height: 1.05;
            color: #0f172a;
            font-weight: 800;
            margin-top: 0.6rem;
        }

        .kpi-footnote {
            margin-top: 0.65rem;
            font-size: 0.92rem;
            color: #475569;
        }

        .section-label {
            margin-top: 1rem;
            margin-bottom: 0.8rem;
            font-weight: 800;
            font-size: 1.25rem;
            color: #0f172a;
        }

        .panel-shell {
            background: rgba(255, 255, 255, 0.84);
            border: 1px solid rgba(15, 23, 42, 0.06);
            border-radius: 24px;
            box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
            padding: 0.9rem 1rem 0.25rem;
            margin-bottom: 1rem;
        }

        .panel-title {
            font-size: 1.03rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.2rem;
        }

        .panel-copy {
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 0.65rem;
        }

        .copilot-shell {
            background: linear-gradient(160deg, rgba(15, 23, 42, 0.98) 0%, rgba(21, 94, 117, 0.96) 100%);
            border-radius: 28px;
            padding: 1.4rem 1.5rem;
            color: #f8fafc;
            box-shadow: 0 24px 70px rgba(8, 15, 32, 0.18);
            margin-top: 0.4rem;
        }

        .copilot-title {
            font-size: 1.25rem;
            font-weight: 800;
            margin-bottom: 0.25rem;
        }

        .copilot-copy {
            color: rgba(226, 232, 240, 0.82);
            margin-bottom: 0.9rem;
        }

        .insight-box {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px;
            padding: 1rem 1.1rem;
            margin-top: 0.8rem;
        }

        .stPlotlyChart > div {
            border-radius: 18px;
        }

        div[data-testid="stMetric"] {
            background: transparent;
            border: none;
            box-shadow: none;
        }

        .powerbi-hint {
            background: #fff7ed;
            color: #9a3412;
            border: 1px solid #fdba74;
            border-radius: 16px;
            padding: 0.95rem 1rem;
            margin-bottom: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def currency(value: float) -> str:
    return f"${value:,.2f}"


def build_filter_signature(context: dict, question: str) -> str:
    payload = f"{context}|{question}"
    return md5(payload.encode("utf-8")).hexdigest()


def render_hero(total_rows: int, filtered_rows: int, min_date, max_date) -> None:
    st.markdown(
        f"""
        <div class="hero-shell">
            <div class="hero-eyebrow">Executive Command Center</div>
            <h1 class="hero-title">{config.app_title}</h1>
            <div class="hero-copy">
                Monitor sales performance, explore regional and category shifts, and generate
                executive-ready AI commentary from the exact slice of data currently in view.
            </div>
            <div class="hero-badges">
                <div class="hero-badge">{filtered_rows:,} records in current view</div>
                <div class="hero-badge">Dataset span: {min_date} to {max_date}</div>
                <div class="hero-badge">Source rows loaded: {total_rows:,}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, footnote: str, col) -> None:
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-label">{label}</div>
                <div class="kpi-value">{value}</div>
                <div class="kpi-footnote">{footnote}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def section_title(label: str) -> None:
    st.markdown(f'<div class="section-label">{label}</div>', unsafe_allow_html=True)


def panel_start(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="panel-shell">
            <div class="panel-title">{title}</div>
            <div class="panel-copy">{copy}</div>
        """,
        unsafe_allow_html=True,
    )


def panel_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def style_figure(fig, color_sequence: list[str], height: int = 350):
    fig.update_layout(
        height=height,
        margin=dict(l=12, r=12, t=16, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(248,250,252,0.6)",
        font=dict(family="Manrope, sans-serif", color="#0f172a"),
        colorway=color_sequence,
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(gridcolor="rgba(148,163,184,0.18)", zeroline=False)
    return fig


@st.cache_data(show_spinner=False)
def get_data():
    return load_sales_data()


inject_styles()
df = get_data()

with st.sidebar:
    st.markdown("## Dashboard Filters")
    st.caption("Narrow the view to generate focused KPIs, charts, and AI explanations.")
    min_date = df["Order Date"].min().date()
    max_date = df["Order Date"].max().date()
    selected_dates = st.date_input(
        "Order date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = min_date, max_date

    selected_regions = st.multiselect("Region", sorted(df["Region"].dropna().unique()))
    selected_segments = st.multiselect("Segment", sorted(df["Segment"].dropna().unique()))
    selected_categories = st.multiselect("Category", sorted(df["Category"].dropna().unique()))

    available_sub_categories = df["Sub-Category"]
    if selected_categories:
        available_sub_categories = df[df["Category"].isin(selected_categories)]["Sub-Category"]
    selected_sub_categories = st.multiselect(
        "Sub-Category",
        sorted(available_sub_categories.dropna().unique()),
    )

    st.markdown("---")
    st.caption("Tip: generate AI insights after adjusting filters to get context-specific recommendations.")

filtered_df = apply_filters(
    df,
    start_date=start_date,
    end_date=end_date,
    regions=selected_regions,
    segments=selected_segments,
    categories=selected_categories,
    sub_categories=selected_sub_categories,
)

if filtered_df.empty:
    st.warning("No data matches the selected filters.")
    st.stop()

metrics = compute_overview_metrics(filtered_df)
trend_df = monthly_sales(filtered_df)
region_df = sales_by_dimension(filtered_df, "Region", limit=10)
category_df = sales_by_dimension(filtered_df, "Category", limit=10)
product_df = top_products(filtered_df, limit=8)

render_hero(
    total_rows=df.shape[0],
    filtered_rows=filtered_df.shape[0],
    min_date=start_date,
    max_date=end_date,
)

kpi_cols = st.columns(4)
render_kpi_card(
    "Total Sales",
    currency(metrics.total_sales),
    "Gross sales captured in the current filtered slice.",
    kpi_cols[0],
)
render_kpi_card(
    "Average Order Value",
    currency(metrics.average_order_value),
    "Average revenue per order after the selected filters.",
    kpi_cols[1],
)
render_kpi_card(
    "Orders",
    f"{metrics.total_orders:,}",
    "Count of orders included in the live dashboard view.",
    kpi_cols[2],
)
render_kpi_card(
    "Unique Customers",
    f"{metrics.unique_customers:,}",
    "Distinct customers contributing to the visible sales base.",
    kpi_cols[3],
)

section_title("Performance View")
overview_left, overview_right = st.columns([1.6, 1])

with overview_left:
    panel_start("Monthly Sales Trend", "Track momentum shifts across the selected period.")
    trend_fig = px.line(
        trend_df,
        x="Month",
        y="Sales",
        markers=True,
    )
    trend_fig.update_traces(line=dict(width=4), marker=dict(size=8))
    style_figure(trend_fig, ["#0f766e", "#155e75"], height=360)
    st.plotly_chart(trend_fig, use_container_width=True)
    panel_end()

with overview_right:
    panel_start("Sales by Region", "Identify where demand concentration is strongest.")
    region_fig = px.bar(
        region_df,
        x="Region",
        y="Sales",
        color="Sales",
        color_continuous_scale=["#99f6e4", "#0f766e", "#134e4a"],
    )
    region_fig.update_layout(coloraxis_showscale=False)
    style_figure(region_fig, ["#0f766e"], height=360)
    st.plotly_chart(region_fig, use_container_width=True)
    panel_end()

detail_left, detail_right = st.columns(2)

with detail_left:
    panel_start("Category Contribution", "Compare how each product family is shaping topline revenue.")
    category_fig = px.bar(
        category_df,
        x="Category",
        y="Sales",
        color="Category",
        color_discrete_sequence=["#0f766e", "#155e75", "#f59e0b", "#ef4444", "#14b8a6"],
    )
    category_fig.update_layout(showlegend=False)
    style_figure(category_fig, ["#0f766e", "#155e75"], height=350)
    st.plotly_chart(category_fig, use_container_width=True)
    panel_end()

with detail_right:
    panel_start("Top Products", "Surface the individual products driving the strongest revenue impact.")
    product_fig = px.bar(
        product_df.sort_values("Sales"),
        x="Sales",
        y="Product Name",
        orientation="h",
        color="Sales",
        color_continuous_scale=["#dbeafe", "#0ea5e9", "#1d4ed8"],
    )
    product_fig.update_layout(coloraxis_showscale=False)
    style_figure(product_fig, ["#1d4ed8"], height=350)
    st.plotly_chart(product_fig, use_container_width=True)
    panel_end()

section_title("AI Copilot")
st.markdown(
    """
    <div class="copilot-shell">
        <div class="copilot-title">Narrative Intelligence</div>
        <div class="copilot-copy">
            Ask for an executive summary, a chart explanation, or a focused recommendation based on the current dashboard state.
        </div>
    """,
    unsafe_allow_html=True,
)

insight_context = build_insight_context(filtered_df)
prompt_left, prompt_right = st.columns([2.2, 1])
with prompt_left:
    question = st.text_input(
        "Question for the model",
        placeholder="Example: Which category needs attention and why?",
        label_visibility="collapsed",
    )
with prompt_right:
    auto_refresh_ai = st.toggle("Auto-refresh insights", value=False)

if "insight_cache" not in st.session_state:
    st.session_state.insight_cache = {}

signature = build_filter_signature(insight_context, question)
generate_col, spacer_col = st.columns([0.4, 1.6])
with generate_col:
    should_generate = st.button("Generate Insight", type="primary", use_container_width=True) or (
        auto_refresh_ai and signature not in st.session_state.insight_cache
    )

if should_generate:
    with st.spinner("Generating executive insight..."):
        st.session_state.insight_cache[signature] = generate_executive_insight(
            insight_context,
            question=question or None,
        )

result = st.session_state.insight_cache.get(signature)
st.markdown('<div class="insight-box">', unsafe_allow_html=True)
if result:
    if result.status == "success":
        st.markdown(result.content)
    elif result.status in {"missing_dependency", "missing_api_key"}:
        st.info(result.content)
    else:
        st.error(result.content)
else:
    st.info("Generate an AI insight to analyze the currently filtered view.")
st.markdown("</div></div>", unsafe_allow_html=True)

with st.expander("View analytics payload sent to the model"):
    st.json(insight_context)

section_title("Embedded Reporting")
render_powerbi_section()
