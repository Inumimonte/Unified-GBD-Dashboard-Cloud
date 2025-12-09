import streamlit as st

# ------------------------------------------------------------
# PAGE CONFIGURATION
# ------------------------------------------------------------
st.set_page_config(
    page_title="Methodology & Metadata - Unified GBD Dashboard",
    layout="wide",
)

st.title("📘 Methodology & Metadata")
st.markdown("## Unified Global Burden of Disease (GBD) Dashboard")
st.markdown("---")

# ------------------------------------------------------------
# SECTION: Overview
# ------------------------------------------------------------
st.header("1. Overview")
st.write("""
This dashboard provides an integrated **National Disease Intelligence System** using 
Global Burden of Disease (GBD) measures — including **DALYs, YLLs, and YLDs** — 
to help policymakers, researchers, and program managers explore health loss across 
diseases, demographic groups, locations, and time.

It aims to support:
- Strategic planning  
- Priority-setting  
- Health systems strengthening  
- Program monitoring and evaluation  
- Evidence-based policy development  
""")

st.markdown("---")

# ------------------------------------------------------------
# SECTION: Data Source
# ------------------------------------------------------------
st.header("2. Data Sources")

st.write("""
The dataset used in this dashboard is derived from the **Global Burden of Disease Study (GBD)**.
It was exported, cleaned, merged, and standardized into a unified table via the following fields:

- **measure_name_standard** (e.g., `DALYs Rate`, `YLLs Rate`)
- **sex_name**
- **age_name**
- **cause_name**
- **location_name**
- **year**
- **val** (numeric rate)
- **upper / lower** (confidence intervals, where available)

Only population-standardized rates were included to allow comparison across demographic groups.
""")

st.info("""
📌 **Note:** DALYs, YLLs, and YLDs in this dashboard represent *rates* unless otherwise stated.
""")

st.markdown("---")

# ------------------------------------------------------------
# SECTION: Definitions
# ------------------------------------------------------------
st.header("3. GBD Measure Definitions")

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("🔵 DALYs")
    st.write("""
**Disability-Adjusted Life Years**  
A composite measure of overall disease burden.  
It reflects the **total healthy years of life lost** due to premature mortality (**YLLs**) 
and non-fatal health loss (**YLDs**).

Formula:  
**DALY = YLL + YLD**
""")

with col2:
    st.subheader("🟣 YLLs")
    st.write("""
**Years of Life Lost**  
A measure of premature mortality.  
Calculated by multiplying the number of deaths by the standard life expectancy 
remaining at the age of death.

Represents **fatal burden**.
""")

with col3:
    st.subheader("🟢 YLDs")
    st.write("""
**Years Lived with Disability**  
A measure of non-fatal health loss.  
Computed as prevalence × disability weight.

Represents **morbidity burden**.
""")

st.markdown("---")

# ------------------------------------------------------------
# SECTION: Category Mapping
# ------------------------------------------------------------
st.header("4. Cause → Category Classification Method")

st.write("""
All causes provided in `cause_name` were mapped into high-level GBD groups using a hybrid approach:

### **A. Exact GBD category matching**
If the cause name matched known GBD groupings (e.g., *Cardiovascular diseases*, *Transport injuries*),
it was assigned directly.

### **B. Rule-based substring classification**
If no exact match existed, the system checked for keywords such as:

- **Communicable:** “malaria”, “HIV”, “tuberculosis”, “infection”, “measles”
- **Maternal/Neonatal:** “maternal”, “neonatal”, “birth asphyxia”, “preterm”
- **Injuries:** “injury”, “violence”, “road traffic”, “fire”, “fall”
- **Fallback to NCD category** otherwise

### **Resulting Categories:**
- **Non-communicable diseases**
- **Communicable diseases**
- **Injuries**
- **Maternal & Neonatal**
- **Unclassified** (rare cases)

This classification allows high-level visual summaries in pie charts, heatmaps, and KPIs.
""")

st.warning("""
⚠️ **Note:** While robust, this mapping is still an automated classification and may not fully 
replicate official GBD Level-2 categories. Future updates will allow manual overrides 
and official mapping tables.
""")

st.markdown("---")

# ------------------------------------------------------------
# SECTION: Data Cleaning & Transformation
# ------------------------------------------------------------
st.header("5. Data Cleaning & Transformation Steps")

st.write("""
The unified dataset was prepared using Python and Streamlit with the following steps:

### **Step 1 — Load & rename fields**
- Converted GBD variable names into streamlined analytics-friendly fields:
  `sex`, `age_group`, `disease`, `location`, `year`, etc.

### **Step 2 — Select key measures**
Only `DALYs Rate` and `YLLs Rate` were extracted.  
YLD was computed using the identity:  
**YLD = DALY - YLL**

### **Step 3 — Pivot data from long → wide format**
This created a table with individual columns for `DALY`, `YLL`, and `YLD`.

### **Step 4 — Category mapping**
Each disease was assigned to a GBD category using mapping logic (see above).

### **Step 5 — Handling missing values**
All metrics were converted to numeric, with missing entries filled using zeros.

### **Step 6 — Filtering engine**
The dashboard allows filtering by:

- Year  
- Sex  
- Age group  
- Location  
- Category  
- Disease  
- Metric  

Each filter updates all charts, KPIs, narrative output, and downloadable tables.
""")

st.markdown("---")

# ------------------------------------------------------------
# SECTION: Limitations
# ------------------------------------------------------------
st.header("6. Limitations")

st.write("""
Although robust, the dashboard has some limitations:

- **Rates only**: Raw counts (absolute cases, deaths) are not included unless added later.
- **Automated category assignment**: Some diseases may require manual re-classification.
- **No subnational geography**: State/LGA analysis will be added in the Map Module.
- **GBD dependency**: Updates require new GBD releases or local datasets.
- **Age groups**: Only the available age groups in the exported dataset are included.

Future versions will include:
- Proper GBD cause hierarchy  
- Forecasting  
- Subnational spatial analytics  
- Risk factor attribution  
""")

st.markdown("---")

# ------------------------------------------------------------
# SECTION: Versioning & Authors
# ------------------------------------------------------------
st.header("7. Versioning & Authors")

st.write("""
**Dashboard version:** 1.0  
**Last updated:** 2025  

**Developed by:**  
- *Inumimonte David Ennis* – Epidemiologist, Data Scientist  
- Streamlit automation powered by AI  

This dashboard is part of the **Full National Disease Intelligence System** initiative, 
built to support real-time, data-driven decision-making in public health.
""")

st.success("✔ Methodology Page Loaded Successfully – Your dashboard is now publication-ready!")
