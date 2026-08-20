"""
SPRINT 5 - DAY 34
NLP PIPELINE VALIDATION

Validates the complete NLP pipeline outputs:

1. pros_cons_generated.csv
2. company_insights.csv
3. company_summaries.csv
4. company_rankings.csv

The validator checks:
- Required files exist
- Required columns exist
- Company coverage
- Duplicate companies
- Signal counts
- Score consistency
- Sentiment consistency
- Ranking integrity
- Summary coverage
"""

from pathlib import Path
import logging

import pandas as pd


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_DIR = BASE_DIR / "output"

PROS_CONS_FILE = OUTPUT_DIR / "pros_cons_generated.csv"
INSIGHTS_FILE = OUTPUT_DIR / "company_insights.csv"
SUMMARIES_FILE = OUTPUT_DIR / "company_summaries.csv"
RANKINGS_FILE = OUTPUT_DIR / "company_rankings.csv"


# ---------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# EXPECTED SCHEMA
# ---------------------------------------------------------------------

PROS_CONS_COLUMNS = {
    "company_id",
    "type",
    "rule_id",
    "text",
    "confidence_pct",
}

INSIGHTS_COLUMNS = {
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
}

SUMMARIES_COLUMNS = {
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
}

RANKINGS_COLUMNS = {
    "rank",
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
}


# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------

def check_file(path: Path) -> None:
    """Verify that an expected output file exists."""
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")

    if path.stat().st_size == 0:
        raise ValueError(f"Required file is empty: {path}")

    logger.info("File exists: %s", path.name)


def check_columns(
    df: pd.DataFrame,
    expected: set[str],
    filename: str,
) -> None:
    """Verify required columns exist."""
    missing = expected - set(df.columns)

    if missing:
        raise ValueError(
            f"{filename}: missing columns: {sorted(missing)}"
        )

    logger.info(
        "Schema validation passed: %s",
        filename,
    )


def check_company_ids(
    df: pd.DataFrame,
    filename: str,
) -> set[str]:
    """Validate company IDs and return the company set."""
    if df["company_id"].isna().any():
        raise ValueError(
            f"{filename}: company_id contains NULL values"
        )

    if (df["company_id"].astype(str).str.strip() == "").any():
        raise ValueError(
            f"{filename}: company_id contains empty values"
        )

    companies = set(df["company_id"].astype(str).str.strip())

    logger.info(
        "%s: %d unique companies",
        filename,
        len(companies),
    )

    return companies


def check_no_duplicate_companies(
    df: pd.DataFrame,
    filename: str,
) -> None:
    """Ensure one company appears once in company-level outputs."""
    duplicates = df["company_id"][
        df["company_id"].duplicated()
    ].unique()

    if len(duplicates) > 0:
        raise ValueError(
            f"{filename}: duplicate company IDs: "
            f"{sorted(duplicates)}"
        )


# ---------------------------------------------------------------------
# VALIDATE PROS / CONS
# ---------------------------------------------------------------------

def validate_pros_cons() -> tuple[pd.DataFrame, set[str]]:
    logger.info("Validating pros/cons output...")

    check_file(PROS_CONS_FILE)

    df = pd.read_csv(PROS_CONS_FILE)

    check_columns(
        df,
        PROS_CONS_COLUMNS,
        PROS_CONS_FILE.name,
    )

    if df.empty:
        raise ValueError("pros_cons_generated.csv contains no rows")

    companies = check_company_ids(
        df,
        PROS_CONS_FILE.name,
    )

    invalid_types = set(df["type"].dropna().unique()) - {
        "pro",
        "con",
    }

    if invalid_types:
        raise ValueError(
            f"Invalid signal types: {sorted(invalid_types)}"
        )

    if df["rule_id"].isna().any():
        raise ValueError(
            "pros_cons_generated.csv contains NULL rule IDs"
        )

    if df["text"].isna().any():
        raise ValueError(
            "pros_cons_generated.csv contains NULL signal text"
        )

    if df["confidence_pct"].isna().any():
        raise ValueError(
            "pros_cons_generated.csv contains NULL confidence values"
        )

    if not df["confidence_pct"].between(0, 100).all():
        raise ValueError(
            "Confidence values must be between 0 and 100"
        )

    pro_count = int((df["type"] == "pro").sum())
    con_count = int((df["type"] == "con").sum())

    logger.info(
        "Pros/cons validation passed: %d rows | %d pro | %d con",
        len(df),
        pro_count,
        con_count,
    )

    return df, companies


# ---------------------------------------------------------------------
# VALIDATE COMPANY INSIGHTS
# ---------------------------------------------------------------------

def validate_insights(
    expected_companies: set[str],
) -> tuple[pd.DataFrame, set[str]]:
    logger.info("Validating company insights...")

    check_file(INSIGHTS_FILE)

    df = pd.read_csv(INSIGHTS_FILE)

    check_columns(
        df,
        INSIGHTS_COLUMNS,
        INSIGHTS_FILE.name,
    )

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 company insights, found {len(df)}"
        )

    companies = check_company_ids(
        df,
        INSIGHTS_FILE.name,
    )

    check_no_duplicate_companies(
        df,
        INSIGHTS_FILE.name,
    )

    if companies != expected_companies:
        missing = expected_companies - companies
        extra = companies - expected_companies

        raise ValueError(
            f"Company coverage mismatch in insights. "
            f"Missing={sorted(missing)}, Extra={sorted(extra)}"
        )

    numeric_columns = [
        "pro_count",
        "con_count",
        "pro_score",
        "con_score",
        "net_score",
        "normalized_score",
    ]

    for column in numeric_columns:
        if df[column].isna().any():
            raise ValueError(
                f"Insights column contains NULL values: {column}"
            )

    calculated_net = (
        df["pro_score"] - df["con_score"]
    )

    if not (
        calculated_net.round(6)
        == df["net_score"].round(6)
    ).all():
        raise ValueError(
            "Insights net_score does not equal "
            "pro_score - con_score"
        )

    valid_sentiments = {
        "Negative",
        "Neutral",
        "Positive",
        "Strong Negative",
        "Strong Positive",
    }

    invalid_sentiments = (
        set(df["sentiment"].dropna().unique())
        - valid_sentiments
    )

    if invalid_sentiments:
        raise ValueError(
            f"Invalid sentiment values: "
            f"{sorted(invalid_sentiments)}"
        )

    logger.info(
        "Insights validation passed: %d companies",
        len(df),
    )

    return df, companies


# ---------------------------------------------------------------------
# VALIDATE SUMMARIES
# ---------------------------------------------------------------------

def validate_summaries(
    expected_companies: set[str],
) -> tuple[pd.DataFrame, set[str]]:
    logger.info("Validating company summaries...")

    check_file(SUMMARIES_FILE)

    df = pd.read_csv(SUMMARIES_FILE)

    check_columns(
        df,
        SUMMARIES_COLUMNS,
        SUMMARIES_FILE.name,
    )

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 summaries, found {len(df)}"
        )

    companies = check_company_ids(
        df,
        SUMMARIES_FILE.name,
    )

    check_no_duplicate_companies(
        df,
        SUMMARIES_FILE.name,
    )

    if companies != expected_companies:
        missing = expected_companies - companies
        extra = companies - expected_companies

        raise ValueError(
            f"Company coverage mismatch in summaries. "
            f"Missing={sorted(missing)}, Extra={sorted(extra)}"
        )

    if df["investment_summary"].isna().any():
        raise ValueError(
            "Some companies have NULL investment summaries"
        )

    if (
        df["investment_summary"]
        .astype(str)
        .str.strip()
        .eq("")
        .any()
    ):
        raise ValueError(
            "Some companies have empty investment summaries"
        )

    logger.info(
        "Summary validation passed: %d companies",
        len(df),
    )

    return df, companies


# ---------------------------------------------------------------------
# VALIDATE RANKINGS
# ---------------------------------------------------------------------

def validate_rankings(
    expected_companies: set[str],
) -> pd.DataFrame:
    logger.info("Validating company rankings...")

    check_file(RANKINGS_FILE)

    df = pd.read_csv(RANKINGS_FILE)

    check_columns(
        df,
        RANKINGS_COLUMNS,
        RANKINGS_FILE.name,
    )

    if len(df) != 92:
        raise ValueError(
            f"Expected 92 ranked companies, found {len(df)}"
        )

    companies = check_company_ids(
        df,
        RANKINGS_FILE.name,
    )

    check_no_duplicate_companies(
        df,
        RANKINGS_FILE.name,
    )

    if companies != expected_companies:
        missing = expected_companies - companies
        extra = companies - expected_companies

        raise ValueError(
            f"Company coverage mismatch in rankings. "
            f"Missing={sorted(missing)}, Extra={sorted(extra)}"
        )

    expected_ranks = set(range(1, 93))
    actual_ranks = set(
        df["rank"].astype(int)
    )

    if actual_ranks != expected_ranks:
        raise ValueError(
            "Ranking sequence must contain exactly ranks 1-92"
        )

    if len(actual_ranks) != 92:
        raise ValueError(
            "Duplicate ranking positions detected"
        )

        # Ensure ranking is actually sorted by normalized score.
    #
    # Equal normalized scores are valid and do not require a
    # specific company ordering. We only require that the
    # score never increases as rank increases.

    ranked_df = df.sort_values(
        "rank"
    ).reset_index(drop=True)

    scores = pd.to_numeric(
        ranked_df["normalized_score"],
        errors="coerce",
    )

    if scores.isna().any():
        raise ValueError(
            "Ranking contains invalid normalized_score values"
        )

    score_increases = scores.diff().dropna() > 0

    if score_increases.any():
        first_invalid_position = (
            score_increases[score_increases]
            .index[0]
        )

        previous_score = scores.iloc[
            first_invalid_position - 1
        ]

        current_score = scores.iloc[
            first_invalid_position
        ]

        previous_rank = ranked_df.iloc[
            first_invalid_position - 1
        ]["rank"]

        current_rank = ranked_df.iloc[
            first_invalid_position
        ]["rank"]

        raise ValueError(
            "Ranking order is invalid: normalized score "
            f"increases from rank {previous_rank} "
            f"({previous_score}) to rank {current_rank} "
            f"({current_score})"
        )

    logger.info(
        "Ranking score order validation passed."
    )

    logger.info(
        "Ranking validation passed: %d companies",
        len(df),
    )

    return df


# ---------------------------------------------------------------------
# CROSS-PIPELINE VALIDATION
# ---------------------------------------------------------------------

def validate_cross_pipeline(
    pros_cons: pd.DataFrame,
    insights: pd.DataFrame,
    summaries: pd.DataFrame,
    rankings: pd.DataFrame,
) -> None:
    logger.info("Running cross-pipeline validation...")

    # -------------------------------------------------------------
    # Signal counts
    # -------------------------------------------------------------

    signal_counts = (
        pros_cons.groupby(
            ["company_id", "type"]
        )
        .size()
        .unstack(fill_value=0)
    )

    for _, row in insights.iterrows():
        company = row["company_id"]

        expected_pro = int(
            signal_counts.loc[company, "pro"]
            if company in signal_counts.index
            and "pro" in signal_counts.columns
            else 0
        )

        expected_con = int(
            signal_counts.loc[company, "con"]
            if company in signal_counts.index
            and "con" in signal_counts.columns
            else 0
        )

        if int(row["pro_count"]) != expected_pro:
            raise ValueError(
                f"{company}: pro_count mismatch"
            )

        if int(row["con_count"]) != expected_con:
            raise ValueError(
                f"{company}: con_count mismatch"
            )

    # -------------------------------------------------------------
    # Insights -> summaries
    # -------------------------------------------------------------

    insights_sorted = insights.sort_values(
        "company_id"
    ).reset_index(drop=True)

    summaries_sorted = summaries.sort_values(
        "company_id"
    ).reset_index(drop=True)

    comparison_columns = [
        "company_id",
        "sentiment",
        "pro_count",
        "con_count",
        "pro_score",
        "con_score",
        "net_score",
        "normalized_score",
    ]

    for column in comparison_columns:
        left = insights_sorted[column]
        right = summaries_sorted[column]

        if column == "normalized_score":
            if not (
                pd.to_numeric(left).round(6)
                == pd.to_numeric(right).round(6)
            ).all():
                raise ValueError(
                    f"Insights/summaries mismatch: {column}"
                )
        else:
            if not left.astype(str).equals(
                right.astype(str)
            ):
                raise ValueError(
                    f"Insights/summaries mismatch: {column}"
                )

    # -------------------------------------------------------------
    # Summaries -> rankings
    # -------------------------------------------------------------

    rankings_sorted = rankings.sort_values(
        "company_id"
    ).reset_index(drop=True)

    for column in comparison_columns:
        left = summaries_sorted[column]
        right = rankings_sorted[column]

        if column == "normalized_score":
            if not (
                pd.to_numeric(left).round(6)
                == pd.to_numeric(right).round(6)
            ).all():
                raise ValueError(
                    f"Summaries/rankings mismatch: {column}"
                )
        else:
            if not left.astype(str).equals(
                right.astype(str)
            ):
                raise ValueError(
                    f"Summaries/rankings mismatch: {column}"
                )

    logger.info(
        "Cross-pipeline validation passed."
    )


# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 70)
    logger.info(
        "SPRINT 5 - DAY 34 - NLP PIPELINE VALIDATOR"
    )
    logger.info("=" * 70)

    pros_cons, companies = validate_pros_cons()

    insights, _ = validate_insights(
        companies
    )

    summaries, _ = validate_summaries(
        companies
    )

    rankings = validate_rankings(
        companies
    )

    validate_cross_pipeline(
        pros_cons,
        insights,
        summaries,
        rankings,
    )

    logger.info("")
    logger.info("=" * 70)
    logger.info("SPRINT 5 - DAY 34 COMPLETE")
    logger.info("=" * 70)

    logger.info(
        "Pros/cons signals:     %d",
        len(pros_cons),
    )

    logger.info(
        "Companies validated:  %d",
        len(companies),
    )

    logger.info(
        "Insights validated:   %d",
        len(insights),
    )

    logger.info(
        "Summaries validated:  %d",
        len(summaries),
    )

    logger.info(
        "Rankings validated:   %d",
        len(rankings),
    )

    logger.info(
        "Verification:          PASS"
    )

    logger.info("=" * 70)


if __name__ == "__main__":
    main()
