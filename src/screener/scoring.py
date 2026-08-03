"""
Composite Quality Scoring Engine

Calculates a weighted composite quality score
without modifying the original financial metrics.
"""

from pathlib import Path

import pandas as pd

QUALITY_WEIGHTS = {
    "return_on_equity": 0.25,
    "return_on_capital_employed": 0.20,
    "revenue_cagr": 0.20,
    "free_cash_flow": 0.15,
    "operating_cash_flow_margin": 0.10,
    "debt_to_equity": 0.10,
}


def calculate_quality_score(df):
    """
    Calculate weighted composite quality score.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    scored = df.copy()

    normalized = pd.DataFrame(index=scored.index)

    positive_metrics = [
        "return_on_equity",
        "return_on_capital_employed",
        "revenue_cagr",
        "free_cash_flow",
        "operating_cash_flow_margin",
    ]

    for column in positive_metrics:

        maximum = scored[column].max()

        if maximum > 0:
            normalized[column] = scored[column] / maximum
        else:
            normalized[column] = 0

    maximum = scored["debt_to_equity"].max()

    if maximum > 0:
        normalized["debt_to_equity"] = (
            1 - scored["debt_to_equity"] / maximum
        )
    else:
        normalized["debt_to_equity"] = 0

    score = 0

    for column, weight in QUALITY_WEIGHTS.items():
        score += normalized[column] * weight

    scored["composite_quality_score"] = (
        score * 100
    ).round(2)

    scored = scored.sort_values(
        by="composite_quality_score",
        ascending=False,
    )

    return scored


def main():

    df = pd.read_csv(
        Path("data/processed/financial_ratios.csv")
    )

    scored = calculate_quality_score(df)

    print(
        scored[
            [
                "company",
                "return_on_equity",
                "return_on_capital_employed",
                "revenue_cagr",
                "composite_quality_score",
            ]
        ]
    )


if __name__ == "__main__":
    main()