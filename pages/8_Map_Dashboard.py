import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Geospatial Map - Unified GBD Dashboard",
    layout="wide",
)

st.title("🗺️ Geospatial Disease Burden Map")
st.subheader("Unified GBD Dashboard – Nigeria State-Level View (Bubble Map)")
st.markdown("---")

st.info(
    "This page displays a bubble map of disease burden across Nigerian states using "
    "state centroid coordinates. No GeoJSON file is required."
)

# ------------------------------------------------------------
# HELPER: MAP cause_name → High-level Category (same as app.py)
# ------------------------------------------------------------
def map_cause_to_category(cause: str) -> str:
    if pd.isna(cause):
        return "Unclassified"

    c_raw = str(cause).strip()
    c = c_raw.lower()

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

    lc_raw = c_raw.lower()
    if lc_raw in maternal_neonatal:
        return "Maternal & Neonatal"
    if lc_raw in communicable:
        return "Communicable diseases"
    if lc_raw in injuries:
        return "Injuries"
    if lc_raw in ncds:
        return "Non-communicable diseases"

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

    return "Non-communicable diseases"


# ------------------------------------------------------------
# STATE CENTROIDS – matches your location names exactly
# ------------------------------------------------------------
STATE_COORDS = {
    "Abia":          {"lat": 5.5320,  "lon": 7.4860},
    "Adamawa":       {"lat": 9.3265,  "lon": 12.3984},
    "Akwa Ibom":     {"lat": 4.9057,  "lon": 7.8537},
    "Anambra":       {"lat": 6.2100,  "lon": 7.0700},
    "Bauchi":        {"lat": 10.3156, "lon": 9.8442},
    "Bayelsa":       {"lat": 4.7719,  "lon": 6.0699},
    "Benue":         {"lat": 7.1900,  "lon": 8.1300},
    "Borno":         {"lat": 11.8333, "lon": 13.1500},
    "Cross River":   {"lat": 5.8702,  "lon": 8.5988},
    "Delta":         {"lat": 5.8904,  "lon": 5.6800},
    "Ebonyi":        {"lat": 6.3249,  "lon": 8.1137},
    "Edo":           {"lat": 6.5244,  "lon": 5.8987},
    "Ekiti":         {"lat": 7.6306,  "lon": 5.2193},
    "Enugu":         {"lat": 6.4402,  "lon": 7.4943},
    "Gombe":         {"lat": 10.2897, "lon": 11.1673},
    "Imo":           {"lat": 5.4763,  "lon": 7.0260},
    "Jigawa":        {"lat": 12.2280, "lon": 9.5616},
    "Kaduna":        {"lat": 10.5105, "lon": 7.4165},
    "Kano":          {"lat": 12.0000, "lon": 8.5167},
    "Katsina":       {"lat": 12.9855, "lon": 7.6170},
    "Kebbi":         {"lat": 12.4500, "lon": 4.1999},
    "Kogi":          {"lat": 7.7337,  "lon": 6.6903},
    "Kwara":         {"lat": 8.5000,  "lon": 4.5500},
    "Lagos":         {"lat": 6.5244,  "lon": 3.3792},
    "Nasarawa":      {"lat": 8.5400,  "lon": 8.5200},
    "Niger":         {"lat": 9.6000,  "lon": 6.5500},
    "Ogun":          {"lat": 7.1600,  "lon": 3.3500},
    "Ondo":          {"lat": 7.2500,  "lon": 5.2000},
    "Osun":          {"lat": 7.8000,  "lon": 4.5167},
    "Oyo":           {"lat": 7.9700,  "lon": 3.5900},
    "Plateau":       {"lat": 9.2500,  "lon": 9.0833},
    "Rivers":        {"lat": 4.8156,  "lon": 7.0498},
    "Sokoto":        {"lat": 13.0600, "lon": 5.2400},
    "Taraba":        {"lat": 8.8900,  "lon": 11.3600},
    "Yobe":          {"lat": 12.2963, "lon": 11.4369},
    "Zamfara":       {"lat": 12.1700, "lon": 6.6600},
    "FCT (Abuja)":   {"lat": 9.0765,  "lon": 7.3986},
}


# ------------------------------------------------------------
# DATA LOADER – same logic as app.py
# ------------------------------------------------------------
@st.cache_data
def load_data():
    data_path = Path("data") / "Unified_GBD_Fact_Table_CLEAN.csv"
    df_raw = pd.read_csv(data_path)

    df_raw = df_raw.rename(
        columns={
            "year": "year",
            "sex_name": "sex",
            "age_name": "age_group",
            "cause_name": "disease",
            "location_name": "location",
        }
    )

    df_raw["category"] = df_raw["disease"].apply(map_cause_to_category)

    wanted_measures = ["DALYs Rate", "YLLs Rate"]
    df_metric = df_raw[df_raw["measure_name_standard"].isin(wanted_measures)].copy()

    if df_metric.empty:
        st.error("No rows found for measures 'DALYs Rate' and 'YLLs Rate'.")
        st.stop()

    index_cols = ["year", "sex", "age_group", "location", "category", "disease"]
    df_metric = df_metric[index_cols + ["measure_name_standard", "val"]]

    wide = df_metric.pivot_table(
        index=index_cols,
        columns="measure_name_standard",
        values="val",
        aggfunc="sum",
    ).reset_index()

    rename_measure_cols = {}
    if "DALYs Rate" in wide.columns:
        rename_measure_cols["DALYs Rate"] = "DALY"
    if "YLLs Rate" in wide.columns:
        rename_measure_cols["YLLs Rate"] = "YLL"

    wide = wide.rename(columns=rename_measure_cols)

    for col in ["DALY", "YLL"]:
        if col not in wide.columns:
            wide[col] = 0.0
        wide[col] = pd.to_numeric(wide[col], errors="coerce").fillna(0.0)

    wide["YLD"] = wide["DALY"] - wide["YLL"]
    wide["YLD"] = pd.to_numeric(wide["YLD"], errors="coerce").fillna(0.0)

    wide["year"] = wide["year"].astype(int)

    return wide


df = load_data()

years = sorted(df["year"].unique())
sexes = sorted(df["sex"].dropna().unique())
age_groups = sorted(df["age_group"].dropna().unique())
categories = sorted(df["category"].dropna().unique())
diseases = sorted(df["disease"].dropna().unique())
locations = sorted(df["location"].dropna().unique())

# ------------------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------------------
st.sidebar.header("Map Filters")

selected_year = st.sidebar.selectbox("Year", options=years, index=len(years) - 1)
selected_metric = st.sidebar.selectbox("Metric", options=["DALY", "YLL", "YLD"], index=0)
selected_sex = st.sidebar.selectbox("Sex", options=["All"] + list(sexes), index=0)
selected_age = st.sidebar.selectbox("Age group", options=["All"] + list(age_groups), index=0)
selected_category = st.sidebar.selectbox("Category", options=["All"] + list(categories), index=0)
selected_disease = st.sidebar.selectbox("Disease (cause)", options=["All"] + list(diseases), index=0)

metric_col = selected_metric

# ------------------------------------------------------------
# FILTER DATA
# ------------------------------------------------------------
def filter_df_for_map(
    df: pd.DataFrame,
    year,
    sex,
    age,
    category,
    disease,
):
    dff = df.copy()
    if year is not None:
        dff = dff[dff["year"] == year]
    if sex is not None and sex != "All":
        dff = dff[dff["sex"] == sex]
    if age is not None and age != "All":
        dff = dff[dff["age_group"] == age]
    if category is not None and category != "All":
        dff = dff[dff["category"] == category]
    if disease is not None and disease != "All":
        dff = dff[dff["disease"] == disease]
    return dff


filtered = filter_df_for_map(
    df,
    selected_year,
    selected_sex,
    selected_age,
    selected_category,
    selected_disease,
)

if filtered.empty:
    st.warning("No data available for the selected filter combination.")
    st.stop()

df_map = (
    filtered.groupby("location", as_index=False)[metric_col]
    .sum()
    .sort_values(metric_col, ascending=False)
)

# ------------------------------------------------------------
# MERGE WITH COORDINATES
# ------------------------------------------------------------
coords_df = (
    pd.DataFrame.from_dict(STATE_COORDS, orient="index")
    .reset_index()
    .rename(columns={"index": "location"})
)

df_map = df_map.merge(coords_df, on="location", how="left")

missing_coords = df_map[df_map["lat"].isna()]["location"].unique()
if len(missing_coords) > 0:
    st.warning(
        "Some locations do not have coordinates defined and will not appear on the map: "
        + ", ".join(missing_coords)
    )
    df_map = df_map.dropna(subset=["lat", "lon"])

if df_map.empty:
    st.error("No mappable locations after merging coordinates.")
    st.stop()

# ------------------------------------------------------------
# MAIN BUBBLE MAP (no GeoJSON needed)
# ------------------------------------------------------------
st.markdown("### Bubble Map of Disease Burden by State")

st.write(
    f"Showing **{metric_col} (rate)** by state for year **{selected_year}** "
    f"with filters: Sex = **{selected_sex}**, Age group = **{selected_age}**, "
    f"Category = **{selected_category}**, Disease = **{selected_disease}**."
)

fig_map = px.scatter_geo(
    df_map,
    lat="lat",
    lon="lon",
    scope="africa",
    color=metric_col,
    size=metric_col,
    hover_name="location",
    hover_data={metric_col: ":,.2f"},
    color_continuous_scale="Reds",
    size_max=30,
    labels={metric_col: f"{metric_col} (rate)"},
)

fig_map.update_layout(
    margin=dict(l=10, r=10, t=30, b=10),
    geo=dict(
        showland=True,
        landcolor="rgb(240,240,240)",
        showcountries=True,
        countrycolor="gray",
    ),
)

st.plotly_chart(fig_map, use_container_width=True)

# ------------------------------------------------------------
# TOP LOCATIONS TABLE & BAR CHART
# ------------------------------------------------------------
st.markdown("---")
st.markdown(f"### Top Locations by {metric_col} (rate)")

c1, c2 = st.columns((1.1, 1))

with c1:
    top_n = st.slider("Number of top locations to display", min_value=5, max_value=20, value=10)
    df_top = df_map.head(top_n)
    st.dataframe(df_top[["location", metric_col]].reset_index(drop=True))

with c2:
    fig_bar = px.bar(
        df_top,
        x="location",
        y=metric_col,
        labels={"location": "Location", metric_col: f"{metric_col} (rate)"},
    )
    fig_bar.update_layout(
        xaxis_tickangle=-45,
        margin=dict(l=40, r=10, t=30, b=80),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ------------------------------------------------------------
# NARRATIVE SUMMARY
# ------------------------------------------------------------
st.markdown("---")
st.markdown("### Map Narrative Summary")

top_loc = df_map.iloc[0]["location"]
top_val = df_map.iloc[0][metric_col]

median_val = df_map[metric_col].median()
min_loc = df_map.iloc[-1]["location"]
min_val = df_map.iloc[-1][metric_col]

sex_phrase = "all sexes" if selected_sex == "All" else selected_sex.lower()
age_phrase = "all ages" if selected_age == "All" else selected_age.lower()
cat_phrase = "all categories" if selected_category == "All" else selected_category
dis_phrase = "all diseases" if selected_disease == "All" else selected_disease

text = (
    f"In {selected_year}, the highest **{metric_col} rate** was observed in **{top_loc}**, "
    f"with a value of approximately **{top_val:,.2f}**. "
    f"The lowest {metric_col} rate was seen in **{min_loc}** "
    f"at about **{min_val:,.2f}**.\n\n"
    f"The median {metric_col} rate across all locations was around **{median_val:,.2f}**. "
    f"These estimates are based on data for **{sex_phrase}**, **{age_phrase}**, "
    f"category = **{cat_phrase}**, and disease = **{dis_phrase}**."
)

st.write(text)
