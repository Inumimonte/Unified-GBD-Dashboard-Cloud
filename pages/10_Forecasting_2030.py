import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Forecasting – 2030 Projections",
    layout="wide",
)

st.title("📈 Forecasting Engine – 2030 Projections")
st.subheader("Unified GBD Dashboard – Simple Trend-Based Projections")
st.markdown("---")

st.info(
    "This page uses simple time-series trends (linear regression) on historical DALY/YLL/YLD rates "
    "to project values up to 2030. These are **not official forecasts**, but indicative scenarios."
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
# DATA LOADER – same logic as app.py
# ------------------------------------------------------------
from pathlib import Path  # make sure this import is at the top of the file

@st.cache_data
def load_data():
    data_dir = Path("data")
    parquet_path = data_dir / "Unified_GBD_Fact_Table_CLEAN.parquet"

    if parquet_path.exists():
        df_raw = pd.read_parquet(parquet_path)
    else:
        st.error(f"Data file not found: {parquet_path}")
        st.stop()

    # keep the rest of your processing code below exactly as it was
    # (filtering by year, disease, forecasting prep, etc.)


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
locations = sorted(df["location"].dropna().unique())
categories = sorted(df["category"].dropna().unique())
diseases = sorted(df["disease"].dropna().unique())

# ------------------------------------------------------------
# SIDEBAR FILTERS
# ------------------------------------------------------------
st.sidebar.header("Forecast Filters")

selected_metric = st.sidebar.selectbox("Metric", options=["DALY", "YLL", "YLD"], index=0)
selected_sex = st.sidebar.selectbox("Sex", options=["All"] + list(sexes), index=0)
selected_age = st.sidebar.selectbox("Age group", options=["All"] + list(age_groups), index=0)
selected_location = st.sidebar.selectbox("Location", options=["All"] + list(locations), index=0)
selected_category = st.sidebar.selectbox("Category", options=["All"] + list(categories), index=0)
selected_disease = st.sidebar.selectbox("Disease (cause)", options=["All"] + list(diseases), index=0)

max_hist_year = max(years)
forecast_end = st.sidebar.slider("Forecast up to year", min_value=max_hist_year + 1, max_value=2035, value=2030)

metric_col = selected_metric

# ------------------------------------------------------------
# FILTER DATA FOR FORECAST
# ------------------------------------------------------------
def filter_df_for_forecast(
    df: pd.DataFrame,
    sex,
    age,
    location,
    category,
    disease,
):
    dff = df.copy()
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


df_filt = filter_df_for_forecast(
    df,
    selected_sex,
    selected_age,
    selected_location,
    selected_category,
    selected_disease,
)

if df_filt.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Aggregate by year
ts = (
    df_filt.groupby("year", as_index=False)[metric_col]
    .sum()
    .sort_values("year")
)

if ts.shape[0] < 3:
    st.warning(
        "Not enough historical years to fit a stable trend. "
        "At least 3 years of data are recommended."
    )
    st.dataframe(ts)
    st.stop()

# ------------------------------------------------------------
# FIT SIMPLE LINEAR TREND: metric ~ year
# ------------------------------------------------------------
x = ts["year"].values
y = ts[metric_col].values

# Fit y = a * year + b
a, b = np.polyfit(x, y, 1)

future_years = np.arange(x.min(), forecast_end + 1)
y_pred = a * future_years + b

df_forecast = pd.DataFrame(
    {
        "year": future_years,
        metric_col: y_pred,
        "type": ["Forecast" if yr > max_hist_year else "Observed" for yr in future_years],
    }
)

# Merge actual observed values where available (overwrite forecast values for observed years)
df_forecast = df_forecast.merge(
    ts[["year", metric_col]].rename(columns={metric_col: "observed_val"}),
    on="year",
    how="left",
)
df_forecast[metric_col] = df_forecast["observed_val"].fillna(df_forecast[metric_col])
df_forecast.drop(columns=["observed_val"], inplace=True)

# ------------------------------------------------------------
# PLOTS & TABLE
# ------------------------------------------------------------
st.markdown("### Forecasted Trend")

c1, c2 = st.columns((1.3, 1))

with c1:
    fig = px.line(
        df_forecast,
        x="year",
        y=metric_col,
        color="type",
        markers=True,
        labels={"year": "Year", metric_col: f"{metric_col} (rate)", "type": ""},
    )
    fig.update_layout(
        margin=dict(l=40, r=10, t=30, b=40),
    )
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.markdown("**Observed vs Projected Values**")
    st.dataframe(
        df_forecast.sort_values("year").reset_index(drop=True),
        use_container_width=True,
    )

st.markdown("---")

# ------------------------------------------------------------
# NARRATIVE SUMMARY
# ------------------------------------------------------------
st.markdown("### Forecast Narrative Summary")

start_year = int(ts["year"].min())
end_year = int(ts["year"].max())
start_val = float(ts.loc[ts["year"] == start_year, metric_col].values[0])
end_val = float(ts.loc[ts["year"] == end_year, metric_col].values[0])
proj_val_2030 = float(df_forecast.loc[df_forecast["year"] == forecast_end, metric_col].values[0])

abs_change = end_val - start_val
pct_change = (abs_change / start_val * 100) if start_val != 0 else None

sex_phrase = "all sexes" if selected_sex == "All" else selected_sex.lower()
age_phrase = "all ages" if selected_age == "All" else selected_age.lower()
loc_phrase = "all locations" if selected_location == "All" else selected_location
cat_phrase = "all categories" if selected_category == "All" else selected_category
dis_phrase = "all diseases" if selected_disease == "All" else selected_disease

summary = (
    f"Between {start_year} and {end_year}, the {metric_col} rate changed from "
    f"approximately {start_val:,.2f} to {end_val:,.2f} for {sex_phrase}, {age_phrase}, "
    f"in {loc_phrase}, category = {cat_phrase}, disease = {dis_phrase}.\n\n"
)

if pct_change is not None:
    summary += f"This represents a **{pct_change:+.1f}% change** over the observed period.\n\n"

summary += (
    f"Assuming the historical linear trend continues, the projected {metric_col} rate "
    f"for {forecast_end} is about **{proj_val_2030:,.2f}**.\n\n"
    "These are **trend-based projections only** and should be interpreted with caution. "
    "They do not account for new interventions, shocks, or changes in risk factor profiles."
)

st.write(summary)


