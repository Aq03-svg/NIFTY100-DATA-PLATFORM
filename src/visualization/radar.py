"""
Radar Chart Generator

Creates radar charts for company comparison.
"""

from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


DATA_PATH = Path("data/processed/financial_ratios.csv")


def load_data():
    """
    Load processed financial ratios.
    """

    return pd.read_csv(DATA_PATH)


def prepare_metrics(df):
    """
    Normalize metrics for radar chart plotting.
    """

    metrics = [
        "return_on_equity",
        "return_on_capital_employed",
        "net_profit_margin",
        "debt_to_equity",
        "free_cash_flow",
        "revenue_cagr",
    ]

    prepared = df.copy()

    for metric in metrics:

        if metric == "debt_to_equity":

            maximum = prepared[metric].max()

            if maximum > 0:
                prepared[metric] = (
                    1 - prepared[metric] / maximum
                )

        else:

            maximum = prepared[metric].max()

            if maximum > 0:
                prepared[metric] = (
                    prepared[metric] / maximum
                )

    return prepared



def plot_radar_chart(df):
    """
    Plot and save radar charts for every company.
    """

    import numpy as np
    import matplotlib.pyplot as plt
    from pathlib import Path

    metrics = [
        "return_on_equity",
        "return_on_capital_employed",
        "net_profit_margin",
        "debt_to_equity",
        "free_cash_flow",
        "revenue_cagr",
    ]

    labels = [
        "ROE",
        "ROCE",
        "NPM",
        "D/E",
        "FCF",
        "Revenue CAGR",
    ]

    output_dir = Path("reports/radar_charts")
    output_dir.mkdir(parents=True, exist_ok=True)

    angles = np.linspace(
        0,
        2 * np.pi,
        len(metrics),
        endpoint=False,
    ).tolist()

    angles += angles[:1]

    for _, row in df.iterrows():

        values = row[metrics].tolist()
        values += values[:1]

        # Peer average excluding current company
        peer_df = df[df["company"] != row["company"]]

        if not peer_df.empty:
            peer_values = peer_df[metrics].mean().tolist()
            peer_values += peer_values[:1]
        else:
            peer_values = values

        fig, ax = plt.subplots(
            figsize=(7, 7),
            subplot_kw=dict(polar=True),
        )

        # Company
        ax.plot(
            angles,
            values,
            linewidth=2,
            label=row["company"],
        )

        ax.fill(
            angles,
            values,
            alpha=0.25,
        )

        # Peer average
        ax.plot(
            angles,
            peer_values,
            linestyle="--",
            linewidth=2,
            label="Peer Average",
        )

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)

        ax.set_ylim(0, 1)

        ax.set_title(
            row["company"],
            fontsize=16,
            pad=20,
        )

        ax.legend(
            loc="upper right",
            bbox_to_anchor=(1.2, 1.1),
        )

        filename = (
            row["company"]
            .replace(" ", "_")
            + "_radar.png"
        )

        plt.savefig(
            output_dir / filename,
            dpi=300,
            bbox_inches="tight",
        )

        plt.close(fig)

        print(
            f"Saved: {output_dir / filename}"
        )

def save_chart():
    """
    Placeholder.
    """

    pass


def main():

    df = load_data()

    prepared = prepare_metrics(df)

    plot_radar_chart(prepared)


if __name__ == "__main__":
    main()