"""
Peer Comparison Engine

Compare selected companies using the
composite quality score and key financial metrics.
"""

from pathlib import Path

import pandas as pd

from src.screener.scoring import calculate_quality_score


def compare_companies(df, companies):
    """
    Return a ranked comparison of selected companies.

    Parameters
    ----------
    df : pandas.DataFrame

    companies : list

    Returns
    -------
    pandas.DataFrame
    """

    peers = df[df["company"].isin(companies)]

    peers = peers.sort_values(
        by="composite_quality_score",
        ascending=False,
    )

    peers["rank"] = range(1, len(peers) + 1)

    return peers


def main():

    df = pd.read_csv(
        Path("data/processed/financial_ratios.csv")
    )

    df = calculate_quality_score(df)

    peers = compare_companies(
        df,
        ["ABC Ltd", "XYZ Ltd"],
    )

    print(
        peers[
            [
                "rank",
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