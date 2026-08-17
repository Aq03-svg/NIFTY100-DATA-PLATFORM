"""
NIFTY 100 Capital Allocation Analysis

Analyzes how companies generate, deploy, and finance capital.
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_cf,
    get_bs,
    get_pl,
    get_ratios,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Capital",
    page_icon="💰",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def extract_year(value):
    """
    Extract a four-digit financial year from values such as:

        Mar 2024
        Dec 2012
        2024
        TTM
    """

    if pd.isna(value):
        return None

    match = re.search(r"(20\d{2})", str(value))

    if match:
        return int(match.group(1))

    return None


def numeric(series):
    """
    Convert a pandas Series to numeric values.
    """

    return pd.to_numeric(
        series,
        errors="coerce",
    )


def prepare_year_column(df):
    """
    Add a numeric financial_year column.
    """

    if df.empty or "year" not in df.columns:
        return df

    result = df.copy()

    result["financial_year"] = result["year"].apply(
        extract_year
    )

    result = result[
        result["financial_year"].notna()
    ].copy()

    result["financial_year"] = (
        result["financial_year"]
        .astype(int)
    )

    return result


def latest_years(df):
    """
    Return available financial years.
    """

    if df.empty or "financial_year" not in df.columns:
        return []

    return sorted(
        df["financial_year"]
        .dropna()
        .unique()
        .tolist()
    )


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title("Nifty 100 Capital Allocation Analysis")

st.markdown(
    "### Capital generation, deployment and financing intelligence"
)


# ---------------------------------------------------------------------
# Load companies
# ---------------------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("No company data is available.")
    st.stop()


companies = companies.sort_values(
    "company_name"
).reset_index(drop=True)


# ---------------------------------------------------------------------
# Company selector
# ---------------------------------------------------------------------

company_options = {
    f"{row['company_name']} ({row['company_id']})":
    row["company_id"]
    for _, row in companies.iterrows()
}


selected_company_label = st.selectbox(
    "Select company",
    list(company_options.keys()),
)


selected_company = company_options[
    selected_company_label
]


company_row = companies[
    companies["company_id"] == selected_company
].iloc[0]


# ---------------------------------------------------------------------
# Company heading
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    company_row["company_name"]
)

st.caption(
    f"NSE Ticker: {selected_company}"
)


# ---------------------------------------------------------------------
# Load financial data
# ---------------------------------------------------------------------

cash_flow = prepare_year_column(
    get_cf(selected_company)
)

balance_sheet = prepare_year_column(
    get_bs(selected_company)
)

profit_loss = prepare_year_column(
    get_pl(selected_company)
)

ratios = prepare_year_column(
    get_ratios(selected_company)
)


# ---------------------------------------------------------------------
# Validate data
# ---------------------------------------------------------------------

if (
    cash_flow.empty
    and balance_sheet.empty
    and profit_loss.empty
):
    st.error(
        "Capital allocation data is not available "
        "for this company."
    )
    st.stop()


# ---------------------------------------------------------------------
# Available years
# ---------------------------------------------------------------------

all_years = set()

for df in [
    cash_flow,
    balance_sheet,
    profit_loss,
    ratios,
]:

    all_years.update(
        latest_years(df)
    )


available_years = sorted(
    all_years
)

if not available_years:
    st.error(
        "No financial years are available."
    )
    st.stop()


selected_year = st.selectbox(
    "Select financial year",
    available_years,
    index=len(available_years) - 1,
)


# ---------------------------------------------------------------------
# Selected year data
# ---------------------------------------------------------------------

cf_year = cash_flow[
    cash_flow["financial_year"]
    == selected_year
].copy()

bs_year = balance_sheet[
    balance_sheet["financial_year"]
    == selected_year
].copy()

pl_year = profit_loss[
    profit_loss["financial_year"]
    == selected_year
].copy()

ratios_year = ratios[
    ratios["financial_year"]
    == selected_year
].copy()


# ---------------------------------------------------------------------
# Helper to retrieve one value
# ---------------------------------------------------------------------

def get_value(df, column):
    """
    Return the median numeric value for a column.
    """

    if df.empty or column not in df.columns:
        return None

    values = numeric(
        df[column]
    ).dropna()

    if values.empty:
        return None

    return float(
        values.median()
    )


# ---------------------------------------------------------------------
# Capital allocation metrics
# ---------------------------------------------------------------------

operating_cash_flow = get_value(
    cf_year,
    "operating_activity",
)

investing_cash_flow = get_value(
    cf_year,
    "investing_activity",
)

financing_cash_flow = get_value(
    cf_year,
    "financing_activity",
)

net_cash_flow = get_value(
    cf_year,
    "net_cash_flow",
)

capex = get_value(
    ratios_year,
    "capex_cr",
)

free_cash_flow = get_value(
    ratios_year,
    "free_cash_flow_cr",
)

borrowings = get_value(
    bs_year,
    "borrowings",
)

reserves = get_value(
    bs_year,
    "reserves",
)

total_assets = get_value(
    bs_year,
    "total_assets",
)

dividend_payout = get_value(
    pl_year,
    "dividend_payout",
)

sales = get_value(
    pl_year,
    "sales",
)

net_profit = get_value(
    pl_year,
    "net_profit",
)


# ---------------------------------------------------------------------
# Capital Allocation Overview
# ---------------------------------------------------------------------

st.subheader(
    f"Capital Allocation Overview — {selected_year}"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Operating Cash Flow",
        "N/A"
        if operating_cash_flow is None
        else f"{operating_cash_flow:,.2f} Cr",
    )


with col2:

    st.metric(
        "Free Cash Flow",
        "N/A"
        if free_cash_flow is None
        else f"{free_cash_flow:,.2f} Cr",
    )


with col3:

    st.metric(
        "Capital Expenditure",
        "N/A"
        if capex is None
        else f"{capex:,.2f} Cr",
    )


with col4:

    st.metric(
        "Net Cash Flow",
        "N/A"
        if net_cash_flow is None
        else f"{net_cash_flow:,.2f} Cr",
    )


col5, col6, col7, col8 = st.columns(4)


with col5:

    st.metric(
        "Borrowings",
        "N/A"
        if borrowings is None
        else f"{borrowings:,.2f} Cr",
    )


with col6:

    st.metric(
        "Reserves",
        "N/A"
        if reserves is None
        else f"{reserves:,.2f} Cr",
    )


with col7:

    st.metric(
        "Dividend Payout",
        "N/A"
        if dividend_payout is None
        else f"{dividend_payout:,.2f}%",
    )


with col8:

    st.metric(
        "Net Profit",
        "N/A"
        if net_profit is None
        else f"{net_profit:,.2f} Cr",
    )


# ---------------------------------------------------------------------
# Cash Flow Trend
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Cash Flow Trend"
)


if cash_flow.empty:

    st.info(
        "Cash flow data is not available."
    )

else:

    cf_chart = cash_flow.copy()

    required_columns = [
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    for column in required_columns:

        if column in cf_chart.columns:

            cf_chart[column] = numeric(
                cf_chart[column]
            )

    cf_chart = cf_chart[
        [
            "financial_year",
            *[
                column
                for column in required_columns
                if column in cf_chart.columns
            ],
        ]
    ]

    cf_chart = (
        cf_chart
        .groupby(
            "financial_year",
            as_index=False,
        )
        .median()
    )

    cf_long = cf_chart.melt(
        id_vars=[
            "financial_year"
        ],
        var_name="cash_flow_type",
        value_name="amount",
    )

    labels = {
        "operating_activity":
            "Operating Cash Flow",
        "investing_activity":
            "Investing Cash Flow",
        "financing_activity":
            "Financing Cash Flow",
        "net_cash_flow":
            "Net Cash Flow",
    }

    cf_long["cash_flow_type"] = (
        cf_long["cash_flow_type"]
        .map(labels)
        .fillna(
            cf_long["cash_flow_type"]
        )
    )

    fig = px.line(
        cf_long,
        x="financial_year",
        y="amount",
        color="cash_flow_type",
        markers=True,
        title=(
            f"{company_row['company_name']} — "
            "Cash Flow Trend"
        ),
    )

    fig.update_layout(
        height=500,
        xaxis_title="Financial Year",
        yaxis_title="Amount (₹ Cr)",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Capital Expenditure and Free Cash Flow
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Capital Expenditure & Free Cash Flow"
)


if ratios.empty:

    st.info(
        "Capital expenditure and free cash flow "
        "data is not available."
    )

else:

    capex_chart = ratios.copy()

    for column in [
        "capex_cr",
        "free_cash_flow_cr",
    ]:

        if column in capex_chart.columns:

            capex_chart[column] = numeric(
                capex_chart[column]
            )

    available_columns = [
        column
        for column in [
            "capex_cr",
            "free_cash_flow_cr",
        ]
        if column in capex_chart.columns
    ]

    capex_chart = capex_chart[
        [
            "financial_year",
            *available_columns,
        ]
    ]

    capex_chart = (
        capex_chart
        .groupby(
            "financial_year",
            as_index=False,
        )
        .median()
    )

    capex_long = capex_chart.melt(
        id_vars=[
            "financial_year"
        ],
        var_name="metric",
        value_name="amount",
    )

    metric_labels = {
        "capex_cr": "Capital Expenditure",
        "free_cash_flow_cr": "Free Cash Flow",
    }

    capex_long["metric"] = (
        capex_long["metric"]
        .map(metric_labels)
        .fillna(
            capex_long["metric"]
        )
    )

    fig = px.bar(
        capex_long,
        x="financial_year",
        y="amount",
        color="metric",
        barmode="group",
        title=(
            f"{company_row['company_name']} — "
            "CapEx vs Free Cash Flow"
        ),
    )

    fig.update_layout(
        height=500,
        xaxis_title="Financial Year",
        yaxis_title="Amount (₹ Cr)",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Capital Structure
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Capital Structure Trend"
)


if balance_sheet.empty:

    st.info(
        "Balance sheet data is not available."
    )

else:

    structure_chart = balance_sheet.copy()

    for column in [
        "borrowings",
        "reserves",
        "total_assets",
    ]:

        if column in structure_chart.columns:

            structure_chart[column] = numeric(
                structure_chart[column]
            )

    structure_columns = [
        column
        for column in [
            "borrowings",
            "reserves",
            "total_assets",
        ]
        if column in structure_chart.columns
    ]

    structure_chart = structure_chart[
        [
            "financial_year",
            *structure_columns,
        ]
    ]

    structure_chart = (
        structure_chart
        .groupby(
            "financial_year",
            as_index=False,
        )
        .median()
    )

    structure_long = structure_chart.melt(
        id_vars=[
            "financial_year"
        ],
        var_name="metric",
        value_name="amount",
    )

    structure_labels = {
        "borrowings": "Borrowings",
        "reserves": "Reserves",
        "total_assets": "Total Assets",
    }

    structure_long["metric"] = (
        structure_long["metric"]
        .map(structure_labels)
        .fillna(
            structure_long["metric"]
        )
    )

    fig = px.line(
        structure_long,
        x="financial_year",
        y="amount",
        color="metric",
        markers=True,
        title=(
            f"{company_row['company_name']} — "
            "Capital Structure"
        ),
    )

    fig.update_layout(
        height=500,
        xaxis_title="Financial Year",
        yaxis_title="Amount (₹ Cr)",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Dividend Payout Trend
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Dividend Payout Trend"
)


if profit_loss.empty:

    st.info(
        "Profit & Loss data is not available."
    )

else:

    dividend_chart = profit_loss.copy()

    if "dividend_payout" in dividend_chart.columns:

        dividend_chart[
            "dividend_payout"
        ] = numeric(
            dividend_chart[
                "dividend_payout"
            ]
        )

        dividend_chart = (
            dividend_chart[
                [
                    "financial_year",
                    "dividend_payout",
                ]
            ]
            .groupby(
                "financial_year",
                as_index=False,
            )
            .median()
        )

        fig = px.line(
            dividend_chart,
            x="financial_year",
            y="dividend_payout",
            markers=True,
            title=(
                f"{company_row['company_name']} — "
                "Dividend Payout Trend"
            ),
        )

        fig.update_layout(
            height=450,
            xaxis_title="Financial Year",
            yaxis_title="Dividend Payout (%)",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:

        st.info(
            "Dividend payout data is not available."
        )


# ---------------------------------------------------------------------
# Capital Efficiency Summary
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Capital Allocation Summary"
)


summary_rows = []


if operating_cash_flow is not None:
    summary_rows.append(
        {
            "Metric": "Operating Cash Flow",
            "Value": f"{operating_cash_flow:,.2f} Cr",
        }
    )


if free_cash_flow is not None:
    summary_rows.append(
        {
            "Metric": "Free Cash Flow",
            "Value": f"{free_cash_flow:,.2f} Cr",
        }
    )


if capex is not None:
    summary_rows.append(
        {
            "Metric": "Capital Expenditure",
            "Value": f"{capex:,.2f} Cr",
        }
    )


if borrowings is not None:
    summary_rows.append(
        {
            "Metric": "Borrowings",
            "Value": f"{borrowings:,.2f} Cr",
        }
    )


if reserves is not None:
    summary_rows.append(
        {
            "Metric": "Reserves",
            "Value": f"{reserves:,.2f} Cr",
        }
    )


if dividend_payout is not None:
    summary_rows.append(
        {
            "Metric": "Dividend Payout",
            "Value": f"{dividend_payout:,.2f}%",
        }
    )


if summary_rows:

    summary_df = pd.DataFrame(
        summary_rows
    )

    st.dataframe(
        summary_df,
        width="stretch",
        hide_index=True,
    )

else:

    st.info(
        "Capital allocation summary data "
        "is not available."
    )


# ---------------------------------------------------------------------
# Historical Financial Data
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Historical Capital Allocation Data"
)


if not cash_flow.empty:

    historical = cash_flow.copy()

    columns = [
        "financial_year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]

    columns = [
        column
        for column in columns
        if column in historical.columns
    ]

    historical = historical[
        columns
    ].copy()

    rename_map = {
        "financial_year": "Year",
        "operating_activity":
            "Operating Cash Flow (Cr)",
        "investing_activity":
            "Investing Cash Flow (Cr)",
        "financing_activity":
            "Financing Cash Flow (Cr)",
        "net_cash_flow":
            "Net Cash Flow (Cr)",
    }

    historical = historical.rename(
        columns=rename_map
    )

    numeric_columns = [
        column
        for column in historical.columns
        if column != "Year"
    ]

    for column in numeric_columns:

        historical[column] = numeric(
            historical[column]
        )

    historical = (
        historical
        .sort_values("Year")
        .drop_duplicates(
            subset=["Year"]
        )
    )

    st.dataframe(
        historical,
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

st.divider()

with st.expander(
    "Capital Allocation Methodology"
):

    st.markdown(
        """
### Capital Allocation Methodology

This page evaluates how a company generates,
deploys and finances capital using historical
financial statement data.

**Operating Cash Flow**

Measures cash generated from core operating
activities.

**Investing Cash Flow**

Represents cash used or generated through
investments and capital deployment.

**Financing Cash Flow**

Captures financing-related cash movements,
including debt and equity-related activities.

**Free Cash Flow**

Represents the cash remaining after capital
expenditure.

**Capital Expenditure**

Measures investment in long-term assets and
business capacity.

**Capital Structure**

Uses borrowings, reserves and total assets
to provide a view of the company's financing
structure.

**Dividend Payout**

Shows the proportion of earnings distributed
to shareholders.

All figures are derived from the NIFTY 100
SQLite database and are presented for the
selected financial year.
"""
    )