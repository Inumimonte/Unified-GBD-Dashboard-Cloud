import streamlit as st
import pandas as pd
import plotly.express as px

from gbd_utils import load_data

st.set_page_config(
    page_title="Maternal & Neonatal Disorders Explorer",
    page_icon="👩‍🍼",
    layout="wide",
)

st.title("👩‍🍼👶 Maternal & Neonatal Disorders Explorer")

# -------------------------------------------------------------------
# Load and subset data
# -------------------------------------------------------------------
data = load_data()

maternal_data = data[data["source_file"] == "Maternal Disorder.csv"].copy()
neonatal_data = data[data["source_file"] == "Neonatal Disorder.csv"].copy()

if maternal_data.empty or neonatal_data.empty:
    st.error("Maternal and/or Neonatal rows not found from the source CSVs.")
    st.stop()

# Optional: restrict to key causes (in case the CSV has extras)
MATERNAL_CAUSES = [
    "Maternal disorders",
    "Maternal abortion and miscarriage",
    "Maternal hypertensive disorders",
    "Maternal hemorrhage",
    "Maternal sepsis and other maternal infections",
    "Maternal obstructed labor and uterine rupture",
    "Ectopic pregnancy",
    "Other direct maternal disorders",
]

NEONATAL_CAUSES = [
    "Neonatal disorders",
    "Neonatal preterm birth",
    "Neonatal encephalopathy due to birth asphyxia and trauma",
    "Neonatal sepsis and other neonatal infections",
]

maternal_data = maternal_data[maternal_data["cause_name"].isin(MATERNAL_CAUSES)].copy()
neonatal_data = neonatal_data[neonatal_data["cause_name"].isin(NEONATAL_CAUSES)].copy()

# Color maps (optional – can omit or adjust)
MATERNAL_COLORS = {
    "Maternal disorders": "#1f77b4",
    "Maternal abortion and miscarriage": "#ff7f0e",
    "Maternal hypertensive disorders": "#2ca02c",
    "Maternal hemorrhage": "#d62728",
    "Maternal sepsis and other maternal infections": "#9467bd",
    "Maternal obstructed labor and uterine rupture": "#8c564b",
    "Ectopic pregnancy": "#e377c2",
    "Other direct maternal disorders": "#7f7f7f",
}

NEONATAL_COLORS = {
    "Neonatal disorders": "#17becf",
    "Neonatal preterm birth": "#bcbd22",
    "Neonatal encephalopathy due to birth asphyxia and trauma": "#ff9896",
    "Neonatal sepsis and other neonatal infections": "#98df8a",
}

# -------------------------------------------------------------------
# Sidebar filters (shared)
# -------------------------------------------------------------------
with st.sidebar:
    st.header("Filters • Maternal & Neonatal")

    metric_options = sorted(
        set(maternal_data["measure_name_standard"].unique())
        | set(neonatal_data["measure_name_standard"].unique())
    )
    default_metric = "DALYs Rate" if "DALYs Rate" in metric_options else metric_options[0]

    selected_metric = st.selectbox(
        "Select metric",
        metric_options,
        index=metric_options.index(default_metric),
        help="Metric used for both maternal and neonatal charts.",
    )

    years = st.multiselect(
        "Year",
        sorted(data["year"].unique()),
        default=sorted(data["year"].unique()),
    )

    locations = st.multiselect(
        "States / locations",
        sorted(data["location_name"].unique()),
        default=sorted(data["location_name"].unique()),
    )

    sexes = st.multiselect(
        "Sex",
        sorted(data["sex_name"].unique()),
        default=sorted(data["sex_name"].unique()),
    )

    ages = st.multiselect(
        "Age group",
        sorted(data["age_name"].unique()),
        default=sorted(data["age_name"].unique()),
    )

    # 🔹 New: pick which maternal causes to compare
    maternal_cause_sel = st.multiselect(
        "Maternal causes to include (for comparison)",
        MATERNAL_CAUSES,
        default=MATERNAL_CAUSES,
    )

    # 🔹 New: pick which neonatal causes to compare
    neonatal_cause_sel = st.multiselect(
        "Neonatal causes to include (for comparison)",
        NEONATAL_CAUSES,
        default=NEONATAL_CAUSES,
    )

    st.caption(f"Metric in use: **{selected_metric}**")


# -------------------------------------------------------------------
# Apply filters
# -------------------------------------------------------------------
maternal_filtered = maternal_data[
    (maternal_data["measure_name_standard"] == selected_metric)
    & (maternal_data["year"].isin(years))
    & (maternal_data["location_name"].isin(locations))
    & (maternal_data["sex_name"].isin(sexes))
    & (maternal_data["age_name"].isin(ages))
    & (maternal_data["cause_name"].isin(maternal_cause_sel))
].copy()

neonatal_filtered = neonatal_data[
    (neonatal_data["measure_name_standard"] == selected_metric)
    & (neonatal_data["year"].isin(years))
    & (neonatal_data["location_name"].isin(locations))
    & (neonatal_data["sex_name"].isin(sexes))
    & (neonatal_data["age_name"].isin(ages))
    & (neonatal_data["cause_name"].isin(neonatal_cause_sel))
].copy()

if maternal_filtered.empty and neonatal_filtered.empty:
    st.warning("No maternal or neonatal records match the current filters.")
    st.stop()

# Combined total for percentage shares
maternal_total = maternal_filtered["val"].sum()
neonatal_total = neonatal_filtered["val"].sum()
combined_total = maternal_total + neonatal_total

# -------------------------------------------------------------------
# Maternal section
# -------------------------------------------------------------------
st.markdown("## Maternal Disorders")

if maternal_filtered.empty:
    st.info("No maternal records match the current filters.")
else:
    mat_cause_agg = (
        maternal_filtered.groupby("cause_name", as_index=False)["val"]
        .sum()
        .sort_values("val", ascending=False)
    )

    dom_mat = mat_cause_agg.iloc[0]["cause_name"]
    dom_mat_val = mat_cause_agg.iloc[0]["val"]
    mat_share_of_total = (
        dom_mat_val / mat_cause_agg["val"].sum() * 100
        if mat_cause_agg["val"].sum() > 0
        else 0
    )
    mat_share_of_mn = (
        maternal_total / combined_total * 100 if combined_total > 0 else 0
    )

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown("**Dominant Maternal Cause**")
        st.markdown(
            f"<h2 style='margin-top:0'>{dom_mat}</h2>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(f"**Maternal Burden Value** ({selected_metric})")
        st.metric(label="", value=f"{maternal_total:,.1f}")
    with c3:
        st.markdown("**% of Total Maternal+Neonatal Burden**")
        st.metric(label="", value=f"{mat_share_of_mn:,.1f}%")

    st.caption(f"Maternal rows after filters: **{len(maternal_filtered):,}**")

    # Top maternal causes (bar)
    st.markdown("### Top Maternal Causes by Burden")
    top_mat = mat_cause_agg.head(10)

    fig_mat_bar = px.bar(
        top_mat,
        x="val",
        y="cause_name",
        orientation="h",
        color="cause_name",
        color_discrete_map=MATERNAL_COLORS,
        labels={"val": selected_metric, "cause_name": "Maternal cause"},
        title=f"Top Maternal Causes by {selected_metric}",
    )
    fig_mat_bar.update_layout(
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
    st.plotly_chart(fig_mat_bar, use_container_width=True)

    # Maternal trend over time by cause
    st.markdown("### Maternal Trend Over Time by Cause")

    mat_trend = (
        maternal_filtered.groupby(["year", "cause_name"], as_index=False)["val"]
        .mean()
        .sort_values(["cause_name", "year"])
    )

    fig_mat_trend = px.line(
        mat_trend,
        x="year",
        y="val",
        color="cause_name",
        markers=True,
        color_discrete_map=MATERNAL_COLORS,
        labels={"val": selected_metric, "cause_name": "Maternal cause"},
        title=f"Maternal {selected_metric} Trend Over Time by Cause",
    )
    fig_mat_trend.update_layout(
        margin=dict(l=80, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    st.plotly_chart(fig_mat_trend, use_container_width=True)

# -------------------------------------------------------------------
# Neonatal section
# -------------------------------------------------------------------
st.markdown("## Neonatal Disorders")

if neonatal_filtered.empty:
    st.info("No neonatal records match the current filters.")
else:
    neo_cause_agg = (
        neonatal_filtered.groupby("cause_name", as_index=False)["val"]
        .sum()
        .sort_values("val", ascending=False)
    )

    dom_neo = neo_cause_agg.iloc[0]["cause_name"]
    dom_neo_val = neo_cause_agg.iloc[0]["val"]
    neo_share_of_total = (
        dom_neo_val / neo_cause_agg["val"].sum() * 100
        if neo_cause_agg["val"].sum() > 0
        else 0
    )
    neo_share_of_mn = (
        neonatal_total / combined_total * 100 if combined_total > 0 else 0
    )

    c1, c2, c3 = st.columns([2, 1, 1])

    with c1:
        st.markdown("**Dominant Neonatal Cause**")
        st.markdown(
            f"<h2 style='margin-top:0'>{dom_neo}</h2>",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(f"**Neonatal Burden Value** ({selected_metric})")
        st.metric(label="", value=f"{neonatal_total:,.1f}")
    with c3:
        st.markdown("**% of Total Maternal+Neonatal Burden**")
        st.metric(label="", value=f"{neo_share_of_mn:,.1f}%")

    st.caption(f"Neonatal rows after filters: **{len(neonatal_filtered):,}**")

    # Top neonatal causes (bar)
    st.markdown("### Top Neonatal Causes by Burden")
    top_neo = neo_cause_agg.head(10)

    fig_neo_bar = px.bar(
        top_neo,
        x="val",
        y="cause_name",
        orientation="h",
        color="cause_name",
        color_discrete_map=NEONATAL_COLORS,
        labels={"val": selected_metric, "cause_name": "Neonatal cause"},
        title=f"Top Neonatal Causes by {selected_metric}",
    )
    fig_neo_bar.update_layout(
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
    st.plotly_chart(fig_neo_bar, use_container_width=True)

    # Neonatal trend over time by cause
    st.markdown("### Neonatal Trend Over Time by Cause")

    neo_trend = (
        neonatal_filtered.groupby(["year", "cause_name"], as_index=False)["val"]
        .mean()
        .sort_values(["cause_name", "year"])
    )

    fig_neo_trend = px.line(
        neo_trend,
        x="year",
        y="val",
        color="cause_name",
        markers=True,
        color_discrete_map=NEONATAL_COLORS,
        labels={"val": selected_metric, "cause_name": "Neonatal cause"},
        title=f"Neonatal {selected_metric} Trend Over Time by Cause",
    )
    fig_neo_trend.update_layout(
        margin=dict(l=80, r=40, t=60, b=40),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )
    st.plotly_chart(fig_neo_trend, use_container_width=True)
    # -----------------------------
# Compare two maternal causes by state
# -----------------------------
st.markdown("### Compare two maternal causes by state")

mat_compare_causes = sorted(maternal_filtered["cause_name"].unique())
if len(mat_compare_causes) < 2:
    st.info("Not enough maternal causes in the filtered data to compare (need at least 2).")
else:
    col_a, col_b = st.columns(2)
    with col_a:
        primary_mat_cause = st.selectbox(
            "Primary maternal cause",
            mat_compare_causes,
            key="mat_compare_primary",
        )
    with col_b:
        secondary_mat_cause = st.selectbox(
            "Comparison maternal cause",
            mat_compare_causes,
            index=1 if len(mat_compare_causes) > 1 else 0,
            key="mat_compare_secondary",
        )

    if primary_mat_cause == secondary_mat_cause:
        st.warning("Please choose two different maternal causes to compare.")
    else:
        mat_compare_df = (
            maternal_filtered[maternal_filtered["cause_name"].isin([primary_mat_cause, secondary_mat_cause])]
            .groupby(["location_name", "cause_name"], as_index=False)["val"]
            .sum()
        )

        fig_mat_compare = px.bar(
            mat_compare_df,
            x="location_name",
            y="val",
            color="cause_name",
            barmode="group",
            labels={
                "location_name": "State / location",
                "val": selected_metric,
                "cause_name": "Maternal cause",
            },
            title=f"{selected_metric} by state: {primary_mat_cause} vs {secondary_mat_cause}",
        )
        fig_mat_compare.update_layout(
            xaxis_tickangle=-45,
            height=500,
            margin=dict(t=80, r=40, b=120, l=80),
        )

        st.plotly_chart(fig_mat_compare, use_container_width=True)

        st.download_button(
            "Download maternal comparison data (CSV)",
            data=mat_compare_df.to_csv(index=False).encode("utf-8"),
            file_name="maternal_compare_two_causes_by_state.csv",
            mime="text/csv",
            key="mat_compare_download",
        )

# -----------------------------
# Compare two neonatal causes by state
# -----------------------------
st.markdown("### Compare two neonatal causes by state")

neo_compare_causes = sorted(neonatal_filtered["cause_name"].unique())
if len(neo_compare_causes) < 2:
    st.info("Not enough neonatal causes in the filtered data to compare (need at least 2).")
else:
    col_a, col_b = st.columns(2)
    with col_a:
        primary_neo_cause = st.selectbox(
            "Primary neonatal cause",
            neo_compare_causes,
            key="neo_compare_primary",
        )
    with col_b:
        secondary_neo_cause = st.selectbox(
            "Comparison neonatal cause",
            neo_compare_causes,
            index=1 if len(neo_compare_causes) > 1 else 0,
            key="neo_compare_secondary",
        )

    if primary_neo_cause == secondary_neo_cause:
        st.warning("Please choose two different neonatal causes to compare.")
    else:
        neo_compare_df = (
            neonatal_filtered[neonatal_filtered["cause_name"].isin([primary_neo_cause, secondary_neo_cause])]
            .groupby(["location_name", "cause_name"], as_index=False)["val"]
            .sum()
        )

        fig_neo_compare = px.bar(
            neo_compare_df,
            x="location_name",
            y="val",
            color="cause_name",
            barmode="group",
            labels={
                "location_name": "State / location",
                "val": selected_metric,
                "cause_name": "Neonatal cause",
            },
            title=f"{selected_metric} by state: {primary_neo_cause} vs {secondary_neo_cause}",
        )
        fig_neo_compare.update_layout(
            xaxis_tickangle=-45,
            height=500,
            margin=dict(t=80, r=40, b=120, l=80),
        )

        st.plotly_chart(fig_neo_compare, use_container_width=True)

        st.download_button(
            "Download neonatal comparison data (CSV)",
            data=neo_compare_df.to_csv(index=False).encode("utf-8"),
            file_name="neonatal_compare_two_causes_by_state.csv",
            mime="text/csv",
            key="neo_compare_download",
        )


# -------------------------------------------------------------------
# Data preview + downloads
# -------------------------------------------------------------------
st.markdown("### Data Preview & Downloads")

c_mat, c_neo = st.columns(2)

with c_mat:
    st.markdown("**Maternal data (filtered)**")
    if maternal_filtered.empty:
        st.write("No maternal data for current filters.")
    else:
        st.dataframe(maternal_filtered.head(100))
        mat_csv = maternal_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download maternal data (CSV)",
            data=mat_csv,
            file_name="maternal_filtered.csv",
            mime="text/csv",
            key="download_maternal_data",
        )

with c_neo:
    st.markdown("**Neonatal data (filtered)**")
    if neonatal_filtered.empty:
        st.write("No neonatal data for current filters.")
    else:
        st.dataframe(neonatal_filtered.head(100))
        neo_csv = neonatal_filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download neonatal data (CSV)",
            data=neo_csv,
            file_name="neonatal_filtered.csv",
            mime="text/csv",
            key="download_neonatal_data",
        )
