import streamlit as st
import pandas as pd
import plotly.express as px

from gbd_utils import load_data

st.set_page_config(page_title="Injuries Dashboard", page_icon="💊", layout="wide")

st.title("💊 Injuries Dashboard")

# -------------------------------------------------------------------
# Load and subset data
# -------------------------------------------------------------------
data = load_data()

# Keep only rows coming from the Injuries file
injury_data = data[data["source_file"] == "Injuries_Rate.csv"].copy()

if injury_data.empty:
    st.error("No rows found from 'Injuries_Rate.csv' in the unified dataset.")
    st.stop()

# -------------------------------------------------------------------
# Sidebar filters
# -------------------------------------------------------------------
with st.sidebar:
    st.header("Filters (Injuries)")

    # Metric selector
    metric_options = sorted(injury_data["measure_name_standard"].unique())
    default_metric = "DALYs Rate" if "DALYs Rate" in metric_options else metric_options[0]

    selected_metric = st.selectbox(
        "Injury metric",
        metric_options,
        index=metric_options.index(default_metric),
        help="Select which metric (rate) to analyze for injuries.",
    )

    years = st.multiselect(
        "Year",
        sorted(injury_data["year"].unique()),
        default=sorted(injury_data["year"].unique()),
    )

    states = st.multiselect(
        "States / locations",
        sorted(injury_data["location_name"].unique()),
        default=sorted(injury_data["location_name"].unique()),
    )

    sexes = st.multiselect(
        "Sex",
        sorted(injury_data["sex_name"].unique()),
        default=sorted(injury_data["sex_name"].unique()),
    )

    ages = st.multiselect(
        "Age group",
        sorted(injury_data["age_name"].unique()),
        default=sorted(injury_data["age_name"].unique()),
    )

    # 🔹 New: choose which injury causes you want to compare/include
    cause_options = sorted(injury_data["cause_name"].unique())
    selected_causes = st.multiselect(
        "Injury causes to include (for comparison)",
        cause_options,
        default=cause_options,  # start with all included
    )

    st.caption(f"Metric in use: **{selected_metric}**")

# -------------------------------------------------------------------
# Apply filters
# -------------------------------------------------------------------
filtered = injury_data[
    (injury_data["measure_name_standard"] == selected_metric)
    & (injury_data["year"].isin(years))
    & (injury_data["location_name"].isin(states))
    & (injury_data["sex_name"].isin(sexes))
    & (injury_data["age_name"].isin(ages))
    & (injury_data["cause_name"].isin(selected_causes)) 
].copy()

if filtered.empty:
    st.warning("No injury records match the current filters.")
    st.stop()

# -------------------------------------------------------------------
# Key metrics
# -------------------------------------------------------------------
cause_agg = (
    filtered.groupby("cause_name", as_index=False)["val"]
    .sum()
    .sort_values("val", ascending=False)
)

dominant_cause_row = cause_agg.iloc[0]
dominant_cause = dominant_cause_row["cause_name"]
dominant_val = dominant_cause_row["val"]
total_burden = cause_agg["val"].sum()
dominant_share = (dominant_val / total_burden * 100) if total_burden > 0 else 0

st.subheader("Key Injury Metrics")

c1, c2, c3 = st.columns([2, 1, 1])

with c1:
    st.markdown("**Dominant injury cause**")
    st.markdown(
        f"<h2 style='margin-top:0'>{dominant_cause}</h2>",
        unsafe_allow_html=True,
    )

with c2:
    st.markdown(f"**Total {selected_metric}**")
    st.metric(
        label="",
        value=f"{total_burden:,.1f}",
    )

with c3:
    st.markdown(f"**% contribution of {dominant_cause}**")
    st.metric(
        label="",
        value=f"{dominant_share:,.1f}%",
    )

st.caption(f"Rows after filters: **{len(filtered):,}**")

# -------------------------------------------------------------------
# Top injury causes (bar)
# -------------------------------------------------------------------
st.markdown("### Top Injury Causes by Burden")

top10 = cause_agg.head(10)

fig_bar = px.bar(
    top10,
    x="val",
    y="cause_name",
    orientation="h",
    color="cause_name",
    labels={"val": selected_metric, "cause_name": "Injury cause"},
    title=f"Top 10 Injury Causes by {selected_metric}",
)

fig_bar.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    margin=dict(l=220, r=40, t=60, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)

st.plotly_chart(fig_bar, use_container_width=True)

# -------------------------------------------------------------------
# Trend over time by cause
# -------------------------------------------------------------------
st.markdown("### Injury Trend Over Time by Cause")

trend_cause = (
    filtered.groupby(["year", "cause_name"], as_index=False)["val"]
    .mean()
    .sort_values(["cause_name", "year"])
)

fig_trend = px.line(
    trend_cause,
    x="year",
    y="val",
    color="cause_name",
    markers=True,
    labels={"val": selected_metric, "cause_name": "Injury cause"},
    title=f"{selected_metric} Trend Over Time by Injury Cause",
)

fig_trend.update_layout(
    margin=dict(l=80, r=40, t=60, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)

st.plotly_chart(fig_trend, use_container_width=True)

# -------------------------------------------------------------------
# Trend over time by cause & state (top N or custom)
# -------------------------------------------------------------------
st.markdown("### Injury Trend Over Time by Cause & State")

cause_for_states = st.selectbox(
    "Select injury cause for state-level trend",
    sorted(filtered["cause_name"].unique()),
)

subset_cause = filtered[filtered["cause_name"] == cause_for_states].copy()

mode = st.radio(
    "State view mode",
    ["Top N states (by burden)", "Choose states manually"],
    horizontal=True,
)

if mode == "Top N states (by burden)":
    N = st.slider("Number of top states (N)", min_value=3, max_value=15, value=5)
    state_totals = (
        subset_cause.groupby("location_name", as_index=False)["val"]
        .sum()
        .sort_values("val", ascending=False)
    )
    top_states = list(state_totals.head(N)["location_name"])
    state_list = top_states
    st.caption(
        "Top states by total "
        f"**{cause_for_states} – {selected_metric}**: "
        + ", ".join(top_states)
    )
else:
    state_list = st.multiselect(
        "Choose states manually",
        sorted(subset_cause["location_name"].unique()),
        default=sorted(subset_cause["location_name"].unique())[:5],
    )

apply_smoothing = st.checkbox("Apply 3-year moving average smoothing", value=False)

state_trend = (
    subset_cause[subset_cause["location_name"].isin(state_list)]
    .groupby(["year", "location_name"], as_index=False)["val"]
    .mean()
    .sort_values(["location_name", "year"])
)

if apply_smoothing and not state_trend.empty:
    # Simple 3-year rolling mean per state
    state_trend["val"] = (
        state_trend
        .groupby("location_name")["val"]
        .rolling(3, min_periods=1)
        .mean()
        .reset_index(level=0, drop=True)
    )

# National average line
nat_trend = (
    subset_cause.groupby("year", as_index=False)["val"]
    .mean()
    .rename(columns={"val": "national_avg"})
)

fig_state_trend = px.line(
    state_trend,
    x="year",
    y="val",
    color="location_name",
    markers=True,
    labels={
        "val": selected_metric,
        "location_name": "State / location",
    },
    title=f"{selected_metric} Trend for '{cause_for_states}' by State",
)

# Add national average as separate trace
if not nat_trend.empty:
    fig_state_trend.add_scatter(
        x=nat_trend["year"],
        y=nat_trend["national_avg"],
        mode="lines",
        name="National average",
        line=dict(dash="dash"),
    )

fig_state_trend.update_layout(
    margin=dict(l=80, r=40, t=60, b=40),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
    ),
)

st.plotly_chart(fig_state_trend, use_container_width=True)

# -------------------------------------------------------------------
# State ranking for injuries
# -------------------------------------------------------------------
st.markdown("### State Ranking for Injuries")

state_totals_all = (
    filtered.groupby("location_name", as_index=False)["val"]
    .sum()
    .sort_values("val", ascending=False)
)

top5 = state_totals_all.head(5)
bottom5 = state_totals_all.tail(5).sort_values("val", ascending=True)

c_top, c_bottom = st.columns(2)

with c_top:
    st.markdown("**Top 5 states by total injury burden**")
    fig_top = px.bar(
        top5,
        x="val",
        y="location_name",
        orientation="h",
        labels={"val": selected_metric, "location_name": "State"},
    )
    fig_top.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=120, r=10, t=40, b=40),
    )
    st.plotly_chart(fig_top, use_container_width=True)
    st.dataframe(top5.rename(columns={"val": "total_burden"}))

with c_bottom:
    st.markdown("**Bottom 5 states by total injury burden**")
    fig_bottom = px.bar(
        bottom5,
        x="val",
        y="location_name",
        orientation="h",
        labels={"val": selected_metric, "location_name": "State"},
    )
    fig_bottom.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        margin=dict(l=120, r=10, t=40, b=40),
    )
    st.plotly_chart(fig_bottom, use_container_width=True)
    st.dataframe(bottom5.rename(columns={"val": "total_burden"}))

    # -----------------------------
# Compare two injury causes by state
# -----------------------------
st.markdown("### Compare two injury causes by state")

# only use causes that exist after current filters
inj_compare_causes = sorted(filtered["cause_name"].unique())
if len(inj_compare_causes) < 2:
    st.info("Not enough injury causes in the filtered data to compare (need at least 2).")
else:
    col_a, col_b = st.columns(2)
    with col_a:
        primary_inj_cause = st.selectbox(
            "Primary injury cause",
            inj_compare_causes,
            key="inj_compare_primary",
        )
    with col_b:
        secondary_inj_cause = st.selectbox(
            "Comparison injury cause",
            inj_compare_causes,
            index=1 if len(inj_compare_causes) > 1 else 0,
            key="inj_compare_secondary",
        )

    if primary_inj_cause == secondary_inj_cause:
        st.warning("Please choose two different injury causes to compare.")
    else:
        inj_compare_df = (
            filtered[filtered["cause_name"].isin([primary_inj_cause, secondary_inj_cause])]
            .groupby(["location_name", "cause_name"], as_index=False)["val"]
            .sum()
        )

        fig_inj_compare = px.bar(
            inj_compare_df,
            x="location_name",
            y="val",
            color="cause_name",
            barmode="group",
            labels={
                "location_name": "State / location",
                "val": selected_metric,
                "cause_name": "Injury cause",
            },
            title=f"{selected_metric} by state: {primary_inj_cause} vs {secondary_inj_cause}",
        )
        fig_inj_compare.update_layout(
            xaxis_tickangle=-45,
            height=500,
            margin=dict(t=80, r=40, b=120, l=80),
        )

        st.plotly_chart(fig_inj_compare, use_container_width=True)

        # optional download for this comparison
        st.download_button(
            "Download comparison data (CSV)",
            data=inj_compare_df.to_csv(index=False).encode("utf-8"),
            file_name="injury_compare_two_causes_by_state.csv",
            mime="text/csv",
            key="inj_compare_download",
        )


# -------------------------------------------------------------------
# Data preview + download
# -------------------------------------------------------------------
st.markdown("### Filtered Injury Data Preview")
st.dataframe(filtered.head(100))

csv_bytes = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download filtered injury data (CSV)",
    data=csv_bytes,
    file_name="injuries_filtered.csv",
    mime="text/csv",
    key="download_injury_data",
)
