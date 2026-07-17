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