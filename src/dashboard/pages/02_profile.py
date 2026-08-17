"""
NIFTY 100 Analytics - Company Profile Screen
"""

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_analysis,
    get_pros_and_cons,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Company Profile",
    page_icon="🏢",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def parse_number(value):
    """
    Convert a numeric or percentage-like value into float.
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


def clean_text(value):
    """
    Convert a database value into clean display text.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def calculate_revenue_cagr(
    ticker,
    year=2024,
):
    """
    Calculate 5-year Revenue CAGR from profit/loss data.

    Uses:
        start year = selected year - 5
        end year   = selected year
    """

    profit_loss = get_pl(ticker)

    if profit_loss.empty:
        return None

    data = profit_loss.copy()

    data["sales"] = pd.to_numeric(
        data["sales"],
        errors="coerce",
    )

    data = data[
        data["year"]
        .astype(str)
        .str.startswith("Mar ")
    ].copy()

    if data.empty:
        return None

    data["year_number"] = pd.to_numeric(
        data["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "year_number",
            "sales",
        ]
    )

    start_year = year - 5

    start = data[
        data["year_number"] == start_year
    ]

    end = data[
        data["year_number"] == year
    ]

    if start.empty or end.empty:
        return None

    start_sales = start["sales"].median()
    end_sales = end["sales"].median()

    if (
        pd.isna(start_sales)
        or pd.isna(end_sales)
        or start_sales <= 0
        or end_sales <= 0
    ):
        return None

    return (
        (
            end_sales / start_sales
        )
        ** (1 / 5)
        - 1
    ) * 100


def get_latest_ratio_row(
    ticker,
    year=2024,
):
    """
    Get the selected year's financial ratio row.

    Duplicate company/year records are reduced
    using median values.
    """

    ratios = get_ratios(ticker)

    if ratios.empty:
        return None

    selected = ratios[
        ratios["year"]
        .astype(str)
        .str.contains(
            str(year),
            na=False,
        )
    ].copy()

    if selected.empty:
        return None

    numeric_columns = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "cash_from_operations_cr",
        "interest_coverage",
        "asset_turnover",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
    ]

    available = [
        column
        for column in numeric_columns
        if column in selected.columns
    ]

    for column in available:
        selected[column] = pd.to_numeric(
            selected[column],
            errors="coerce",
        )

    if not available:
        return selected.iloc[0]

    result = (
        selected[available]
        .median()
    )

    return result


def get_historical_profit_loss(
    ticker,
):
    """
    Load historical Profit & Loss data
    for charting.
    """

    data = get_pl(ticker)

    if data.empty:
        return pd.DataFrame()

    data = data.copy()

    data["year_number"] = pd.to_numeric(
        data["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    data["sales"] = pd.to_numeric(
        data["sales"],
        errors="coerce",
    )

    data["net_profit"] = pd.to_numeric(
        data["net_profit"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "year_number",
        ]
    )

    # Exclude TTM
    data = data[
        data["year"]
        .astype(str)
        .str.startswith("Mar ")
    ]

    # Reduce duplicate year rows
    data = (
        data
        .groupby(
            "year_number",
            as_index=False,
        )[
            [
                "sales",
                "net_profit",
            ]
        ]
        .median()
        .sort_values(
            "year_number"
        )
    )

    return data.tail(10)


def get_historical_ratios(
    ticker,
):
    """
    Load historical ROE data for charting.
    """

    data = get_ratios(ticker)

    if data.empty:
        return pd.DataFrame()

    data = data.copy()

    data["year_number"] = pd.to_numeric(
        data["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    data["return_on_equity_pct"] = pd.to_numeric(
        data["return_on_equity_pct"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "year_number",
        ]
    )

    data = data[
        data["year"]
        .astype(str)
        .str.startswith("Mar ")
    ]

    data = (
        data
        .groupby(
            "year_number",
            as_index=False,
        )[
            "return_on_equity_pct"
        ]
        .median()
        .sort_values(
            "year_number"
        )
    )

    return data.tail(10)


def get_roce_value(
    company_row,
):
    """
    Extract ROCE from the companies table.
    """

    return parse_number(
        company_row.get(
            "roce_percentage"
        )
    )


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title(
    "Company Profile"
)

st.markdown(
    "Explore detailed financial information, "
    "fundamentals, historical performance, and "
    "pros and cons for NIFTY 100 companies."
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


# ---------------------------------------------------------------------
# Company selector
# ---------------------------------------------------------------------

company_options = companies[
    "company_id"
].tolist()

company_names = (
    companies
    .set_index("company_id")[
        "company_name"
    ]
    .to_dict()
)


search_options = []

for ticker in company_options:

    name = company_names.get(
        ticker,
        "",
    )

    search_options.append(
        f"{ticker} — {name}"
    )


selected_company = st.selectbox(
    "Search company or NSE ticker",
    search_options,
    index=0,
)


# ---------------------------------------------------------------------
# Extract ticker
# ---------------------------------------------------------------------

if not selected_company:

    st.info(
        "Select a company to view its profile."
    )

    st.stop()


ticker = selected_company.split(
    " — ",
    1,
)[0].strip()


# ---------------------------------------------------------------------
# Company lookup
# ---------------------------------------------------------------------

company_matches = companies[
    companies["company_id"] == ticker
]

if company_matches.empty:

    st.warning(
        "Ticker not found — please try another."
    )

    st.stop()


company = company_matches.iloc[0]


company_name = clean_text(
    company.get(
        "company_name"
    )
)

sector = clean_text(
    company.get(
        "broad_sector",
        "",
    )
)

sub_sector = clean_text(
    company.get(
        "sub_sector",
        "",
    )
)

about_company = clean_text(
    company.get(
        "about_company",
        "",
    )
)

nse_ticker = clean_text(
    company.get(
        "company_id",
        ticker,
    )
)


# ---------------------------------------------------------------------
# Sector fallback
# ---------------------------------------------------------------------

if not sector:

    sector_data = None

    try:

        from src.dashboard.utils.db import (
            get_sectors,
        )

        sectors = get_sectors()

        if not sectors.empty:

            sector_rows = sectors[
                sectors["company_id"]
                == ticker
            ]

            if not sector_rows.empty:

                sector_row = (
                    sector_rows.iloc[0]
                )

                sector = clean_text(
                    sector_row.get(
                        "broad_sector",
                        "",
                    )
                )

                sub_sector = clean_text(
                    sector_row.get(
                        "sub_sector",
                        "",
                    )
                )

    except Exception:
        pass


# ---------------------------------------------------------------------
# Company profile card
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    company_name
)

profile_col1, profile_col2 = st.columns(
    [1, 3]
)

with profile_col1:

    logo = clean_text(
        company.get(
            "company_logo",
            "",
        )
    )

    if logo:

        try:
            st.image(
                logo,
                width=130,
            )
        except Exception:
            pass


with profile_col2:

    st.markdown(
        f"**NSE Ticker:** `{nse_ticker}`"
    )

    if sector:

        st.markdown(
            f"**Sector:** {sector}"
        )

    if sub_sector:

        st.markdown(
            f"**Sub-sector:** {sub_sector}"
        )

    if about_company:

        st.markdown(
            f"**About:** {about_company}"
        )


# ---------------------------------------------------------------------
# Financial data
# ---------------------------------------------------------------------

SELECTED_YEAR = 2024

ratio_row = get_latest_ratio_row(
    ticker,
    SELECTED_YEAR,
)

roe = None
net_profit_margin = None
debt_to_equity = None
free_cash_flow = None

if ratio_row is not None:

    roe = parse_number(
        ratio_row.get(
            "return_on_equity_pct"
        )
    )

    net_profit_margin = parse_number(
        ratio_row.get(
            "net_profit_margin_pct"
        )
    )

    debt_to_equity = parse_number(
        ratio_row.get(
            "debt_to_equity"
        )
    )

    free_cash_flow = parse_number(
        ratio_row.get(
            "free_cash_flow_cr"
        )
    )


roce = get_roce_value(
    company
)

revenue_cagr = calculate_revenue_cagr(
    ticker,
    SELECTED_YEAR,
)


# ---------------------------------------------------------------------
# KPI section
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    f"Key Financial Metrics — {SELECTED_YEAR}"
)

kpi1, kpi2, kpi3 = st.columns(3)

kpi4, kpi5, kpi6 = st.columns(3)


with kpi1:

    st.metric(
        "ROE",
        (
            "N/A"
            if roe is None
            else f"{roe:.2f}%"
        ),
    )


with kpi2:

    st.metric(
        "ROCE",
        (
            "N/A"
            if roce is None
            else f"{roce:.2f}%"
        ),
    )


with kpi3:

    st.metric(
        "Net Profit Margin",
        (
            "N/A"
            if net_profit_margin is None
            else f"{net_profit_margin:.2f}%"
        ),
    )


with kpi4:

    st.metric(
        "Debt / Equity",
        (
            "N/A"
            if debt_to_equity is None
            else f"{debt_to_equity:.2f}"
        ),
    )


with kpi5:

    st.metric(
        "Revenue CAGR 5yr",
        (
            "N/A"
            if revenue_cagr is None
            else f"{revenue_cagr:.2f}%"
        ),
    )


with kpi6:

    st.metric(
        "Free Cash Flow",
        (
            "N/A"
            if free_cash_flow is None
            else f"{free_cash_flow:,.2f} Cr"
        ),
    )


# ---------------------------------------------------------------------
# Revenue and Net Profit chart
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Revenue & Net Profit — 10 Year Trend"
)

profit_loss = get_historical_profit_loss(
    ticker
)

if profit_loss.empty:

    st.info(
        "Historical profit and loss data "
        "is not available."
    )

else:

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=profit_loss[
                "year_number"
            ],
            y=profit_loss[
                "sales"
            ],
            mode="lines+markers",
            name="Revenue",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=profit_loss[
                "year_number"
            ],
            y=profit_loss[
                "net_profit"
            ],
            mode="lines+markers",
            name="Net Profit",
        )
    )

    fig.update_layout(
        title=(
            f"{company_name} — "
            "Revenue & Net Profit"
        ),
        xaxis_title="Financial Year",
        yaxis_title="Amount (₹ Cr)",
        hovermode="x unified",
        height=500,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------------------
# ROE chart
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "ROE & ROCE — 10 Year Trend"
)

historical_ratios = get_historical_ratios(
    ticker
)

if historical_ratios.empty:

    st.info(
        "Historical ROE data is not available."
    )

else:

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=historical_ratios[
                "year_number"
            ],
            y=historical_ratios[
                "return_on_equity_pct"
            ],
            mode="lines+markers",
            name="ROE",
        )
    )

    # ROCE is stored in the companies table
    # as the latest available value.
    if roce is not None:

        fig.add_trace(
            go.Scatter(
                x=historical_ratios[
                    "year_number"
                ],
                y=[
                    roce
                    for _ in range(
                        len(
                            historical_ratios
                        )
                    )
                ],
                mode="lines+markers",
                name="ROCE",
            )
        )

    fig.update_layout(
        title=(
            f"{company_name} — "
            "ROE & ROCE"
        ),
        xaxis_title="Financial Year",
        yaxis_title="Percentage (%)",
        hovermode="x unified",
        height=500,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------------------
# Pros and Cons
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Pros & Cons"
)

try:

    pros_cons = get_pros_and_cons(
        ticker
    )

except Exception:

    pros_cons = pd.DataFrame()


if pros_cons.empty:

    st.info(
        "Pros and cons information is not available "
        "for this company."
    )

else:

    row = pros_cons.iloc[0]

    pros_value = clean_text(
        row.get(
            "pros",
            "",
        )
    )

    cons_value = clean_text(
        row.get(
            "cons",
            "",
        )
    )

    pros_col, cons_col = st.columns(2)

    with pros_col:

        st.markdown(
            "### ✅ Pros"
        )

        if pros_value:

            pros_items = re.split(
                r"\n|•|;",
                pros_value,
            )

            for item in pros_items:

                item = item.strip()

                if item:

                    st.markdown(
                        f"✅ {item}"
                    )

        else:

            st.info(
                "No pros available."
            )

    with cons_col:

        st.markdown(
            "### ❌ Cons"
        )

        if cons_value:

            cons_items = re.split(
                r"\n|•|;",
                cons_value,
            )

            for item in cons_items:

                item = item.strip()

                if item:

                    st.markdown(
                        f"❌ {item}"
                    )

        else:

            st.info(
                "No cons available."
            )