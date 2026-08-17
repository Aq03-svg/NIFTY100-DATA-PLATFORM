"""
Shared database loader for the Streamlit dashboard.

Provides cached access to the NIFTY 100 SQLite database.
"""

from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st


# ---------------------------------------------------------------------
# Database configuration
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "db" / "nifty100.db"


def _get_connection():
    """
    Create a SQLite database connection.
    """
    return sqlite3.connect(DB_PATH)


# ---------------------------------------------------------------------
# Companies
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_companies():
    """
    Return all companies.
    """

    query = """
        SELECT
            id AS company_id,
            company_logo,
            company_name,
            chart_link,
            about_company,
            website,
            nse_profile,
            bse_profile,
            face_value,
            book_value,
            roce_percentage,
            roe_percentage
        FROM companies
        ORDER BY company_name
    """

    with _get_connection() as conn:
        return pd.read_sql_query(query, conn)


# ---------------------------------------------------------------------
# Financial Ratios
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """
    Return financial ratios for a company.

    Parameters
    ----------
    ticker : str
        Company ID / ticker.

    year : str or int, optional
        Financial year.
        If omitted, all available years are returned.
    """

    query = """
        SELECT
            fr.company_id,
            c.company_name,
            fr.year,
            fr.net_profit_margin_pct,
            fr.operating_profit_margin_pct,
            fr.return_on_equity_pct,
            c.roce_percentage,
            fr.debt_to_equity,
            fr.interest_coverage,
            fr.asset_turnover,
            fr.free_cash_flow_cr,
            fr.capex_cr,
            fr.earnings_per_share,
            fr.book_value_per_share,
            fr.dividend_payout_ratio_pct,
            fr.total_debt_cr,
            fr.cash_from_operations_cr
        FROM financial_ratios fr
        LEFT JOIN companies c
            ON fr.company_id = c.id
        WHERE fr.company_id = ?
    """

    params = [ticker]

    if year is not None:
        query += " AND fr.year = ?"
        params.append(str(year))

    query += " ORDER BY fr.year"

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=params,
        )


# ---------------------------------------------------------------------
# Profit & Loss
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pl(ticker):
    """
    Return Profit & Loss data for a company.
    """

    query = """
        SELECT
            pl.company_id,
            c.company_name,
            pl.year,
            pl.sales,
            pl.expenses,
            pl.operating_profit,
            pl.opm_percentage,
            pl.other_income,
            pl.interest,
            pl.depreciation,
            pl.profit_before_tax,
            pl.tax_percentage,
            pl.net_profit,
            pl.eps,
            pl.dividend_payout
        FROM profit_loss pl
        LEFT JOIN companies c
            ON pl.company_id = c.id
        WHERE pl.company_id = ?
        ORDER BY pl.year
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[ticker],
        )


# ---------------------------------------------------------------------
# Balance Sheet
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_bs(ticker):
    """
    Return Balance Sheet data for a company.
    """

    query = """
        SELECT
            bs.company_id,
            c.company_name,
            bs.year,
            bs.equity_capital,
            bs.reserves,
            bs.borrowings,
            bs.other_liabilities,
            bs.total_liabilities,
            bs.fixed_assets,
            bs.cwip,
            bs.investments,
            bs.other_asset,
            bs.total_assets
        FROM balance_sheet bs
        LEFT JOIN companies c
            ON bs.company_id = c.id
        WHERE bs.company_id = ?
        ORDER BY bs.year
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[ticker],
        )


# ---------------------------------------------------------------------
# Cash Flow
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_cf(ticker):
    """
    Return Cash Flow data for a company.
    """

    query = """
        SELECT
            cf.company_id,
            c.company_name,
            cf.year,
            cf.operating_activity,
            cf.investing_activity,
            cf.financing_activity,
            cf.net_cash_flow
        FROM cash_flow cf
        LEFT JOIN companies c
            ON cf.company_id = c.id
        WHERE cf.company_id = ?
        ORDER BY cf.year
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[ticker],
        )


# ---------------------------------------------------------------------
# Sectors
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_sectors():
    """
    Return sector information for all companies.
    """

    query = """
        SELECT
            s.company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category
        FROM sectors s
        LEFT JOIN companies c
            ON s.company_id = c.id
        ORDER BY s.broad_sector, c.company_name
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
        )


# ---------------------------------------------------------------------
# Peer Groups
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_peers(group_name):
    """
    Return companies belonging to a peer group.

    Parameters
    ----------
    group_name : str
        Peer group name.
    """

    query = """
        SELECT
            pg.peer_group_name,
            pg.company_id,
            c.company_name,
            pg.is_benchmark
        FROM peer_groups pg
        LEFT JOIN companies c
            ON pg.company_id = c.id
        WHERE pg.peer_group_name = ?
        ORDER BY
            pg.is_benchmark DESC,
            c.company_name
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[group_name],
        )


# ---------------------------------------------------------------------
# Pros and Cons
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_pros_and_cons(ticker):
    """
    Return pros and cons for a company.

    Parameters
    ----------
    ticker : str
        Company ID / ticker.

    Returns
    -------
    pandas.DataFrame
        Columns:
            company_id
            company_name
            pros
            cons
    """

    query = """
        SELECT
            pc.company_id,
            c.company_name,
            pc.pros,
            pc.cons
        FROM prosandcons pc
        LEFT JOIN companies c
            ON pc.company_id = c.id
        WHERE pc.company_id = ?
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[ticker],
        )


# ---------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_analysis(ticker):
    """
    Return company analysis metrics.
    """

    query = """
        SELECT
            a.company_id,
            c.company_name,
            a.compounded_sales_growth,
            a.compounded_profit_growth,
            a.stock_price_cagr,
            a.roe
        FROM analysis a
        LEFT JOIN companies c
            ON a.company_id = c.id
        WHERE a.company_id = ?
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[ticker],
        )


# ---------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------

@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return market and valuation data for a company.
    """

    query = """
        SELECT
            mc.company_id,
            c.company_name,
            mc.year,
            mc.market_cap_crore,
            mc.enterprise_value_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct
        FROM market_cap mc
        LEFT JOIN companies c
            ON mc.company_id = c.id
        WHERE mc.company_id = ?
        ORDER BY mc.year
    """

    with _get_connection() as conn:
        return pd.read_sql_query(
            query,
            conn,
            params=[ticker],
        )


# ---------------------------------------------------------------------
# Simple standalone test
# ---------------------------------------------------------------------

if __name__ == "__main__":

    print("Database:", DB_PATH)
    print("Database exists:", DB_PATH.exists())

    companies = get_companies()

    print("\nCompanies:")
    print(companies.head())

    if not companies.empty:

        ticker = companies.iloc[0]["company_id"]

        print(f"\nTesting ticker: {ticker}")

        print("\nFinancial Ratios:")
        print(get_ratios(ticker).head())

        print("\nProfit & Loss:")
        print(get_pl(ticker).head())

        print("\nBalance Sheet:")
        print(get_bs(ticker).head())

        print("\nCash Flow:")
        print(get_cf(ticker).head())

        print("\nPros and Cons:")
        print(get_pros_and_cons(ticker).head())

        print("\nValuation:")
        print(get_valuation(ticker).head())

    print("\nDatabase loader test completed.")