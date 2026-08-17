"""
NIFTY 100 Analytics - Sector Analysis
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_sectors,
    get_analysis,
    get_valuation,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Sector Analysis",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def parse_percentage(value):
    """
    Convert percentage-like values into numeric values.

    Examples:
        15%   -> 15.0
        15.2  -> 15.2
        15.2% -> 15.2
    """

    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        text,
    )

    if match:
        return float(match.group())

    return None


def get_year_rows(df, year):
    """
    Return rows matching the selected financial year.

    Handles database values such as:
        Mar 2024
        2024
        FY 2024
    """

    if df.empty or "year" not in df.columns:
        return pd.DataFrame()

    return df[
        df["year"].astype(str).str.contains(
            str(year),
            na=False,
            regex=False,
        )
    ].copy()


def get_revenue_cagr(ticker):
    """
    Return compounded sales growth for a company.
    """

    analysis = get_analysis(ticker)

    if analysis.empty:
        return None

    if "compounded_sales_growth" not in analysis.columns:
        return None

    return parse_percentage(
        analysis.iloc[0][
            "compounded_sales_growth"
        ]
    )


def get_sector_metrics(
    companies,
    sectors,
    selected_year,
):
    """
    Build company-level financial metrics
    required for sector aggregation.
    """

    rows = []

    # -------------------------------------------------------------
    # Sector mapping
    # -------------------------------------------------------------

    sector_map = sectors[
        [
            "company_id",
            "broad_sector",
            "sub_sector",
        ]
    ].drop_duplicates(
        subset=["company_id"]
    )

    company_data = companies.merge(
        sector_map,
        on="company_id",
        how="left",
    )

    # -------------------------------------------------------------
    # Company-level data
    # -------------------------------------------------------------

    for _, company in company_data.iterrows():

        ticker = company["company_id"]

        sector = company.get(
            "broad_sector"
        )

        if pd.isna(sector):
            continue

        # ---------------------------------------------------------
        # Financial ratios
        # ---------------------------------------------------------

        ratios = get_ratios(ticker)

        if ratios.empty:
            continue

        selected_ratios = get_year_rows(
            ratios,
            selected_year,
        )

        if selected_ratios.empty:
            continue

        # If duplicate rows exist for the same
        # company/year, use the median.

        ratio_numeric_columns = [
            "return_on_equity_pct",
            "debt_to_equity",
            "free_cash_flow_cr",
            "cash_from_operations_cr",
        ]

        available_ratio_columns = [
            column
            for column in ratio_numeric_columns
            if column in selected_ratios.columns
        ]

        for column in available_ratio_columns:

            selected_ratios[column] = pd.to_numeric(
                selected_ratios[column],
                errors="coerce",
            )

        ratio_values = {}

        for column in available_ratio_columns:

            ratio_values[column] = (
                selected_ratios[column]
                .median()
            )

        # ---------------------------------------------------------
        # ROE
        # ---------------------------------------------------------

        roe = ratio_values.get(
            "return_on_equity_pct"
        )

        # ---------------------------------------------------------
        # ROCE
        # ---------------------------------------------------------

        roce = parse_percentage(
            company.get(
                "roce_percentage"
            )
        )

        # ---------------------------------------------------------
        # Debt-to-equity
        # ---------------------------------------------------------

        debt_to_equity = ratio_values.get(
            "debt_to_equity"
        )

        # ---------------------------------------------------------
        # Revenue CAGR
        # ---------------------------------------------------------

        revenue_cagr = get_revenue_cagr(
            ticker
        )

        # ---------------------------------------------------------
        # Valuation
        # ---------------------------------------------------------

        valuation = get_valuation(
            ticker
        )

        pe_ratio = None

        if not valuation.empty:

            selected_valuation = get_year_rows(
                valuation,
                selected_year,
            )

            if not selected_valuation.empty:

                selected_valuation[
                    "pe_ratio"
                ] = pd.to_numeric(
                    selected_valuation[
                        "pe_ratio"
                    ],
                    errors="coerce",
                )

                pe_ratio = (
                    selected_valuation[
                        "pe_ratio"
                    ].median()
                )

        # ---------------------------------------------------------
        # Add company row
        # ---------------------------------------------------------

        rows.append(
            {
                "company_id": ticker,
                "company": company[
                    "company_name"
                ],
                "sector": sector,
                "sub_sector": company.get(
                    "sub_sector"
                ),
                "roe": roe,
                "roce": roce,
                "revenue_cagr": revenue_cagr,
                "pe_ratio": pe_ratio,
                "debt_to_equity": debt_to_equity,
            }
        )

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title(
    "Nifty 100 Sector Analysis"
)

st.markdown(
    "### Sector-wise Financial Intelligence"
)

st.caption(
    "Compare profitability, growth, leverage and "
    "valuation across NIFTY 100 sectors."
)


# ---------------------------------------------------------------------
# Load database
# ---------------------------------------------------------------------

companies = get_companies()
sectors = get_sectors()

if companies.empty:

    st.error(
        "No company data is available."
    )

    st.stop()


if sectors.empty:

    st.error(
        "No sector data is available."
    )

    st.stop()


# ---------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------

col1, col2 = st.columns(2)


with col1:

    available_years = list(
        range(2019, 2025)
    )

    selected_year = st.selectbox(
        "Financial year",
        available_years,
        index=len(
            available_years
        ) - 1,
    )


with col2:

    available_sectors = sorted(
        sectors[
            "broad_sector"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_sector = st.selectbox(
        "Select sector",
        [
            "All Sectors"
        ] + available_sectors,
    )


# ---------------------------------------------------------------------
# Build financial dataset
# ---------------------------------------------------------------------

with st.spinner(
    "Loading sector financial metrics..."
):

    sector_data = get_sector_metrics(
        companies,
        sectors,
        selected_year,
    )


if sector_data.empty:

    st.warning(
        "Sector financial data is not available "
        f"for {selected_year}."
    )

    st.info(
        "The database stores financial years in formats "
        "such as 'Mar 2024'. The dashboard automatically "
        "matches the selected year against those values."
    )

    st.stop()


# ---------------------------------------------------------------------
# Sector summary
# ---------------------------------------------------------------------

sector_summary = (
    sector_data
    .groupby(
        "sector",
        as_index=False,
    )
    .agg(
        company_count=(
            "company_id",
            "nunique",
        ),
        average_roe=(
            "roe",
            "mean",
        ),
        average_roce=(
            "roce",
            "mean",
        ),
        average_revenue_cagr=(
            "revenue_cagr",
            "mean",
        ),
        median_pe=(
            "pe_ratio",
            "median",
        ),
        median_de=(
            "debt_to_equity",
            "median",
        ),
    )
)


# ---------------------------------------------------------------------
# Selected sector data
# ---------------------------------------------------------------------

if selected_sector == "All Sectors":

    selected_data = sector_data.copy()

else:

    selected_data = sector_data[
        sector_data["sector"]
        == selected_sector
    ].copy()


# ---------------------------------------------------------------------
# Sector overview
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    f"Sector Overview — {selected_year}"
)


displayed_companies = (
    selected_data[
        "company_id"
    ].nunique()
)


average_roe = selected_data[
    "roe"
].mean()


average_roce = selected_data[
    "roce"
].mean()


average_cagr = selected_data[
    "revenue_cagr"
].mean()


median_pe = selected_data[
    "pe_ratio"
].median()


median_de = selected_data[
    "debt_to_equity"
].median()


col1, col2, col3 = st.columns(3)
col4, col5, col6 = st.columns(3)


with col1:

    st.metric(
        "Companies",
        displayed_companies,
    )


with col2:

    st.metric(
        "Average ROE",
        "N/A"
        if pd.isna(average_roe)
        else f"{average_roe:.2f}%",
    )


with col3:

    st.metric(
        "Average ROCE",
        "N/A"
        if pd.isna(average_roce)
        else f"{average_roce:.2f}%",
    )


with col4:

    st.metric(
        "Average Revenue CAGR",
        "N/A"
        if pd.isna(average_cagr)
        else f"{average_cagr:.2f}%",
    )


with col5:

    st.metric(
        "Median P/E",
        "N/A"
        if pd.isna(median_pe)
        else f"{median_pe:.2f}",
    )


with col6:

    st.metric(
        "Median D/E",
        "N/A"
        if pd.isna(median_de)
        else f"{median_de:.2f}",
    )


# ---------------------------------------------------------------------
# Company distribution
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "NIFTY 100 Company Distribution by Sector"
)


distribution_df = (
    sector_summary
    .sort_values(
        "company_count",
        ascending=False,
    )
)


fig = px.bar(
    distribution_df,
    x="sector",
    y="company_count",
    text="company_count",
    labels={
        "sector": "Sector",
        "company_count": "Companies",
    },
)


fig.update_traces(
    textposition="outside"
)


fig.update_layout(
    height=500,
)


st.plotly_chart(
    fig,
    width="stretch",
)


# ---------------------------------------------------------------------
# Profitability comparison
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Sector Profitability Comparison"
)


profitability_df = sector_summary[
    [
        "sector",
        "average_roe",
        "average_roce",
    ]
].copy()


profitability_long = profitability_df.melt(
    id_vars="sector",
    value_vars=[
        "average_roe",
        "average_roce",
    ],
    var_name="metric",
    value_name="value",
)


profitability_long[
    "metric"
] = profitability_long[
    "metric"
].replace(
    {
        "average_roe": "ROE",
        "average_roce": "ROCE",
    }
)


fig = px.bar(
    profitability_long,
    x="sector",
    y="value",
    color="metric",
    barmode="group",
    labels={
        "sector": "Sector",
        "value": "Percentage (%)",
        "metric": "Metric",
    },
)


fig.update_layout(
    height=550,
)


st.plotly_chart(
    fig,
    width="stretch",
)


# ---------------------------------------------------------------------
# Revenue growth
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Sector Revenue Growth Comparison"
)


growth_df = (
    sector_summary[
        [
            "sector",
            "average_revenue_cagr",
        ]
    ]
    .dropna(
        subset=[
            "average_revenue_cagr"
        ]
    )
    .sort_values(
        "average_revenue_cagr",
        ascending=False,
    )
)


if growth_df.empty:

    st.info(
        "Revenue CAGR data is not available."
    )

else:

    fig = px.bar(
        growth_df,
        x="sector",
        y="average_revenue_cagr",
        text="average_revenue_cagr",
        labels={
            "sector": "Sector",
            "average_revenue_cagr": (
                "Average Revenue CAGR (%)"
            ),
        },
    )

    fig.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    fig.update_layout(
        height=500,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Valuation comparison
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Sector Valuation Comparison"
)


valuation_df = sector_summary[
    [
        "sector",
        "median_pe",
        "median_de",
    ]
].copy()


valuation_long = valuation_df.melt(
    id_vars="sector",
    value_vars=[
        "median_pe",
        "median_de",
    ],
    var_name="metric",
    value_name="value",
)


valuation_long[
    "metric"
] = valuation_long[
    "metric"
].replace(
    {
        "median_pe": "P/E",
        "median_de": "Debt-to-Equity",
    }
)


fig = px.bar(
    valuation_long,
    x="sector",
    y="value",
    color="metric",
    barmode="group",
    labels={
        "sector": "Sector",
        "value": "Value",
        "metric": "Metric",
    },
)


fig.update_layout(
    height=550,
)


st.plotly_chart(
    fig,
    width="stretch",
)


# ---------------------------------------------------------------------
# Sector comparison table
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Sector Comparison Table"
)


display_sector_summary = (
    sector_summary
    .copy()
    .sort_values(
        "average_revenue_cagr",
        ascending=False,
        na_position="last",
    )
)


display_sector_summary = (
    display_sector_summary.rename(
        columns={
            "sector": "Sector",
            "company_count": "Companies",
            "average_roe": "Average ROE (%)",
            "average_roce": "Average ROCE (%)",
            "average_revenue_cagr": (
                "Average Revenue CAGR (%)"
            ),
            "median_pe": "Median P/E",
            "median_de": "Median D/E",
        }
    )
)


numeric_columns = [
    "Average ROE (%)",
    "Average ROCE (%)",
    "Average Revenue CAGR (%)",
    "Median P/E",
    "Median D/E",
]


for column in numeric_columns:

    display_sector_summary[
        column
    ] = display_sector_summary[
        column
    ].round(2)


st.dataframe(
    display_sector_summary,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# Selected sector companies
# ---------------------------------------------------------------------

if selected_sector != "All Sectors":

    st.divider()

    st.subheader(
        f"{selected_sector} — Company Analysis"
    )


    company_table = selected_data[
        [
            "company_id",
            "company",
            "roe",
            "roce",
            "revenue_cagr",
            "pe_ratio",
            "debt_to_equity",
        ]
    ].copy()


    company_table = (
        company_table.rename(
            columns={
                "company_id": "Ticker",
                "company": "Company",
                "roe": "ROE (%)",
                "roce": "ROCE (%)",
                "revenue_cagr": (
                    "Revenue CAGR (%)"
                ),
                "pe_ratio": "P/E",
                "debt_to_equity": "D/E",
            }
        )
    )


    company_table = company_table.sort_values(
        "ROE (%)",
        ascending=False,
        na_position="last",
    )


    for column in [
        "ROE (%)",
        "ROCE (%)",
        "Revenue CAGR (%)",
        "P/E",
        "D/E",
    ]:

        company_table[
            column
        ] = company_table[
            column
        ].round(2)


    st.dataframe(
        company_table,
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Sector performance highlights
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Sector Performance Highlights"
)


valid_growth = sector_summary[
    "average_revenue_cagr"
].dropna()


if valid_growth.empty:

    st.info(
        "Revenue growth data is insufficient "
        "to rank sectors."
    )

else:

    best_index = (
        sector_summary[
            "average_revenue_cagr"
        ].idxmax()
    )

    weakest_index = (
        sector_summary[
            "average_revenue_cagr"
        ].idxmin()
    )


    best_sector = sector_summary.loc[
        best_index
    ]


    weakest_sector = sector_summary.loc[
        weakest_index
    ]


    col1, col2 = st.columns(2)


    with col1:

        st.success(
            f"**Highest Revenue Growth:** "
            f"{best_sector['sector']} — "
            f"{best_sector['average_revenue_cagr']:.2f}%"
        )


    with col2:

        st.warning(
            f"**Lowest Revenue Growth:** "
            f"{weakest_sector['sector']} — "
            f"{weakest_sector['average_revenue_cagr']:.2f}%"
        )


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

st.divider()

with st.expander(
    "Sector Analysis Methodology"
):

    st.markdown(
        """
        **Sector grouping**

        Companies are grouped using the `broad_sector`
        classification stored in the NIFTY 100 database.

        **Financial year**

        The selected year is matched against financial-year
        values stored in the database. This supports values
        such as `Mar 2024` as well as numeric year values.

        **Profitability**

        - Average ROE measures shareholder profitability.
        - Average ROCE measures efficiency of capital employed.

        **Growth**

        - Revenue CAGR uses the compounded sales growth
          available in the company analysis data.

        **Valuation**

        - Median P/E represents the middle valuation multiple
          within each sector.
        - Median D/E represents the middle leverage level.

        **Missing values**

        Missing financial values are excluded from the relevant
        aggregation instead of being treated as zero.

        **Sector comparison**

        Sector-level metrics are calculated from the available
        company-level financial data for the selected financial
        year.
        """
    )


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

st.caption(
    "NIFTY 100 Analytics Platform • Day 26 — Sector Analysis"
)