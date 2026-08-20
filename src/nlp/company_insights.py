"""
Sprint 5 - Day 31
Company-Level Investment Insight Aggregator

Input:
    output/pros_cons_generated.csv

Output:
    output/company_insights.csv

Aggregates the rule-based NLP signals generated on Day 30
into one investment-insight record per company.
"""

from pathlib import Path
import logging

import pandas as pd


# ---------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = PROJECT_ROOT / "output" / "pros_cons_generated.csv"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "company_insights.csv"


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

REQUIRED_COLUMNS = {
    "company_id",
    "type",
    "rule_id",
    "text",
    "confidence_pct",
}


# ---------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------

def classify_sentiment(net_score, pro_count, con_count):
    """
    Classify the company's overall investment signal.

    The classification is based on the balance between
    weighted Pro and Con confidence scores.
    """

    if pro_count == 0 and con_count == 0:
        return "Neutral"

    if net_score >= 150:
        return "Strong Positive"

    if net_score >= 50:
        return "Positive"

    if net_score > -50:
        return "Neutral"

    if net_score > -150:
        return "Negative"

    return "Strong Negative"


def validate_input(df):
    """Validate the Day 30 input dataset."""

    missing_columns = REQUIRED_COLUMNS - set(df.columns)

    if missing_columns:
        raise ValueError(
            "Input file is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    if df.empty:
        raise ValueError(
            "Input file contains no signal records."
        )

    logger.info(
        "Input validation passed: %d signal rows",
        len(df),
    )


# ---------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------

def aggregate_company(company_id, company_df):
    """
    Generate one aggregated insight record for one company.
    """

    pros = company_df[
        company_df["type"].str.lower() == "pro"
    ].copy()

    cons = company_df[
        company_df["type"].str.lower() == "con"
    ].copy()

    # -------------------------------------------------------------
    # Counts
    # -------------------------------------------------------------

    pro_count = len(pros)
    con_count = len(cons)

    # -------------------------------------------------------------
    # Weighted confidence scores
    # -------------------------------------------------------------

    pro_score = pros["confidence_pct"].sum()
    con_score = cons["confidence_pct"].sum()

    net_score = pro_score - con_score

    # -------------------------------------------------------------
    # Maximum possible score for normalization
    #
    # Each signal has a maximum confidence of 100.
    # Normalized score therefore represents the balance between
    # positive and negative signal strength on a -100 to +100 scale.
    # -------------------------------------------------------------

    total_signals = pro_count + con_count

    if total_signals > 0:
        normalized_score = (
            net_score / (total_signals * 100)
        ) * 100
    else:
        normalized_score = 0.0

    normalized_score = round(
        normalized_score,
        2,
    )

    # -------------------------------------------------------------
    # Sentiment
    # -------------------------------------------------------------

    sentiment = classify_sentiment(
        net_score,
        pro_count,
        con_count,
    )

    # -------------------------------------------------------------
    # Strongest Pro
    # -------------------------------------------------------------

    if not pros.empty:

        strongest_pro = pros.loc[
            pros["confidence_pct"].idxmax()
        ]

        strongest_pro_rule = (
            strongest_pro["rule_id"]
        )

        strongest_pro_text = (
            strongest_pro["text"]
        )

        strongest_pro_confidence = float(
            strongest_pro["confidence_pct"]
        )

    else:

        strongest_pro_rule = ""
        strongest_pro_text = ""
        strongest_pro_confidence = 0.0

    # -------------------------------------------------------------
    # Strongest Con
    # -------------------------------------------------------------

    if not cons.empty:

        strongest_con = cons.loc[
            cons["confidence_pct"].idxmax()
        ]

        strongest_con_rule = (
            strongest_con["rule_id"]
        )

        strongest_con_text = (
            strongest_con["text"]
        )

        strongest_con_confidence = float(
            strongest_con["confidence_pct"]
        )

    else:

        strongest_con_rule = ""
        strongest_con_text = ""
        strongest_con_confidence = 0.0

    # -------------------------------------------------------------
    # Return aggregated record
    # -------------------------------------------------------------

    return {
        "company_id": company_id,
        "pro_count": pro_count,
        "con_count": con_count,
        "pro_score": round(float(pro_score), 2),
        "con_score": round(float(con_score), 2),
        "net_score": round(float(net_score), 2),
        "normalized_score": normalized_score,
        "sentiment": sentiment,
        "strongest_pro_rule": strongest_pro_rule,
        "strongest_pro_text": strongest_pro_text,
        "strongest_pro_confidence": strongest_pro_confidence,
        "strongest_con_rule": strongest_con_rule,
        "strongest_con_text": strongest_con_text,
        "strongest_con_confidence": strongest_con_confidence,
    }


def generate_company_insights(df):
    """
    Aggregate all signal rows into one row per company.
    """

    records = []

    for company_id, company_df in df.groupby(
        "company_id",
        sort=True,
    ):

        record = aggregate_company(
            company_id,
            company_df,
        )

        records.append(record)

    output = pd.DataFrame(records)

    return output


# ---------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------

def verify_output(
    output,
    input_df,
):
    """
    Verify that aggregation produced one record per company
    and that signal totals are preserved.
    """

    input_companies = (
        input_df["company_id"]
        .nunique()
    )

    output_companies = (
        output["company_id"]
        .nunique()
    )

    if input_companies != output_companies:
        raise RuntimeError(
            "Company count mismatch: "
            f"input={input_companies}, "
            f"output={output_companies}"
        )

    input_pro_count = (
        input_df["type"]
        .str.lower()
        .eq("pro")
        .sum()
    )

    input_con_count = (
        input_df["type"]
        .str.lower()
        .eq("con")
        .sum()
    )

    output_pro_count = output["pro_count"].sum()
    output_con_count = output["con_count"].sum()

    if input_pro_count != output_pro_count:
        raise RuntimeError(
            "Pro signal count mismatch: "
            f"input={input_pro_count}, "
            f"output={output_pro_count}"
        )

    if input_con_count != output_con_count:
        raise RuntimeError(
            "Con signal count mismatch: "
            f"input={input_con_count}, "
            f"output={output_con_count}"
        )

    if output["net_score"].isna().any():
        raise RuntimeError(
            "Output contains missing net scores."
        )

    logger.info(
        "Verification passed: %d companies aggregated",
        output_companies,
    )

    logger.info(
        "Pro signals preserved: %d",
        output_pro_count,
    )

    logger.info(
        "Con signals preserved: %d",
        output_con_count,
    )


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    logger.info("=" * 70)
    logger.info(
        "SPRINT 5 - DAY 31 - COMPANY INSIGHT AGGREGATOR"
    )
    logger.info("=" * 70)

    # -------------------------------------------------------------
    # Check input
    # -------------------------------------------------------------

    if not INPUT_FILE.exists():

        raise FileNotFoundError(
            f"Day 30 output not found: {INPUT_FILE}"
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # -------------------------------------------------------------
    # Load Day 30 signals
    # -------------------------------------------------------------

    logger.info(
        "Loading: %s",
        INPUT_FILE,
    )

    df = pd.read_csv(
        INPUT_FILE
    )

    validate_input(df)

    # -------------------------------------------------------------
    # Clean types
    # -------------------------------------------------------------

    df["company_id"] = (
        df["company_id"]
        .astype(str)
        .str.strip()
    )

    df["type"] = (
        df["type"]
        .astype(str)
        .str.strip()
        .str.lower()
    )

    df["rule_id"] = (
        df["rule_id"]
        .astype(str)
        .str.strip()
    )

    df["text"] = (
        df["text"]
        .astype(str)
        .str.strip()
    )

    df["confidence_pct"] = pd.to_numeric(
        df["confidence_pct"],
        errors="coerce",
    )

    if df["confidence_pct"].isna().any():

        raise ValueError(
            "Invalid confidence_pct values detected."
        )

    # -------------------------------------------------------------
    # Validate signal types
    # -------------------------------------------------------------

    invalid_types = sorted(
        set(df["type"].unique())
        - {"pro", "con"}
    )

    if invalid_types:

        raise ValueError(
            "Unexpected signal types: "
            + ", ".join(invalid_types)
        )

    # -------------------------------------------------------------
    # Generate company-level insights
    # -------------------------------------------------------------

    output = generate_company_insights(
        df
    )

    # -------------------------------------------------------------
    # Verification
    # -------------------------------------------------------------

    verify_output(
        output,
        df,
    )

    # -------------------------------------------------------------
    # Save
    # -------------------------------------------------------------

    output.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    # -------------------------------------------------------------
    # Summary
    # -------------------------------------------------------------

    sentiment_counts = (
        output["sentiment"]
        .value_counts()
        .to_dict()
    )

    print()
    print("=" * 70)
    print("SPRINT 5 - DAY 31 COMPLETE")
    print("=" * 70)

    print(
        f"Input signals:          {len(df)}"
    )

    print(
        f"Companies aggregated:   {len(output)}"
    )

    print(
        f"Total Pro signals:      {output['pro_count'].sum()}"
    )

    print(
        f"Total Con signals:      {output['con_count'].sum()}"
    )

    print()
    print("Sentiment distribution:")

    for sentiment, count in sorted(
        sentiment_counts.items()
    ):
        print(
            f"  {sentiment:<18} {count}"
        )

    print()
    print(
        f"Created: {OUTPUT_FILE}"
    )

    print(
        "Verification:           PASS"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()