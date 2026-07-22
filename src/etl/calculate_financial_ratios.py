"""
Financial Ratio Calculator

Computes all supported financial ratios for every company.
"""

import pandas as pd

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    asset_turnover_ratio,
    compound_annual_growth_rate,
    operating_cash_flow,
    free_cash_flow,
    cash_conversion_ratio,
    operating_cash_flow_margin,
)

def calculate_financial_ratios(df):
    """
    Calculate financial ratios for every company.

    Parameters
    ----------
    df : pandas.DataFrame

    Returns
    -------
    pandas.DataFrame
    """

    ratios = df.copy()

    ratios["net_profit_margin"] = ratios.apply(
        lambda row: net_profit_margin(
            row["net_profit"],
            row["revenue"]
        ),
        axis=1
    )

    ratios["operating_profit_margin"] = ratios.apply(
        lambda row: operating_profit_margin(
            row["operating_profit"],
            row["revenue"]
        ),
        axis=1
    )

    ratios["return_on_equity"] = ratios.apply(
        lambda row: return_on_equity(
            row["net_profit"],
            row["shareholder_equity"]
        ),
        axis=1
        )

    ratios["return_on_assets"] = ratios.apply(
        lambda row: return_on_assets(
            row["net_profit"],
            row["total_assets"]
        ),
        axis=1
        )
    ratios["return_on_capital_employed"] = ratios.apply(
        lambda row: return_on_capital_employed(
            row["ebit"],
            row["capital_employed"],
        ),
        axis=1,
        )
    ratios["debt_to_equity"] = ratios.apply(
        lambda row: debt_to_equity(
            row["total_debt"],
            row["shareholder_equity"],
        ),
        axis=1,
        )
    ratios["interest_coverage_ratio"] = ratios.apply(
        lambda row: interest_coverage_ratio(
            row["ebit"],
            row["interest_expense"],
        ),
        axis=1,
        )
    ratios["net_debt"] = ratios.apply(
        lambda row: net_debt(
            row["total_debt"],
            row["cash_and_equivalents"],
        ),
        axis=1,
        )
    ratios["asset_turnover_ratio"] = ratios.apply(
        lambda row: asset_turnover_ratio(
            row["revenue"],
            row["total_assets"],
        ),
        axis=1,
        )
    ratios["operating_cash_flow"] = ratios.apply(
        lambda row: operating_cash_flow(
            row["cash_from_operations"],
        ),
        axis=1,
        )

    ratios["free_cash_flow"] = ratios.apply(
        lambda row: free_cash_flow(
            row["cash_from_operations"],
            row["capital_expenditure"],
        ),
        axis=1,
        )

    ratios["cash_conversion_ratio"] = ratios.apply(
        lambda row: cash_conversion_ratio(
            row["cash_from_operations"],
            row["net_profit"],
        ),
        axis=1,
        )

    ratios["operating_cash_flow_margin"] = ratios.apply(
        lambda row: operating_cash_flow_margin(
            row["cash_from_operations"],
            row["revenue"],
        ),
        axis=1,
        )

    ratios["revenue_cagr"] = ratios.apply(
        lambda row: compound_annual_growth_rate(
            row["revenue_start"],
            row["revenue_end"],
            row["years"],
        ),
        axis=1,
        )

    return ratios

if __name__ == "__main__":

    sample = pd.DataFrame(
    {
        "company": ["ABC Ltd", "XYZ Ltd"],
        "revenue": [10000, 18000],
        "net_profit": [2000, 3500],
        "operating_profit": [2500, 4200],
        "ebit": [2600, 4400],
        "shareholder_equity": [8000, 15000],
        "capital_employed": [12000, 18000],
        "total_assets": [25000, 40000],
        "total_debt": [5000, 9000],
        "interest_expense": [200, 400],
        "cash_and_equivalents": [1500, 2500],
        "cash_from_operations": [3200, 5100],
        "capital_expenditure": [700, 900],
        "revenue_start": [8000, 15000],
        "revenue_end": [10000, 18000],
        "years": [2, 2],
    }
)

    result = calculate_financial_ratios(sample)

    from pathlib import Path

output_dir = Path("data/processed")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "financial_ratios.csv"

result.to_csv(output_file, index=False)

print(result)

print(f"\nFinancial ratios saved to: {output_file}")