# pages/1_Overview.py

import streamlit as st
import plotly.express as px
from gbd_utils import load_data, filter_data, compute_dominant_cause, CAUSE_COLORS

st.title("📊 Overview")

df = load_data()

# Sidebar-like filters (inside this page)
st.sidebar.header("Filters (Overview)")

years_all = sorted(df["year"].unique())
year_selected = st.sidebar.multiselect("Year", years_all, default=years_all)

locations = sorted(df["location_name"].unique())
location_selected = st.sidebar.multiselect("Location", locations)

measures = sorted(df["measure_name_standard"].unique())
measure_selected = st.sidebar.multiselect("Measure", measures, default=["DALYs Rate"])

sexes = sorted(df["sex_name"].unique())
sex_selected = st.sidebar.multiselect("Sex", sexes)

ages = sorted(df["age_name"].unique())
age_selected = st.sidebar.multiselect("Age group", ages)

df_filtered = filter_data(
    df,
    year=year_selected,
    location=location_selected,
    measure=measure_selected,
    sex=sex_selected,
    age_group=age_selected,
)

st.sidebar.write(f"Filtered rows: {len(df_filtered):,}")

# ---- Key Metrics ----
st.subheader("Key Metrics")

dominant_cause, dominant_val, dominant_share = compute_dominant_cause(df_filtered)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Dominant Cause", value=dominant_cause or "No data")

with col2:
    st.metric(
        "Burden Value",
        value=f"{dominant_val:,.1f}",
        help="Sum of 'val' for the dominant cause within current filters.",
    )

with col3:
    st.metric(
        "% of Total Burden",
        value=f"{dominant_share * 100:,.1f}%",
    )

# ---- Top 10 Causes ----
st.subheader("Top 10 Causes by Burden (val)")

if df_filtered.empty:
    st.warning("No data for the current filter selection.")
else:
    top_causes = (
        df_filtered.groupby("cause_name", as_index=False)["val"]
        .sum()
        .sort_values("val", ascending=False)
        .head(10)
    )

    fig_bar = px.bar(
        top_causes,
        x="val",
        y="cause_name",
        orientation="h",
        color="cause_name",
        color_discrete_map=CAUSE_COLORS,
        labels={"val": "Burden (Rate)", "cause_name": "Cause"},
        title="Top 10 Causes",
    )
    fig_bar.update_layout(yaxis={"categoryorder": "total ascending"})

    st.plotly_chart(fig_bar, use_container_width=True, key="top10_causes_chart")

# ---- Trend Over Time ----
st.subheader("Trend Over Time")

trend = (
    df_filtered
    .groupby(["year", "location_name"], as_index=False)["val"]
    .sum()
    .sort_values("year")
)

if trend.empty:
    st.info("No trend data available for current filters.")
else:
    fig2 = px.line(
        trend,
        x="year",
        y="val",
        color="location_name",
        markers=True,
        title="Trend Over Time by Location",
    )

    st.plotly_chart(fig2, use_container_width=True, key="trend_over_time_chart")

# ---- Filtered Data Preview ----
st.subheader("Filtered Data (Preview)")
st.dataframe(df_filtered.head(100))
