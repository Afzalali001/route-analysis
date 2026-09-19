import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

# Project root (works locally, from any cwd, and on Streamlit Cloud)
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Page Configuration
st.set_page_config(
    page_title="Nassau Candy Route Analysis",
    page_icon="🚚",
    layout="wide"
)

# Dashboard Title
st.title("🚚 Factory-to-Customer Shipping Route Efficiency Dashboard")
st.markdown("""
### Nassau Candy Distributor

Analyze shipping efficiency, bottlenecks, routes and logistics performance.
""")

# -----------------------
# Data Loading (cached across reruns)
# -----------------------

@st.cache_data
def load_data():
    df = pd.read_csv(PROJECT_ROOT / "data/processed/feature_engineered_data.csv")
    route_summary = pd.read_csv(PROJECT_ROOT / "data/processed/route_state_summary.csv")
    return df, route_summary

df, route_summary = load_data()

# -----------------------
# Sidebar Filters
# -----------------------

st.sidebar.header("🔍 Filters")

selected_region = st.sidebar.selectbox(
    "Select Region",
    ["All"] + sorted(df["Region"].unique().tolist())
)

selected_ship_mode = st.sidebar.selectbox(
    "Select Ship Mode",
    ["All"] + sorted(df["Ship Mode"].unique().tolist())
)

filtered_df = df.copy()

if selected_region != "All":
    filtered_df = filtered_df[filtered_df["Region"] == selected_region]

if selected_ship_mode != "All":
    filtered_df = filtered_df[filtered_df["Ship Mode"] == selected_ship_mode]

if filtered_df.empty:
    st.warning("⚠️ No shipments match the selected filters. Try a different Region or Ship Mode.")
    st.stop()

# -----------------------
# Aggregations (computed once per rerun)
# -----------------------

filtered_route_summary = (
    filtered_df.groupby("Factory_State_Route")
    .agg(
        Total_Shipments=("Order ID", "count"),
        Average_Lead_Time=("Shipping Lead Time", "mean")
    )
    .reset_index()
)

ship_mode = (
    filtered_df.groupby("Ship Mode")
    .agg(
        Total_Shipments=("Order ID", "count"),
        Average_Lead_Time=("Shipping Lead Time", "mean")
    )
    .reset_index()
)

region_summary = (
    filtered_df.groupby("Region")
    .agg(
        Total_Shipments=("Order ID", "count"),
        Average_Lead_Time=("Shipping Lead Time", "mean")
    )
    .reset_index()
)

state_summary = (
    filtered_df.groupby("State/Province")
    .agg(
        Total_Shipments=("Order ID", "count"),
        Average_Lead_Time=("Shipping Lead Time", "mean")
    )
    .reset_index()
)

# ==========================
# KPI Cards
# ==========================

st.divider()
st.header("📊 Route Analysis")

delay = (filtered_df["Delay Flag"] == "Delayed").mean() * 100

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📦 Total Shipments", len(filtered_df))

with col2:
    st.metric(
        "🚚 Avg Lead Time",
        f"{filtered_df['Shipping Lead Time'].mean():.2f} Days"
    )

with col3:
    st.metric("⏰ Delay %", f"{delay:.2f}%")

with col4:
    st.metric("💰 Total Sales", f"${filtered_df['Sales'].sum():,.0f}")

# ==========================
# Route Volume & Efficiency
# ==========================

st.subheader("📦 Route Volume & Efficiency")

kpi1, kpi2 = st.columns(2)

with kpi1:
    top_volume = route_summary["Route_Volume"].max()
    top_route = route_summary.loc[
        route_summary["Route_Volume"].idxmax(),
        "Factory_State_Route"
    ]
    st.metric("📦 Highest Volume Route", f"{top_volume:,} Shipments")
    st.caption(top_route)

with kpi2:
    best_score = route_summary["Route_Efficiency_Score"].max()
    best_route = route_summary.loc[
        route_summary["Route_Efficiency_Score"].idxmax(),
        "Factory_State_Route"
    ]
    st.metric("🎯 Best Route Efficiency", f"{best_score:.1f}/100")
    st.caption(best_route)

# ==========================
# Top 10 Routes Table
# ==========================

st.subheader("📦 Top 10 Routes by Shipment Volume")

route_volume_display = (
    route_summary[
        ["Factory_State_Route", "Route_Volume", "Average_Lead_Time", "Route_Efficiency_Score"]
    ]
    .sort_values("Route_Volume", ascending=False)
    .head(10)
    .assign(
        Average_Lead_Time=lambda d: d["Average_Lead_Time"].round(2),
        Route_Efficiency_Score=lambda d: d["Route_Efficiency_Score"].round(1),
    )
    .rename(columns={
        "Factory_State_Route": "Route",
        "Route_Volume": "Shipments",
        "Average_Lead_Time": "Avg Lead Time (Days)",
        "Route_Efficiency_Score": "Efficiency Score"
    })
)

st.dataframe(route_volume_display, width="stretch", hide_index=True)

# ==========================
# Top / Bottom 10 Route Charts
# ==========================

top10 = filtered_route_summary.nsmallest(10, "Average_Lead_Time")
bottom10 = filtered_route_summary.nlargest(10, "Average_Lead_Time")

fig = px.bar(
    top10,
    x="Average_Lead_Time",
    y="Factory_State_Route",
    orientation="h",
    title="🏆 Top 10 Most Efficient Routes",
    color="Average_Lead_Time"
)

fig2 = px.bar(
    bottom10,
    x="Average_Lead_Time",
    y="Factory_State_Route",
    orientation="h",
    title="⚠️ Bottom 10 Least Efficient Routes",
    color="Average_Lead_Time"
)

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig, width="stretch", key="top10_chart")

with col2:
    st.plotly_chart(fig2, width="stretch", key="bottom10_chart")

# ==========================
# Ship Mode Performance
# ==========================

st.divider()
st.header("🚚 Ship Mode Analysis")

fig3 = px.bar(
    ship_mode,
    x="Ship Mode",
    y="Average_Lead_Time",
    color="Ship Mode",
    title="🚚 Average Shipping Lead Time by Ship Mode",
    text_auto=".2f"
)

st.plotly_chart(fig3, width="stretch")

st.subheader("📋 Ship Mode Summary")
st.dataframe(ship_mode, width="stretch")

# ==========================
# Region Performance
# ==========================

st.divider()
st.header("🌍 Geographic Analysis")
st.subheader("🌍 Region Performance")

fig4 = px.bar(
    region_summary,
    x="Region",
    y="Average_Lead_Time",
    color="Region",
    title="Average Shipping Lead Time by Region",
    text_auto=".2f"
)

st.plotly_chart(fig4, width="stretch")

st.subheader("📍 Top 10 States with Highest Lead Time")

top_states = state_summary.nlargest(10, "Average_Lead_Time")

fig5 = px.bar(
    top_states,
    x="Average_Lead_Time",
    y="State/Province",
    orientation="h",
    color="Average_Lead_Time",
    title="Top 10 States with Highest Shipping Lead Time",
    text_auto=".2f"
)

st.plotly_chart(fig5, width="stretch")

# ==========================
# Business Insights
# ==========================

st.divider()
st.header("📈 Business Insights")

fastest_route = filtered_route_summary.loc[
    filtered_route_summary["Average_Lead_Time"].idxmin()
]

slowest_route = filtered_route_summary.loc[
    filtered_route_summary["Average_Lead_Time"].idxmax()
]

best_ship_mode = ship_mode.loc[
    ship_mode["Average_Lead_Time"].idxmin()
]

worst_region = region_summary.loc[
    region_summary["Average_Lead_Time"].idxmax()
]

st.success(
    f"🏆 Fastest Route: {fastest_route['Factory_State_Route']} "
    f"({fastest_route['Average_Lead_Time']:.2f} days)"
)

st.error(
    f"⚠️ Slowest Route: {slowest_route['Factory_State_Route']} "
    f"({slowest_route['Average_Lead_Time']:.2f} days)"
)

st.info(f"🚚 Best Ship Mode: {best_ship_mode['Ship Mode']}")

st.warning(f"🌍 Region Needing Attention: {worst_region['Region']}")

# ==========================
# Download & Footer
# ==========================

st.download_button(
    label="📥 Download Filtered Data",
    data=filtered_df.to_csv(index=False),
    file_name="filtered_shipping_data.csv",
    mime="text/csv"
)

st.divider()

st.markdown("""
### 📌 Dashboard Information

**Project:** Factory-to-Customer Shipping Route Efficiency Analysis

**Developed By:** Yash

**Tools Used:** Python | Pandas | Streamlit | Plotly
""")
