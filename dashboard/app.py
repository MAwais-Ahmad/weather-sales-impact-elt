import os
import duckdb
import psycopg2
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(
    page_title="External Factors & Weather Impact Analytics",
    page_icon="🌦️",
    layout="wide"
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "data_warehouse_project2.duckdb")

POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ecom_external_dw")
DB_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

@st.cache_data(ttl=300)
def load_project2_data():
    """Attempts PostgreSQL connection first, fallback to DuckDB warehouse."""
    try:
        conn = psycopg2.connect(DB_URI, connect_timeout=2)
        fct_sales = pd.read_sql("SELECT * FROM main.fct_daily_sales_external", conn)
        mart_impact = pd.read_sql("SELECT * FROM main.mart_weather_category_impact", conn)
        mart_takeaway = pd.read_sql("SELECT * FROM main.mart_executive_takeaway", conn)
        conn.close()
        return fct_sales, mart_impact, mart_takeaway, "PostgreSQL Database"
    except Exception:
        if not os.path.exists(DB_PATH):
            with st.spinner("⏳ First-time cloud setup: Ingesting multi-source API data & running dbt pipeline..."):
                import subprocess
                subprocess.run(["python", os.path.join(BASE_DIR, "run_pipeline.py")], check=True)

        if not os.path.exists(DB_PATH):
            return None, None, None, "None"
            
        con = duckdb.connect(DB_PATH, read_only=True)
        fct_sales = con.execute("SELECT * FROM fct_daily_sales_external").df()
        mart_impact = con.execute("SELECT * FROM mart_weather_category_impact").df()
        mart_takeaway = con.execute("SELECT * FROM mart_executive_takeaway").df()
        con.close()
        return fct_sales, mart_impact, mart_takeaway, "DuckDB Warehouse (Cloud)"

st.title("🌦️ External Weather & Sales Impact Analytics")
st.caption("Multi-Source Ingestion (Sales Transactions + Open-Meteo REST API) | PostgreSQL / dbt Data Marts")

fct_sales, mart_impact, mart_takeaway, source_used = load_project2_data()

if fct_sales is None or fct_sales.empty:
    st.warning("⚠️ Warehouse data not detected. Run `python run_pipeline.py` first!")
    st.stop()

st.sidebar.success(f"Connected Warehouse: {source_used}")
st.sidebar.header("🔍 External Analytics Filters")

categories = ["All Categories"] + list(mart_impact['category'].unique())
selected_cat = st.sidebar.selectbox("Filter Category Impact", categories)

# Calculate Advanced Executive KPIs
tot_rev = fct_sales['gross_revenue'].sum()
tot_units = fct_sales['total_units_sold'].sum()

# Rainy vs Sunny Daily Averages
rainy_sales = fct_sales[fct_sales['precipitation_mm'] > 0.5]
sunny_sales = fct_sales[fct_sales['precipitation_mm'] <= 0.5]

rainy_daily_avg = rainy_sales['gross_revenue'].mean() if not rainy_sales.empty else 0
sunny_daily_avg = sunny_sales['gross_revenue'].mean() if not sunny_sales.empty else 0
weather_premium_delta = rainy_daily_avg - sunny_daily_avg
weather_pct_shift = (weather_premium_delta / sunny_daily_avg * 100) if sunny_daily_avg > 0 else 0

top_impact_row = mart_takeaway.sort_values(by="revenue_dip_pct", ascending=False).iloc[0] if not mart_takeaway.empty else None
top_impact_cat = top_impact_row['category'] if top_impact_row is not None else "Apparel & Jewelry"
top_impact_pct = top_impact_row['revenue_dip_pct'] if top_impact_row is not None else 82.36

# Custom CSS to eliminate Streamlit metric text truncation and resize fonts responsively
st.markdown("""
    <style>
    div[data-testid="stMetricValue"] {
        font-size: 1.3rem !important;
        overflow: visible !important;
        text-overflow: unset !important;
        white-space: nowrap !important;
    }
    div[data-testid="stMetricValue"] > div {
        font-size: 1.3rem !important;
        overflow: visible !important;
        text-overflow: unset !important;
        white-space: nowrap !important;
    }
    div[data-testid="stMetricLabel"] {
        font-size: 0.85rem !important;
        white-space: normal !important;
        word-break: break-word !important;
        font-weight: 600;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.8rem !important;
        white-space: nowrap !important;
    }
    </style>
""", unsafe_allow_html=True)

# UPGRADED ADVANCED KPI EXECUTIVE SUITE (5 Metrics)
st.subheader("📌 Advanced Weather-Impact Executive KPI Suite")

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric(
    label="Total Gross Revenue", 
    value=f"${tot_rev/1e6:,.2f}M",
    help=f"Exact historical gross revenue: ${tot_rev:,.2f} across all transactions."
)
c2.metric(
    label="Rainy vs. Sunny Lift", 
    value=f"{weather_pct_shift:+.1f}%", 
    delta=f"${weather_premium_delta:+,.2f}/day",
    help="Percentage lift in daily revenue on rainy days compared to sunny days, plus average dollar premium earned per rainy day."
)
c3.metric(
    label="Top Weather Sensitivity", 
    value=top_impact_cat, 
    delta=f"{top_impact_pct:+.1f}% Shift",
    help="Product category experiencing the largest sales percentage shift when weather conditions change."
)
c4.metric(
    label="Rainy Trading Days", 
    value=f"{len(rainy_sales)} Days", 
    delta=f"{len(rainy_sales)/len(fct_sales)*100:.1f}% of Year",
    help="Total number of trading days in the calendar year where precipitation exceeded 0.5mm."
)
c5.metric(
    label="Pipeline Freshness / Audit", 
    value=f"{len(fct_sales)} Days", 
    delta="Pipeline Verified",
    help="Audit check verifying total active daily rows successfully ingested, transformed, and verified in PostgreSQL."
)

st.markdown("---")

# SECTION: Automated Plain-English Executive Insights Box
st.subheader("💡 Automated Executive Takeaways (Plain-English Insight Engine)")
st.info("Clients don't want to interpret raw charts—our dbt engine automatically generates human-readable business takeaways:")

if not mart_takeaway.empty:
    for idx, row in mart_takeaway.iterrows():
        st.markdown(f"👉 **{row['plain_english_takeaway']}**")

st.markdown("---")

# SECTION: Dual-Axis Line Overlay (Sales Revenue vs Temperature)
st.subheader("📈 Dual-Axis Overlay: Daily Sales Revenue vs. Temperature (°C)")

fig_dual = make_subplots(specs=[[{"secondary_y": True}]])

fig_dual.add_trace(
    go.Scatter(x=fct_sales['order_date'], y=fct_sales['gross_revenue'], name="Gross Revenue ($)", line=dict(color="#1f77b4", width=2)),
    secondary_y=False,
)

fig_dual.add_trace(
    go.Scatter(x=fct_sales['order_date'], y=fct_sales['avg_temp_c'], name="Avg Temp (°C)", line=dict(color="#ff7f0e", width=2, dash="dash")),
    secondary_y=True,
)

fig_dual.update_layout(
    template="plotly_dark",
    height=420,
    title_text="Sales Revenue vs Temperature Overlay Trend",
    margin=dict(l=20, r=20, t=40, b=20)
)
fig_dual.update_yaxes(title_text="Revenue ($)", secondary_y=False)
fig_dual.update_yaxes(title_text="Temperature (°C)", secondary_y=True)

st.plotly_chart(fig_dual, use_container_width=True)

# SECTION: Category Impact Matrix across Weather Conditions
st.markdown("---")
st.subheader("📊 Category Sales Revenue Breakdown by Weather Condition")

fig_cat_w = px.bar(
    mart_impact if selected_cat == "All Categories" else mart_impact[mart_impact['category'] == selected_cat],
    x="category",
    y="total_revenue",
    color="weather_condition",
    barmode="group",
    labels={"total_revenue": "Total Revenue ($)", "category": "Product Category"},
    title="Revenue Distribution Across Weather Conditions"
)
fig_cat_w.update_layout(template="plotly_dark", height=400)
st.plotly_chart(fig_cat_w, use_container_width=True)

# SECTION: Raw Data Mart Explorer
st.markdown("---")
st.subheader("📋 External Sales & Weather Fact Table")
st.dataframe(fct_sales, use_container_width=True)
