"""
NIFTY 100 Analytics - Home Screen
"""

import re

import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_sectors,
    get_valuation,
)
from src.screener.scoring import calculate_quality_score


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Home",
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
        '15%' -> 15.0
        '15.2' -> 15.2
        15.2 -> 15.2
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


def latest_ratio_rows(df, year):
    """
    Return ratio rows for the selected year.

    Duplicate rows for the same company/year are
    reduced using the median.
    """

    if df.empty:
        return pd.DataFrame()

    selected = df[
        df["year"].astype(str).str.contains(
            str(year),
            na=False,
        )
    ].copy()

    if selected.empty:
        return selected

    numeric_columns = [
        "return_on_equity_pct",
        "debt_to_equity",
        "free_cash_flow_cr",
        "cash_from_operations_cr",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
    ]

    available_columns = [
        column
        for column in numeric_columns
        if column in selected.columns
    ]

    for column in available_columns:

        selected[column] = pd.to_numeric(
            selected[column],
            errors="coerce",
        )

    selected = (
        selected
        .groupby(
            ["company_id", "company_name"],
            as_index=False,
        )[available_columns]
        .median()
    )

    return selected


def get_all_latest_ratios(companies, year):
    """
    Load ratio data for all companies
    for the selected year.
    """

    rows = []

    for ticker in companies["company_id"]:

        ratios = get_ratios(ticker)

        if ratios.empty:
            continue

        selected = latest_ratio_rows(
            ratios,
            year,
        )

        if not selected.empty:
            rows.append(selected)

    if not rows:
        return pd.DataFrame()

    return pd.concat(
        rows,
        ignore_index=True,
    )


def calculate_revenue_cagr(
    ticker,
    year,
):
    """
    Calculate 5-year revenue CAGR directly from
    the profit_loss sales history.

    Example:

        2019 -> 2024

    CAGR =
        ((2024 sales / 2019 sales) ** (1 / 5) - 1) * 100
    """

    profit_loss = get_pl(ticker)

    if profit_loss.empty:
        return None

    sales_data = profit_loss.copy()

    # Convert sales to numeric.
    sales_data["sales"] = pd.to_numeric(
        sales_data["sales"],
        errors="coerce",
    )

    # Keep only annual March records.
    # Excludes TTM and older December records.
    sales_data = sales_data[
        sales_data["year"]
        .astype(str)
        .str.startswith("Mar ")
    ].copy()

    if sales_data.empty:
        return None

    # Extract the year number.
    sales_data["year_number"] = pd.to_numeric(
        sales_data["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    sales_data = sales_data.dropna(
        subset=[
            "year_number",
            "sales",
        ]
    )

    if sales_data.empty:
        return None

    start_year = year - 5

    start_rows = sales_data[
        sales_data["year_number"] == start_year
    ]

    end_rows = sales_data[
        sales_data["year_number"] == year
    ]

    if (
        start_rows.empty
        or end_rows.empty
    ):
        return None

    start_sales = start_rows[
        "sales"
    ].median()

    end_sales = end_rows[
        "sales"
    ].median()

    if (
        pd.isna(start_sales)
        or pd.isna(end_sales)
        or start_sales <= 0
        or end_sales <= 0
    ):
        return None

    cagr = (
        (
            end_sales
            / start_sales
        )
        ** (1 / 5)
        - 1
    ) * 100

    return float(cagr)


def get_revenue_cagr_values(
    companies,
    year,
):
    """
    Calculate 5-year revenue CAGR for all
    available companies.
    """

    rows = []

    for ticker in companies["company_id"]:

        revenue_cagr = calculate_revenue_cagr(
            ticker,
            year,
        )

        if revenue_cagr is not None:

            rows.append(
                {
                    "company_id": ticker,
                    "revenue_cagr": revenue_cagr,
                }
            )

    return pd.DataFrame(rows)


def get_quality_score_data(
    companies,
    year,
):
    """
    Build the financial metric DataFrame required
    by the Sprint 3 composite quality scoring engine.

    Required metrics:

        return_on_equity
        return_on_capital_employed
        revenue_cagr
        free_cash_flow
        operating_cash_flow_margin
        debt_to_equity
    """

    rows = []

    for ticker in companies["company_id"]:

        # -------------------------------------------------------------
        # Financial ratios
        # -------------------------------------------------------------

        ratios = get_ratios(ticker)

        if ratios.empty:
            continue

        selected_ratios = latest_ratio_rows(
            ratios,
            year,
        )

        if selected_ratios.empty:
            continue

        ratio_row = selected_ratios.iloc[0]

        # -------------------------------------------------------------
        # Company information
        # -------------------------------------------------------------

        company_rows = companies[
            companies["company_id"] == ticker
        ]

        if company_rows.empty:
            continue

        company_row = company_rows.iloc[0]

        # -------------------------------------------------------------
        # ROE
        # -------------------------------------------------------------

        roe = pd.to_numeric(
            ratio_row.get(
                "return_on_equity_pct"
            ),
            errors="coerce",
        )

        # -------------------------------------------------------------
        # Debt-to-equity
        # -------------------------------------------------------------

        debt_to_equity = pd.to_numeric(
            ratio_row.get(
                "debt_to_equity"
            ),
            errors="coerce",
        )

        # -------------------------------------------------------------
        # ROCE
        # -------------------------------------------------------------

        roce = parse_percentage(
            company_row.get(
                "roce_percentage"
            )
        )

        # -------------------------------------------------------------
        # Revenue CAGR
        # -------------------------------------------------------------

        revenue_cagr = calculate_revenue_cagr(
            ticker,
            year,
        )

        # -------------------------------------------------------------
        # Free cash flow
        # -------------------------------------------------------------

        free_cash_flow = pd.to_numeric(
            ratio_row.get(
                "free_cash_flow_cr"
            ),
            errors="coerce",
        )

        # -------------------------------------------------------------
        # Operating cash flow margin
        # -------------------------------------------------------------

        operating_cash_flow = pd.to_numeric(
            ratio_row.get(
                "cash_from_operations_cr"
            ),
            errors="coerce",
        )

        operating_cash_flow_margin = None

        profit_loss = get_pl(ticker)

        if not profit_loss.empty:

            selected_pl = profit_loss[
                profit_loss["year"]
                .astype(str)
                .str.contains(
                    str(year),
                    na=False,
                )
            ].copy()

            if not selected_pl.empty:

                selected_pl["sales"] = pd.to_numeric(
                    selected_pl["sales"],
                    errors="coerce",
                )

                sales = selected_pl[
                    "sales"
                ].median()

                if (
                    pd.notna(
                        operating_cash_flow
                    )
                    and pd.notna(sales)
                    and sales != 0
                ):

                    operating_cash_flow_margin = (
                        operating_cash_flow
                        / sales
                    ) * 100

        # -------------------------------------------------------------
        # Validate required metrics
        # -------------------------------------------------------------

        required_values = [
            roe,
            roce,
            revenue_cagr,
            free_cash_flow,
            operating_cash_flow_margin,
            debt_to_equity,
        ]

        if any(
            pd.isna(value)
            for value in required_values
        ):
            continue

        rows.append(
            {
                "company_id": ticker,
                "company": company_row[
                    "company_name"
                ],
                "return_on_equity": float(
                    roe
                ),
                "return_on_capital_employed": float(
                    roce
                ),
                "revenue_cagr": float(
                    revenue_cagr
                ),
                "free_cash_flow": float(
                    free_cash_flow
                ),
                "operating_cash_flow_margin": float(
                    operating_cash_flow_margin
                ),
                "debt_to_equity": float(
                    debt_to_equity
                ),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title("Nifty 100 Analytics")

st.markdown(
    "### Nifty 100 Financial Intelligence Overview"
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
# Year selector
# ---------------------------------------------------------------------

available_years = list(
    range(
        2019,
        2025,
    )
)

selected_year = st.selectbox(
    "Select financial year",
    available_years,
    index=len(
        available_years
    ) - 1,
)


# ---------------------------------------------------------------------
# Load ratios
# ---------------------------------------------------------------------

ratios = get_all_latest_ratios(
    companies,
    selected_year,
)


# ---------------------------------------------------------------------
# KPI calculations
# ---------------------------------------------------------------------

if ratios.empty:

    average_roe = None
    median_de = None

else:

    average_roe = ratios[
        "return_on_equity_pct"
    ].mean()

    median_de = ratios[
        "debt_to_equity"
    ].median()


# ---------------------------------------------------------------------
# Valuation data
# ---------------------------------------------------------------------

valuation_rows = []

for ticker in companies[
    "company_id"
]:

    valuation = get_valuation(
        ticker
    )

    if valuation.empty:
        continue

    selected = valuation[
        valuation["year"]
        .astype(str)
        == str(selected_year)
    ]

    if selected.empty:
        continue

    row = selected.iloc[-1]

    valuation_rows.append(
        {
            "company_id": ticker,
            "pe_ratio": pd.to_numeric(
                row["pe_ratio"],
                errors="coerce",
            ),
        }
    )


valuation_df = pd.DataFrame(
    valuation_rows
)

if valuation_df.empty:

    median_pe = None

else:

    median_pe = valuation_df[
        "pe_ratio"
    ].median()


# ---------------------------------------------------------------------
# Revenue CAGR
# ---------------------------------------------------------------------

cagr_df = get_revenue_cagr_values(
    companies,
    selected_year,
)

if cagr_df.empty:

    median_cagr = None

else:

    median_cagr = cagr_df[
        "revenue_cagr"
    ].median()


# ---------------------------------------------------------------------
# Debt-free companies
# ---------------------------------------------------------------------

if ratios.empty:

    debt_free_count = 0

else:

    debt_free_count = int(
        (
            ratios[
                "debt_to_equity"
            ].fillna(0)
            == 0
        ).sum()
    )


# ---------------------------------------------------------------------
# KPI display
# ---------------------------------------------------------------------

col1, col2, col3 = st.columns(3)

col4, col5, col6 = st.columns(3)


with col1:

    st.metric(
        "Average ROE",
        (
            "N/A"
            if average_roe is None
            else f"{average_roe:.2f}%"
        ),
    )


with col2:

    st.metric(
        "Median P/E",
        (
            "N/A"
            if median_pe is None
            else f"{median_pe:.2f}"
        ),
    )


with col3:

    st.metric(
        "Median D/E",
        (
            "N/A"
            if median_de is None
            else f"{median_de:.2f}"
        ),
    )


with col4:

    st.metric(
        "Total Companies",
        len(companies),
    )


with col5:

    st.metric(
        "Median Revenue CAGR 5yr",
        (
            "N/A"
            if median_cagr is None
            else f"{median_cagr:.2f}%"
        ),
    )


with col6:

    st.metric(
        "Debt-Free Companies",
        debt_free_count,
    )


# ---------------------------------------------------------------------
# Sector breakdown
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Sector Breakdown"
)

sectors = get_sectors()

if sectors.empty:

    st.info(
        "Sector data is not available."
    )

else:

    sector_counts = (
        sectors
        .groupby(
            "broad_sector"
        )
        .size()
        .reset_index(
            name="company_count"
        )
        .sort_values(
            "company_count",
            ascending=False,
        )
    )

    fig = px.pie(
        sector_counts,
        names="broad_sector",
        values="company_count",
        hole=0.55,
        title="Nifty 100 Companies by Sector",
    )

    fig.update_layout(
        height=500,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ---------------------------------------------------------------------
# Top 5 companies by composite quality score
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Top 5 Companies by Composite Quality Score"
)

try:

    scoring_df = get_quality_score_data(
        companies,
        selected_year,
    )

    if scoring_df.empty:

        st.info(
            "Composite quality scores are not "
            "available for the selected year."
        )

    else:

        # -------------------------------------------------------------
        # Reuse Sprint 3 scoring engine
        # -------------------------------------------------------------

        scored_df = calculate_quality_score(
            scoring_df
        )

        top_5 = scored_df.head(
            5
        ).copy()

        st.info(
            "Composite score ranking uses the "
            "Sprint 3 quality scoring engine and "
            "financial data available for the "
            "selected year."
        )

        display_columns = [
            "company_id",
            "company",
            "return_on_equity",
            "return_on_capital_employed",
            "revenue_cagr",
            "debt_to_equity",
            "composite_quality_score",
        ]

        st.dataframe(
            top_5[
                display_columns
            ],
            use_container_width=True,
            hide_index=True,
        )


except Exception as exc:

    st.warning(
        "Unable to calculate the "
        "top-company ranking: "
        f"{exc}"
    )