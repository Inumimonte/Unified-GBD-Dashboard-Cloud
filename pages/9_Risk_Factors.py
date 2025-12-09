import streamlit as st
import pandas as pd
from pathlib import Path

# ------------------------------------------------------------
# PAGE CONFIG
# ------------------------------------------------------------
st.set_page_config(
    page_title="Risk Factor Intelligence - Unified GBD Dashboard",
    layout="wide",
)

st.title("🧪 Risk Factor Intelligence")
st.subheader("Unified GBD Dashboard – Framework for Future Risk Factor Data")
st.markdown("---")

st.info(
    "This page is a **placeholder** for future risk factor analytics. "
    "As soon as a compatible risk factor dataset is added, it will automatically "
    "power charts and tables here."
)

# ------------------------------------------------------------
# EXPECTED DATASET PATH
# ------------------------------------------------------------
DATA_PATH = Path("data") / "Unified_GBD_Risk_Factors.csv"

if not DATA_PATH.exists():
    # --------------------------------------------------------
    # NO DATA YET – SHOW DESIGN SPEC & DOCUMENTATION
    # --------------------------------------------------------
    st.warning(
        f"⚠️ No risk factor dataset found at `{DATA_PATH}`.\n\n"
        "Once a file with this name is added to the `data` folder, "
        "this page will switch from 'framework mode' to a live analytics view."
    )

    st.markdown("### 1. Purpose of this Page")
    st.write(
        """
        The **Risk Factor Intelligence** page is designed to answer questions like:

        - Which **risk factors** contribute most to DALYs or YLLs nationally?
        - How do risk contributions vary by **sex**, **age group**, or **location**?
        - What are the **top risk factors** for a given disease (e.g., stroke, IHD)?
        - How have risk contributions **changed over time**?

        It will mirror the structure of the main dashboard, but focused on:
        **behavioral, metabolic, environmental, and other risk factors.**
        """
    )

    st.markdown("### 2. Expected Risk Factor Data Structure")
    st.write(
        """
        When you are ready to add risk factor data, create a CSV file named:

        ```text
        data/Unified_GBD_Risk_Factors.csv
        ```

        A recommended column structure is:

        - `risk_name` – e.g., High systolic blood pressure, Smoking, High BMI  
        - `risk_category` – e.g., Behavioral, Metabolic, Environmental  
        - `measure_name_standard` – e.g., DALYs Rate, YLLs Rate, YLDs Rate, PAF  
        - `cause_name` – disease or cause linked to the risk factor  
        - `location_name` – state / country / region  
        - `sex_name` – Male / Female / Both  
        - `age_name` – age group label  
        - `year` – numeric year  
        - `val` – numeric value (rate or fraction)  
        - `lower`, `upper` – optional confidence interval bounds  

        Once such a file exists, this page will be able to:
        - Pivot `measure_name_standard` into separate metrics (e.g. DALY/YLL/YLD/PAF)
        - Aggregate by risk, disease, category, or geography
        """
    )

    st.markdown("### 3. Planned Analytics on this Page")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🔝 Top Risk Factors")
        st.write(
            """
            - Ranking of risk factors by **attributable DALYs/YLLs**  
            - Filters for **Year**, **Sex**, **Age group**, **Location**  
            - Separate views by **risk category** (behavioral, metabolic, etc.)  
            """
        )

        st.markdown("#### 📈 Trends Over Time")
        st.write(
            """
            - Time series of DALYs/YLLs/YLDs **by risk factor**  
            - Ability to compare **two risk factors** side by side  
            - Highlighting of **increasing vs. decreasing** risks  
            """
        )

    with col2:
        st.markdown("#### 🧬 Risk–Disease Matrix")
        st.write(
            """
            - Heatmap of **risk factors vs. diseases**  
            - Shows which risks drive which causes  
            - Helps to identify **high-impact intervention targets**  
            """
        )

        st.markdown("#### 🌍 Geographic Risk Patterns")
        st.write(
            """
            - State-level variation in risk exposure or attributable burden  
            - Integration with the **map page** once risk data is geo-tagged  
            """
        )

    st.markdown("### 4. How to Activate this Page")
    st.write(
        """
        1. Prepare a CSV file named `Unified_GBD_Risk_Factors.csv`  
        2. Place it inside the `data` folder of this project  
        3. Ensure it has at least the following columns:

           ```text
           risk_name, risk_category, measure_name_standard,
           cause_name, location_name, sex_name, age_name, year, val
           ```

        4. Reload the Streamlit app.  
        5. This page will automatically switch from documentation mode to **live analytics mode**.
        """
    )

    st.success("Framework mode active – ready for future risk factor data.")
else:
    # --------------------------------------------------------
    # DATA EXISTS – BASIC LIVE VIEW (future-ready)
    # --------------------------------------------------------
    st.success(f"✅ Risk factor dataset found at `{DATA_PATH}`. Basic analytics enabled.")

    @st.cache_data
    def load_risk_data(path: Path) -> pd.DataFrame:
        df = pd.read_csv(path)

        # Try to standardize common names if present
        df = df.rename(
            columns={
                "location_name": "location",
                "sex_name": "sex",
                "age_name": "age_group",
                "cause_name": "disease",
            }
        )

        # Basic safety checks
        required_cols = ["risk_name", "measure_name_standard", "val", "year"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            st.error(
                "The risk factor file is missing required columns: "
                + ", ".join(missing)
            )
            st.stop()

        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
        df["val"] = pd.to_numeric(df["val"], errors="coerce")

        return df

    df_risk = load_risk_data(DATA_PATH)

    st.markdown("### 1. Quick Overview of Risk Factor Data")
    st.write("Preview of the first 10 rows:")
    st.dataframe(df_risk.head(10))

    years = sorted(df_risk["year"].dropna().unique())
    risks = sorted(df_risk["risk_name"].dropna().unique())
    measures = sorted(df_risk["measure_name_standard"].dropna().unique())

    st.markdown("---")
    st.markdown("### 2. Simple Risk Factor Explorer")

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_year = st.selectbox("Year", options=["All"] + list(years), index=0)
    with c2:
        sel_measure = st.selectbox("Measure", options=measures, index=0)
    with c3:
        sel_risk = st.selectbox("Risk factor (optional filter)", options=["All"] + list(risks), index=0)

    df_view = df_risk[df_risk["measure_name_standard"] == sel_measure].copy()
    if sel_year != "All":
        df_view = df_view[df_view["year"] == sel_year]
    if sel_risk != "All":
        df_view = df_view[df_view["risk_name"] == sel_risk]

    if df_view.empty:
        st.info("No data available for the selected filters.")
    else:
        st.markdown(f"#### Top risk factors by `{sel_measure}`")

        top_tbl = (
            df_view.groupby("risk_name", as_index=False)["val"]
            .mean()
            .sort_values("val", ascending=False)
            .head(15)
        )

        c4, c5 = st.columns((1.1, 1))
        with c4:
            st.dataframe(top_tbl.reset_index(drop=True))

        with c5:
            fig = px.bar(
                top_tbl,
                x="val",
                y="risk_name",
                orientation="h",
                labels={"val": sel_measure, "risk_name": "Risk factor"},
            )
            fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
                margin=dict(l=120, r=10, t=30, b=40),
            )
            st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.markdown("### 3. Next Steps for Risk Factor Analytics")
    st.write(
        """
        This basic view confirms the dataset is readable. Future enhancements may include:
        
        - Risk–disease heatmaps  
        - Time trends of risk-attributable DALYs/YLLs/YLDs  
        - Geographic variation by state or region  
        - Comparative risk profiling by sex, age, and location  
        """
    )

    st.success("Live mode active – risk factor data is being used.")
