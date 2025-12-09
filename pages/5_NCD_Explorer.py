import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from gbd_utils import load_data

# -------------------------
# Config & constants
# -------------------------

# List of NCD causes we want to focus on
NCD_CAUSES = [
    "Chronic kidney disease",
    "Diabetes mellitus",
    "Stroke",
    "Ischemic heart disease",
    "Hypertensive heart disease",
]

# Color mapping for consistency across charts
NCD_COLORS = {
    "Chronic kidney disease": "#1f77b4",      # blue
    "Diabetes mellitus": "#ff7f0e",          # orange
    "Stroke": "#2ca02c",                     # green
    "Ischemic heart disease": "#d62728",     # red
    "Hypertensive heart disease": "#9467bd", # purple
}

# -------------------------
# Load & prepare data
# -------------------------

data = load_data()

# Filter to NCD causes
ncd_data = data[data["cause_name"].isin(NCD_CAUSES)].copy()

if ncd_data.empty:
    st.error(
        "No NCD data found in the unified GBD fact table. "
        "Please verify that NCD-related rows are present."
    )
    st.stop()

# Ensure year is integer
if not np.issubdtype(ncd_data["year"].dtype, np.integer):
    ncd_data["year"] = ncd_data["year"].astype(int)

# Only keep rate-type measures for NCD (if multiple exist)
metric_options = sorted(ncd_data["measure_name_standard"].unique())
default_metric = (
    "NCD Rate" if "NCD Rate" in metric_options else metric_options[0]
)

# -------------------------
# Sidebar filters
# -------------------------

st.sidebar.header("Filters (NCD Explorer)")

metric_sel = st.sidebar.selectbox(
    "Select NCD metric",
    metric_options,
    index=metric_options.index(default_metric)
    if default_metric in metric_options
    else 0,
)

years = sorted(ncd_data["year"].unique())
year_min_all, year_max_all = int(min(years)), int(max(years))

year_range = st.sidebar.slider(
    "Year range",
    min_value=year_min_all,
    max_value=year_max_all,
    value=(year_min_all, year_max_all),
    step=1,
)

locations = sorted(ncd_data["location_name"].unique())
loc_default = locations  # all states by default

loc_sel = st.sidebar.multiselect(
    "States / locations",
    options=locations,
    default=loc_default,
)

sex_options = sorted(ncd_data["sex_name"].unique())
sex_sel = st.sidebar.multiselect(
    "Sex",
    options=sex_options,
    default=sex_options,
)

age_options = sorted(ncd_data["age_name"].unique())
# For NCDs we might be most interested in adults; but keep all by default
age_sel = st.sidebar.multiselect(
    "Age groups",
    options=age_options,
    default=age_options,
)

cause_options = [c for c in NCD_CAUSES if c in ncd_data["cause_name"].unique()]
if not cause_options:
    cause_options = sorted(ncd_data["cause_name"].unique())

cause_sel = st.sidebar.multiselect(
    "NCD causes to include",
    options=cause_options,
    default=cause_options,
)

# -------------------------
# Apply filters
# -------------------------

filtered = ncd_data[
    (ncd_data["measure_name_standard"] == metric_sel)
    & (ncd_data["year"].between(year_range[0], year_range[1]))
    & (ncd_data["location_name"].isin(loc_sel))
    & (ncd_data["sex_name"].isin(sex_sel))
    & (ncd_data["age_name"].isin(age_sel))
    & (ncd_data["cause_name"].isin(cause_sel))
].copy()

if filtered.empty:
    st.warning("No NCD data for the current filters.")
    st.stop()

year_min = int(filtered["year"].min())
year_max = int(filtered["year"].max())

# -------------------------
# Page header
# -------------------------

st.title("🫀 Non-Communicable Disease (NCD) Explorer")

st.markdown(
    """
This page focuses on **major NCDs** (stroke, heart disease, diabetes, kidney disease, etc.)
using the unified GBD fact table.

You can:
- Filter by **year, state, sex, age group, and NCD cause**
- Compare **burden across NCDs**
- Explore **trends over time**
- Drill down to **state-level trends and rankings**.
"""
)

st.markdown(f"**Rows after filter:** {len(filtered):,}")

# -------------------------
# Key NCD metrics
# -------------------------

st.markdown("### Key NCD Metrics")

cause_agg = (
    filtered.groupby("cause_name", as_index=False)["val"]
    .sum()
    .rename(columns={"val": "total_burden"})
)

total_ncd_burden = cause_agg["total_burden"].sum()
dominant_row = cause_agg.loc[cause_agg["total_burden"].idxmax()]

dominant_cause = dominant_row["cause_name"]
dominant_value = dominant_row["total_burden"]
dominant_pct = (
    dominant_value / total_ncd_burden * 100 if total_ncd_burden > 0 else 0
)

col_k1, col_k2, col_k3 = st.columns(3)

with col_k1:
    st.markdown("**Dominant NCD cause**")
    st.markdown(
        f"<h2 style='margin-top: -0.3rem;'>{dominant_cause}</h2>",
        unsafe_allow_html=True,
    )

with col_k2:
    st.markdown(f"**Total {metric_sel} (all selected NCDs)**")
    st.markdown(
        f"<h2 style='margin-top: -0.3rem;'>{dominant_value:,.1f}</h2>",
        unsafe_allow_html=True,
    )

with col_k3:
    st.markdown(
        f"**% contribution of {dominant_cause}** "
        f"({year_min}–{year_max})"
    )
    st.markdown(
        f"<h2 style='margin-top: -0.3rem;'>{dominant_pct:,.1f}%</h2>",
        unsafe_allow_html=True,
    )

# -------------------------
# Burden by NCD cause (bar)
# -------------------------

st.markdown("### Burden by NCD cause")

fig_ncd_bar = px.bar(
    cause_agg.sort_values("total_burden", ascending=True),
    x="total_burden",
    y="cause_name",
    orientation="h",
    labels={
        "total_burden": metric_sel,
        "cause_name": "NCD cause",
    },
    title=f"{metric_sel} for selected NCD causes ({year_min}–{year_max})",
    color="cause_name",
    color_discrete_map=NCD_COLORS,
)

fig_ncd_bar.update_layout(
    height=400,
    margin=dict(l=160, r=40, t=60, b=40),
    yaxis={"categoryorder": "total ascending"},
    showlegend=True,
)

st.plotly_chart(fig_ncd_bar, use_container_width=True, key="ncd_bar")

# -------------------------
# Trend over time by NCD cause
# -------------------------

st.markdown("### Trend over time by NCD cause")

trend_ncd = (
    filtered.groupby(["year", "cause_name"], as_index=False)["val"]
    .sum()
)

fig_ncd_trend = px.line(
    trend_ncd,
    x="year",
    y="val",
    color="cause_name",
    color_discrete_map=NCD_COLORS,
    markers=True,
    labels={
        "year": "Year",
        "val": metric_sel,
        "cause_name": "NCD cause",
    },
    title=f"{metric_sel} trend over time by NCD cause",
)

fig_ncd_trend.update_layout(
    height=420,
    margin=dict(l=80, r=40, t=60, b=60),
)

st.plotly_chart(fig_ncd_trend, use_container_width=True, key="ncd_trend")

# -------------------------
# Trend over time by NCD cause & state
# -------------------------

st.markdown("### Trend over time by NCD cause & state")

col_cause, col_mode = st.columns([2, 1])

with col_cause:
    cause_state_sel = st.selectbox(
        "Select NCD cause for state-level trend",
        options=cause_options,
        index=0,
    )

with col_mode:
    state_view_mode = st.radio(
        "State view mode",
        options=["Top N states (by burden)", "Choose states manually"],
        index=0,
    )

df_cause_state = filtered[filtered["cause_name"] == cause_state_sel].copy()

if df_cause_state.empty:
    st.info(f"No data for {cause_state_sel} with current filters.")
else:
    # Aggregate over sex/age if multiple selected
    df_cause_state = (
        df_cause_state.groupby(["year", "location_name"], as_index=False)["val"]
        .sum()
    )

    # Optionally compute national average
    nat_trend = (
        df_cause_state.groupby("year", as_index=False)["val"]
        .mean()
        .rename(columns={"val": "national_avg"})
    )

    if state_view_mode == "Top N states (by burden)":
        col_n, col_smooth = st.columns([1, 2])
        with col_n:
            top_n = st.slider(
                "Number of top states (N)",
                min_value=3,
                max_value=15,
                value=5,
                step=1,
            )
        with col_smooth:
            smooth = st.checkbox("Apply 3-year moving average smoothing", value=False)

        state_totals = (
            df_cause_state.groupby("location_name", as_index=False)["val"]
            .sum()
            .rename(columns={"val": "total_burden"})
            .sort_values("total_burden", ascending=False)
        )
        top_states = state_totals.head(top_n)["location_name"].tolist()

        st.markdown(
            f"**Top {top_n} states by total '{cause_state_sel}' burden** "
            f"({year_min}–{year_max}): "
            + ", ".join(top_states)
        )

        df_trend_state = df_cause_state[df_cause_state["location_name"].isin(top_states)].copy()

    else:
        smooth = st.checkbox("Apply 3-year moving average smoothing", value=False)
        state_sel_manual = st.multiselect(
            "Choose states",
            options=locations,
            default=sorted(df_cause_state["location_name"].unique())[:5],
        )
        if not state_sel_manual:
            st.info("Select at least one state to display.")
            df_trend_state = pd.DataFrame(columns=df_cause_state.columns)
        else:
            df_trend_state = df_cause_state[df_cause_state["location_name"].isin(state_sel_manual)].copy()

    if not df_trend_state.empty:
        # Optional smoothing
        if smooth:
            df_trend_state = (
                df_trend_state
                .sort_values(["location_name", "year"])
                .groupby("location_name", as_index=False)
                .apply(
                    lambda d: d.assign(
                        val=d["val"].rolling(window=3, min_periods=1).mean()
                    )
                )
            )

        fig_state_trend = px.line(
            df_trend_state,
            x="year",
            y="val",
            color="location_name",
            labels={
                "year": "Year",
                "val": metric_sel,
                "location_name": "State / location",
            },
            title=f"Trend for '{cause_state_sel}' by state",
            markers=True,
        )

        # Add national average line
        fig_state_trend.add_scatter(
            x=nat_trend["year"],
            y=nat_trend["national_avg"],
            mode="lines",
            name="National average",
            line=dict(dash="dash"),
        )

        fig_state_trend.update_layout(
            height=450,
            margin=dict(l=80, r=40, t=60, b=60),
        )

        st.plotly_chart(
            fig_state_trend,
            use_container_width=True,
            key="ncd_state_trend",
        )

    # -------------------------
    # State ranking for this NCD cause
    # -------------------------

    st.markdown(
        f"#### State ranking for '{cause_state_sel}' "
        f"({year_min}–{year_max}, {metric_sel})"
    )

    state_agg = (
        df_cause_state.groupby("location_name", as_index=False)["val"]
        .sum()
        .rename(columns={"val": "total_burden"})
        .sort_values("total_burden", ascending=False)
    )

    total_disease_burden = state_agg["total_burden"].sum()
    state_agg["pct_of_disease"] = (
        state_agg["total_burden"] / total_disease_burden * 100
        if total_disease_burden > 0
        else 0
    )

    top_rank = state_agg.head(5)
    fig_rank = px.bar(
        top_rank,
        x="total_burden",
        y="location_name",
        orientation="h",
        labels={
            "total_burden": f"Total {metric_sel}",
            "location_name": "State",
        },
        title=(
            f"Top 5 states by total '{cause_state_sel}' burden "
            f"({year_min}–{year_max})"
        ),
    )
    fig_rank.update_layout(
        height=350,
        margin=dict(l=160, r=40, t=60, b=40),
        yaxis={"categoryorder": "total ascending"},
    )
    st.plotly_chart(fig_rank, use_container_width=True, key="ncd_rank_bar")

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        st.markdown(
            f"**Top 5 states**  \n"
            f"<span style='font-size: 0.85em;'>"
            f"({year_min}–{year_max}, share of total {cause_state_sel} burden)"
            f"</span>",
            unsafe_allow_html=True,
        )
        top5 = state_agg.head(5).copy().reset_index(drop=True)
        top5["pct_of_disease"] = top5["pct_of_disease"].map(
            lambda x: f"{x:,.1f}%"
        )
        st.dataframe(
            top5.rename(
                columns={
                    "location_name": "State",
                    "total_burden": f"Total {metric_sel}",
                    "pct_of_disease": "% of disease burden",
                }
            ),
            use_container_width=True,
        )

    with col_r2:
        st.markdown(
            f"**Bottom 5 states**  \n"
            f"<span style='font-size: 0.85em;'>"
            f"({year_min}–{year_max}, share of total {cause_state_sel} burden)"
            f"</span>",
            unsafe_allow_html=True,
        )
        bottom5 = (
            state_agg.tail(5)
            .sort_values("total_burden", ascending=True)
            .copy()
            .reset_index(drop=True)
        )
        bottom5["pct_of_disease"] = bottom5["pct_of_disease"].map(
            lambda x: f"{x:,.1f}%"
        )
        st.dataframe(
            bottom5.rename(
                columns={
                    "location_name": "State",
                    "total_burden": f"Total {metric_sel}",
                    "pct_of_disease": "% of disease burden",
                }
            ),
            use_container_width=True,
        )
# -----------------------------
# Compare two NCD causes by state
# -----------------------------

# -----------------------------
# Compare two NCD causes by state
# -----------------------------
st.markdown("### Compare two NCD causes by state")

# Use your existing NCD filtered dataframe (called `filtered`)
ncd_compare_causes = sorted(filtered["cause_name"].unique())

if len(ncd_compare_causes) < 2:
    st.info("Not enough NCD causes in the filtered data to compare (need at least 2).")
else:
    col_a, col_b = st.columns(2)
    with col_a:
        primary_ncd_cause = st.selectbox(
            "Primary NCD cause",
            ncd_compare_causes,
            key="ncd_compare_primary",
        )
    with col_b:
        secondary_ncd_cause = st.selectbox(
            "Comparison NCD cause",
            ncd_compare_causes,
            index=1 if len(ncd_compare_causes) > 1 else 0,
            key="ncd_compare_secondary",
        )

    if primary_ncd_cause == secondary_ncd_cause:
        st.warning("Please choose two different NCD causes to compare.")
    else:
        ncd_compare_df = (
            filtered[filtered["cause_name"].isin([primary_ncd_cause, secondary_ncd_cause])]
            .groupby(["location_name", "cause_name"], as_index=False)["val"]
            .sum()
        )

        fig_ncd_compare = px.bar(
            ncd_compare_df,
            x="location_name",
            y="val",
            color="cause_name",
            barmode="group",
            labels={
                "location_name": "State / location",
                "val": metric_sel,          # 🔹 use metric_sel here
                "cause_name": "NCD cause",
            },
            title=f"{metric_sel} by state: {primary_ncd_cause} vs {secondary_ncd_cause}",
        )
        fig_ncd_compare.update_layout(
            xaxis_tickangle=-45,
            height=500,
            margin=dict(t=80, r=40, b=120, l=80),
        )

        st.plotly_chart(fig_ncd_compare, use_container_width=True)

        st.download_button(
            "Download NCD comparison data (CSV)",
            data=ncd_compare_df.to_csv(index=False).encode("utf-8"),
            file_name="ncd_compare_two_causes_by_state.csv",
            mime="text/csv",
            key="ncd_compare_download",
        )



# -------------------------
# Summary across NCD causes
# -------------------------

st.markdown(
    f"### Summary by NCD cause: highest and lowest burden states "
    f"({year_min}–{year_max})"
)

summary_rows = []
for cd in cause_options:
    df_cd = filtered[filtered["cause_name"] == cd]
    if df_cd.empty:
        continue

    agg_cd = (
        df_cd.groupby("location_name", as_index=False)["val"]
        .sum()
        .rename(columns={"val": "total_burden"})
        .sort_values("total_burden", ascending=False)
    )

    total_cd = agg_cd["total_burden"].sum()
    agg_cd["pct_of_disease"] = (
        agg_cd["total_burden"] / total_cd * 100 if total_cd > 0 else 0
    )

    top_state = agg_cd.iloc[0]
    bottom_state = agg_cd.iloc[-1]

    summary_rows.append(
        {
            "NCD cause": cd,
            "Top state": top_state["location_name"],
            f"Top state {metric_sel}": round(top_state["total_burden"], 1),
            "Top state % of cause burden": f"{top_state['pct_of_disease']:,.1f}%",
            "Bottom state": bottom_state["location_name"],
            f"Bottom state {metric_sel}": round(
                bottom_state["total_burden"], 1
            ),
            "Bottom state % of cause burden": f"{bottom_state['pct_of_disease']:,.1f}%",
        }
    )

if summary_rows:
    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True)
else:
    st.info("No state summary available for the current filters.")

# -------------------------
# Download filtered NCD data
# -------------------------

with st.expander("Download NCD data (CSV)"):
    csv_bytes = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download current NCD view as CSV",
        data=csv_bytes,
        file_name="NCD_filtered_data.csv",
        mime="text/csv",
        key="ncd_download",
    )
