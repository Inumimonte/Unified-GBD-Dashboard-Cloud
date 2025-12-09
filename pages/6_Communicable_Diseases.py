import streamlit as st
import plotly.express as px
import pandas as pd

from gbd_utils import load_data, filter_data

# ------------------------------------------------------------
# Constants
# ------------------------------------------------------------
CD_CAUSES = ["Malaria", "HIV/AIDS", "Tuberculosis"]

CD_COLORS = {
    "Malaria": "#1f77b4",       # blue
    "HIV/AIDS": "#d62728",      # red
    "Tuberculosis": "#2ca02c",  # green
}

STATE_COLORS = {
    "Abuja": "#1f77b4",
    "FCT": "#1f77b4",
    "Lagos": "#ff7f0e",
    "Rivers": "#2ca02c",
    "Kano": "#d62728",
    "Kaduna": "#9467bd",
    "Borno": "#8c564b",
    "Yobe": "#e377c2",
    "Adamawa": "#7f7f7f",
    "Gombe": "#17becf",
    "Bayelsa": "#bcbd22",
}
STATE_COLORS_WITH_NATIONAL = STATE_COLORS | {"National average": "#000000"}


def format_num(x: float) -> str:
    """Nice number formatting for metrics."""
    try:
        return f"{x:,.1f}"
    except Exception:
        return str(x)


# ------------------------------------------------------------
# Page title + intro
# ------------------------------------------------------------
st.title("🦠 Communicable Diseases Explorer (Malaria, HIV/AIDS, Tuberculosis)")

st.markdown(
    """
This page focuses on the **three core communicable diseases**:

- **Malaria**
- **HIV/AIDS**
- **Tuberculosis**

It uses the unified GBD fact table and supports multiple metrics:
**DALYs Rate, Mortality Rate, Incidence Rate, Prevalence Rate, YLLs Rate**.

You can slice by **state, sex, age group, year**, and explore:
- National burden & trends
- State-level trends and rankings
- Comparison between diseases
- Download-ready datasets for further analysis
"""
)

# ------------------------------------------------------------
# Load unified fact table & filter to CD causes
# ------------------------------------------------------------
df = load_data()
cd_df = df[df["cause_name"].isin(CD_CAUSES)].copy()

if cd_df.empty:
    st.error("No data found for Malaria, HIV/AIDS, and Tuberculosis in the unified table.")
    st.stop()

# ------------------------------------------------------------
# Sidebar filters
# ------------------------------------------------------------
st.sidebar.header("Filters · Communicable Diseases")

# Metric switcher
metric_options = sorted(cd_df["measure_name_standard"].unique())
default_metric = "DALYs Rate" if "DALYs Rate" in metric_options else metric_options[0]
metric_index = metric_options.index(default_metric)
metric_sel = st.sidebar.selectbox("Metric", metric_options, index=metric_index)

# Locations
locations = sorted(cd_df["location_name"].unique())
location_selected = st.sidebar.multiselect("Location (state)", locations)

# Years
years_all = sorted(cd_df["year"].unique())
year_selected = st.sidebar.multiselect("Year", years_all, default=years_all)

# Sex
sexes = sorted(cd_df["sex_name"].unique())
sex_selected = st.sidebar.multiselect("Sex", sexes)

# Age groups
ages = sorted(cd_df["age_name"].unique())
age_selected = st.sidebar.multiselect("Age group", ages)

st.sidebar.caption(f"Metric in use: **{metric_sel}**")

# ------------------------------------------------------------
# Apply filters using helper
# ------------------------------------------------------------
base = cd_df[cd_df["measure_name_standard"] == metric_sel].copy()

filtered = filter_data(
    base,
    year=year_selected,
    location=location_selected,
    sex=sex_selected,
    age_group=age_selected,
)

if filtered.empty:
    st.warning("No data for the current filters.")
    st.stop()
    # Year range for all subsequent summaries (for clarity in titles)
year_min = int(filtered["year"].min())
year_max = int(filtered["year"].max())


# ------------------------------------------------------------
# Cause selection (within Malaria / HIV / TB)
# ------------------------------------------------------------
st.markdown("### Cause selection")

cause_options = [c for c in CD_CAUSES if c in filtered["cause_name"].unique()]
selected_causes = st.multiselect(
    "Select communicable diseases to include",
    options=cause_options,
    default=cause_options,
)
if selected_causes:
    filtered = filtered[filtered["cause_name"].isin(selected_causes)]

st.caption(f"Rows after cause filter: **{len(filtered):,}**")

if filtered.empty:
    st.warning("No rows remain after applying the cause filter.")
    st.stop()

# ------------------------------------------------------------
# Key metrics
# ------------------------------------------------------------
st.markdown("### Key Communicable Disease Metrics")

cause_agg = (
    filtered.groupby("cause_name", as_index=False)["val"]
    .sum()
    .sort_values("val", ascending=False)
)

dom_cause = cause_agg.iloc[0]["cause_name"]
dom_val = cause_agg.iloc[0]["val"]
total_val = cause_agg["val"].sum()
share_total = dom_val / total_val if total_val > 0 else 0

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Dominant CD cause", value=dom_cause)
with col2:
    st.metric(f"Total {metric_sel}", value=format_num(total_val))
with col3:
    st.metric(
        f"% contribution of {dom_cause}",
        value=f"{share_total * 100:,.1f}%"
    )

# ------------------------------------------------------------
# Insights card
# ------------------------------------------------------------
with st.expander("Automatic insight highlights"):
    first_year = filtered["year"].min()
    last_year = filtered["year"].max()

    # Change over time by disease
    change_rows = []
    for cd in cause_options:
        df_cd = filtered[filtered["cause_name"] == cd]
        if df_cd.empty:
            continue
        start = (
            df_cd[df_cd["year"] == first_year]["val"].mean()
            if (df_cd["year"] == first_year).any()
            else None
        )
        end = (
            df_cd[df_cd["year"] == last_year]["val"].mean()
            if (df_cd["year"] == last_year).any()
            else None
        )
        if start is not None and end is not None:
            abs_change = end - start
            pct_change = (abs_change / start) * 100 if start != 0 else None
            change_rows.append((cd, abs_change, pct_change))

    if change_rows:
        for cd, abs_change, pct_change in change_rows:
            direction = "increased" if abs_change > 0 else "decreased"
            st.info(
                f"- **{cd}** {direction} by "
                f"{abs(abs_change):,.1f} ({abs(pct_change):.1f}%) between "
                f"{first_year} and {last_year}."
            )
    else:
        st.write("Not enough data across years to compute change summaries.")

# ------------------------------------------------------------
# Burden by communicable disease (bar)
# ------------------------------------------------------------
st.markdown("### Burden by communicable disease (Malaria vs HIV/AIDS vs TB)")

fig_cause_bar = px.bar(
    cause_agg,
    x="val",
    y="cause_name",
    orientation="h",
    color="cause_name",
    color_discrete_map=CD_COLORS,
    labels={"val": metric_sel, "cause_name": "Communicable disease"},
    title=f"{metric_sel} for Malaria, HIV/AIDS, and Tuberculosis",
)

fig_cause_bar.update_layout(
    height=350,
    margin=dict(l=200, r=40, t=60, b=40),
    yaxis={"categoryorder": "total ascending"},
)
st.plotly_chart(fig_cause_bar, use_container_width=True, key="cd_cause_bar")

# ------------------------------------------------------------
# Trend over time by communicable disease (national)
# ------------------------------------------------------------
st.markdown("### Trend over time by communicable disease")

trend_cd = (
    filtered.groupby(["year", "cause_name"], as_index=False)["val"]
    .sum()
    .sort_values(["year", "cause_name"])
)

if trend_cd.empty:
    st.info("No trend data for current filters.")
else:
    smooth_nat = st.checkbox(
        "Apply 3-year moving average smoothing (national trend)",
        value=False,
        key="cd_nat_smooth",
    )

    trend_plot_nat = trend_cd.copy()
    if smooth_nat:
        trend_plot_nat["val_plot"] = (
            trend_plot_nat.groupby("cause_name")["val"]
            .rolling(window=3, min_periods=1, center=True)
            .mean()
            .reset_index(level=0, drop=True)
        )
    else:
        trend_plot_nat["val_plot"] = trend_plot_nat["val"]

    fig_trend_cd = px.line(
        trend_plot_nat,
        x="year",
        y="val_plot",
        color="cause_name",
        color_discrete_map=CD_COLORS,
        markers=True,
        labels={"val_plot": metric_sel, "year": "Year"},
        title=f"{metric_sel} trend over time (Malaria, HIV/AIDS, TB)",
    )

    fig_trend_cd.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=40, b=80),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )

    fig_trend_cd.update_traces(
        hovertemplate=(
            "Year: %{x}<br>"
            "Cause: %{legendgroup}<br>"
            f"{metric_sel}: "+"%{y:,.1f}<extra></extra>"
        )
    )

    st.plotly_chart(fig_trend_cd, use_container_width=True, key="cd_trend_cause")

    # Grouped bar by year
    st.markdown("#### Yearly comparison by disease (grouped bar)")
    fig_trend_bar = px.bar(
        trend_cd,
        x="year",
        y="val",
        color="cause_name",
        barmode="group",
        color_discrete_map=CD_COLORS,
        labels={"val": metric_sel, "year": "Year", "cause_name": "Communicable disease"},
        title=f"{metric_sel} by year and disease (grouped)",
    )
    fig_trend_bar.update_layout(
        height=400,
        margin=dict(l=40, r=40, t=40, b=60),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
        ),
    )
    st.plotly_chart(fig_trend_bar, use_container_width=True, key="cd_trend_bar_grouped")

# ------------------------------------------------------------
# Trend over time by communicable disease & state
# ------------------------------------------------------------
st.markdown("### Trend over time by Communicable Disease & State")

cause_state_sel = st.selectbox(
    "Select communicable disease for state-level trend",
    options=cause_options,
    key="cd_state_cause_sel",
)

df_cause_state = filtered[filtered["cause_name"] == cause_state_sel]

if df_cause_state.empty:
    st.warning("No data found for this cause with the current filters.")
else:
    view_mode = st.radio(
        "State view mode",
        options=["Top N states (by burden)", "Choose states manually"],
        horizontal=True,
        key="cd_state_view_mode",
    )

    top_n = st.slider(
        "Number of top states (N)",
        min_value=3,
        max_value=15,
        value=5,
        step=1,
        key="cd_state_topn",
    )

    smooth_state = st.checkbox(
        "Apply 3-year moving average smoothing (state trends)",
        value=False,
        key="cd_state_smooth",
    )

    if view_mode == "Top N states (by burden)":
        top_states = (
            df_cause_state.groupby("location_name")["val"]
            .sum()
            .sort_values(ascending=False)
            .head(top_n)
            .index.tolist()
        )
        state_list = top_states
        st.markdown(
            f"**Top {top_n} states by total '{cause_state_sel}' burden:** "
            + ", ".join(top_states)
        )
    else:
        all_states_for_cause = sorted(df_cause_state["location_name"].unique())
        default_states = all_states_for_cause[: min(5, len(all_states_for_cause))]
        state_list = st.multiselect(
            "Select states to compare",
            options=all_states_for_cause,
            default=default_states,
            key="cd_state_custom",
        )
        if not state_list:
            st.warning("Select at least one state to show the trend.")
            state_list = []

    if state_list:
        df_states = df_cause_state[df_cause_state["location_name"].isin(state_list)]

        # National average line
        nat = (
            df_cause_state.groupby("year", as_index=False)["val"]
            .mean()
            .rename(columns={"val": "val"})
        )
        nat["location_name"] = "National average"

        trend_state = pd.concat(
            [
                df_states[["year", "location_name", "val"]],
                nat[["year", "location_name", "val"]],
            ],
            ignore_index=True,
        ).sort_values(["location_name", "year"])

        if smooth_state:
            trend_state["val_plot"] = (
                trend_state.groupby("location_name")["val"]
                .rolling(window=3, min_periods=1, center=True)
                .mean()
                .reset_index(level=0, drop=True)
            )
        else:
            trend_state["val_plot"] = trend_state["val"]

        fig_state_trend = px.line(
            trend_state,
            x="year",
            y="val_plot",
            color="location_name",
            color_discrete_map=STATE_COLORS_WITH_NATIONAL,
            markers=True,
            labels={"val_plot": metric_sel, "location_name": "State / Location"},
            title=f"Trend for '{cause_state_sel}' by state",
        )

        fig_state_trend.update_traces(
            hovertemplate=(
                "Year: %{x}<br>"
                "Location: %{legendgroup}<br>"
                f"{metric_sel}: "+"%{y:,.1f}<extra></extra>"
            )
        )

        # Peak annotation across all states
        peak_row = trend_state.loc[trend_state["val_plot"].idxmax()]
        fig_state_trend.add_annotation(
            x=peak_row["year"],
            y=peak_row["val_plot"],
            text=f"{peak_row['location_name']}: {peak_row['val_plot']:,.0f}",
            showarrow=True,
            arrowhead=2,
            ax=0,
            ay=-40,
            bgcolor="rgba(0,0,0,0.6)",
            font=dict(color="white", size=10),
        )

        fig_state_trend.update_layout(
            height=450,
            margin=dict(l=60, r=60, t=60, b=80),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.2,
                xanchor="center",
                x=0.5,
            ),
        )
        st.plotly_chart(fig_state_trend, use_container_width=True, key="cd_trend_state")

        # State ranking for this disease
                # State ranking for this disease (with year range + % of national burden)
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

        # % of total national burden for this disease
        total_disease_burden = state_agg["total_burden"].sum()
        state_agg["pct_of_disease"] = (
            state_agg["total_burden"] / total_disease_burden * 100
            if total_disease_burden > 0
            else 0
        )

        # Bar chart: top N states
        top_rank = state_agg.head(top_n)
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
                f"Top {top_n} states by total '{cause_state_sel}' burden "
                f"({year_min}–{year_max})"
            ),
        )
        fig_rank.update_layout(
            height=350,
            margin=dict(l=160, r=40, t=60, b=40),
            yaxis={"categoryorder": "total ascending"},
        )
        st.plotly_chart(fig_rank, use_container_width=True, key="cd_rank_bar")

        # Top & bottom tables with % of disease burden
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

        # Summary across diseases: top & bottom state per disease
        st.markdown(
            f"#### Summary by disease: highest and lowest burden states "
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
                    "Disease": cd,
                    "Top state": top_state["location_name"],
                    f"Top state {metric_sel}": round(top_state["total_burden"], 1),
                    "Top state % of disease burden": f"{top_state['pct_of_disease']:,.1f}%",
                    "Bottom state": bottom_state["location_name"],
                    f"Bottom state {metric_sel}": round(
                        bottom_state["total_burden"], 1
                    ),
                    "Bottom state % of disease burden": f"{bottom_state['pct_of_disease']:,.1f}%",
                }
            )

        if summary_rows:
            summary_df = pd.DataFrame(summary_rows)
            st.dataframe(summary_df, use_container_width=True)
        else:
            st.info("No state summary available for the current filters.")

        # Downloads
        with st.expander("Download CD data (CSV)"):
            csv_filtered = filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                "Download filtered CD data",
                data=csv_filtered,
                file_name="cd_filtered.csv",
                mime="text/csv",
                key="cd_download_filtered",
            )

            csv_trend = trend_state.to_csv(index=False).encode("utf-8")
            st.download_button(
                f"Download state trend for '{cause_state_sel}'",
                data=csv_trend,
                file_name=f"cd_trend_{cause_state_sel.replace(' ', '_')}.csv",
                mime="text/csv",
                key="cd_download_trend",
            )

# ------------------------------------------------------------
# Compare two communicable diseases by state
# ------------------------------------------------------------
st.markdown("### Compare two communicable diseases by state")

cause_pair = st.multiselect(
    "Select exactly two diseases",
    options=cause_options,
    max_selections=2,
    key="cd_compare_pair",
)

comp_top_n = st.slider(
    "Number of top states (N) for comparison",
    min_value=3,
    max_value=15,
    value=5,
    step=1,
    key="cd_compare_topn",
)

if len(cause_pair) == 2:
    df_pair = filtered[filtered["cause_name"].isin(cause_pair)]
    if df_pair.empty:
        st.info("No data for these two diseases with the current filters.")
    else:
        agg_pair = (
            df_pair.groupby(["cause_name", "location_name"], as_index=False)["val"]
            .sum()
            .rename(columns={"val": "total_burden"})
        )

        base_cause = cause_pair[0]
        top_states_pair = (
            agg_pair[agg_pair["cause_name"] == base_cause]
            .sort_values("total_burden", ascending=False)
            .head(comp_top_n)["location_name"]
            .tolist()
        )

        agg_pair_top = agg_pair[agg_pair["location_name"].isin(top_states_pair)]

        fig_compare = px.bar(
            agg_pair_top,
            x="total_burden",
            y="location_name",
            color="cause_name",
            barmode="group",
            labels={
                "total_burden": f"Total {metric_sel}",
                "location_name": "State",
                "cause_name": "Communicable disease",
            },
            title=(
                f"Comparison of '{cause_pair[0]}' and '{cause_pair[1]}' "
                f"in Top {comp_top_n} states (by {base_cause} burden)"
            ),
            color_discrete_map=CD_COLORS,
        )
        fig_compare.update_layout(
            height=400,
            margin=dict(l=260, r=60, t=80, b=60),
        )
        st.plotly_chart(fig_compare, use_container_width=True, key="cd_compare_causes")
else:
    st.info("Select exactly two diseases above to see the comparison.")

# ------------------------------------------------------------
# Heatmap: disease vs state
# ------------------------------------------------------------
st.markdown("### Heatmap of burden by state and disease")

heat_top_n = st.slider(
    "Number of top states (by total CD burden) for heatmap",
    min_value=5,
    max_value=30,
    value=15,
    step=1,
    key="cd_heat_topn",
)

heat_agg = (
    filtered.groupby(["location_name", "cause_name"], as_index=False)["val"]
    .sum()
)

top_states_heat = (
    heat_agg.groupby("location_name")["val"]
    .sum()
    .sort_values(ascending=False)
    .head(heat_top_n)
    .index.tolist()
)

heat_df = heat_agg[heat_agg["location_name"].isin(top_states_heat)]
heat_pivot = heat_df.pivot(
    index="location_name",
    columns="cause_name",
    values="val",
).fillna(0)

if not heat_pivot.empty:
    fig_heat = px.imshow(
        heat_pivot,
        labels=dict(
            x="Communicable disease",
            y="State",
            color=metric_sel,
        ),
        aspect="auto",
        title=f"{metric_sel} heatmap for top {heat_top_n} states",
    )
    st.plotly_chart(fig_heat, use_container_width=True, key="cd_heatmap")
else:
    st.info("Not enough data to generate heatmap for selected filters.")

# ------------------------------------------------------------
# Data preview
# ------------------------------------------------------------
with st.expander("Filtered Communicable Disease data preview"):
    st.dataframe(filtered.head(50), use_container_width=True)
