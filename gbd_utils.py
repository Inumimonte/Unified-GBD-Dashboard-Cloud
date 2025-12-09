# gbd_utils.py

import pandas as pd
import streamlit as st

DATA_PATH = "data/Unified_GBD_Fact_Table_CLEAN.csv"

# Cause colors for charts
CAUSE_COLORS = {
    "Malaria": "#2ca02c",      # green
    "HIV/AIDS": "#d62728",     # red
    "Tuberculosis": "#ff7f0e"  # orange
}


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH)
    df["year"] = df["year"].astype(int)
    return df


def filter_data(
    df,
    year=None,
    location=None,
    measure=None,
    sex=None,
    age_group=None,
):
    df_filtered = df.copy()

    if year:
        df_filtered = df_filtered[df_filtered["year"].isin(year)]
    if location:
        df_filtered = df_filtered[df_filtered["location_name"].isin(location)]
    if measure:
        df_filtered = df_filtered[df_filtered["measure_name_standard"].isin(measure)]
    if sex:
        df_filtered = df_filtered[df_filtered["sex_name"].isin(sex)]
    if age_group:
        df_filtered = df_filtered[df_filtered["age_name"].isin(age_group)]

    return df_filtered


def compute_dominant_cause(df_filtered):
    if df_filtered.empty:
        return None, 0, 0

    grouped = (
        df_filtered.groupby("cause_name", as_index=False)["val"]
        .sum()
        .sort_values("val", ascending=False)
    )

    dominant_row = grouped.iloc[0]
    total_val = grouped["val"].sum()

    dominant_cause = dominant_row["cause_name"]
    dominant_val = dominant_row["val"]
    dominant_share = dominant_val / total_val if total_val > 0 else 0

    return dominant_cause, dominant_val, dominant_share
