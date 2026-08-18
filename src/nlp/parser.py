"""
Sprint 5 - Day 29
Analysis Text Parser

Parses CAGR/percentage text fields from data/raw/analysis.xlsx.

Target fields:
    - compounded_sales_growth
    - compounded_profit_growth
    - stock_price_cagr
    - roe

Expected text pattern:
    10 Years: 21%
    5 Years: 24%
    3 Years: 17%

Output:
    output/analysis_parsed.csv
    output/parse_failures.csv
    output/cagr_validation.csv

The parser also cross-validates parsed sales CAGR values
against CAGR calculated from the actual NIFTY 100 Profit & Loss
data stored in SQLite.

Divergence greater than 5% is flagged for manual review.
"""

from pathlib import Path
import logging
import re
import sqlite3

import pandas as pd

from src.analytics.ratios import compound_annual_growth_rate


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ANALYSIS_FILE = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "analysis.xlsx"
)

DB_FILE = (
    PROJECT_ROOT
    / "db"
    / "nifty100.db"
)

OUTPUT_DIR = PROJECT_ROOT / "output"

PARSED_OUTPUT = (
    OUTPUT_DIR
    / "analysis_parsed.csv"
)

FAILURE_OUTPUT = (
    OUTPUT_DIR
    / "parse_failures.csv"
)

VALIDATION_OUTPUT = (
    OUTPUT_DIR
    / "cagr_validation.csv"
)


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Required fields
# ---------------------------------------------------------------------

TARGET_FIELDS = [
    "compounded_sales_growth",
    "compounded_profit_growth",
    "stock_price_cagr",
    "roe",
]


# ---------------------------------------------------------------------
# Required regex from Sprint 5 specification
# ---------------------------------------------------------------------

PARSER_PATTERN = re.compile(
    r"(\d+)\s*Years?:?\s*([\d.]+)%",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def clean_column_name(column):
    """
    Normalize an Excel column name.
    """

    return (
        str(column)
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def clean_text(value):
    """
    Convert a cell value into clean text.
    """

    if pd.isna(value):
        return ""

    return str(value).strip()


def parse_metric_text(value):
    """
    Parse text using the required Sprint 5 regex.

    Examples
    --------
    '10 Years: 21%' -> (10, 21.0)
    '5 Years: 24%'  -> (5, 24.0)
    '3 Years: 17%'  -> (3, 17.0)

    Returns
    -------
    tuple[int | None, float | None]
    """

    text = clean_text(value)

    if not text:
        return None, None

    match = PARSER_PATTERN.search(text)

    if not match:
        return None, None

    period_years = int(match.group(1))
    value_pct = float(match.group(2))

    return period_years, value_pct


def load_analysis_file():
    """
    Load analysis.xlsx.

    The workbook contains a title row before the actual
    column headers, therefore header=1 is required.
    """

    if not ANALYSIS_FILE.exists():
        raise FileNotFoundError(
            f"Analysis file not found: {ANALYSIS_FILE}"
        )

    logger.info(
        "Loading analysis workbook: %s",
        ANALYSIS_FILE,
    )

    df = pd.read_excel(
        ANALYSIS_FILE,
        sheet_name="Analysis",
        header=1,
    )

    df.columns = [
        clean_column_name(column)
        for column in df.columns
    ]

    logger.info(
        "Loaded analysis data: %d rows x %d columns",
        len(df),
        len(df.columns),
    )

    return df


def validate_input_columns(df):
    """
    Validate that all required columns exist.
    """

    required_columns = [
        "company_id",
        *TARGET_FIELDS,
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            "Missing required columns in analysis.xlsx: "
            + ", ".join(missing)
        )


# ---------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------

def parse_analysis(df):
    """
    Parse all target metric fields.

    Returns
    -------
    parsed_df : DataFrame

    failures_df : DataFrame
    """

    parsed_rows = []
    failure_rows = []

    for _, row in df.iterrows():

        company_id = clean_text(
            row["company_id"]
        )

        if not company_id:
            continue

        for metric_type in TARGET_FIELDS:

            raw_value = clean_text(
                row[metric_type]
            )

            if not raw_value:

                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "raw_text": raw_value,
                        "reason": "Empty value",
                    }
                )

                continue

            period_years, value_pct = (
                parse_metric_text(raw_value)
            )

            if period_years is None:

                failure_rows.append(
                    {
                        "company_id": company_id,
                        "metric_type": metric_type,
                        "raw_text": raw_value,
                        "reason": (
                            "Regex pattern did not match"
                        ),
                    }
                )

                continue

            parsed_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": metric_type,
                    "period_years": period_years,
                    "value_pct": value_pct,
                }
            )

    parsed_df = pd.DataFrame(
        parsed_rows,
        columns=[
            "company_id",
            "metric_type",
            "period_years",
            "value_pct",
        ],
    )

    failures_df = pd.DataFrame(
        failure_rows,
        columns=[
            "company_id",
            "metric_type",
            "raw_text",
            "reason",
        ],
    )

    return parsed_df, failures_df


# ---------------------------------------------------------------------
# Financial Year Helpers
# ---------------------------------------------------------------------

def extract_year(year_value):
    """
    Extract a four-digit calendar year from financial-year text.

    Examples
    --------
    'Mar 2024' -> 2024
    'Dec 2012' -> 2012
    '2023'     -> 2023

    TTM is ignored because it does not represent a
    historical financial year.
    """

    text = clean_text(year_value)

    if not text:
        return None

    if text.upper() == "TTM":
        return None

    match = re.search(
        r"(19|20)\d{2}",
        text,
    )

    if not match:
        return None

    return int(match.group())


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

def load_profit_loss_data():
    """
    Load actual NIFTY 100 Profit & Loss data from SQLite.

    The data is used to calculate historical revenue CAGR
    for the companies present in analysis.xlsx.
    """

    if not DB_FILE.exists():

        raise FileNotFoundError(
            f"SQLite database not found: {DB_FILE}"
        )

    query = """
        SELECT
            company_id,
            year,
            sales
        FROM profit_loss
        ORDER BY company_id, year
    """

    with sqlite3.connect(DB_FILE) as connection:

        df = pd.read_sql_query(
            query,
            connection,
        )

    if df.empty:

        logger.warning(
            "Profit & Loss table returned no records."
        )

        return df

    df["financial_year"] = df["year"].apply(
        extract_year
    )

    df["sales"] = pd.to_numeric(
        df["sales"],
        errors="coerce",
    )

    df = df.dropna(
        subset=[
            "company_id",
            "financial_year",
            "sales",
        ]
    )

    df["financial_year"] = (
        df["financial_year"]
        .astype(int)
    )

    logger.info(
        "Loaded %d Profit & Loss records "
        "for CAGR validation.",
        len(df),
    )

    return df


# ---------------------------------------------------------------------
# CAGR calculation
# ---------------------------------------------------------------------

def calculate_sales_cagr(
    profit_loss_df,
    company_id,
    period_years,
):
    """
    Calculate historical revenue/sales CAGR.

    The calculation uses the earliest and latest available
    historical sales values separated by the requested number
    of years.

    Returns
    -------
    float | None
    """

    if profit_loss_df.empty:
        return None

    company_df = profit_loss_df[
        profit_loss_df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
        == str(company_id)
        .strip()
        .upper()
    ].copy()

    if company_df.empty:
        return None

    company_df = company_df.sort_values(
        "financial_year"
    )

    target_years = int(period_years)

    if target_years <= 0:
        return None

    latest_year = int(
        company_df["financial_year"].max()
    )

    target_start_year = (
        latest_year - target_years
    )

    # Prefer an exact historical year.
    exact_start = company_df[
        company_df["financial_year"]
        == target_start_year
    ]

    if not exact_start.empty:

        start_row = exact_start.iloc[-1]

    else:

        # If the exact year is unavailable,
        # use the closest available year at or before
        # the target year.
        eligible = company_df[
            company_df["financial_year"]
            <= target_start_year
        ]

        if eligible.empty:
            return None

        start_row = eligible.iloc[-1]

    latest_rows = company_df[
        company_df["financial_year"]
        == latest_year
    ]

    if latest_rows.empty:
        return None

    end_row = latest_rows.iloc[-1]

    beginning_sales = pd.to_numeric(
        start_row["sales"],
        errors="coerce",
    )

    ending_sales = pd.to_numeric(
        end_row["sales"],
        errors="coerce",
    )

    if (
        pd.isna(beginning_sales)
        or pd.isna(ending_sales)
    ):
        return None

    actual_years = (
        latest_year
        - int(start_row["financial_year"])
    )

    if actual_years <= 0:
        return None

    cagr = compound_annual_growth_rate(
        beginning_sales,
        ending_sales,
        actual_years,
    )

    return cagr


# ---------------------------------------------------------------------
# CAGR Cross Validation
# ---------------------------------------------------------------------

def cross_validate_cagr(parsed_df):
    """
    Cross-validate parsed compounded sales growth values
    against CAGR calculated from the actual Profit & Loss data.

    A divergence greater than 5% is flagged for manual review.

    Notes
    -----
    Only compounded_sales_growth is cross-validated here.

    The other analysis metrics require separate source data:

        compounded_profit_growth
        stock_price_cagr
        roe

    Therefore they are not incorrectly compared against
    revenue CAGR.
    """

    validation_columns = [
        "company_id",
        "metric_type",
        "period_years",
        "parsed_value_pct",
        "computed_value_pct",
        "divergence_pct",
        "validation_status",
        "start_year",
        "end_year",
    ]

    if parsed_df.empty:

        return pd.DataFrame(
            columns=validation_columns
        )

    sales_growth = parsed_df[
        parsed_df["metric_type"]
        == "compounded_sales_growth"
    ].copy()

    if sales_growth.empty:

        return pd.DataFrame(
            columns=validation_columns
        )

    try:

        profit_loss_df = (
            load_profit_loss_data()
        )

    except Exception as exc:

        logger.warning(
            "Could not load Profit & Loss data: %s",
            exc,
        )

        return pd.DataFrame(
            columns=validation_columns
        )

    if profit_loss_df.empty:

        return pd.DataFrame(
            columns=validation_columns
        )

    validation_rows = []

    for _, row in sales_growth.iterrows():

        company_id = row["company_id"]

        period_years = int(
            row["period_years"]
        )

        parsed_value = pd.to_numeric(
            row["value_pct"],
            errors="coerce",
        )

        company_df = profit_loss_df[
            profit_loss_df["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
            == str(company_id)
            .strip()
            .upper()
        ].copy()

        computed_value = (
            calculate_sales_cagr(
                profit_loss_df,
                company_id,
                period_years,
            )
        )

        if company_df.empty:

            validation_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": (
                        "compounded_sales_growth"
                    ),
                    "period_years": period_years,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "validation_status": (
                        "No company data"
                    ),
                    "start_year": None,
                    "end_year": None,
                }
            )

            continue

        latest_year = int(
            company_df["financial_year"].max()
        )

        target_start_year = (
            latest_year - period_years
        )

        eligible = company_df[
            company_df["financial_year"]
            <= target_start_year
        ]

        if not eligible.empty:

            start_year = int(
                eligible.iloc[-1][
                    "financial_year"
                ]
            )

        else:

            start_year = None

        if computed_value is None:

            validation_rows.append(
                {
                    "company_id": company_id,
                    "metric_type": (
                        "compounded_sales_growth"
                    ),
                    "period_years": period_years,
                    "parsed_value_pct": parsed_value,
                    "computed_value_pct": None,
                    "divergence_pct": None,
                    "validation_status": (
                        "No computed CAGR"
                    ),
                    "start_year": start_year,
                    "end_year": latest_year,
                }
            )

            continue

        divergence = abs(
            float(parsed_value)
            - float(computed_value)
        )

        status = (
            "MANUAL_REVIEW"
            if divergence > 5
            else "PASS"
        )

        validation_rows.append(
            {
                "company_id": company_id,
                "metric_type": (
                    "compounded_sales_growth"
                ),
                "period_years": period_years,
                "parsed_value_pct": (
                    float(parsed_value)
                ),
                "computed_value_pct": (
                    float(computed_value)
                ),
                "divergence_pct": round(
                    divergence,
                    2,
                ),
                "validation_status": status,
                "start_year": start_year,
                "end_year": latest_year,
            }
        )

    return pd.DataFrame(
        validation_rows,
        columns=validation_columns,
    )


# ---------------------------------------------------------------------
# Failure Handling
# ---------------------------------------------------------------------

def add_validation_failures(
    failures_df,
    validation_df,
):
    """
    Add CAGR divergence flags to parse_failures.csv.

    Parsing failures remain intact.

    Validation failures are appended as separate records
    with a clear reason.
    """

    if (
        validation_df is None
        or validation_df.empty
    ):
        return failures_df

    review_df = validation_df[
        validation_df["validation_status"]
        == "MANUAL_REVIEW"
    ].copy()

    if review_df.empty:
        return failures_df

    validation_failures = pd.DataFrame(
        {
            "company_id": review_df[
                "company_id"
            ],
            "metric_type": review_df[
                "metric_type"
            ],
            "raw_text": review_df.apply(
                lambda row: (
                    f"Parsed={row['parsed_value_pct']}%, "
                    f"Computed={row['computed_value_pct']}%, "
                    f"Divergence={row['divergence_pct']}%"
                ),
                axis=1,
            ),
            "reason": (
                "CAGR divergence > 5% - "
                "manual review required"
            ),
        }
    )

    return pd.concat(
        [
            failures_df,
            validation_failures,
        ],
        ignore_index=True,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():
    """
    Run the complete Sprint 5 Day 29 parser.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger.info("=" * 70)
    logger.info(
        "SPRINT 5 - DAY 29 - ANALYSIS TEXT PARSER"
    )
    logger.info("=" * 70)

    # -------------------------------------------------------------
    # 1. Load analysis.xlsx
    # -------------------------------------------------------------

    df = load_analysis_file()

    # -------------------------------------------------------------
    # 2. Validate schema
    # -------------------------------------------------------------

    validate_input_columns(df)

    logger.info(
        "Required analysis columns validated successfully."
    )

    # -------------------------------------------------------------
    # 3. Parse text fields
    # -------------------------------------------------------------

    parsed_df, failures_df = (
        parse_analysis(df)
    )

    # -------------------------------------------------------------
    # 4. Save parsed output
    # -------------------------------------------------------------

    parsed_df.to_csv(
        PARSED_OUTPUT,
        index=False,
    )

    logger.info(
        "Parsed output saved: %s",
        PARSED_OUTPUT,
    )

    # -------------------------------------------------------------
    # 5. CAGR cross-validation
    # -------------------------------------------------------------

    validation_df = cross_validate_cagr(
        parsed_df
    )

    if (
        validation_df is not None
        and not validation_df.empty
    ):

        logger.info(
            "CAGR validation completed: %d comparisons",
            len(validation_df),
        )

        passed = (
            validation_df[
                "validation_status"
            ]
            == "PASS"
        ).sum()

        manual_review = (
            validation_df[
                "validation_status"
            ]
            == "MANUAL_REVIEW"
        ).sum()

        no_data = (
            validation_df[
                "validation_status"
            ]
            == "No computed CAGR"
        ).sum()

        logger.info(
            "CAGR validation passed: %d",
            passed,
        )

        logger.info(
            "CAGR manual review flags: %d",
            manual_review,
        )

        logger.info(
            "CAGR records without computed value: %d",
            no_data,
        )

        validation_df.to_csv(
            VALIDATION_OUTPUT,
            index=False,
        )

        logger.info(
            "CAGR validation saved: %s",
            VALIDATION_OUTPUT,
        )

    else:

        logger.warning(
            "No CAGR validation records were produced."
        )

    # -------------------------------------------------------------
    # 6. Add validation failures
    # -------------------------------------------------------------

    failures_df = (
        add_validation_failures(
            failures_df,
            validation_df,
        )
    )

    failures_df.to_csv(
        FAILURE_OUTPUT,
        index=False,
    )

    logger.info(
        "Parse failures saved: %s",
        FAILURE_OUTPUT,
    )

    # -------------------------------------------------------------
    # 7. Summary
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print(
        "SPRINT 5 - DAY 29 COMPLETE"
    )
    print("=" * 70)

    print(
        f"Input rows:              {len(df)}"
    )

    print(
        f"Parsed records:          {len(parsed_df)}"
    )

    print(
        f"Failure records:         {len(failures_df)}"
    )

    if (
        validation_df is not None
        and not validation_df.empty
    ):

        passed = (
            validation_df[
                "validation_status"
            ]
            == "PASS"
        ).sum()

        manual_review = (
            validation_df[
                "validation_status"
            ]
            == "MANUAL_REVIEW"
        ).sum()

        print(
            f"CAGR validations:        {len(validation_df)}"
        )

        print(
            f"CAGR validation passed:  {passed}"
        )

        print(
            f"CAGR manual review:      {manual_review}"
        )

    else:

        print(
            "CAGR validations:        0"
        )

    print()

    print(
        f"Created: {PARSED_OUTPUT}"
    )

    print(
        f"Created: {FAILURE_OUTPUT}"
    )

    if VALIDATION_OUTPUT.exists():

        print(
            f"Created: {VALIDATION_OUTPUT}"
        )

    print(
        "=" * 70
    )


if __name__ == "__main__":
    main()