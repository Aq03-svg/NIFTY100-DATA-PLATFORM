import plotly.express as px


def market_cap_chart(df):

    fig = px.bar(
        df,
        x="company_id",
        y="market_cap",
        title="Top 10 Companies by Market Capitalization",
        text_auto=".2s",
    )

    fig.update_layout(
        height=500,
        xaxis_title="Company",
        yaxis_title="Market Cap (Crore)",
    )

    return fig


def sector_chart(df):

    fig = px.pie(
        df,
        names="broad_sector",
        values="companies",
        title="Sector Distribution",
    )

    return fig
def stock_price_chart(df):

    fig = px.line(

        df,

        x="date",

        y="close_price",

        title="Stock Price Trend"

    )

    fig.update_layout(

        xaxis_title="Date",

        yaxis_title="Close Price (₹)",

        height=450

    )

    return fig

import plotly.express as px


def revenue_trend_chart(df):

    fig = px.line(
        df,
        x="year",
        y="sales",
        markers=True,
        title="Revenue Trend"
    )

    fig.update_layout(xaxis_title="Year",
                      yaxis_title="Sales (₹ Cr)")

    return fig


def profit_trend_chart(df):

    fig = px.line(
        df,
        x="year",
        y="net_profit",
        markers=True,
        title="Net Profit Trend"
    )

    fig.update_layout(xaxis_title="Year",
                      yaxis_title="Net Profit (₹ Cr)")

    return fig