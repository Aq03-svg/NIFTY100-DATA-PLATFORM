"""
Sprint 5 - Day 32
Company Investment Summary Generator

Builds concise, deterministic investment summaries from the
Day 31 company insights output.

Input:
    output/company_insights.csv

Output:
    output/company_summaries.csv

The generator does NOT introduce new financial rules.
It summarizes the already validated Day 31 signals.
"""

from pathlib import Path
import logging

import pandas as pd


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "output" / "company_insights.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "company_summaries.csv"


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Required columns
# ---------------------------------------------------------------------

REQUIRED_COLUMNS = [
    "company_id",
    "pro_count",
    "con_count",
    "pro_score",
    "con_score",
    "net_score",
    "normalized_score",
    "sentiment",
    "strongest_pro_rule",
    "strongest_pro_text",
    "strongest_pro_confidence",
    "strongest_con_rule",
    "strongest_con_text",
    "strongest_con_confidence",
]


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def validate_input(df):
    """Validate the Day 31 company insights dataset."""

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Missing required columns: "
            + ", ".join(missing_columns)
        )

    if df["company_id"].isna().any():
        raise ValueError(
            "Input contains missing company_id values."
        )

    if df["company_id"].duplicated().any():
        duplicates = (
            df.loc[
                df["company_id"].duplicated(),
                "company_id",
            ]
            .astype(str)
            .tolist()
        )

        raise ValueError(
            "Duplicate company_id values found: "
            + ", ".join(duplicates)
        )

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 companies, found {len(df)}."
        )

    logger.info(
        "Input validation passed: %d companies",
        len(df),
    )


# ---------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------

def clean_text(value):
    """Return clean text or empty string."""

    if pd.isna(value):
        return ""

    return str(value).strip()


def format_number(value, decimals=2):
    """Format numeric values safely."""

    if pd.isna(value):
        return "0"

    return f"{float(value):.{decimals}f}"


# ---------------------------------------------------------------------
# Summary generation
# ---------------------------------------------------------------------

def generate_summary(row):
    """
    Generate a concise investment-oriented summary.

    This function only interprets Day 31's already calculated
    sentiment and signal scores.
    """

    company_id = clean_text(row["company_id"])

    sentiment = clean_text(
        row["sentiment"]
    )

    pro_count = int(row["pro_count"])

    con_count = int(row["con_count"])

    normalized_score = float(
        row["normalized_score"]
    )

    strongest_pro = clean_text(
        row["strongest_pro_text"]
    )

    strongest_con = clean_text(
        row["strongest_con_text"]
    )

    score_text = format_number(
        normalized_score
    )

    # -------------------------------------------------------------
    # Sentiment-specific opening
    # -------------------------------------------------------------

    if sentiment == "Strong Positive":

        opening = (
            f"{company_id} shows a strong positive investment "
            f"profile with a normalized score of {score_text}."
        )

    elif sentiment == "Positive":

        opening = (
            f"{company_id} shows a positive investment profile "
            f"with a normalized score of {score_text}."
        )

    elif sentiment == "Neutral":

        opening = (
            f"{company_id} shows a balanced investment profile "
            f"with a normalized score of {score_text}."
        )

    elif sentiment == "Negative":

        opening = (
            f"{company_id} shows a negative investment profile "
            f"with a normalized score of {score_text}."
        )

    elif sentiment == "Strong Negative":

        opening = (
            f"{company_id} shows a strong negative investment "
            f"profile with a normalized score of {score_text}."
        )

    else:

        opening = (
            f"{company_id} has a normalized investment score "
            f"of {score_text}."
        )

    # -------------------------------------------------------------
    # Signal balance
    # -------------------------------------------------------------

    signal_text = (
        f"The analysis identifies {pro_count} positive signal"
        f"{'' if pro_count == 1 else 's'} and "
        f"{con_count} negative signal"
        f"{'' if con_count == 1 else 's'}."
    )

    # -------------------------------------------------------------
    # Strongest positive factor
    # -------------------------------------------------------------

    if strongest_pro:

        pro_text = (
            f"Key positive factor: {strongest_pro}"
        )

    else:

        pro_text = (
            "No qualifying positive factor was identified."
        )

    # -------------------------------------------------------------
    # Strongest negative factor
    # -------------------------------------------------------------

    if strongest_con:

        con_text = (
            f"Key risk factor: {strongest_con}"
        )

    else:

        con_text = (
            "No qualifying negative factor was identified."
        )

    return (
        opening
        + " "
        + signal_text
        + " "
        + pro_text
        + " "
        + con_text
    )


# ---------------------------------------------------------------------
# Build output
# ---------------------------------------------------------------------

def build_output(df):
    """Create the Day 32 company summary dataset."""

    output = df[
        [
            "company_id",
            "sentiment",
            "pro_count",
            "con_count",
            "pro_score",
            "con_score",
            "net_score",
            "normalized_score",
            "strongest_pro_rule",
            "strongest_pro_confidence",
            "strongest_con_rule",
            "strongest_con_confidence",
        ]
    ].copy()

    output["investment_summary"] = df.apply(
        generate_summary,
        axis=1,
    )

    output = output[
        [
            "company_id",
            "sentiment",
            "pro_count",
            "con_count",
            "pro_score",
            "con_score",
            "net_score",
            "normalized_score",
            "strongest_pro_rule",
            "strongest_pro_confidence",
            "strongest_con_rule",
            "strongest_con_confidence",
            "investment_summary",
        ]
    ]

    return output


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    logger.info("=" * 70)
    logger.info(
        "SPRINT 5 - DAY 32 - COMPANY SUMMARY GENERATOR"
    )
    logger.info("=" * 70)

    # -------------------------------------------------------------
    # Check input
    # -------------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}"
        )

    logger.info(
        "Loading: %s",
        INPUT_FILE,
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    logger.info(
        "Loaded %d rows",
        len(df),
    )

    # -------------------------------------------------------------
    # Validate
    # -------------------------------------------------------------

    validate_input(df)

    # -------------------------------------------------------------
    # Generate summaries
    # -------------------------------------------------------------

    output = build_output(df)

    # -------------------------------------------------------------
    # Final validation
    # -------------------------------------------------------------

    if len(output) != 92:

        raise ValueError(
            f"Expected 92 summary rows, found {len(output)}."
        )

    if output["company_id"].duplicated().any():

        raise ValueError(
            "Duplicate company_id values detected "
            "in generated output."
        )

    if output["investment_summary"].isna().any():

        raise ValueError(
            "Generated output contains missing summaries."
        )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # -------------------------------------------------------------
    # Sentiment verification
    # -------------------------------------------------------------

    sentiment_counts = (
        output["sentiment"]
        .value_counts()
        .sort_index()
    )

    logger.info(
        "Generated summaries: %d",
        len(output),
    )

    logger.info(
        "Output validation passed."
    )

    # -------------------------------------------------------------
    # Console summary
    # -------------------------------------------------------------

    print()
    print("=" * 70)
    print("SPRINT 5 - DAY 32 COMPLETE")
    print("=" * 70)

    print(
        f"Companies processed:     {len(df)}"
    )

    print(
        f"Summaries generated:     {len(output)}"
    )

    print()
    print("Sentiment distribution:")

    for sentiment, count in sentiment_counts.items():

        print(
            f"  {sentiment:<18} {count}"
        )

    print()
    print(
        f"Created: {OUTPUT_FILE}"
    )

    print(
        "Verification:             PASS"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()