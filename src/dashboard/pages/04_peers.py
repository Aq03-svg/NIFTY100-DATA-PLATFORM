"""
NIFTY 100 Analytics - Peer Comparison

Compares companies within predefined peer groups using
financial quality, growth, leverage and valuation metrics.
"""

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from src.dashboard.utils.db import (
    get_companies,
    get_peers,
    get_ratios,
    get_valuation,
    get_sectors,
)


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics - Peer Comparison",
    page_icon="👥",
    layout="wide",
)


# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def safe_numeric(value):
    """
    Safely convert a value to numeric.
    """

    return pd.to_numeric(
        value,
        errors="coerce",
    )


def select_year_rows(df, year):
    """
    Select rows matching a financial year.
    """

    if df is None or df.empty:
        return pd.DataFrame()

    if "year" not in df.columns:
        return pd.DataFrame()

    return df[
        df["year"]
        .astype(str)
        .str.contains(
            str(year),
            na=False,
        )
    ].copy()


def get_ratio_row(ticker, year):
    """
    Return a clean ratio row for a company/year.

    Duplicate rows are consolidated using median values.
    """

    ratios = get_ratios(ticker)

    if ratios.empty:
        return None

    selected = select_year_rows(
        ratios,
        year,
    )

    if selected.empty:
        return None

    numeric_columns = [
        "return_on_equity_pct",
        "roce_percentage",
        "debt_to_equity",
        "free_cash_flow_cr",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "interest_coverage",
        "earnings_per_share",
        "book_value_per_share",
        "cash_from_operations_cr",
    ]

    available = [
        column
        for column in numeric_columns
        if column in selected.columns
    ]

    for column in available:
        selected[column] = pd.to_numeric(
            selected[column],
            errors="coerce",
        )

    grouped = (
        selected
        .groupby(
            [
                "company_id",
                "company_name",
            ],
            as_index=False,
        )[available]
        .median()
    )

    if grouped.empty:
        return None

    return grouped.iloc[0]


def calculate_revenue_cagr(
    ticker,
    selected_year,
):
    """
    Calculate five-year revenue CAGR directly from
    Profit & Loss data.

    This keeps peer comparison independent of the
    optional analysis table.
    """

    from src.dashboard.utils.db import get_pl

    pl = get_pl(ticker)

    if pl.empty:
        return np.nan

    if "sales" not in pl.columns:
        return np.nan

    data = pl[
        pl["year"]
        .astype(str)
        .str.match(
            r"^(Mar|Dec)\s\d{4}$",
            na=False,
        )
    ].copy()

    if data.empty:
        return np.nan

    data["year_num"] = pd.to_numeric(
        data["year"]
        .astype(str)
        .str.extract(
            r"(\d{4})"
        )[0],
        errors="coerce",
    )

    data["sales"] = pd.to_numeric(
        data["sales"],
        errors="coerce",
    )

    data = data.dropna(
        subset=[
            "year_num",
            "sales",
        ]
    )

    if data.empty:
        return np.nan

    target_year = int(selected_year)

    end_rows = data[
        data["year_num"] == target_year
    ]

    if end_rows.empty:
        return np.nan

    end_value = end_rows[
        "sales"
    ].median()

    start_year = target_year - 5

    start_rows = data[
        data["year_num"] == start_year
    ]

    if start_rows.empty:

        earlier = data[
            data["year_num"] < target_year
        ]

        if earlier.empty:
            return np.nan

        closest_year = earlier[
            "year_num"
        ].max()

        start_rows = data[
            data["year_num"]
            == closest_year
        ]

        actual_years = (
            target_year
            - int(closest_year)
        )

    else:

        actual_years = 5

    if start_rows.empty:
        return np.nan

    start_value = start_rows[
        "sales"
    ].median()

    if (
        pd.isna(start_value)
        or pd.isna(end_value)
        or start_value <= 0
        or end_value <= 0
        or actual_years <= 0
    ):
        return np.nan

    return (
        (
            end_value
            / start_value
        )
        ** (1 / actual_years)
        - 1
    ) * 100


def get_valuation_row(
    ticker,
    year,
):
    """
    Get valuation data for the selected year.

    Falls back to the latest available year if the
    selected year does not exist.
    """

    valuation = get_valuation(ticker)

    if valuation.empty:
        return None

    selected = valuation[
        valuation["year"]
        .astype(str)
        == str(year)
    ]

    if selected.empty:
        selected = valuation.tail(1)

    if selected.empty:
        return None

    row = selected.iloc[-1]

    return {
        "pe_ratio": safe_numeric(
            row.get("pe_ratio")
        ),
        "pb_ratio": safe_numeric(
            row.get("pb_ratio")
        ),
        "ev_ebitda": safe_numeric(
            row.get("ev_ebitda")
        ),
        "dividend_yield": safe_numeric(
            row.get(
                "dividend_yield_pct"
            )
        ),
        "market_cap": safe_numeric(
            row.get(
                "market_cap_crore"
            )
        ),
    }


def build_peer_dataframe(
    peer_members,
    selected_year,
):
    """
    Build a complete peer-comparison DataFrame.
    """

    rows = []

    for _, peer in peer_members.iterrows():

        ticker = peer["company_id"]

        ratio = get_ratio_row(
            ticker,
            selected_year,
        )

        if ratio is None:
            continue

        valuation = get_valuation_row(
            ticker,
            selected_year,
        )

        if valuation is None:

            valuation = {
                "pe_ratio": np.nan,
                "pb_ratio": np.nan,
                "ev_ebitda": np.nan,
                "dividend_yield": np.nan,
                "market_cap": np.nan,
            }

        revenue_cagr = calculate_revenue_cagr(
            ticker,
            selected_year,
        )

        rows.append(
            {
                "company_id": ticker,
                "company": peer.get(
                    "company_name",
                    ticker,
                ),
                "is_benchmark": int(
                    safe_numeric(
                        peer.get(
                            "is_benchmark",
                            0,
                        )
                    )
                    or 0
                ),
                "roe": safe_numeric(
                    ratio.get(
                        "return_on_equity_pct"
                    )
                ),
                "roce": safe_numeric(
                    ratio.get(
                        "roce_percentage"
                    )
                ),
                "revenue_cagr": revenue_cagr,
                "debt_to_equity": safe_numeric(
                    ratio.get(
                        "debt_to_equity"
                    )
                ),
                "fcf": safe_numeric(
                    ratio.get(
                        "free_cash_flow_cr"
                    )
                ),
                "net_profit_margin": safe_numeric(
                    ratio.get(
                        "net_profit_margin_pct"
                    )
                ),
                "operating_margin": safe_numeric(
                    ratio.get(
                        "operating_profit_margin_pct"
                    )
                ),
                "interest_coverage": safe_numeric(
                    ratio.get(
                        "interest_coverage"
                    )
                ),
                "pe_ratio": valuation[
                    "pe_ratio"
                ],
                "pb_ratio": valuation[
                    "pb_ratio"
                ],
                "ev_ebitda": valuation[
                    "ev_ebitda"
                ],
                "dividend_yield": valuation[
                    "dividend_yield"
                ],
                "market_cap": valuation[
                    "market_cap"
                ],
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title("Nifty 100 Peer Comparison")

st.markdown(
    """
Compare companies within the same peer group using
financial quality, growth, leverage and valuation metrics.
"""
)


# ---------------------------------------------------------------------
# Load companies
# ---------------------------------------------------------------------

companies = get_companies()

if companies.empty:

    st.error(
        "No company data is available."
    )

    st.stop()


# ---------------------------------------------------------------------
# Financial year selector
# ---------------------------------------------------------------------

available_years = list(
    range(
        2019,
        2025,
    )
)

selected_year = st.selectbox(
    "Financial Year",
    available_years,
    index=len(
        available_years
    ) - 1,
)


# ---------------------------------------------------------------------
# Discover peer groups
# ---------------------------------------------------------------------

peer_group_query = """
SELECT DISTINCT peer_group_name
FROM peer_groups
WHERE peer_group_name IS NOT NULL
ORDER BY peer_group_name
"""


# get_peers() requires a group name, so discover available
# groups directly through the database connection used by db.py.

try:

    from src.dashboard.utils.db import _get_connection

    with _get_connection() as conn:

        peer_groups_df = pd.read_sql_query(
            peer_group_query,
            conn,
        )

except Exception as exc:

    st.error(
        f"Unable to load peer groups: {exc}"
    )

    st.stop()


if peer_groups_df.empty:

    st.warning(
        "No peer groups are available in the database."
    )

    st.stop()


peer_groups = (
    peer_groups_df[
        "peer_group_name"
    ]
    .dropna()
    .astype(str)
    .tolist()
)


# ---------------------------------------------------------------------
# Peer group selector
# ---------------------------------------------------------------------

selected_group = st.selectbox(
    "Select Peer Group",
    peer_groups,
)


# ---------------------------------------------------------------------
# Load peer members
# ---------------------------------------------------------------------

peer_members = get_peers(
    selected_group
)

if peer_members.empty:

    st.warning(
        "No companies are available for the selected peer group."
    )

    st.stop()


# ---------------------------------------------------------------------
# Build comparison data
# ---------------------------------------------------------------------

with st.spinner(
    "Loading peer financial data..."
):

    peer_df = build_peer_dataframe(
        peer_members,
        selected_year,
    )


if peer_df.empty:

    st.error(
        "Financial data could not be loaded for "
        "the selected peer group."
    )

    st.stop()


# ---------------------------------------------------------------------
# Benchmark
# ---------------------------------------------------------------------

benchmark_df = peer_df[
    peer_df["is_benchmark"] == 1
].copy()


if benchmark_df.empty:

    benchmark_df = peer_df.head(1).copy()

    benchmark_available = False

else:

    benchmark_available = True


benchmark_name = benchmark_df.iloc[0][
    "company"
]


# ---------------------------------------------------------------------
# Header information
# ---------------------------------------------------------------------

st.divider()

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:

    st.metric(
        "Peer Group",
        selected_group,
    )

with info_col2:

    st.metric(
        "Companies",
        len(peer_df),
    )

with info_col3:

    st.metric(
        "Benchmark",
        benchmark_name,
    )


if not benchmark_available:

    st.info(
        "No benchmark was explicitly marked in this "
        "peer group. The first available company is "
        "being used as the comparison reference."
    )


# ---------------------------------------------------------------------
# Benchmark metrics
# ---------------------------------------------------------------------

benchmark = benchmark_df.iloc[0]


st.subheader(
    f"Benchmark: {benchmark_name}"
)

benchmark_cols = st.columns(6)

benchmark_metrics = [
    (
        "ROE",
        benchmark["roe"],
        "%",
    ),
    (
        "ROCE",
        benchmark["roce"],
        "%",
    ),
    (
        "Revenue CAGR",
        benchmark["revenue_cagr"],
        "%",
    ),
    (
        "P/E",
        benchmark["pe_ratio"],
        "",
    ),
    (
        "D/E",
        benchmark["debt_to_equity"],
        "",
    ),
    (
        "Market Cap",
        benchmark["market_cap"],
        " Cr",
    ),
]


for column, metric in zip(
    benchmark_cols,
    benchmark_metrics,
):

    label, value, suffix = metric

    with column:

        if pd.isna(value):

            display_value = "N/A"

        elif suffix == "%":

            display_value = (
                f"{value:.2f}%"
            )

        elif suffix == " Cr":

            display_value = (
                f"{value:,.0f} Cr"
            )

        else:

            display_value = (
                f"{value:.2f}"
            )

        st.metric(
            label,
            display_value,
        )


# ---------------------------------------------------------------------
# Relative performance
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Relative Performance vs Benchmark"
)


comparison_metrics = [
    "roe",
    "roce",
    "revenue_cagr",
    "debt_to_equity",
    "pe_ratio",
    "pb_ratio",
    "fcf",
    "dividend_yield",
]


comparison_labels = {
    "roe": "ROE (%)",
    "roce": "ROCE (%)",
    "revenue_cagr": "Revenue CAGR (%)",
    "debt_to_equity": "D/E",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B",
    "fcf": "FCF (₹ Cr)",
    "dividend_yield": "Dividend Yield (%)",
}


relative_df = peer_df.copy()


for metric in comparison_metrics:

    benchmark_value = benchmark[metric]

    if pd.isna(benchmark_value):

        relative_df[
            f"{metric}_vs_benchmark"
        ] = np.nan

    else:

        relative_df[
            f"{metric}_vs_benchmark"
        ] = (
            relative_df[metric]
            - benchmark_value
        )


# ---------------------------------------------------------------------
# Peer comparison table
# ---------------------------------------------------------------------

display_df = peer_df[
    [
        "company_id",
        "company",
        "is_benchmark",
        "roe",
        "roce",
        "revenue_cagr",
        "debt_to_equity",
        "fcf",
        "pe_ratio",
        "pb_ratio",
        "dividend_yield",
        "market_cap",
    ]
].copy()


display_df = display_df.rename(
    columns={
        "company_id": "Ticker",
        "company": "Company",
        "is_benchmark": "Benchmark",
        "roe": "ROE (%)",
        "roce": "ROCE (%)",
        "revenue_cagr": "Revenue CAGR (%)",
        "debt_to_equity": "D/E",
        "fcf": "FCF (₹ Cr)",
        "pe_ratio": "P/E",
        "pb_ratio": "P/B",
        "dividend_yield": "Dividend Yield (%)",
        "market_cap": "Market Cap (₹ Cr)",
    }
)


numeric_display_columns = [
    "ROE (%)",
    "ROCE (%)",
    "Revenue CAGR (%)",
    "D/E",
    "FCF (₹ Cr)",
    "P/E",
    "P/B",
    "Dividend Yield (%)",
    "Market Cap (₹ Cr)",
]


for column in numeric_display_columns:

    display_df[column] = display_df[
        column
    ].round(2)


display_df["Benchmark"] = display_df[
    "Benchmark"
].map(
    {
        1: "Yes",
        0: "",
    }
)


st.subheader(
    "Peer Comparison Table"
)

st.dataframe(
    display_df,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Peer Comparison Charts"
)


# ---------------------------------------------------------------------
# ROE comparison
# ---------------------------------------------------------------------

chart_df = peer_df.dropna(
    subset=["roe"]
).copy()

if not chart_df.empty:

    fig_roe = px.bar(
        chart_df.sort_values(
            "roe",
            ascending=False,
        ),
        x="company",
        y="roe",
        title="ROE Comparison",
        labels={
            "company": "Company",
            "roe": "ROE (%)",
        },
    )

    fig_roe.update_layout(
        height=450,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(
        fig_roe,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Revenue CAGR comparison
# ---------------------------------------------------------------------

chart_df = peer_df.dropna(
    subset=["revenue_cagr"]
).copy()

if not chart_df.empty:

    fig_growth = px.bar(
        chart_df.sort_values(
            "revenue_cagr",
            ascending=False,
        ),
        x="company",
        y="revenue_cagr",
        title="Revenue CAGR Comparison",
        labels={
            "company": "Company",
            "revenue_cagr": "Revenue CAGR (%)",
        },
    )

    fig_growth.update_layout(
        height=450,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(
        fig_growth,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Valuation comparison
# ---------------------------------------------------------------------

valuation_chart_df = peer_df[
    [
        "company",
        "pe_ratio",
        "pb_ratio",
    ]
].copy()

valuation_chart_df = valuation_chart_df.dropna(
    subset=[
        "pe_ratio",
        "pb_ratio",
    ],
    how="all",
)

if not valuation_chart_df.empty:

    melted = valuation_chart_df.melt(
        id_vars="company",
        value_vars=[
            "pe_ratio",
            "pb_ratio",
        ],
        var_name="metric",
        value_name="value",
    )

    melted["metric"] = melted[
        "metric"
    ].map(
        {
            "pe_ratio": "P/E",
            "pb_ratio": "P/B",
        }
    )

    fig_valuation = px.bar(
        melted,
        x="company",
        y="value",
        color="metric",
        barmode="group",
        title="Valuation Comparison",
        labels={
            "company": "Company",
            "value": "Multiple",
            "metric": "Metric",
        },
    )

    fig_valuation.update_layout(
        height=450,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(
        fig_valuation,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Leverage comparison
# ---------------------------------------------------------------------

leverage_df = peer_df.dropna(
    subset=["debt_to_equity"]
).copy()

if not leverage_df.empty:

    fig_de = px.bar(
        leverage_df.sort_values(
            "debt_to_equity",
            ascending=True,
        ),
        x="company",
        y="debt_to_equity",
        title="Debt-to-Equity Comparison",
        labels={
            "company": "Company",
            "debt_to_equity": "Debt / Equity",
        },
    )

    fig_de.update_layout(
        height=450,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(
        fig_de,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Peer ranking
# ---------------------------------------------------------------------

st.divider()

st.subheader(
    "Peer Quality Ranking"
)


ranking_df = peer_df.copy()


# A simple relative ranking based on available
# quality-oriented metrics.

ranking_metrics = [
    "roe",
    "roce",
    "revenue_cagr",
    "debt_to_equity",
]


for metric in ranking_metrics:

    ranking_df[
        f"{metric}_rank"
    ] = ranking_df[
        metric
    ].rank(
        ascending=(
            metric
            == "debt_to_equity"
        ),
        method="average",
        na_option="keep",
    )


rank_columns = [
    f"{metric}_rank"
    for metric in ranking_metrics
]


ranking_df["average_rank"] = ranking_df[
    rank_columns
].mean(
    axis=1,
)


ranking_df = ranking_df.sort_values(
    "average_rank",
    ascending=True,
)


ranking_display = ranking_df[
    [
        "company_id",
        "company",
        "roe",
        "roce",
        "revenue_cagr",
        "debt_to_equity",
        "average_rank",
    ]
].copy()


ranking_display = ranking_display.rename(
    columns={
        "company_id": "Ticker",
        "company": "Company",
        "roe": "ROE (%)",
        "roce": "ROCE (%)",
        "revenue_cagr": "Revenue CAGR (%)",
        "debt_to_equity": "D/E",
        "average_rank": "Average Rank",
    }
)


for column in [
    "ROE (%)",
    "ROCE (%)",
    "Revenue CAGR (%)",
    "D/E",
    "Average Rank",
]:

    ranking_display[column] = ranking_display[
        column
    ].round(2)


st.dataframe(
    ranking_display,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------

st.divider()

csv_data = display_df.to_csv(
    index=False
).encode(
    "utf-8"
)


st.download_button(
    label="Download Peer Comparison CSV",
    data=csv_data,
    file_name=(
        f"peer_comparison_"
        f"{selected_group.replace(' ', '_')}_"
        f"{selected_year}.csv"
    ),
    mime="text/csv",
    width="stretch",
)


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

with st.expander(
    "Peer Comparison Methodology"
):

    st.markdown(
        """
### Peer Comparison

Companies are grouped using the peer-group definitions
stored in the project's `peer_groups` database table.

The comparison includes:

- **ROE** — Return on Equity
- **ROCE** — Return on Capital Employed
- **Revenue CAGR** — Five-year revenue growth
- **D/E** — Debt-to-Equity
- **FCF** — Free Cash Flow
- **P/E** — Price-to-Earnings
- **P/B** — Price-to-Book
- **Dividend Yield**
- **Market Capitalization**
- **EV/EBITDA**
- **Interest Coverage**

The company marked as the benchmark in the database is
used as the primary reference point.

If a peer group has no explicit benchmark, the first
available company is used as a fallback reference.

Revenue CAGR is calculated directly from the Profit &
Loss history when required data is available.
        """
    )