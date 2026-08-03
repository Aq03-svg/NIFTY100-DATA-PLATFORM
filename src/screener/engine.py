from src.screener.scoring import calculate_quality_score
from pathlib import Path

import logging
import pandas as pd
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)

CONFIG_PATH = Path("config/screener_config.yaml")
COLUMN_MAPPING = {
    "roe": "return_on_equity",
    "roce": "return_on_capital_employed",
    "roa": "return_on_assets",
    "npm": "net_profit_margin",
    "debt_to_equity": "debt_to_equity",
    "free_cash_flow": "free_cash_flow",
    "revenue_cagr": "revenue_cagr",
    "cash_conversion_ratio": "cash_conversion_ratio",
    "operating_cash_flow_margin": "operating_cash_flow_margin",
    "asset_turnover_ratio": "asset_turnover_ratio",
}


def load_config():
    """
    Load screener configuration.
    """

    with open(CONFIG_PATH, "r") as file:
        return yaml.safe_load(file)

DATA_PATH = Path("data/processed/financial_ratios.csv")


def load_financial_ratios():
    """
    Load processed financial ratios.
    """

    return pd.read_csv(DATA_PATH)

def get_column_name(metric):
    """
    Convert a screener metric name into the
    corresponding DataFrame column name.
    """

    return COLUMN_MAPPING.get(metric, metric)

def apply_filters(df, filters):
    """
    Apply threshold filters to the financial ratios DataFrame.

    Parameters
    ----------
    df : pandas.DataFrame
    filters : dict

    Returns
    -------
    pandas.DataFrame
    """

    filtered = df.copy()

    for metric, threshold in filters.items():

        if metric.endswith("_min"):

            metric_name = metric.replace("_min", "")
            column = get_column_name(metric_name)

            filtered = filtered[
                filtered[column] >= threshold
            ]

        elif metric.endswith("_max"):

            metric_name = metric.replace("_max", "")
            column = get_column_name(metric_name)

            if column not in filtered.columns:
                raise ValueError(
                    f"Column '{column}' not found in financial ratios."
                )

            filtered = filtered[
                filtered[column] <= threshold
            ]   
    filtered = filtered.sort_values(
        by="return_on_equity",
        ascending=False,
    )

    return filtered

def main():

    config = load_config()

    df = load_financial_ratios()

    preset = "quality_compounder"

    filters = config[preset]

    filtered = apply_filters(df, filters)
    filtered = calculate_quality_score(filtered)

    logging.info("Loaded preset: %s", preset)
    logging.info("\n%s", filtered)

if __name__ == "__main__":
    main()