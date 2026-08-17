"""
NIFTY 100 Analytics - Stock Screener

Interactive financial screening engine for NIFTY 100 companies.
Uses SQLite data through the shared dashboard database loader
and the Sprint 3 composite quality scoring engine.
"""

import numpy as np
import pandas as pd
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_ratios,
    get_pl,
    get_valuation,
    get_sectors,
    get_analysis,
)

from src.screener.scoring import calculate_quality_score


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Screener",
    page_icon="🔎",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def safe_numeric(value):
    """
    Convert a value to numeric safely.
    """

    try:
        return pd.to_numeric(
            value,
            errors="coerce",
        )
    except Exception:
        return np.nan


def year_matches(series, year):
    """
    Match financial-year strings robustly.

    Examples:
        2024 -> Mar 2024
        2024 -> Dec 2024
        2024 -> 2024
    """

    return series.astype(str).str.contains(
        str(year),
        na=False,
    )


def select_year_rows(df, year):
    """
    Select rows corresponding to the requested financial year.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    if "year" not in df.columns:
        return pd.DataFrame()

    return df[
        year_matches(
            df["year"],
            year,
        )
    ].copy()


def get_latest_ratio_row(ticker, year):
    """
    Get one clean financial-ratio row for a company/year.

    Duplicate rows are reduced using median aggregation.
    """

    ratios = get_ratios(ticker)

    if ratios.empty:
        return None

    selected = select_year_rows(
        ratios,
        year,
    )

    if selected.empty:
        return None

    numeric_columns = [
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "return_on_equity_pct",
        "debt_to_equity",
        "interest_coverage",
        "asset_turnover",
        "free_cash_flow_cr",
        "capex_cr",
        "earnings_per_share",
        "book_value_per_share",
        "dividend_payout_ratio_pct",
        "total_debt_cr",
        "cash_from_operations_cr",
        "roce_percentage",
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

    grouped = (
        selected
        .groupby(
            ["company_id", "company_name"],
            as_index=False,
        )[available_columns]
        .median()
    )

    if grouped.empty:
        return None

    return grouped.iloc[0]


def calculate_cagr(start_value, end_value, years):
    """
    Calculate CAGR safely.

    CAGR is only calculated when both values are positive.
    """

    start_value = safe_numeric(start_value)
    end_value = safe_numeric(end_value)

    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or start_value <= 0
        or end_value <= 0
        or years <= 0
    ):
        return np.nan

    try:
        return (
            (end_value / start_value)
            ** (1 / years)
            - 1
        ) * 100
    except Exception:
        return np.nan


def calculate_growth_from_pl(
    ticker,
    metric,
    selected_year,
):
    """
    Calculate 5-year CAGR directly from Profit & Loss data.

    Supported metrics:
        sales
        net_profit

    This is used as a fallback when the analysis table does
    not contain the corresponding growth metric.
    """

    pl = get_pl(ticker)

    if pl.empty:
        return np.nan

    if metric not in pl.columns:
        return np.nan

    financial_rows = pl[
        pl["year"].astype(str).str.match(
            r"^(Mar|Dec)\s\d{4}$",
            na=False,
        )
    ].copy()

    if financial_rows.empty:
        return np.nan

    financial_rows["year_number"] = pd.to_numeric(
        financial_rows["year"].astype(str).str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    financial_rows[metric] = pd.to_numeric(
        financial_rows[metric],
        errors="coerce",
    )

    financial_rows = financial_rows.dropna(
        subset=[
            "year_number",
            metric,
        ]
    )

    if financial_rows.empty:
        return np.nan

    target_year = int(selected_year)

    target_rows = financial_rows[
        financial_rows["year_number"] == target_year
    ]

    if target_rows.empty:
        # Fall back to the latest available year.
        target_rows = financial_rows[
            financial_rows["year_number"]
            == financial_rows["year_number"].max()
        ]

    if target_rows.empty:
        return np.nan

    end_value = target_rows[metric].median()

    start_year = target_year - 5

    start_rows = financial_rows[
        financial_rows["year_number"] == start_year
    ]

    if start_rows.empty:
        # Find the closest available year at least 4 years earlier.
        earlier = financial_rows[
            financial_rows["year_number"] < target_year
        ]

        if earlier.empty:
            return np.nan

        possible_year = earlier["year_number"].max()

        start_rows = financial_rows[
            financial_rows["year_number"] == possible_year
        ]

        actual_start_year = possible_year

    else:
        actual_start_year = start_year

    if start_rows.empty:
        return np.nan

    start_value = start_rows[metric].median()

    years = target_year - int(actual_start_year)

    if years < 1:
        return np.nan

    return calculate_cagr(
        start_value,
        end_value,
        years,
    )


def get_revenue_cagr(
    ticker,
    selected_year,
):
    """
    Get 5-year revenue CAGR.

    First attempts to use the analysis table.
    Falls back to Profit & Loss calculation.
    """

    try:
        analysis = get_analysis(ticker)

        if not analysis.empty:

            column = "compounded_sales_growth"

            if column in analysis.columns:

                value = safe_numeric(
                    analysis.iloc[0][column]
                )

                if pd.notna(value):
                    return float(value)

                text = str(
                    analysis.iloc[0][column]
                ).replace("%", "").strip()

                value = safe_numeric(text)

                if pd.notna(value):
                    return float(value)

    except Exception:
        pass

    return calculate_growth_from_pl(
        ticker,
        "sales",
        selected_year,
    )


def get_pat_cagr(
    ticker,
    selected_year,
):
    """
    Get 5-year PAT CAGR.

    First attempts to use the analysis table.
    Falls back to Profit & Loss calculation.
    """

    try:
        analysis = get_analysis(ticker)

        if not analysis.empty:

            column = "compounded_profit_growth"

            if column in analysis.columns:

                value = safe_numeric(
                    analysis.iloc[0][column]
                )

                if pd.notna(value):
                    return float(value)

                text = str(
                    analysis.iloc[0][column]
                ).replace("%", "").strip()

                value = safe_numeric(text)

                if pd.notna(value):
                    return float(value)

    except Exception:
        pass

    return calculate_growth_from_pl(
        ticker,
        "net_profit",
        selected_year,
    )


def get_company_screening_data(
    companies,
    selected_year,
):
    """
    Build the complete screening dataset.

    One row per company.
    """

    rows = []

    for _, company in companies.iterrows():

        ticker = company["company_id"]

        ratio_row = get_latest_ratio_row(
            ticker,
            selected_year,
        )

        if ratio_row is None:
            continue

        valuation = get_valuation(ticker)

        pe_ratio = np.nan
        pb_ratio = np.nan
        dividend_yield = np.nan
        market_cap = np.nan
        ev_ebitda = np.nan

        if not valuation.empty:

            selected_valuation = (
                valuation[
                    valuation["year"].astype(str)
                    == str(selected_year)
                ]
            )

            if selected_valuation.empty:

                # Use the latest available valuation year
                # when the selected financial year is unavailable.
                selected_valuation = valuation.tail(1)

            if not selected_valuation.empty:

                valuation_row = (
                    selected_valuation.iloc[-1]
                )

                pe_ratio = safe_numeric(
                    valuation_row.get(
                        "pe_ratio"
                    )
                )

                pb_ratio = safe_numeric(
                    valuation_row.get(
                        "pb_ratio"
                    )
                )

                dividend_yield = safe_numeric(
                    valuation_row.get(
                        "dividend_yield_pct"
                    )
                )

                market_cap = safe_numeric(
                    valuation_row.get(
                        "market_cap_crore"
                    )
                )

                ev_ebitda = safe_numeric(
                    valuation_row.get(
                        "ev_ebitda"
                    )
                )

        # -------------------------------------------------------------
        # Financial ratios
        # -------------------------------------------------------------

        roe = safe_numeric(
            ratio_row.get(
                "return_on_equity_pct"
            )
        )

        roce = safe_numeric(
            ratio_row.get(
                "roce_percentage"
            )
        )

        debt_to_equity = safe_numeric(
            ratio_row.get(
                "debt_to_equity"
            )
        )

        interest_coverage = safe_numeric(
            ratio_row.get(
                "interest_coverage"
            )
        )

        fcf = safe_numeric(
            ratio_row.get(
                "free_cash_flow_cr"
            )
        )

        operating_profit_margin = safe_numeric(
            ratio_row.get(
                "operating_profit_margin_pct"
            )
        )

        net_profit_margin = safe_numeric(
            ratio_row.get(
                "net_profit_margin_pct"
            )
        )

        cfo = safe_numeric(
            ratio_row.get(
                "cash_from_operations_cr"
            )
        )

        # -------------------------------------------------------------
        # Profit & Loss
        # -------------------------------------------------------------

        pl = get_pl(ticker)

        operating_cash_flow_margin = np.nan

        if not pl.empty:

            selected_pl = select_year_rows(
                pl,
                selected_year,
            )

            if not selected_pl.empty:

                sales = pd.to_numeric(
                    selected_pl["sales"],
                    errors="coerce",
                ).median()

                if (
                    pd.notna(cfo)
                    and pd.notna(sales)
                    and sales != 0
                ):
                    operating_cash_flow_margin = (
                        cfo / sales
                    ) * 100

        # -------------------------------------------------------------
        # Growth
        # -------------------------------------------------------------

        revenue_cagr = get_revenue_cagr(
            ticker,
            selected_year,
        )

        pat_cagr = get_pat_cagr(
            ticker,
            selected_year,
        )

        # -------------------------------------------------------------
        # Sector
        # -------------------------------------------------------------

        sector = ""

        company_sector = pd.DataFrame()

        try:

            sectors = get_sectors()

            if not sectors.empty:

                company_sector = sectors[
                    sectors["company_id"]
                    == ticker
                ]

                if not company_sector.empty:

                    sector = str(
                        company_sector.iloc[0].get(
                            "broad_sector",
                            "",
                        )
                    )

        except Exception:
            sector = ""

        rows.append(
            {
                "company_id": ticker,
                "company": company["company_name"],
                "sector": sector,
                "return_on_equity": roe,
                "return_on_capital_employed": roce,
                "revenue_cagr": revenue_cagr,
                "pat_cagr": pat_cagr,
                "free_cash_flow": fcf,
                "operating_cash_flow_margin": (
                    operating_cash_flow_margin
                ),
                "debt_to_equity": debt_to_equity,
                "interest_coverage": interest_coverage,
                "operating_profit_margin": (
                    operating_profit_margin
                ),
                "net_profit_margin": (
                    net_profit_margin
                ),
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "dividend_yield": dividend_yield,
                "market_cap_crore": market_cap,
                "ev_ebitda": ev_ebitda,
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Load companies
# ---------------------------------------------------------------------

st.title("Nifty 100 Screener")

st.markdown(
    "Screen NIFTY 100 companies using financial quality, "
    "growth, valuation, dividend and leverage metrics."
)

companies = get_companies()

if companies.empty:
    st.error(
        "No company data is available."
    )
    st.stop()


# ---------------------------------------------------------------------
# Financial year
# ---------------------------------------------------------------------

available_years = list(
    range(
        2019,
        2025,
    )
)

selected_year = st.selectbox(
    "Financial Year",
    available_years,
    index=len(available_years) - 1,
)


# ---------------------------------------------------------------------
# Load screening data
# ---------------------------------------------------------------------

with st.spinner(
    "Loading NIFTY 100 financial data..."
):

    screening_df = get_company_screening_data(
        companies,
        selected_year,
    )


if screening_df.empty:

    st.error(
        "No screening data is available."
    )

    st.stop()


# ---------------------------------------------------------------------
# Clean numeric columns
# ---------------------------------------------------------------------

numeric_columns = [
    "return_on_equity",
    "return_on_capital_employed",
    "revenue_cagr",
    "pat_cagr",
    "free_cash_flow",
    "operating_cash_flow_margin",
    "debt_to_equity",
    "interest_coverage",
    "operating_profit_margin",
    "net_profit_margin",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield",
    "market_cap_crore",
    "ev_ebitda",
]

for column in numeric_columns:

    screening_df[column] = pd.to_numeric(
        screening_df[column],
        errors="coerce",
    )


# ---------------------------------------------------------------------
# Screening presets
# ---------------------------------------------------------------------

st.subheader("Screening Presets")

preset_columns = st.columns(6)

with preset_columns[0]:
    quality_preset = st.button(
        "Quality",
        width="stretch",
    )

with preset_columns[1]:
    value_preset = st.button(
        "Value",
        width="stretch",
    )

with preset_columns[2]:
    growth_preset = st.button(
        "Growth",
        width="stretch",
    )

with preset_columns[3]:
    dividend_preset = st.button(
        "Dividend",
        width="stretch",
    )

with preset_columns[4]:
    debt_free_preset = st.button(
        "Debt-Free",
        width="stretch",
    )

with preset_columns[5]:
    turnaround_preset = st.button(
        "Turnaround",
        width="stretch",
    )


# ---------------------------------------------------------------------
# Default filters
# ---------------------------------------------------------------------

default_roe = 0.0
default_roce = 0.0
default_revenue_cagr = 0.0
default_pat_cagr = 0.0
default_fcf = 0.0
default_opm = 0.0
default_de = 20.0
default_pe = 200.0
default_pb = 50.0
default_dividend = 0.0
default_interest = 0.0


# ---------------------------------------------------------------------
# Preset values
# ---------------------------------------------------------------------

if quality_preset:

    default_roe = 15.0
    default_roce = 15.0
    default_revenue_cagr = 10.0
    default_pat_cagr = 10.0
    default_fcf = 0.0
    default_opm = 10.0
    default_de = 2.0
    default_pe = 100.0
    default_pb = 20.0
    default_dividend = 0.0
    default_interest = 3.0

elif value_preset:

    default_roe = 10.0
    default_roce = 10.0
    default_revenue_cagr = 5.0
    default_pat_cagr = 5.0
    default_fcf = 0.0
    default_opm = 5.0
    default_de = 3.0
    default_pe = 30.0
    default_pb = 5.0
    default_dividend = 0.0
    default_interest = 2.0

elif growth_preset:

    default_roe = 15.0
    default_roce = 15.0
    default_revenue_cagr = 15.0
    default_pat_cagr = 15.0
    default_fcf = 0.0
    default_opm = 10.0
    default_de = 5.0
    default_pe = 150.0
    default_pb = 30.0
    default_dividend = 0.0
    default_interest = 1.0

elif dividend_preset:

    default_roe = 10.0
    default_roce = 10.0
    default_revenue_cagr = 5.0
    default_pat_cagr = 5.0
    default_fcf = 0.0
    default_opm = 5.0
    default_de = 5.0
    default_pe = 100.0
    default_pb = 20.0
    default_dividend = 2.0
    default_interest = 1.0

elif debt_free_preset:

    default_roe = 10.0
    default_roce = 10.0
    default_revenue_cagr = 5.0
    default_pat_cagr = 5.0
    default_fcf = 0.0
    default_opm = 5.0
    default_de = 0.0
    default_pe = 150.0
    default_pb = 30.0
    default_dividend = 0.0
    default_interest = 3.0

elif turnaround_preset:

    default_roe = 0.0
    default_roce = 0.0
    default_revenue_cagr = 0.0
    default_pat_cagr = 0.0
    default_fcf = 0.0
    default_opm = 0.0
    default_de = 10.0
    default_pe = 200.0
    default_pb = 50.0
    default_dividend = 0.0
    default_interest = 1.0


# ---------------------------------------------------------------------
# Screening filters
# ---------------------------------------------------------------------

st.subheader("Screening Filters")

filter_col1, filter_col2 = st.columns(2)


with filter_col1:

    roe_min = st.slider(
        "ROE — Minimum (%)",
        min_value=-100.0,
        max_value=500.0,
        value=float(default_roe),
        step=1.0,
    )

    de_max = st.slider(
        "D/E — Maximum",
        min_value=0.0,
        max_value=20.0,
        value=min(
            float(default_de),
            20.0,
        ),
        step=0.1,
    )

    fcf_min = st.slider(
        "FCF — Minimum (₹ Cr)",
        min_value=-100000.0,
        max_value=100000.0,
        value=float(default_fcf),
        step=100.0,
    )

    revenue_cagr_min = st.slider(
        "Revenue CAGR — Minimum (%)",
        min_value=-100.0,
        max_value=100.0,
        value=float(default_revenue_cagr),
        step=1.0,
    )

    pat_cagr_min = st.slider(
        "PAT CAGR — Minimum (%)",
        min_value=-100.0,
        max_value=100.0,
        value=float(default_pat_cagr),
        step=1.0,
    )

    roce_min = st.slider(
        "ROCE — Minimum (%)",
        min_value=-100.0,
        max_value=500.0,
        value=float(default_roce),
        step=1.0,
    )


with filter_col2:

    opm_min = st.slider(
        "OPM — Minimum (%)",
        min_value=-100.0,
        max_value=100.0,
        value=float(default_opm),
        step=1.0,
    )

    pe_max = st.slider(
        "P/E — Maximum",
        min_value=0.0,
        max_value=200.0,
        value=float(default_pe),
        step=1.0,
    )

    pb_max = st.slider(
        "P/B — Maximum",
        min_value=0.0,
        max_value=100.0,
        value=float(default_pb),
        step=1.0,
    )

    dividend_min = st.slider(
        "Dividend Yield — Minimum (%)",
        min_value=0.0,
        max_value=20.0,
        value=float(default_dividend),
        step=0.5,
    )

    interest_min = st.slider(
        "Interest Coverage — Minimum",
        min_value=0.0,
        max_value=100.0,
        value=float(default_interest),
        step=0.5,
    )


# ---------------------------------------------------------------------
# Sector filter
# ---------------------------------------------------------------------

sector_values = sorted(
    [
        str(value)
        for value in screening_df["sector"].dropna().unique()
        if str(value).strip()
    ]
)

selected_sectors = st.multiselect(
    "Sector",
    options=sector_values,
    default=[],
)


# ---------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------

filtered_df = screening_df.copy()


def apply_min_filter(
    df,
    column,
    minimum,
):
    """
    Apply a minimum filter while retaining rows
    where the metric is available.
    """

    return df[
        df[column].notna()
        & (
            df[column]
            >= minimum
        )
    ].copy()


def apply_max_filter(
    df,
    column,
    maximum,
):
    """
    Apply a maximum filter while retaining rows
    where the metric is available.
    """

    return df[
        df[column].notna()
        & (
            df[column]
            <= maximum
        )
    ].copy()


filtered_df = apply_min_filter(
    filtered_df,
    "return_on_equity",
    roe_min,
)

filtered_df = apply_max_filter(
    filtered_df,
    "debt_to_equity",
    de_max,
)

filtered_df = apply_min_filter(
    filtered_df,
    "free_cash_flow",
    fcf_min,
)

filtered_df = apply_min_filter(
    filtered_df,
    "revenue_cagr",
    revenue_cagr_min,
)

filtered_df = apply_min_filter(
    filtered_df,
    "pat_cagr",
    pat_cagr_min,
)

filtered_df = apply_min_filter(
    filtered_df,
    "return_on_capital_employed",
    roce_min,
)

filtered_df = apply_min_filter(
    filtered_df,
    "operating_profit_margin",
    opm_min,
)

filtered_df = apply_max_filter(
    filtered_df,
    "pe_ratio",
    pe_max,
)

filtered_df = apply_max_filter(
    filtered_df,
    "pb_ratio",
    pb_max,
)

filtered_df = apply_min_filter(
    filtered_df,
    "dividend_yield",
    dividend_min,
)

filtered_df = apply_min_filter(
    filtered_df,
    "interest_coverage",
    interest_min,
)


if selected_sectors:

    filtered_df = filtered_df[
        filtered_df["sector"].isin(
            selected_sectors
        )
    ].copy()


# ---------------------------------------------------------------------
# Composite quality score
# ---------------------------------------------------------------------

if not filtered_df.empty:

    scoring_rows = []

    for _, row in filtered_df.iterrows():

        required_metrics = [
            row["return_on_equity"],
            row["return_on_capital_employed"],
            row["revenue_cagr"],
            row["free_cash_flow"],
            row["operating_cash_flow_margin"],
            row["debt_to_equity"],
        ]

        if any(
            pd.isna(value)
            for value in required_metrics
        ):
            continue

        scoring_rows.append(
            {
                "company_id": row["company_id"],
                "company": row["company"],
                "return_on_equity": float(
                    row["return_on_equity"]
                ),
                "return_on_capital_employed": float(
                    row[
                        "return_on_capital_employed"
                    ]
                ),
                "revenue_cagr": float(
                    row["revenue_cagr"]
                ),
                "free_cash_flow": float(
                    row["free_cash_flow"]
                ),
                "operating_cash_flow_margin": float(
                    row[
                        "operating_cash_flow_margin"
                    ]
                ),
                "debt_to_equity": float(
                    row["debt_to_equity"]
                ),
            }
        )

    if scoring_rows:

        scoring_df = pd.DataFrame(
            scoring_rows
        )

        scored_df = calculate_quality_score(
            scoring_df
        )

        score_columns = [
            "company_id",
            "composite_quality_score",
        ]

        score_lookup = (
            scored_df[score_columns]
            .drop_duplicates(
                subset=["company_id"]
            )
        )

        filtered_df = filtered_df.merge(
            score_lookup,
            on="company_id",
            how="left",
        )

    else:

        filtered_df[
            "composite_quality_score"
        ] = np.nan

else:

    filtered_df[
        "composite_quality_score"
    ] = np.nan


# ---------------------------------------------------------------------
# Screening results
# ---------------------------------------------------------------------

st.divider()

st.subheader("Screening Results")

st.info(
    f"{len(filtered_df)} companies match your filters."
)


if filtered_df.empty:

    st.warning(
        "No companies match the selected criteria. "
        "Try relaxing one or more filters."
    )

    st.stop()


# ---------------------------------------------------------------------
# Sort results
# ---------------------------------------------------------------------

if (
    "composite_quality_score"
    in filtered_df.columns
):

    filtered_df = filtered_df.sort_values(
        by=[
            "composite_quality_score",
            "return_on_equity",
        ],
        ascending=[
            False,
            False,
        ],
        na_position="last",
    )


# ---------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------

display_columns = [
    "company_id",
    "company",
    "sector",
    "return_on_equity",
    "return_on_capital_employed",
    "revenue_cagr",
    "pat_cagr",
    "free_cash_flow",
    "debt_to_equity",
    "pe_ratio",
    "pb_ratio",
    "dividend_yield",
    "interest_coverage",
    "composite_quality_score",
]


available_display_columns = [
    column
    for column in display_columns
    if column in filtered_df.columns
]


display_df = filtered_df[
    available_display_columns
].copy()


# ---------------------------------------------------------------------
# Rename columns
# ---------------------------------------------------------------------

display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company": "Company",
        "sector": "Sector",
        "return_on_equity": "ROE (%)",
        "return_on_capital_employed": "ROCE (%)",
        "revenue_cagr": "Revenue CAGR (%)",
        "pat_cagr": "PAT CAGR (%)",
        "free_cash_flow": "FCF (₹ Cr)",
        "debt_to_equity": "D/E",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield": "Dividend Yield (%)",
        "interest_coverage": "Interest Coverage",
        "composite_quality_score": "Quality Score",
    }
)


# ---------------------------------------------------------------------
# Format numerical values
# ---------------------------------------------------------------------

percentage_columns = [
    "ROE (%)",
    "ROCE (%)",
    "Revenue CAGR (%)",
    "PAT CAGR (%)",
    "Dividend Yield (%)",
]

decimal_columns = [
    "D/E",
    "P/E",
    "P/B",
    "Interest Coverage",
    "Quality Score",
]

currency_columns = [
    "FCF (₹ Cr)",
]


for column in percentage_columns:

    if column in display_df.columns:

        display_df[column] = display_df[
            column
        ].round(2)


for column in decimal_columns:

    if column in display_df.columns:

        display_df[column] = display_df[
            column
        ].round(2)


for column in currency_columns:

    if column in display_df.columns:

        display_df[column] = display_df[
            column
        ].round(2)


# ---------------------------------------------------------------------
# Results table
# ---------------------------------------------------------------------

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# Download results
# ---------------------------------------------------------------------

csv_data = display_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="Download Screening Results CSV",
    data=csv_data,
    file_name=(
        f"nifty100_screener_{selected_year}.csv"
    ),
    mime="text/csv",
    width="stretch",
)


# ---------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------

st.divider()

st.subheader("Screening Summary")

summary_col1, summary_col2, summary_col3, summary_col4 = (
    st.columns(4)
)


with summary_col1:

    st.metric(
        "Matching Companies",
        len(filtered_df),
    )


with summary_col2:

    if (
        "return_on_equity"
        in filtered_df.columns
    ):

        value = filtered_df[
            "return_on_equity"
        ].mean()

        st.metric(
            "Average ROE",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )


with summary_col3:

    if (
        "revenue_cagr"
        in filtered_df.columns
    ):

        value = filtered_df[
            "revenue_cagr"
        ].mean()

        st.metric(
            "Average Revenue CAGR",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}%",
        )


with summary_col4:

    if (
        "composite_quality_score"
        in filtered_df.columns
    ):

        value = filtered_df[
            "composite_quality_score"
        ].max()

        st.metric(
            "Highest Quality Score",
            "N/A"
            if pd.isna(value)
            else f"{value:.2f}",
        )


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

with st.expander(
    "Screening Methodology"
):

    st.markdown(
        """
### Screening methodology

The screener combines:

- **ROE** — Return on Equity
- **ROCE** — Return on Capital Employed
- **Revenue CAGR** — 5-year revenue growth
- **PAT CAGR** — 5-year profit growth
- **FCF** — Free Cash Flow
- **OPM** — Operating Profit Margin
- **D/E** — Debt-to-Equity
- **P/E** — Price-to-Earnings
- **P/B** — Price-to-Book
- **Dividend Yield**
- **Interest Coverage**

### Composite Quality Score

The composite score reuses the Sprint 3 scoring engine.

Weights:

| Metric | Weight |
|---|---:|
| ROE | 25% |
| ROCE | 20% |
| Revenue CAGR | 20% |
| Free Cash Flow | 15% |
| Operating Cash Flow Margin | 10% |
| Debt-to-Equity | 10% |

Higher values are preferred for the positive metrics,
while lower debt-to-equity receives a higher score.

Companies without all six metrics required by the
quality scoring engine receive no composite score,
but remain visible in the screening results.
        """
    )