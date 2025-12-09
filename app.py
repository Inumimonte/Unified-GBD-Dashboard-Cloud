import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ------------------------------------------------------------
# HELPER: MAP cause_name → High-level Category
# ------------------------------------------------------------
def map_cause_to_category(cause: str) -> str:
    """
    Map GBD-style cause_name into one of:
    - Non-communicable diseases
    - Communicable diseases
    - Injuries
    - Maternal & Neonatal
    """
    if pd.isna(cause):
        return "Unclassified"

    c_raw = str(cause).strip()
    c = c_raw.lower()

    # Explicit groups based on common GBD level-2 cause names
    maternal_neonatal = {
        "maternal disorders",
        "neonatal disorders",
    }

    communicable = {
        "enteric infections",
        "respiratory infections and tuberculosis",
        "hiv/aids and sexually transmitted infections",
        "neglected tropical diseases and malaria",
        "nutritional deficiencies",
        "other infectious diseases",
    }

    injuries = {
        "transport injuries",
        "unintentional injuries",
        "self-harm and interpersonal violence",
        "exposure to forces of nature",
    }

    ncds = {
        "cardiovascular diseases",
        "neoplasms",
        "chronic respiratory diseases",
        "digestive diseases",
        "diabetes and kidney diseases",
        "neurological disorders",
        "mental disorders",
        "substance use disorders",
        "musculoskeletal disorders",
        "skin and subcutaneous diseases",
        "sense organ diseases",
        "oral disorders",
        "other non-communicable diseases",
        "gynecological diseases",
    }

    # First try exact (case-insensitive) matching
    lc_raw = c_raw.lower()
    if lc_raw in maternal_neonatal:
        return "Maternal & Neonatal"
    if lc_raw in communicable:
        return "Communicable diseases"
    if lc_raw in injuries:
        return "Injuries"
    if lc_raw in ncds:
        return "Non-communicable diseases"

    # Then try substring / heuristic rules
    if "maternal" in c or "neonatal" in c or "birth asphyxia" in c or "preterm" in c:
        return "Maternal & Neonatal"

    if (
        "tuberculosis" in c
        or "malaria" in c
        or "hiv" in c
        or "aids" in c
        or "infection" in c
        or "diarrheal" in c
        or "diarrhoea" in c
        or "measles" in c
        or "meningitis" in c
    ):
        return "Communicable diseases"

    if "injury" in c or "violence" in c or "road" in c or "transport" in c or "fire" in c:
        return "Injuries"

    # If nothing matches, default to NCD
    return "Non-communicable diseases"


# ------------------------------------------------------------
# DATA LOADER – using your columns and mapping to categories
# ------------------------------------------------------------
@st.cache_data
def load_data():
    data_path = Path("data") / "Unified_GBD_Fact_Table_CLEAN.parquet"
    df_raw = pd.read_csv(data_path)

    # Rename to internal standard names
    df_raw = df_raw.rename(
        columns={
            "year": "year",
            "sex_name": "sex",
            "age_name": "age_group",
            "cause_name": "disease",
            "location_name": "location",
        }
    )

    # Derive high-level category from disease
    df_raw["category"] = df_raw["disease"].apply(map_cause_to_category)

    # Keep only DALYs Rate and YLLs Rate from measure_name_standard
    wanted_measures = ["DALYs Rate", "YLLs Rate"]
    df_metric = df_raw[df_raw["measure_name_standard"].isin(wanted_measures)].copy()

    if df_metric.empty:
        st.error("No rows found for measures 'DALYs Rate' and 'YLLs Rate'.")
        st.stop()

    index_cols = ["year", "sex", "age_group", "location", "category", "disease"]
    df_metric = df_metric[index_cols + ["measure_name_standard", "val"]]

    # Pivot long → wide: columns become 'DALYs Rate', 'YLLs Rate'
    wide = df_metric.pivot_table(
        index=index_cols,
        columns="measure_name_standard",
        values="val",
        aggfunc="sum",
    ).reset_index()

    # Rename to DALY and YLL
    rename_measure_cols = {}
    if "DALYs Rate" in wide.columns:
        rename_measure_cols["DALYs Rate"] = "DALY"
    if "YLLs Rate" in wide.columns:
        rename_measure_cols["YLLs Rate"] = "YLL"

    wide = wide.rename(columns=rename_measure_cols)

    # Ensure DALY and YLL exist & numeric
    for col in ["DALY", "YLL"]:
        if col not in wide.columns:
            wide[col] = 0.0
        wide[col] = pd.to_numeric(wide[col], errors="coerce").fillna(0.0)

    # Compute YLD = DALY - YLL
    wide["YLD"] = wide["DALY"] - wide["YLL"]
    wide["YLD"] = pd.to_numeric(wide["YLD"], errors="coerce").fillna(0.0)

    wide["year"] = wide["year"].astype(int)

    return wide


# ------------------------------------------------------------
# HELPER FUNCTIONS (unchanged)
# ------------------------------------------------------------
def compute_kpis(filtered: pd.DataFrame):
    total_daly = filtered["DALY"].sum()
    total_yll = filtered["YLL"].sum()
    total_yld = filtered["YLD"].sum()

    cat_tbl = (
        filtered.groupby("category", as_index=False)["DALY"]
        .sum()
        .sort_values("DALY", ascending=False)
    )

    dominant_category = "N/A"
    dominant_share = 0.0

    if not cat_tbl.empty and total_daly > 0:
        dominant_category = cat_tbl.iloc[0]["category"]
        dominant_share = float(cat_tbl.iloc[0]["DALY"]) / float(total_daly)

    return total_daly, total_yll, total_yld, dominant_category, dominant_share


def format_big_number(x):
    if pd.isna(x):
        return "N/A"
    x = float(x)
    if abs(x) >= 1_000_000_000:
        return f"{x/1_000_000_000:.1f}B"
    if abs(x) >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    if abs(x) >= 1_000:
        return f"{x/1_000:.1f}K"
    return f"{x:,.0f}"


def filter_df(df, year, sex, age, location, category, disease):
    dff = df.copy()
    if year is not None:
        dff = dff[dff["year"] == year]
    if sex is not None and sex != "All":
        dff = dff[dff["sex"] == sex]
    if age is not None and age != "All":
        dff = dff[dff["age_group"] == age]
    if location is not None and location != "All":
        dff = dff[dff["location"] == location]
    if category is not None and category != "All":
        dff = dff[dff["category"] == category]
    if disease is not None and disease != "All":
        dff = dff[dff["disease"] == disease]
    return dff


# ------------------------------------------------------------
# STREAMLIT PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Unified GBD Dashboard – National Overview",
    layout="wide",
)

st.title("Full National Disease Intelligence System")
st.subheader("Unified GBD Dashboard – National Overview")

st.markdown(
    """
Welcome to the **Unified GBD Dashboard**, a multi-page national disease intelligence
suite built around global burden of disease concepts.

Use the **left sidebar** to navigate across modules:

- 🏠 **National Overview (this page)** – high-level DALY / YLL / YLD patterns by year, sex, age, location, category and cause.  
- 🩺 **NCD Explore** – drill into non-communicable diseases, trends, and leading NCD causes.  
- 🦠 **Communicable Explore** – infectious diseases, under-5 conditions, and other CMNND causes.  
- 💥 **Injuries Explore** – transport injuries, violence, and other injury-related burden.  
- 👶 **Maternal & Neonatal** – maternal disorders and neonatal conditions, with a life-course lens.  
- 🗺️ **Geospatial Map** – state-level view of burden using an interactive bubble map.  
- 🧪 **Risk Factor Intelligence** – framework page for future behavioral, metabolic, and environmental risk factor data.  
- 📘 **Methodology & Metadata** – definitions, data sources, cleaning steps, and limitations.
    """
)

st.markdown("---")

# ------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------
df = load_data()

years = sorted(df["year"].unique())
sexes = sorted(df["sex"].dropna().unique())
age_groups = sorted(df["age_group"].dropna().unique())
locations = sorted(df["location"].dropna().unique())
categories = sorted(df["category"].dropna().unique())
diseases = sorted(df["disease"].dropna().unique())

# ------------------------------------------------------------
# SIDEBAR FILTERS (Enhanced)
# ------------------------------------------------------------
st.sidebar.header("Filters")

selected_year = st.sidebar.selectbox("Year", options=years, index=len(years) - 1)
selected_sex = st.sidebar.selectbox("Sex", options=["All"] + list(sexes), index=0)
selected_age = st.sidebar.selectbox("Age group", options=["All"] + list(age_groups), index=0)
selected_location = st.sidebar.selectbox("Location", options=["All"] + list(locations), index=0)
selected_category = st.sidebar.selectbox("Category", options=["All"] + list(categories), index=0)
selected_disease = st.sidebar.selectbox("Disease (cause)", options=["All"] + list(diseases), index=0)
selected_metric = st.sidebar.selectbox("Metric", options=["DALY", "YLL", "YLD"], index=0)

filtered = filter_df(
    df,
    selected_year,
    selected_sex,
    selected_age,
    selected_location,
    selected_category,
    selected_disease,
)

# ------------------------------------------------------------
# KPI CARDS
# ------------------------------------------------------------
st.markdown("### National Burden Overview")

col1, col2, col3, col4 = st.columns(4)

if filtered.empty:
    col1.metric("Total DALYs", "N/A")
    col2.metric("Total YLLs", "N/A")
    col3.metric("Total YLDs", "N/A")
    col4.metric("Dominant Category", "N/A", "")
else:
    total_daly, total_yll, total_yld, dom_cat, dom_share = compute_kpis(filtered)

    col1.metric("Total DALYs", format_big_number(total_daly))
    col2.metric("Total YLLs", format_big_number(total_yll))
    col3.metric("Total YLDs", format_big_number(total_yld))

    dom_sub = f"{dom_share * 100:.1f}% of total DALYs" if dom_share > 0 else ""
    col4.metric("Dominant Category", dom_cat, dom_sub)

st.markdown("---")

# ------------------------------------------------------------
# ROW 1: TREND + TOP CAUSES
# ------------------------------------------------------------
st.markdown("### Trends and Leading Causes")

c1, c2 = st.columns((1.1, 1))
metric_col = selected_metric  # DALY / YLL / YLD

with c1:
    st.markdown("**National Burden Trend over Time**")

    trend_df = df.copy()
    if selected_sex != "All":
        trend_df = trend_df[trend_df["sex"] == selected_sex]
    if selected_age != "All":
        trend_df = trend_df[trend_df["age_group"] == selected_age]
    if selected_location != "All":
        trend_df = trend_df[trend_df["location"] == selected_location]
    if selected_category != "All":
        trend_df = trend_df[trend_df["category"] == selected_category]
    if selected_disease != "All":
        trend_df = trend_df[trend_df["disease"] == selected_disease]

    if trend_df.empty:
        st.info("No data available for selected filters.")
    else:
        trend = (
            trend_df.groupby("year", as_index=False)[metric_col]
            .sum()
            .sort_values("year")
        )

        fig_trend = go.Figure()
        fig_trend.add_trace(
            go.Scatter(
                x=trend["year"],
                y=trend[metric_col],
                mode="lines+markers",
                name=metric_col,
            )
        )
        fig_trend.update_layout(
            xaxis_title="Year",
            yaxis_title=f"{metric_col} (rate)",
            legend_title="Metric",
            margin=dict(l=40, r=10, t=30, b=40),
        )
        st.plotly_chart(fig_trend, use_container_width=True)

with c2:
    st.markdown(f"**Top 10 Leading Causes by {metric_col}**")

    if filtered.empty:
        st.info("No data for the selected filters.")
    else:
        top = (
            filtered.groupby("disease", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
            .head(10)
        )

        fig_top = px.bar(
            top,
            x=metric_col,
            y="disease",
            orientation="h",
            labels={metric_col: f"{metric_col} (rate)", "disease": "Cause"},
        )
        fig_top.update_layout(
            yaxis={"categoryorder": "total ascending"},
            margin=dict(l=120, r=10, t=30, b=40),
        )
        st.plotly_chart(fig_top, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# ROW 2: CATEGORY PIE + SEX BAR
# ------------------------------------------------------------
st.markdown("### Category and Sex Disparities")

c3, c4 = st.columns((0.9, 1.1))

with c3:
    st.markdown(f"**Burden by Category ({metric_col})**")

    if filtered.empty:
        st.info("No data for the selected filters.")
    else:
        cat_tbl = (
            filtered.groupby("category", as_index=False)[metric_col]
            .sum()
            .sort_values(metric_col, ascending=False)
        )

        fig_cat = px.pie(
            cat_tbl,
            names="category",
            values=metric_col,
            hole=0.4,
        )
        fig_cat.update_layout(margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_cat, use_container_width=True)

with c4:
    st.markdown("**Burden by Sex (DALYs, YLLs, YLDs)**")

    sex_df = filter_df(
        df,
        selected_year,
        "All",
        selected_age,
        selected_location,
        selected_category,
        selected_disease,
    )
    if sex_df.empty:
        st.info("No data for the selected filters.")
    else:
        sex_tbl = (
            sex_df.groupby("sex", as_index=False)[["DALY", "YLL", "YLD"]]
            .sum()
            .sort_values("sex")
        )

        sex_long = sex_tbl.melt(
            id_vars="sex",
            value_vars=["DALY", "YLL", "YLD"],
            var_name="metric",
            value_name="value",
        )

        fig_sex = px.bar(
            sex_long,
            x="sex",
            y="value",
            color="metric",
            barmode="group",
            labels={"value": "Burden (rate)", "sex": "Sex", "metric": "Metric"},
        )
        fig_sex.update_layout(margin=dict(l=40, r=10, t=30, b=40))
        st.plotly_chart(fig_sex, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------
# ROW 3: AGE HEATMAP + NARRATIVE
# ------------------------------------------------------------
st.markdown("### Age & Category Pattern + Narrative Summary")

c5, c6 = st.columns((1.4, 0.9))

with c5:
    st.markdown(f"**Burden by Age Group and Category ({metric_col})**")

    heat_df = filter_df(
        df,
        selected_year,
        selected_sex,
        "All",
        selected_location,
        selected_category,
        selected_disease,
    )
    if heat_df.empty:
        st.info("No data for the selected filters.")
    else:
        table = (
            heat_df.groupby(["category", "age_group"], as_index=False)[metric_col]
            .sum()
        )
        pivot = table.pivot(index="category", columns="age_group", values=metric_col).fillna(0)

        fig_heat = px.imshow(
            pivot,
            labels=dict(x="Age group", y="Category", color=f"{metric_col} (rate)"),
            aspect="auto",
        )
        fig_heat.update_layout(margin=dict(l=60, r=10, t=30, b=40))
        st.plotly_chart(fig_heat, use_container_width=True)

with c6:
    st.markdown("**National Summary**")

    if filtered.empty:
        st.info("No data for the selected filters.")
    else:
        total_daly, total_yll, total_yld, dom_cat, dom_share = compute_kpis(filtered)

        top_causes = (
            filtered.groupby("disease", as_index=False)["DALY"]
            .sum()
            .sort_values("DALY", ascending=False)
            .head(3)
        )
        top_list = ", ".join(top_causes["disease"].tolist())

        sex_phrase = "all sexes" if selected_sex == "All" else selected_sex.lower()
        age_phrase = "all ages" if selected_age == "All" else selected_age.lower()
        loc_phrase = "all locations" if selected_location == "All" else selected_location
        dom_pct = f"{dom_share * 100:.1f}%" if dom_share > 0 else "N/A"

        text = (
            f"In {selected_year}, the total DALYs rate burden was approximately "
            f"{format_big_number(total_daly)} for {sex_phrase}, {age_phrase}, in {loc_phrase}.\n\n"
            f"{dom_cat} accounted for about {dom_pct} of total DALYs rate. "
            f"The leading causes were: {top_list}.\n\n"
            f"YLLs rate was around {format_big_number(total_yll)}, while YLDs rate was about "
            f"{format_big_number(total_yld)}, highlighting the combined impact of "
            f"premature mortality and non-fatal health loss."
        )

        st.write(text)
        # ------------------------------------------------------------
# ROW 4: RAW DATA TABLE + DOWNLOAD
# ------------------------------------------------------------
st.markdown("---")
st.markdown("### Raw Data View & Download")

with st.expander("Show filtered data table"):
    if filtered.empty:
        st.info("No data available for the selected filters.")
    else:
        # Show a trimmed version of the filtered data
        display_cols = ["year", "location", "sex", "age_group", "category", "disease", "DALY", "YLL", "YLD"]
        display_cols = [c for c in display_cols if c in filtered.columns]
        st.dataframe(filtered[display_cols].sort_values(["year", "location", "category", "disease"]))

if not filtered.empty:
    # Prepare CSV for download
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download filtered data as CSV",
        data=csv,
        file_name=f"GBD_filtered_{selected_year}.csv",
        mime="text/csv",
    )
else:
    st.info("Adjust filters to enable data download.")

