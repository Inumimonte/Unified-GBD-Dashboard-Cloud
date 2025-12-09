import streamlit as st
import plotly.express as px
import pandas as pd

from gbd_utils import load_data

st.title("📌 Insights & Cross-cutting Analytics")

st.markdown(
    """
This page provides **cross-cutting insights** across all domains  
(NCDs, injuries, maternal, neonatal, and other causes) using the unified fact table.

Use the controls below to:
- Choose a **metric** (DALYs, deaths, incidence, etc.)
- Focus on a particular **location** and **year range**
- See **top causes**, **top states for a selected cause**, and **burden trends**
- Read automatically generated **summary interpretations**
"""
)

# ------------------------------------------------------------
# Load data
# ------------------------------------------------------------
df = load_data()

# Basic sanity
if df.empty:
    st.error("No data loaded. Please check the unified fact table.")
    st.stop()

# ------------------------------------------------------------
# Controls
# ------------------------------------------------------------
st.sidebar.header("Insights filters")

# Metric selector
metric_options = sorted(df["measure_name_standard"].unique())
metric_sel = st.sidebar.selectbox("Metric", metric_options)

# Location selector (national/all vs specific state)
locations = ["All locations"] + sorted(df["location_name"].unique())
loc_sel = st.sidebar.selectbox("Location", locations)

# Year range
years_all = sorted(df["year"].unique())
min_year, max_year = min(years_all), max(years_all)
year_range = st.sidebar.slider(
    "Year range",
    min_value=int(min_year),
    max_value=int(max_year),
    value=(int(min_year), int(max_year)),
    step=1,
)

# ------------------------------------------------------------
# Filter data according to selections
# ------------------------------------------------------------
mask = (df["measure_name_standard"] == metric_sel) & \
       (df["year"].between(year_range[0], year_range[1]))

if loc_sel != "All locations":
    mask &= df["location_name"] == loc_sel

f = df[mask].copy()

st.write(f"Filtered rows for insights: **{len(f):,}**")

if f.empty:
    st.warning("No data for the selected filters.")
    st.stop()

# ------------------------------------------------------------
# Overall dominant cause & totals
# ------------------------------------------------------------
cause_agg = (
    f.groupby("cause_name", as_index=False)["val"]
    .sum()
    .sort_values("val", ascending=False)
)

dom_cause = cause_agg.iloc[0]["cause_name"]
dom_val = cause_agg.iloc[0]["val"]
total_val = cause_agg["val"].sum()
share_dom = dom_val / total_val if total_val > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Dominant cause", dom_cause)
with col2:
    st.metric(f"Total {metric_sel}", f"{total_val:,.1f}")
with col3:
    st.metric(f"% contribution of {dom_cause}", f"{share_dom * 100:,.1f}%")

# ------------------------------------------------------------
# Top 10 causes (for metric & filters)
# ------------------------------------------------------------
st.markdown("### Top 10 causes for selected metric")

top10_causes = cause_agg.head(10)

fig_top_causes = px.bar(
    top10_causes,
    x="val",
    y="cause_name",
    orientation="h",
    labels={
        "val": metric_sel,
        "cause_name": "Cause",
    },
    title=f"Top 10 causes by {metric_sel}",
)

fig_top_causes.update_layout(
    height=450,
    margin=dict(l=260, r=40, t=60, b=40),
    yaxis={"categoryorder": "total ascending"},
)

st.plotly_chart(fig_top_causes, use_container_width=True, key="ins_top_causes")

# ------------------------------------------------------------
# National / location trend over time
# ------------------------------------------------------------
st.markdown("### Burden trend over time")

trend = (
    f.groupby("year", as_index=False)["val"]
    .sum()
    .sort_values("year")
)

fig_trend = px.line(
    trend,
    x="year",
    y="val",
    markers=True,
    labels={"val": metric_sel, "year": "Year"},
    title=f"{metric_sel} trend over time ({loc_sel})",
)

fig_trend.update_layout(
    height=400,
    margin=dict(l=40, r=40, t=40, b=80),
)

st.plotly_chart(fig_trend, use_container_width=True, key="ins_trend")

# ------------------------------------------------------------
# Top states for a selected cause
# ------------------------------------------------------------
st.markdown("### Top locations for a selected cause")

cause_for_states = st.selectbox(
    "Select cause to explore state/location ranking",
    options=top10_causes["cause_name"].tolist(),
)

f_cause = f[f["cause_name"] == cause_for_states]

loc_agg = (
    f_cause.groupby("location_name", as_index=False)["val"]
    .sum()
    .sort_values("val", ascending=False)
)

top_n_for_cause = st.slider("Number of top locations", 3, 20, 10, 1)

top_loc = loc_agg.head(top_n_for_cause)

fig_states = px.bar(
    top_loc,
    x="val",
    y="location_name",
    orientation="h",
    labels={
        "val": metric_sel,
        "location_name": "Location",
    },
    title=f"Top {top_n_for_cause} locations for {cause_for_states} ({metric_sel})",
)

fig_states.update_layout(
    height=450,
    margin=dict(l=180, r=40, t=60, b=40),
    yaxis={"categoryorder": "total ascending"},
)

st.plotly_chart(fig_states, use_container_width=True, key="ins_top_locations")

# ------------------------------------------------------------
# Simple text insights
# ------------------------------------------------------------
st.markdown("### Auto-generated insight")

trend_first = trend.iloc[0]
trend_last = trend.iloc[-1]
abs_change = trend_last["val"] - trend_first["val"]
rel_change = (abs_change / trend_first["val"]) if trend_first["val"] != 0 else 0

loc_phrase = "nationally" if loc_sel == "All locations" else f"in **{loc_sel}**"

direction = "increased" if abs_change > 0 else "decreased" if abs_change < 0 else "remained stable"

st.write(
    f"- For **{metric_sel}** {loc_phrase}, the total burden has **{direction}** from "
    f"**{trend_first['year']}** to **{trend_last['year']}**, changing by "
    f"**{abs_change:,.1f}** ({rel_change * 100:,.1f}%)."
)
st.write(
    f"- The leading cause in this period is **{dom_cause}**, contributing about "
    f"**{share_dom * 100:,.1f}%** of the total {metric_sel}."
)
st.write(
    f"- For **{cause_for_states}**, the highest-burden locations are: "
    + ", ".join(top_loc['location_name'].head(5).tolist())
    + "."
)

# ------------------------------------------------------------
# Data preview & download
# ------------------------------------------------------------
with st.expander("Data preview & download"):
    st.write("Filtered data preview (first 50 rows):")
    st.dataframe(f.head(50), use_container_width=True)

    csv_insights = f.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered insights dataset (CSV)",
        data=csv_insights,
        file_name="gbd_insights_filtered.csv",
        mime="text/csv",
        key="download_insights_filtered",
    )
