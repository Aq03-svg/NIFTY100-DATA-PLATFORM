"""
NIFTY 100 Investment Intelligence Report

Executive-style company research report built from
the NIFTY 100 SQLite database.
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_bs,
    get_cf,
    get_sectors,
    get_analysis,
    get_valuation,
    get_pros_and_cons,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Reports",
    page_icon="📋",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def extract_year(value):
    """
    Extract a four-digit year from financial-year values.

    Examples:
        Mar 2024 -> 2024
        Dec 2012 -> 2012
        2024 -> 2024
        TTM -> None
    """

    if pd.isna(value):
        return None

    match = re.search(
        r"(20\d{2})",
        str(value),
    )

    if match:
        return int(match.group(1))

    return None


def numeric_value(value):
    """
    Convert a value into a numeric value.
    """

    return pd.to_numeric(
        value,
        errors="coerce",
    )


def parse_percentage(value):
    """
    Extract a percentage-like numeric value.
    """

    if pd.isna(value):
        return None

    if isinstance(
        value,
        (int, float),
    ):
        return float(value)

    match = re.search(
        r"-?\d+(?:\.\d+)?",
        str(value),
    )

    if match:
        return float(
            match.group()
        )

    return None


def format_number(
    value,
    suffix="",
    decimals=2,
):
    """
    Format numeric values for display.
    """

    if value is None or pd.isna(value):
        return "N/A"

    return (
        f"{float(value):,.{decimals}f}"
        f"{suffix}"
    )


def prepare_financial_year(df):
    """
    Add a numeric financial_year column.
    """

    if df.empty or "year" not in df.columns:
        return df

    result = df.copy()

    result["financial_year"] = (
        result["year"]
        .apply(extract_year)
    )

    result = result[
        result["financial_year"].notna()
    ].copy()

    if result.empty:
        return result

    result["financial_year"] = (
        result["financial_year"]
        .astype(int)
    )

    return result


def get_latest_row(df, year):
    """
    Return the latest matching row for a selected year.
    """

    if df.empty:
        return None

    if "financial_year" in df.columns:

        selected = df[
            df["financial_year"] == year
        ]

    elif "year" in df.columns:

        selected = df[
            df["year"].astype(str).str.contains(
                str(year),
                na=False,
            )
        ]

    else:
        return None

    if selected.empty:
        return None

    return selected.iloc[-1]


def get_median_value(
    df,
    column,
    year,
):
    """
    Return the median value for a metric
    in the selected year.
    """

    if df.empty or column not in df.columns:
        return None

    if "financial_year" in df.columns:

        selected = df[
            df["financial_year"] == year
        ]

    else:

        selected = df[
            df["year"].astype(str).str.contains(
                str(year),
                na=False,
            )
        ]

    if selected.empty:
        return None

    values = pd.to_numeric(
        selected[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return None

    return float(
        values.median()
    )


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title(
    "Nifty 100 Investment Intelligence"
)

st.markdown(
    "### Executive financial research report"
)

st.caption(
    "A consolidated analytical view of company "
    "fundamentals, valuation, growth, leverage "
    "and cash-flow characteristics."
)


# ---------------------------------------------------------------------
# Load companies
# ---------------------------------------------------------------------

companies = get_companies()

if companies.empty:

    st.error(
        "No company data is available."
    )

    st.stop()


companies = (
    companies
    .sort_values("company_name")
    .reset_index(drop=True)
)


# ---------------------------------------------------------------------
# Company selector
# ---------------------------------------------------------------------

company_options = {
    f"{row['company_name']} ({row['company_id']})":
    row["company_id"]
    for _, row in companies.iterrows()
}


selected_label = st.selectbox(
    "Select company",
    list(company_options.keys()),
)


ticker = company_options[
    selected_label
]


company_row = companies[
    companies["company_id"] == ticker
].iloc[0]


# ---------------------------------------------------------------------
# Load company data
# ---------------------------------------------------------------------

ratios = prepare_financial_year(
    get_ratios(ticker)
)

profit_loss = prepare_financial_year(
    get_pl(ticker)
)

balance_sheet = prepare_financial_year(
    get_bs(ticker)
)

cash_flow = prepare_financial_year(
    get_cf(ticker)
)

analysis = get_analysis(ticker)

valuation = prepare_financial_year(
    get_valuation(ticker)
)

sectors = get_sectors()

pros_cons = get_pros_and_cons(
    ticker
)


# ---------------------------------------------------------------------
# Available years
# ---------------------------------------------------------------------

available_years = set()

for dataframe in [
    ratios,
    profit_loss,
    balance_sheet,
    cash_flow,
    valuation,
]:

    if not dataframe.empty:

        available_years.update(
            dataframe[
                "financial_year"
            ]
            .dropna()
            .unique()
            .tolist()
        )


available_years = sorted(
    int(year)
    for year in available_years
)


if not available_years:

    st.error(
        "No financial-year data is available "
        "for this company."
    )

    st.stop()


selected_year = st.selectbox(
    "Financial year",
    available_years,
    index=len(available_years) - 1,
)


# ---------------------------------------------------------------------
# Company identity
# ---------------------------------------------------------------------

st.divider()

st.header(
    company_row["company_name"]
)

st.caption(
    f"NSE Ticker: {ticker}"
)


sector_row = sectors[
    sectors["company_id"] == ticker
]

sector_name = "N/A"
sub_sector = "N/A"

if not sector_row.empty:

    sector_name = (
        sector_row.iloc[0]
        .get("broad_sector", "N/A")
    )

    sub_sector = (
        sector_row.iloc[0]
        .get("sub_sector", "N/A")
    )


identity_col1, identity_col2, identity_col3 = (
    st.columns(3)
)


with identity_col1:

    st.markdown(
        f"**Sector:** {sector_name}"
    )


with identity_col2:

    st.markdown(
        f"**Sub-sector:** {sub_sector}"
    )


with identity_col3:

    website = company_row.get(
        "website"
    )

    if pd.notna(website) and str(website).strip():

        st.markdown(
            f"**Website:** {website}"
        )

    else:

        st.markdown(
            "**Website:** N/A"
        )


# ---------------------------------------------------------------------
# Selected-year datasets
# ---------------------------------------------------------------------

ratios_year = ratios[
    ratios["financial_year"]
    == selected_year
].copy()

pl_year = profit_loss[
    profit_loss["financial_year"]
    == selected_year
].copy()

bs_year = balance_sheet[
    balance_sheet["financial_year"]
    == selected_year
].copy()

cf_year = cash_flow[
    cash_flow["financial_year"]
    == selected_year
].copy()


# ---------------------------------------------------------------------
# Core financial metrics
# ---------------------------------------------------------------------

roe = get_median_value(
    ratios,
    "return_on_equity_pct",
    selected_year,
)

roce = parse_percentage(
    company_row.get(
        "roce_percentage"
    )
)

debt_to_equity = get_median_value(
    ratios,
    "debt_to_equity",
    selected_year,
)

net_profit_margin = get_median_value(
    ratios,
    "net_profit_margin_pct",
    selected_year,
)

operating_margin = get_median_value(
    ratios,
    "operating_profit_margin_pct",
    selected_year,
)

free_cash_flow = get_median_value(
    ratios,
    "free_cash_flow_cr",
    selected_year,
)

cash_from_operations = get_median_value(
    ratios,
    "cash_from_operations_cr",
    selected_year,
)

pe_ratio = get_median_value(
    valuation,
    "pe_ratio",
    selected_year,
)

pb_ratio = get_median_value(
    valuation,
    "pb_ratio",
    selected_year,
)

ev_ebitda = get_median_value(
    valuation,
    "ev_ebitda",
    selected_year,
)

dividend_yield = get_median_value(
    valuation,
    "dividend_yield_pct",
    selected_year,
)

market_cap = get_median_value(
    valuation,
    "market_cap_crore",
    selected_year,
)

sales = get_median_value(
    profit_loss,
    "sales",
    selected_year,
)

net_profit = get_median_value(
    profit_loss,
    "net_profit",
    selected_year,
)

borrowings = get_median_value(
    balance_sheet,
    "borrowings",
    selected_year,
)

reserves = get_median_value(
    balance_sheet,
    "reserves",
    selected_year,
)

capex = get_median_value(
    ratios,
    "capex_cr",
    selected_year,
)


# ---------------------------------------------------------------------
# Revenue CAGR
# ---------------------------------------------------------------------

revenue_cagr = None

if not analysis.empty:

    revenue_cagr = parse_percentage(
        analysis.iloc[0].get(
            "compounded_sales_growth"
        )
    )


profit_cagr = None

if not analysis.empty:

    profit_cagr = parse_percentage(
        analysis.iloc[0].get(
            "compounded_profit_growth"
        )
    )


stock_cagr = None

if not analysis.empty:

    stock_cagr = parse_percentage(
        analysis.iloc[0].get(
            "stock_price_cagr"
        )
    )


# ---------------------------------------------------------------------
# Investment Snapshot
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    f"Investment Snapshot — {selected_year}"
)


col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "ROE",
        format_number(
            roe,
            "%",
        ),
    )


with col2:

    st.metric(
        "ROCE",
        format_number(
            roce,
            "%",
        ),
    )


with col3:

    st.metric(
        "Revenue CAGR",
        format_number(
            revenue_cagr,
            "%",
        ),
    )


with col4:

    st.metric(
        "Net Profit Margin",
        format_number(
            net_profit_margin,
            "%",
        ),
    )


col5, col6, col7, col8 = st.columns(4)


with col5:

    st.metric(
        "Debt / Equity",
        format_number(
            debt_to_equity
        ),
    )


with col6:

    st.metric(
        "P / E",
        format_number(
            pe_ratio
        ),
    )


with col7:

    st.metric(
        "Free Cash Flow",
        format_number(
            free_cash_flow,
            " Cr",
        ),
    )


with col8:

    st.metric(
        "Market Cap",
        format_number(
            market_cap,
            " Cr",
        ),
    )


# ---------------------------------------------------------------------
# Growth & Profitability
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Growth & Profitability"
)


growth_col1, growth_col2 = st.columns(2)


with growth_col1:

    st.markdown(
        "#### Growth Indicators"
    )

    growth_data = pd.DataFrame(
        {
            "Metric": [
                "Revenue CAGR",
                "Profit CAGR",
                "Stock Price CAGR",
            ],
            "Value": [
                revenue_cagr,
                profit_cagr,
                stock_cagr,
            ],
        }
    )

    growth_data = growth_data[
        growth_data["Value"].notna()
    ]

    if not growth_data.empty:

        fig = px.bar(
            growth_data,
            x="Metric",
            y="Value",
            text="Value",
            title="Growth Metrics",
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )

        fig.update_layout(
            height=400,
            yaxis_title="Percentage",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:

        st.info(
            "Growth data is not available."
        )


with growth_col2:

    st.markdown(
        "#### Profitability Indicators"
    )

    profitability_data = pd.DataFrame(
        {
            "Metric": [
                "ROE",
                "ROCE",
                "Net Profit Margin",
                "Operating Profit Margin",
            ],
            "Value": [
                roe,
                roce,
                net_profit_margin,
                operating_margin,
            ],
        }
    )

    profitability_data = (
        profitability_data[
            profitability_data["Value"].notna()
        ]
    )

    if not profitability_data.empty:

        fig = px.bar(
            profitability_data,
            x="Metric",
            y="Value",
            text="Value",
            title="Profitability Metrics",
        )

        fig.update_traces(
            texttemplate="%{text:.2f}%",
            textposition="outside",
        )

        fig.update_layout(
            height=400,
            yaxis_title="Percentage",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:

        st.info(
            "Profitability data is not available."
        )


# ---------------------------------------------------------------------
# Valuation & Capital Structure
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Valuation & Capital Structure"
)


valuation_col1, valuation_col2 = (
    st.columns(2)
)


with valuation_col1:

    valuation_data = pd.DataFrame(
        {
            "Metric": [
                "P/E",
                "P/B",
                "EV/EBITDA",
                "Dividend Yield",
            ],
            "Value": [
                pe_ratio,
                pb_ratio,
                ev_ebitda,
                dividend_yield,
            ],
        }
    )

    valuation_data = valuation_data[
        valuation_data["Value"].notna()
    ]

    if not valuation_data.empty:

        fig = px.bar(
            valuation_data,
            x="Metric",
            y="Value",
            text="Value",
            title="Valuation Metrics",
        )

        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )

        fig.update_layout(
            height=400,
            yaxis_title="Value",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:

        st.info(
            "Valuation data is not available."
        )


with valuation_col2:

    capital_data = pd.DataFrame(
        {
            "Metric": [
                "Debt / Equity",
                "Borrowings",
                "Reserves",
                "Capital Expenditure",
            ],
            "Value": [
                debt_to_equity,
                borrowings,
                reserves,
                capex,
            ],
        }
    )

    capital_data = capital_data[
        capital_data["Value"].notna()
    ]

    if not capital_data.empty:

        fig = px.bar(
            capital_data,
            x="Metric",
            y="Value",
            text="Value",
            title="Capital Structure Metrics",
        )

        fig.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside",
        )

        fig.update_layout(
            height=400,
            yaxis_title="Value",
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:

        st.info(
            "Capital structure data is not available."
        )


# ---------------------------------------------------------------------
# Cash Flow Snapshot
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Cash Flow Snapshot"
)


cash_data = pd.DataFrame(
    {
        "Metric": [
            "Operating Cash Flow",
            "Free Cash Flow",
            "Capital Expenditure",
        ],
        "Value": [
            cash_from_operations,
            free_cash_flow,
            capex,
        ],
    }
)

cash_data = cash_data[
    cash_data["Value"].notna()
]


if not cash_data.empty:

    fig = px.bar(
        cash_data,
        x="Metric",
        y="Value",
        text="Value",
        title=(
            f"{company_row['company_name']} — "
            "Cash Generation"
        ),
    )

    fig.update_traces(
        texttemplate="%{text:,.2f}",
        textposition="outside",
    )

    fig.update_layout(
        height=450,
        yaxis_title="₹ Crore",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

else:

    st.info(
        "Cash-flow data is not available."
    )


# ---------------------------------------------------------------------
# Investment Interpretation
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Investment Intelligence"
)


strengths = []
risks = []


# Profitability

if roe is not None:

    if roe >= 20:
        strengths.append(
            f"Strong ROE of {roe:.2f}%."
        )

    elif roe < 10:
        risks.append(
            f"ROE is relatively low at {roe:.2f}%."
        )


if roce is not None:

    if roce >= 20:
        strengths.append(
            f"Strong capital efficiency with "
            f"ROCE of {roce:.2f}%."
        )

    elif roce < 10:
        risks.append(
            f"ROCE is relatively low at "
            f"{roce:.2f}%."
        )


# Growth

if revenue_cagr is not None:

    if revenue_cagr >= 15:
        strengths.append(
            f"Revenue has grown at "
            f"{revenue_cagr:.2f}% CAGR."
        )

    elif revenue_cagr < 5:
        risks.append(
            f"Revenue growth is modest at "
            f"{revenue_cagr:.2f}% CAGR."
        )


if profit_cagr is not None:

    if profit_cagr >= 15:
        strengths.append(
            f"Profit growth is strong at "
            f"{profit_cagr:.2f}% CAGR."
        )

    elif profit_cagr < 5:
        risks.append(
            f"Profit growth is modest at "
            f"{profit_cagr:.2f}% CAGR."
        )


# Leverage

if debt_to_equity is not None:

    if debt_to_equity <= 0.5:
        strengths.append(
            f"Moderate leverage with D/E of "
            f"{debt_to_equity:.2f}."
        )

    elif debt_to_equity >= 2:
        risks.append(
            f"High leverage with D/E of "
            f"{debt_to_equity:.2f}."
        )


# Cash flow

if free_cash_flow is not None:

    if free_cash_flow > 0:

        strengths.append(
            f"Positive free cash flow of "
            f"₹{free_cash_flow:,.2f} Cr."
        )

    else:

        risks.append(
            "Free cash flow is negative."
        )


# Valuation

if pe_ratio is not None:

    if pe_ratio > 50:
        risks.append(
            f"Elevated P/E valuation of "
            f"{pe_ratio:.2f}."
        )

    elif pe_ratio < 20:
        strengths.append(
            f"Relatively moderate P/E of "
            f"{pe_ratio:.2f}."
        )


summary_col1, summary_col2 = (
    st.columns(2)
)


with summary_col1:

    st.markdown(
        "### Positive Signals"
    )

    if strengths:

        for item in strengths:

            st.success(
                item
            )

    else:

        st.info(
            "No strong positive signals "
            "were identified using the "
            "dashboard thresholds."
        )


with summary_col2:

    st.markdown(
        "### Risk Signals"
    )

    if risks:

        for item in risks:

            st.warning(
                item
            )

    else:

        st.info(
            "No major risk signals were "
            "identified using the dashboard "
            "thresholds."
        )


# ---------------------------------------------------------------------
# Pros & Cons
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Database-Sourced Pros & Cons"
)


if pros_cons.empty:

    st.info(
        "Pros and cons information is not "
        "available for this company."
    )

else:

    pros_col, cons_col = (
        st.columns(2)
    )

    with pros_col:

        st.markdown(
            "### 🟢 Pros"
        )

        pros_values = (
            pros_cons["pros"]
            .dropna()
            .astype(str)
            .unique()
        )

        if len(pros_values) == 0:

            st.info(
                "No pros available."
            )

        else:

            for item in pros_values:

                st.success(
                    item
                )


    with cons_col:

        st.markdown(
            "### 🔴 Cons"
        )

        cons_values = (
            pros_cons["cons"]
            .dropna()
            .astype(str)
            .unique()
        )

        if len(cons_values) == 0:

            st.info(
                "No cons available."
            )

        else:

            for item in cons_values:

                st.warning(
                    item
                )


# ---------------------------------------------------------------------
# Historical Revenue & Profit
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Historical Revenue & Profitability"
)


if not profit_loss.empty:

    historical = profit_loss.copy()

    historical["sales"] = pd.to_numeric(
        historical["sales"],
        errors="coerce",
    )

    historical["net_profit"] = pd.to_numeric(
        historical["net_profit"],
        errors="coerce",
    )

    historical = (
        historical[
            [
                "financial_year",
                "sales",
                "net_profit",
            ]
        ]
        .dropna(
            subset=[
                "financial_year"
            ]
        )
        .groupby(
            "financial_year",
            as_index=False,
        )
        .median()
    )

    historical_long = historical.melt(
        id_vars=[
            "financial_year"
        ],
        var_name="metric",
        value_name="value",
    )

    historical_long["metric"] = (
        historical_long["metric"]
        .map(
            {
                "sales": "Revenue",
                "net_profit": "Net Profit",
            }
        )
        .fillna(
            historical_long["metric"]
        )
    )

    fig = px.line(
        historical_long,
        x="financial_year",
        y="value",
        color="metric",
        markers=True,
        title=(
            f"{company_row['company_name']} — "
            "Historical Revenue & Net Profit"
        ),
    )

    fig.update_layout(
        height=500,
        xaxis_title="Financial Year",
        yaxis_title="₹ Crore",
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

else:

    st.info(
        "Historical Profit & Loss data is "
        "not available."
    )


# ---------------------------------------------------------------------
# Executive Financial Table
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    f"Executive Financial Summary — {selected_year}"
)


report_rows = [
    {
        "Category": "Profitability",
        "Metric": "ROE",
        "Value": format_number(
            roe,
            "%",
        ),
    },
    {
        "Category": "Profitability",
        "Metric": "ROCE",
        "Value": format_number(
            roce,
            "%",
        ),
    },
    {
        "Category": "Profitability",
        "Metric": "Net Profit Margin",
        "Value": format_number(
            net_profit_margin,
            "%",
        ),
    },
    {
        "Category": "Growth",
        "Metric": "Revenue CAGR",
        "Value": format_number(
            revenue_cagr,
            "%",
        ),
    },
    {
        "Category": "Growth",
        "Metric": "Profit CAGR",
        "Value": format_number(
            profit_cagr,
            "%",
        ),
    },
    {
        "Category": "Valuation",
        "Metric": "P/E",
        "Value": format_number(
            pe_ratio,
        ),
    },
    {
        "Category": "Valuation",
        "Metric": "P/B",
        "Value": format_number(
            pb_ratio,
        ),
    },
    {
        "Category": "Leverage",
        "Metric": "Debt / Equity",
        "Value": format_number(
            debt_to_equity,
        ),
    },
    {
        "Category": "Cash Flow",
        "Metric": "Operating Cash Flow",
        "Value": format_number(
            cash_from_operations,
            " Cr",
        ),
    },
    {
        "Category": "Cash Flow",
        "Metric": "Free Cash Flow",
        "Value": format_number(
            free_cash_flow,
            " Cr",
        ),
    },
    {
        "Category": "Capital",
        "Metric": "Capital Expenditure",
        "Value": format_number(
            capex,
            " Cr",
        ),
    },
]


report_df = pd.DataFrame(
    report_rows
)


st.dataframe(
    report_df,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# CSV Download
# ---------------------------------------------------------------------

csv_data = report_df.to_csv(
    index=False
)


st.download_button(
    label="Download Financial Report CSV",
    data=csv_data,
    file_name=(
        f"{ticker}_investment_report_"
        f"{selected_year}.csv"
    ),
    mime="text/csv",
    width="stretch",
)


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

st.divider()

with st.expander(
    "Investment Intelligence Methodology"
):

    st.markdown(
        """
### Report Methodology

This report consolidates information already
available in the NIFTY 100 analytics database.

**Profitability**

ROE, ROCE, net profit margin and operating
profit margin are used to evaluate profitability
and capital efficiency.

**Growth**

Revenue CAGR, profit CAGR and stock-price CAGR
are used to summarize historical growth.

**Valuation**

P/E, P/B, EV/EBITDA and dividend yield are
presented as valuation indicators.

**Leverage**

Debt-to-equity and borrowings are used to
assess financial leverage.

**Cash Flow**

Operating cash flow, free cash flow and
capital expenditure are used to assess
cash-generation capability.

**Investment Intelligence**

Positive and risk signals are generated using
simple transparent thresholds. They are intended
as analytical indicators rather than investment
advice.

**Pros & Cons**

Pros and cons are displayed directly from the
database where available.

No financial metric is modified or overwritten
by the report layer.
"""
    )


# ---------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------

st.caption(
    "NIFTY 100 Analytics Platform • "
    "Investment Intelligence Report"
)