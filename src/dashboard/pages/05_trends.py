"""
NIFTY 100 Analytics - Trend Analysis
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_pl,
    get_ratios,
    get_bs,
    get_cf,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Trends",
    page_icon="📈",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def extract_year(value):
    """
    Extract a four-digit financial year from values such as:

        Mar 2024
        Dec 2020
        2024
        TTM

    TTM returns None.
    """

    if pd.isna(value):
        return None

    match = re.search(r"(19|20)\d{2}", str(value))

    if match:
        return int(match.group())

    return None


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
        result["financial_year"].astype(int)
    )

    return result


def numeric_column(df, column):
    """
    Safely convert a column to numeric.
    """

    if column not in df.columns:
        return pd.Series(
            index=df.index,
            dtype="float64",
        )

    return pd.to_numeric(
        df[column],
        errors="coerce",
    )


def calculate_cagr(start_value, end_value, years):
    """
    Calculate CAGR.

    Returns None when the calculation is not meaningful.
    """

    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or years <= 0
        or start_value <= 0
        or end_value <= 0
    ):
        return None

    return (
        (end_value / start_value) ** (1 / years)
        - 1
    ) * 100


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title("Nifty 100 Trend Analysis")

st.markdown(
    """
    Analyze long-term financial trends for NIFTY 100 companies
    across revenue, profitability, margins, returns, leverage,
    and cash flow.
    """
)


# ---------------------------------------------------------------------
# Load companies
# ---------------------------------------------------------------------

companies = get_companies()

if companies.empty:
    st.error("No company data is available.")
    st.stop()


# ---------------------------------------------------------------------
# Company selector
# ---------------------------------------------------------------------

company_options = (
    companies[
        [
            "company_id",
            "company_name",
        ]
    ]
    .drop_duplicates()
    .sort_values("company_name")
)

company_labels = {
    row["company_id"]:
        f'{row["company_id"]} — {row["company_name"]}'
    for _, row in company_options.iterrows()
}

selected_ticker = st.selectbox(
    "Select company",
    company_options["company_id"].tolist(),
    format_func=lambda ticker: company_labels.get(
        ticker,
        ticker,
    ),
)


company_row = companies[
    companies["company_id"] == selected_ticker
]

if company_row.empty:
    st.error("Company information is unavailable.")
    st.stop()

company_name = company_row.iloc[0]["company_name"]


# ---------------------------------------------------------------------
# Load financial data
# ---------------------------------------------------------------------

pl = prepare_year_column(
    get_pl(selected_ticker)
)

ratios = prepare_year_column(
    get_ratios(selected_ticker)
)

balance_sheet = prepare_year_column(
    get_bs(selected_ticker)
)

cash_flow = prepare_year_column(
    get_cf(selected_ticker)
)


# ---------------------------------------------------------------------
# Company heading
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    f"{company_name} ({selected_ticker})"
)

st.caption(
    "Historical trend analysis based on financial data "
    "available in the NIFTY 100 database."
)


# ---------------------------------------------------------------------
# Available years
# ---------------------------------------------------------------------

year_sources = []

for dataframe in [
    pl,
    ratios,
    balance_sheet,
    cash_flow,
]:

    if (
        not dataframe.empty
        and "financial_year" in dataframe.columns
    ):

        year_sources.extend(
            dataframe["financial_year"]
            .dropna()
            .astype(int)
            .tolist()
        )


if not year_sources:
    st.warning(
        "No historical financial-year data is available "
        "for this company."
    )
    st.stop()


available_years = sorted(
    set(year_sources)
)

start_year_default = (
    available_years[0]
)

end_year_default = (
    available_years[-1]
)


# ---------------------------------------------------------------------
# Analysis period
# ---------------------------------------------------------------------

st.subheader("Analysis Period")

period_col1, period_col2 = st.columns(2)

with period_col1:

    start_year = st.selectbox(
        "Start year",
        available_years,
        index=available_years.index(
            start_year_default
        ),
    )

with period_col2:

    valid_end_years = [
        year
        for year in available_years
        if year >= start_year
    ]

    end_year = st.selectbox(
        "End year",
        valid_end_years,
        index=len(valid_end_years) - 1,
    )


# ---------------------------------------------------------------------
# Filter historical data
# ---------------------------------------------------------------------

pl_period = pl[
    (
        pl["financial_year"] >= start_year
    )
    & (
        pl["financial_year"] <= end_year
    )
].copy()

ratios_period = ratios[
    (
        ratios["financial_year"] >= start_year
    )
    & (
        ratios["financial_year"] <= end_year
    )
].copy()

bs_period = balance_sheet[
    (
        balance_sheet["financial_year"] >= start_year
    )
    & (
        balance_sheet["financial_year"] <= end_year
    )
].copy()

cf_period = cash_flow[
    (
        cash_flow["financial_year"] >= start_year
    )
    & (
        cash_flow["financial_year"] <= end_year
    )
].copy()


# ---------------------------------------------------------------------
# Prepare P&L trend data
# ---------------------------------------------------------------------

if not pl_period.empty:

    pl_trend = (
        pl_period
        .groupby(
            "financial_year",
            as_index=False,
        )
        .agg(
            sales=("sales", "median"),
            operating_profit=(
                "operating_profit",
                "median",
            ),
            net_profit=(
                "net_profit",
                "median",
            ),
            eps=("eps", "median"),
        )
        .sort_values("financial_year")
    )

else:

    pl_trend = pd.DataFrame()


# ---------------------------------------------------------------------
# Prepare ratio trend data
# ---------------------------------------------------------------------

if not ratios_period.empty:

    ratio_columns = [
        "return_on_equity_pct",
        "debt_to_equity",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "interest_coverage",
        "free_cash_flow_cr",
        "cash_from_operations_cr",
    ]

    available_ratio_columns = [
        column
        for column in ratio_columns
        if column in ratios_period.columns
    ]

    for column in available_ratio_columns:

        ratios_period[column] = numeric_column(
            ratios_period,
            column,
        )

    ratio_trend = (
        ratios_period
        .groupby(
            "financial_year",
            as_index=False,
        )[
            available_ratio_columns
        ]
        .median()
        .sort_values("financial_year")
    )

else:

    ratio_trend = pd.DataFrame()


# ---------------------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------------------

start_sales = None
end_sales = None
sales_cagr = None

start_profit = None
end_profit = None
profit_cagr = None

latest_roe = None
latest_de = None
latest_npm = None


if not pl_trend.empty:

    first_row = pl_trend.iloc[0]
    last_row = pl_trend.iloc[-1]

    start_sales = first_row["sales"]
    end_sales = last_row["sales"]

    start_profit = first_row["net_profit"]
    end_profit = last_row["net_profit"]

    period_years = (
        int(last_row["financial_year"])
        - int(first_row["financial_year"])
    )

    sales_cagr = calculate_cagr(
        start_sales,
        end_sales,
        period_years,
    )

    profit_cagr = calculate_cagr(
        start_profit,
        end_profit,
        period_years,
    )


if not ratio_trend.empty:

    latest_ratio = ratio_trend.iloc[-1]

    if "return_on_equity_pct" in ratio_trend.columns:
        latest_roe = latest_ratio[
            "return_on_equity_pct"
        ]

    if "debt_to_equity" in ratio_trend.columns:
        latest_de = latest_ratio[
            "debt_to_equity"
        ]

    if "net_profit_margin_pct" in ratio_trend.columns:
        latest_npm = latest_ratio[
            "net_profit_margin_pct"
        ]


# ---------------------------------------------------------------------
# KPI display
# ---------------------------------------------------------------------

st.subheader("Trend Summary")

k1, k2, k3, k4, k5 = st.columns(5)

with k1:

    st.metric(
        "Revenue CAGR",
        "N/A"
        if sales_cagr is None
        else f"{sales_cagr:.2f}%",
    )

with k2:

    st.metric(
        "Profit CAGR",
        "N/A"
        if profit_cagr is None
        else f"{profit_cagr:.2f}%",
    )

with k3:

    st.metric(
        "Latest ROE",
        "N/A"
        if pd.isna(latest_roe)
        else f"{latest_roe:.2f}%",
    )

with k4:

    st.metric(
        "Latest Net Margin",
        "N/A"
        if pd.isna(latest_npm)
        else f"{latest_npm:.2f}%",
    )

with k5:

    st.metric(
        "Latest D/E",
        "N/A"
        if pd.isna(latest_de)
        else f"{latest_de:.2f}",
    )


# ---------------------------------------------------------------------
# Revenue and profit trend
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Revenue & Net Profit Trend"
)

if pl_trend.empty:

    st.info(
        "Profit & Loss trend data is not available."
    )

else:

    chart_df = pl_trend[
        [
            "financial_year",
            "sales",
            "net_profit",
        ]
    ].copy()

    chart_df = chart_df.melt(
        id_vars="financial_year",
        value_vars=[
            "sales",
            "net_profit",
        ],
        var_name="metric",
        value_name="value",
    )

    chart_df["metric"] = chart_df[
        "metric"
    ].map(
        {
            "sales": "Revenue",
            "net_profit": "Net Profit",
        }
    )

    fig = px.line(
        chart_df,
        x="financial_year",
        y="value",
        color="metric",
        markers=True,
        title=(
            f"{company_name} — Revenue & Net Profit"
        ),
    )

    fig.update_layout(
        xaxis_title="Financial Year",
        yaxis_title="Amount",
        height=500,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Operating profit trend
# ---------------------------------------------------------------------

st.subheader(
    "Operating Profit & EPS Trend"
)

if pl_trend.empty:

    st.info(
        "Operating profit data is not available."
    )

else:

    operating_df = pl_trend[
        [
            "financial_year",
            "operating_profit",
            "eps",
        ]
    ].copy()

    operating_df = operating_df.melt(
        id_vars="financial_year",
        value_vars=[
            "operating_profit",
            "eps",
        ],
        var_name="metric",
        value_name="value",
    )

    operating_df["metric"] = operating_df[
        "metric"
    ].map(
        {
            "operating_profit": "Operating Profit",
            "eps": "EPS",
        }
    )

    fig = px.line(
        operating_df,
        x="financial_year",
        y="value",
        color="metric",
        markers=True,
        title=(
            f"{company_name} — Operating Profit & EPS"
        ),
    )

    fig.update_layout(
        xaxis_title="Financial Year",
        yaxis_title="Value",
        height=500,
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Profitability ratios
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Profitability Trend"
)

if ratio_trend.empty:

    st.info(
        "Financial ratio trend data is not available."
    )

else:

    profitability_columns = [
        column
        for column in [
            "return_on_equity_pct",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
        ]
        if column in ratio_trend.columns
    ]

    if not profitability_columns:

        st.info(
            "Profitability metrics are not available."
        )

    else:

        profitability_df = ratio_trend[
            [
                "financial_year"
            ]
            + profitability_columns
        ].copy()

        profitability_df = profitability_df.melt(
            id_vars="financial_year",
            value_vars=profitability_columns,
            var_name="metric",
            value_name="value",
        )

        profitability_df["metric"] = (
            profitability_df["metric"].map(
                {
                    "return_on_equity_pct": "ROE",
                    "net_profit_margin_pct": (
                        "Net Profit Margin"
                    ),
                    "operating_profit_margin_pct": (
                        "Operating Profit Margin"
                    ),
                }
            )
        )

        fig = px.line(
            profitability_df,
            x="financial_year",
            y="value",
            color="metric",
            markers=True,
            title=(
                f"{company_name} — Profitability Ratios"
            ),
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="Percentage",
            height=500,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


# ---------------------------------------------------------------------
# Leverage trend
# ---------------------------------------------------------------------

st.subheader(
    "Leverage & Interest Coverage Trend"
)

if ratio_trend.empty:

    st.info(
        "Leverage data is not available."
    )

else:

    leverage_columns = [
        column
        for column in [
            "debt_to_equity",
            "interest_coverage",
        ]
        if column in ratio_trend.columns
    ]

    if not leverage_columns:

        st.info(
            "Leverage metrics are not available."
        )

    else:

        leverage_df = ratio_trend[
            [
                "financial_year"
            ]
            + leverage_columns
        ].copy()

        leverage_df = leverage_df.melt(
            id_vars="financial_year",
            value_vars=leverage_columns,
            var_name="metric",
            value_name="value",
        )

        leverage_df["metric"] = (
            leverage_df["metric"].map(
                {
                    "debt_to_equity": (
                        "Debt-to-Equity"
                    ),
                    "interest_coverage": (
                        "Interest Coverage"
                    ),
                }
            )
        )

        fig = px.line(
            leverage_df,
            x="financial_year",
            y="value",
            color="metric",
            markers=True,
            title=(
                f"{company_name} — Leverage & Coverage"
            ),
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="Ratio",
            height=500,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


# ---------------------------------------------------------------------
# Cash flow trend
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Cash Flow Trend"
)

if cf_period.empty:

    st.info(
        "Cash flow data is not available."
    )

else:

    cf_columns = [
        column
        for column in [
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "net_cash_flow",
        ]
        if column in cf_period.columns
    ]

    if cf_columns:

        for column in cf_columns:

            cf_period[column] = numeric_column(
                cf_period,
                column,
            )

        cf_trend = (
            cf_period
            .groupby(
                "financial_year",
                as_index=False,
            )[cf_columns]
            .median()
            .sort_values("financial_year")
        )

        cf_chart = cf_trend.melt(
            id_vars="financial_year",
            value_vars=cf_columns,
            var_name="metric",
            value_name="value",
        )

        cf_chart["metric"] = cf_chart[
            "metric"
        ].map(
            {
                "operating_activity": (
                    "Operating Cash Flow"
                ),
                "investing_activity": (
                    "Investing Cash Flow"
                ),
                "financing_activity": (
                    "Financing Cash Flow"
                ),
                "net_cash_flow": (
                    "Net Cash Flow"
                ),
            }
        )

        fig = px.bar(
            cf_chart,
            x="financial_year",
            y="value",
            color="metric",
            barmode="group",
            title=(
                f"{company_name} — Cash Flow Trend"
            ),
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="Cash Flow",
            height=500,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


# ---------------------------------------------------------------------
# Balance sheet trend
# ---------------------------------------------------------------------

st.subheader(
    "Balance Sheet Trend"
)

if bs_period.empty:

    st.info(
        "Balance Sheet data is not available."
    )

else:

    bs_columns = [
        column
        for column in [
            "reserves",
            "borrowings",
            "total_liabilities",
            "fixed_assets",
            "investments",
            "total_assets",
        ]
        if column in bs_period.columns
    ]

    if bs_columns:

        for column in bs_columns:

            bs_period[column] = numeric_column(
                bs_period,
                column,
            )

        bs_trend = (
            bs_period
            .groupby(
                "financial_year",
                as_index=False,
            )[bs_columns]
            .median()
            .sort_values("financial_year")
        )

        bs_chart = bs_trend.melt(
            id_vars="financial_year",
            value_vars=bs_columns,
            var_name="metric",
            value_name="value",
        )

        bs_chart["metric"] = bs_chart[
            "metric"
        ].map(
            {
                "reserves": "Reserves",
                "borrowings": "Borrowings",
                "total_liabilities": (
                    "Total Liabilities"
                ),
                "fixed_assets": "Fixed Assets",
                "investments": "Investments",
                "total_assets": "Total Assets",
            }
        )

        fig = px.line(
            bs_chart,
            x="financial_year",
            y="value",
            color="metric",
            markers=True,
            title=(
                f"{company_name} — Balance Sheet Trend"
            ),
        )

        fig.update_layout(
            xaxis_title="Financial Year",
            yaxis_title="Amount",
            height=500,
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )


# ---------------------------------------------------------------------
# Historical data table
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Historical Financial Data"
)

if not pl_trend.empty:

    display_df = pl_trend.copy()

    display_df = display_df.rename(
        columns={
            "financial_year": "Year",
            "sales": "Revenue",
            "operating_profit": (
                "Operating Profit"
            ),
            "net_profit": "Net Profit",
            "eps": "EPS",
        }
    )

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

with st.expander(
    "Trend Analysis Methodology"
):

    st.markdown(
        """
        **Data source**

        Historical financial information is read from the
        NIFTY 100 SQLite database.

        **Financial year handling**

        Financial-year labels such as `Mar 2024` and
        `Dec 2023` are converted into their four-digit
        year for chronological analysis. `TTM` records are
        excluded from historical-year charts.

        **Duplicate records**

        Where multiple records exist for the same company
        and financial year, the median value is used.

        **Revenue CAGR**

        Revenue CAGR is calculated between the first and
        last available year in the selected analysis period.

        **Profit CAGR**

        Net-profit CAGR is calculated using the same period.

        **Trend metrics**

        The dashboard analyzes:

        - Revenue
        - Operating Profit
        - Net Profit
        - EPS
        - ROE
        - Net Profit Margin
        - Operating Profit Margin
        - Debt-to-Equity
        - Interest Coverage
        - Operating Cash Flow
        - Investing Cash Flow
        - Financing Cash Flow
        - Net Cash Flow
        - Reserves
        - Borrowings
        - Total Assets
        - Total Liabilities
        """
    )