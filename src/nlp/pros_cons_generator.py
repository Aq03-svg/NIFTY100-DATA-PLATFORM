"""
Sprint 5 - Day 30
NLP Auto Pros/Cons Generator

Generates rule-based investment pros and cons for all companies
available in the NIFTY100 database.

Output:
    output/pros_cons_generated.csv

Columns:
    company_id
    type
    rule_id
    text
    confidence_pct

Only signals with confidence > 60% are included.

The implementation uses the existing SQLite database:
    db/nifty100.db
"""

from pathlib import Path
import sqlite3
import logging
import math

import pandas as pd


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_FILE = PROJECT_ROOT / "db" / "nifty100.db"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "pros_cons_generated.csv"


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------

CONFIDENCE_THRESHOLD = 60


# ---------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------

def safe_float(value):
    """
    Convert a value to float.

    Returns None when the value is missing, invalid, or NaN.
    """

    if value is None:
        return None

    try:
        value = float(value)

        if math.isnan(value):
            return None

        return value

    except (TypeError, ValueError):
        return None


def parse_year(value):
    """
    Extract the calendar year from values such as:

        Mar 2024
        Dec 2012
        TTM

    Returns:
        int | None
    """

    if value is None:
        return None

    text = str(value).strip()

    if len(text) >= 4 and text[-4:].isdigit():
        return int(text[-4:])

    return None


def deduplicate_yearly_data(
    df,
    company_col="company_id",
    year_col="year",
):
    """
    Keep one deterministic record per company/year.

    The source database contains duplicate company/year records.
    Since there is no source-level identifier that distinguishes
    those records, the first record is retained after stable sorting.
    """

    df = df.copy()

    df["_calendar_year"] = df[year_col].apply(parse_year)

    df = df[
        df["_calendar_year"].notna()
    ].copy()

    df = (
        df.sort_values(
            [company_col, "_calendar_year"],
            kind="stable",
        )
        .drop_duplicates(
            subset=[
                company_col,
                "_calendar_year",
            ],
            keep="first",
        )
        .sort_values(
            [company_col, "_calendar_year"],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    return df


def latest_rows(df):
    """
    Return the latest calendar-year row for every company.
    """

    data = deduplicate_yearly_data(df)

    return (
        data.sort_values(
            [
                "company_id",
                "_calendar_year",
            ],
            kind="stable",
        )
        .groupby(
            "company_id",
            as_index=False,
        )
        .tail(1)
        .reset_index(drop=True)
    )


def get_company_history(df, company_id):
    """
    Return chronological history for one company.
    """

    data = df[
        df["company_id"] == company_id
    ].copy()

    if data.empty:
        return data

    data = deduplicate_yearly_data(data)

    return (
        data.sort_values(
            "_calendar_year",
            kind="stable",
        )
        .reset_index(drop=True)
    )


def calculate_cagr(
    start_value,
    end_value,
    years,
):
    """
    Calculate CAGR in percentage terms.

    Formula:
        ((Ending / Beginning) ** (1 / Years) - 1) * 100
    """

    start_value = safe_float(start_value)
    end_value = safe_float(end_value)

    if (
        start_value is None
        or end_value is None
    ):
        return None

    if years is None or years <= 0:
        return None

    if (
        start_value <= 0
        or end_value <= 0
    ):
        return None

    return (
        (
            (end_value / start_value)
            ** (1 / years)
        ) - 1
    ) * 100


def consecutive_positive(
    values,
    minimum_years,
):
    """
    Return True when the latest minimum_years
    observations are positive.
    """

    if len(values) < minimum_years:
        return False

    values = values[-minimum_years:]

    return all(
        safe_float(value) is not None
        and safe_float(value) > 0
        for value in values
    )


def consecutive_negative(
    values,
    minimum_years,
):
    """
    Return True when the latest minimum_years
    observations are negative.
    """

    if len(values) < minimum_years:
        return False

    values = values[-minimum_years:]

    return all(
        safe_float(value) is not None
        and safe_float(value) < 0
        for value in values
    )


def strictly_increasing(
    values,
    minimum_years,
):
    """
    Check whether the latest values strictly increase.
    """

    if len(values) < minimum_years:
        return False

    values = values[-minimum_years:]

    numeric = [
        safe_float(value)
        for value in values
    ]

    if any(
        value is None
        for value in numeric
    ):
        return False

    return all(
        numeric[i] < numeric[i + 1]
        for i in range(len(numeric) - 1)
    )


def strictly_decreasing(
    values,
    minimum_years,
):
    """
    Check whether the latest values strictly decrease.
    """

    if len(values) < minimum_years:
        return False

    values = values[-minimum_years:]

    numeric = [
        safe_float(value)
        for value in values
    ]

    if any(
        value is None
        for value in numeric
    ):
        return False

    return all(
        numeric[i] > numeric[i + 1]
        for i in range(len(numeric) - 1)
    )


# ---------------------------------------------------------------------
# Database Loading
# ---------------------------------------------------------------------

def load_database():
    """
    Load all required datasets from SQLite.
    """

    if not DB_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DB_FILE}"
        )

    connection = sqlite3.connect(DB_FILE)

    try:

        companies = pd.read_sql_query(
            """
            SELECT *
            FROM companies
            """,
            connection,
        )

        ratios = pd.read_sql_query(
            """
            SELECT *
            FROM financial_ratios
            """,
            connection,
        )

        profit_loss = pd.read_sql_query(
            """
            SELECT *
            FROM profit_loss
            """,
            connection,
        )

        cash_flow = pd.read_sql_query(
            """
            SELECT *
            FROM cash_flow
            """,
            connection,
        )

        balance_sheet = pd.read_sql_query(
            """
            SELECT *
            FROM balance_sheet
            """,
            connection,
        )

        market_cap = pd.read_sql_query(
            """
            SELECT *
            FROM market_cap
            """,
            connection,
        )

        sectors = pd.read_sql_query(
            """
            SELECT *
            FROM sectors
            """,
            connection,
        )

    finally:
        connection.close()

    logger.info(
        "Loaded database datasets: "
        "companies=%d, ratios=%d, profit_loss=%d, "
        "cash_flow=%d, balance_sheet=%d, "
        "market_cap=%d, sectors=%d",
        len(companies),
        len(ratios),
        len(profit_loss),
        len(cash_flow),
        len(balance_sheet),
        len(market_cap),
        len(sectors),
    )

    return (
        companies,
        ratios,
        profit_loss,
        cash_flow,
        balance_sheet,
        market_cap,
        sectors,
    )


# ---------------------------------------------------------------------
# Main Rule Engine
# ---------------------------------------------------------------------

def generate_for_company(
    company_id,
    companies,
    ratios,
    profit_loss,
    cash_flow,
    balance_sheet,
    market_cap,
    sectors,
):
    """
    Generate all applicable pros and cons for one company.
    """

    pros = []
    cons = []

    ratio_hist = get_company_history(
        ratios,
        company_id,
    )

    pnl_hist = get_company_history(
        profit_loss,
        company_id,
    )

    cash_hist = get_company_history(
        cash_flow,
        company_id,
    )

    bs_hist = get_company_history(
        balance_sheet,
        company_id,
    )

    market_hist = get_company_history(
        market_cap,
        company_id,
    )

    sector_row = sectors[
        sectors["company_id"] == company_id
    ]

    # -------------------------------------------------------------
    # Company-level ROCE
    #
    # financial_ratios does not contain ROCE.
    # The companies table contains roce_percentage.
    # -------------------------------------------------------------

    company_row = companies[
        companies["id"] == company_id
    ]

    company_roce = None

    if not company_row.empty:

        company_roce = safe_float(
            company_row.iloc[0][
                "roce_percentage"
            ]
        )

    broad_sector = ""

    if not sector_row.empty:

        broad_sector = str(
            sector_row.iloc[0][
                "broad_sector"
            ]
        ).strip()

    is_financial = (
        broad_sector.lower()
        in {
            "financials",
            "financial services",
            "banking",
            "finance",
        }
    )

    # -------------------------------------------------------------
    # Latest records
    # -------------------------------------------------------------

    latest_ratio = (
        ratio_hist.iloc[-1]
        if not ratio_hist.empty
        else None
    )

    latest_pnl = (
        pnl_hist.iloc[-1]
        if not pnl_hist.empty
        else None
    )

    latest_cash = (
        cash_hist.iloc[-1]
        if not cash_hist.empty
        else None
    )

    latest_bs = (
        bs_hist.iloc[-1]
        if not bs_hist.empty
        else None
    )

    latest_market = (
        market_hist.iloc[-1]
        if not market_hist.empty
        else None
    )

    # =============================================================
    # PRO RULE 1
    # ROE > 20% sustained for 3+ years
    # =============================================================

    if not ratio_hist.empty:

        roe_values = ratio_hist[
            "return_on_equity_pct"
        ].tolist()

        if consecutive_positive(
            roe_values,
            3,
        ):

            recent_roe = roe_values[-3:]

            if all(
                safe_float(value) > 20
                for value in recent_roe
            ):

                pros.append(
                    (
                        "PRO1",
                        "Consistently high return on equity "
                        "above 20% demonstrates exceptional "
                        "capital efficiency",
                        90,
                    )
                )

    # =============================================================
    # PRO RULE 2
    # FCF positive for 5+ consecutive years
    # =============================================================

    if not ratio_hist.empty:

        fcf_values = ratio_hist[
            "free_cash_flow_cr"
        ].tolist()

        if consecutive_positive(
            fcf_values,
            5,
        ):

            pros.append(
                (
                    "PRO2",
                    "Strong free cash flow generation over "
                    "5 years signals healthy business fundamentals",
                    90,
                )
            )

    # =============================================================
    # PRO RULE 3
    # D/E = 0 in latest year
    # =============================================================

    if latest_ratio is not None:

        de = safe_float(
            latest_ratio[
                "debt_to_equity"
            ]
        )

        if (
            de is not None
            and de == 0
        ):

            pros.append(
                (
                    "PRO3",
                    "Debt-free balance sheet provides "
                    "financial flexibility and eliminates "
                    "interest burden",
                    95,
                )
            )

    # =============================================================
    # PRO RULE 4
    # Revenue CAGR > 15% over 5 years
    # =============================================================

    if len(pnl_hist) >= 6:

        recent = pnl_hist.tail(6)

        start = recent.iloc[0]["sales"]
        end = recent.iloc[-1]["sales"]

        cagr = calculate_cagr(
            start,
            end,
            5,
        )

        if (
            cagr is not None
            and cagr > 15
        ):

            pros.append(
                (
                    "PRO4",
                    "Revenue growing at above 15% CAGR "
                    "over 5 years reflects strong "
                    "business momentum",
                    95,
                )
            )

    # =============================================================
    # PRO RULE 5
    # OPM > 25% in latest year
    # =============================================================

    if latest_ratio is not None:

        opm = safe_float(
            latest_ratio[
                "operating_profit_margin_pct"
            ]
        )

        if (
            opm is not None
            and opm > 25
        ):

            pros.append(
                (
                    "PRO5",
                    "Operating profit margin above 25% "
                    "indicates strong pricing power and "
                    "cost discipline",
                    90,
                )
            )

    # =============================================================
    # PRO RULE 6
    # PAT CAGR > 20% over 5 years
    # =============================================================

    if len(pnl_hist) >= 6:

        recent = pnl_hist.tail(6)

        start = recent.iloc[0]["net_profit"]
        end = recent.iloc[-1]["net_profit"]

        cagr = calculate_cagr(
            start,
            end,
            5,
        )

        if (
            cagr is not None
            and cagr > 20
        ):

            pros.append(
                (
                    "PRO6",
                    "Net profit compounding at above "
                    "20% over 5 years creates significant "
                    "shareholder value",
                    95,
                )
            )

    # =============================================================
    # PRO RULE 7
    # ICR > 10 OR Debt Free
    # =============================================================

    if latest_ratio is not None:

        icr = safe_float(
            latest_ratio[
                "interest_coverage"
            ]
        )

        de = safe_float(
            latest_ratio[
                "debt_to_equity"
            ]
        )

        if (
            (
                icr is not None
                and icr > 10
            )
            or (
                de is not None
                and de == 0
            )
        ):

            pros.append(
                (
                    "PRO7",
                    "Very high interest coverage ratio "
                    "reflects negligible financial stress "
                    "from debt servicing",
                    90,
                )
            )

    # =============================================================
    # PRO RULE 8
    # Dividend Yield > 2% with FCF positive
    # =============================================================

    if (
        latest_market is not None
        and latest_ratio is not None
    ):

        dividend_yield = safe_float(
            latest_market[
                "dividend_yield_pct"
            ]
        )

        fcf = safe_float(
            latest_ratio[
                "free_cash_flow_cr"
            ]
        )

        if (
            dividend_yield is not None
            and dividend_yield > 2
            and fcf is not None
            and fcf > 0
        ):

            pros.append(
                (
                    "PRO8",
                    "Consistent dividend yield above 2% "
                    "backed by positive free cash flow",
                    90,
                )
            )

    # =============================================================
    # PRO RULE 9
    # EPS CAGR > 15% over 5 years
    # =============================================================

    if len(ratio_hist) >= 6:

        recent = ratio_hist.tail(6)

        start = safe_float(
            recent.iloc[0][
                "earnings_per_share"
            ]
        )

        end = safe_float(
            recent.iloc[-1][
                "earnings_per_share"
            ]
        )

        cagr = calculate_cagr(
            start,
            end,
            5,
        )

        if (
            cagr is not None
            and cagr > 15
        ):

            pros.append(
                (
                    "PRO9",
                    "Earnings per share growing above "
                    "15% CAGR indicates strong earnings "
                    "quality and compounding",
                    90,
                )
            )

    # =============================================================
    # PRO RULE 10
    # ROE improving for 3 consecutive years
    # =============================================================

    if not ratio_hist.empty:

        roe_values = ratio_hist[
            "return_on_equity_pct"
        ].tolist()

        if strictly_increasing(
            roe_values,
            3,
        ):

            pros.append(
                (
                    "PRO10",
                    "Return on equity improving for "
                    "3 consecutive years shows "
                    "strengthening business quality",
                    85,
                )
            )

    # =============================================================
    # PRO RULE 11
    # Revenue CAGR > PAT CAGR
    #
    # The implementation follows the literal condition
    # specified for this rule.
    # =============================================================

    if len(pnl_hist) >= 6:

        recent = pnl_hist.tail(6)

        revenue_cagr = calculate_cagr(
            recent.iloc[0]["sales"],
            recent.iloc[-1]["sales"],
            5,
        )

        pat_cagr = calculate_cagr(
            recent.iloc[0]["net_profit"],
            recent.iloc[-1]["net_profit"],
            5,
        )

        if (
            revenue_cagr is not None
            and pat_cagr is not None
            and revenue_cagr > pat_cagr
        ):

            pros.append(
                (
                    "PRO11",
                    "Revenue growing slower than profits "
                    "shows improving operating leverage "
                    "and scale benefits",
                    80,
                )
            )

    # =============================================================
    # PRO RULE 12
    # Assets growing with declining debt
    # =============================================================

    if len(bs_hist) >= 2:

        assets = bs_hist[
            "total_assets"
        ].tolist()

        debt = bs_hist[
            "borrowings"
        ].tolist()

        if (
            safe_float(assets[-1]) is not None
            and safe_float(assets[-2]) is not None
            and safe_float(debt[-1]) is not None
            and safe_float(debt[-2]) is not None
            and assets[-1] > assets[-2]
            and debt[-1] < debt[-2]
        ):

            pros.append(
                (
                    "PRO12",
                    "Growing asset base funded by internal "
                    "accruals reflects self-sustaining growth",
                    80,
                )
            )

    # =============================================================
    # CON RULE 1
    # D/E > 2 for non-financial companies
    # =============================================================

    if (
        not is_financial
        and latest_ratio is not None
    ):

        de = safe_float(
            latest_ratio[
                "debt_to_equity"
            ]
        )

        if (
            de is not None
            and de > 2
        ):

            cons.append(
                (
                    "CON1",
                    f"Debt-to-equity ratio of {de:.2f} "
                    "is elevated for a non-financial "
                    "company and warrants monitoring",
                    95,
                )
            )

    # =============================================================
    # CON RULE 2
    # FCF negative for 3 consecutive years
    # =============================================================

    if not ratio_hist.empty:

        fcf_values = ratio_hist[
            "free_cash_flow_cr"
        ].tolist()

        if consecutive_negative(
            fcf_values,
            3,
        ):

            cons.append(
                (
                    "CON2",
                    "Free cash flow negative for 3 "
                    "consecutive years raises concern "
                    "about cash generation quality",
                    90,
                )
            )

    # =============================================================
    # CON RULE 3
    # OPM declining for 3 consecutive years
    # =============================================================

    if not ratio_hist.empty:

        opm_values = ratio_hist[
            "operating_profit_margin_pct"
        ].tolist()

        if strictly_decreasing(
            opm_values,
            3,
        ):

            cons.append(
                (
                    "CON3",
                    "Operating margins declining for "
                    "3 consecutive years suggest pricing "
                    "or cost pressure",
                    85,
                )
            )

    # =============================================================
    # CON RULE 4
    # Net profit negative in latest year
    # =============================================================

    if latest_pnl is not None:

        net_profit = safe_float(
            latest_pnl["net_profit"]
        )

        if (
            net_profit is not None
            and net_profit < 0
        ):

            cons.append(
                (
                    "CON4",
                    "Company reported a net loss in "
                    "the most recent financial year",
                    98,
                )
            )

    # =============================================================
    # CON RULE 5
    # Revenue declining for 2+ years
    # =============================================================

    if not pnl_hist.empty:

        sales_values = pnl_hist[
            "sales"
        ].tolist()

        if len(sales_values) >= 3:

            recent = sales_values[-3:]

            if (
                safe_float(recent[0]) is not None
                and safe_float(recent[1]) is not None
                and safe_float(recent[2]) is not None
                and recent[0]
                > recent[1]
                > recent[2]
            ):

                cons.append(
                    (
                        "CON5",
                        "Revenue contraction over "
                        "2 consecutive years indicates "
                        "demand weakness or market share loss",
                        85,
                    )
                )

    # =============================================================
    # CON RULE 6
    # ICR < 1.5
    # =============================================================

    if latest_ratio is not None:

        icr = safe_float(
            latest_ratio[
                "interest_coverage"
            ]
        )

        if (
            icr is not None
            and icr < 1.5
        ):

            cons.append(
                (
                    "CON6",
                    "Interest coverage ratio below 1.5x "
                    "indicates the company is at risk "
                    "of not meeting its debt obligations",
                    95,
                )
            )

    # =============================================================
    # CON RULE 7
    # Dividend payout > 100%
    # =============================================================

    if latest_ratio is not None:

        payout = safe_float(
            latest_ratio[
                "dividend_payout_ratio_pct"
            ]
        )

        if (
            payout is not None
            and payout > 100
        ):

            cons.append(
                (
                    "CON7",
                    "Dividend payout ratio above 100% "
                    "means the company is paying dividends "
                    "from reserves, which is unsustainable",
                    95,
                )
            )

    # =============================================================
    # CON RULE 8
    # D/E rising for 3 consecutive years
    # =============================================================

    if not ratio_hist.empty:

        de_values = ratio_hist[
            "debt_to_equity"
        ].tolist()

        if strictly_increasing(
            de_values,
            3,
        ):

            cons.append(
                (
                    "CON8",
                    "Rising debt-to-equity ratio over "
                    "3 years suggests increasing "
                    "financial leverage risk",
                    85,
                )
            )

    # =============================================================
    # CON RULE 9
    # EPS declining for 3 consecutive years
    # =============================================================

    if not ratio_hist.empty:

        eps_values = ratio_hist[
            "earnings_per_share"
        ].tolist()

        if strictly_decreasing(
            eps_values,
            3,
        ):

            cons.append(
                (
                    "CON9",
                    "Earnings per share declining for "
                    "3 consecutive years reflects "
                    "deteriorating profitability",
                    90,
                )
            )

    # =============================================================
    # CON RULE 10
    # ROCE < 10%
    #
    # ROCE is sourced from the companies table because
    # financial_ratios does not contain a ROCE column.
    # =============================================================

    if (
        company_roce is not None
        and company_roce < 10
    ):

        cons.append(
            (
                "CON10",
                "Return on capital employed below 10% "
                "suggests the business is not generating "
                "sufficient returns on invested capital",
                90,
            )
        )

    # =============================================================
    # CON RULE 11
    # Net Debt > 3x EBITDA
    #
    # The current database schema does not contain a
    # cash and cash-equivalents field.
    #
    # Therefore exact Net Debt cannot be calculated
    # reliably.
    #
    # We intentionally do NOT substitute total debt
    # for net debt.
    #
    # Rule will remain inactive until cash balance data
    # is available.
    # =============================================================

    # No CON11 generated.

    # =============================================================
    # CON RULE 12
    # Revenue CAGR < 5% over 5 years
    # =============================================================

    if len(pnl_hist) >= 6:

        recent = pnl_hist.tail(6)

        revenue_cagr = calculate_cagr(
            recent.iloc[0]["sales"],
            recent.iloc[-1]["sales"],
            5,
        )

        if (
            revenue_cagr is not None
            and revenue_cagr < 5
        ):

            cons.append(
                (
                    "CON12",
                    "Revenue growing at below 5% "
                    "over 5 years lags inflation and "
                    "suggests limited business momentum",
                    85,
                )
            )

    # -----------------------------------------------------------------
    # Return signals
    # -----------------------------------------------------------------

    return pros, cons


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info("=" * 70)
    logger.info(
        "SPRINT 5 - DAY 30 - AUTO PROS/CONS GENERATOR"
    )
    logger.info("=" * 70)

    (
        companies,
        ratios,
        profit_loss,
        cash_flow,
        balance_sheet,
        market_cap,
        sectors,
    ) = load_database()

    company_ids = (
        companies["id"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )

    logger.info(
        "Companies to process: %d",
        len(company_ids),
    )

    rows = []

    for company_id in company_ids:

        pros, cons = generate_for_company(
            company_id,
            companies,
            ratios,
            profit_loss,
            cash_flow,
            balance_sheet,
            market_cap,
            sectors,
        )

        for (
            rule_id,
            text,
            confidence,
        ) in pros:

            if (
                confidence
                > CONFIDENCE_THRESHOLD
            ):

                rows.append(
                    {
                        "company_id": company_id,
                        "type": "pro",
                        "rule_id": rule_id,
                        "text": text,
                        "confidence_pct": confidence,
                    }
                )

        for (
            rule_id,
            text,
            confidence,
        ) in cons:

            if (
                confidence
                > CONFIDENCE_THRESHOLD
            ):

                rows.append(
                    {
                        "company_id": company_id,
                        "type": "con",
                        "rule_id": rule_id,
                        "text": text,
                        "confidence_pct": confidence,
                    }
                )

    output = pd.DataFrame(
        rows,
        columns=[
            "company_id",
            "type",
            "rule_id",
            "text",
            "confidence_pct",
        ],
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # -------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------

    pro_counts = (
        output[
            output["type"] == "pro"
        ]
        .groupby("company_id")
        .size()
    )

    con_counts = (
        output[
            output["type"] == "con"
        ]
        .groupby("company_id")
        .size()
    )

    missing_pro = [
        company
        for company in company_ids
        if company not in pro_counts.index
    ]

    missing_con = [
        company
        for company in company_ids
        if company not in con_counts.index
    ]

    logger.info(
        "Generated signals: %d",
        len(output),
    )

    logger.info(
        "Companies with >=1 pro: %d / %d",
        len(pro_counts),
        len(company_ids),
    )

    logger.info(
        "Companies with >=1 con: %d / %d",
        len(con_counts),
        len(company_ids),
    )

    if missing_pro:

        logger.warning(
            "Companies missing PRO: %s",
            ", ".join(missing_pro),
        )

    if missing_con:

        logger.warning(
            "Companies missing CON: %s",
            ", ".join(missing_con),
        )

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("SPRINT 5 - DAY 30 COMPLETE")
    print("=" * 70)

    print(
        f"Companies processed:     "
        f"{len(company_ids)}"
    )

    print(
        f"Generated signals:       "
        f"{len(output)}"
    )

    print(
        f"Pro signals:             "
        f"{(output['type'] == 'pro').sum()}"
    )

    print(
        f"Con signals:             "
        f"{(output['type'] == 'con').sum()}"
    )

    print(
        f"Companies with pro:      "
        f"{len(pro_counts)} / "
        f"{len(company_ids)}"
    )

    print(
        f"Companies with con:      "
        f"{len(con_counts)} / "
        f"{len(company_ids)}"
    )

    print()
    print(
        f"Created: {OUTPUT_FILE}"
    )

    if (
        not missing_pro
        and not missing_con
    ):

        print(
            "Verification:             PASS"
        )

    else:

        print(
            "Verification:             REVIEW REQUIRED"
        )

    print("=" * 70)


if __name__ == "__main__":
    main()