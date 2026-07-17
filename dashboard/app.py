import streamlit as st

from database import run_query
import queries
import charts
import components


# ---------------------------------------------------
# Page Configuration
# ---------------------------------------------------

st.set_page_config(
    page_title="NIFTY100 Data Platform",
    page_icon="📈",
    layout="wide"
)

st.title("📈 NIFTY100 Data Platform")

st.caption(
    "Interactive Financial Analytics Dashboard for NIFTY100 Companies"
)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------
# Load KPI Data
# ---------------------------------------------------

companies = run_query(queries.TOTAL_COMPANIES).iloc[0]["total"]
sectors = run_query(queries.TOTAL_SECTORS).iloc[0]["total"]
market_cap = run_query(queries.MAX_MARKET_CAP).iloc[0]["max_cap"]

with st.container():

    components.show_kpis(
        companies,
        sectors,
        market_cap
    )

st.divider()

# ---------------------------------------------------
# Charts
# ---------------------------------------------------

market_cap_df = run_query(
    queries.TOP_MARKET_CAP
)

sector_df = run_query(
    queries.SECTOR_DISTRIBUTION
)

fig_market = charts.market_cap_chart(
    market_cap_df
)

fig_sector = charts.sector_chart(
    sector_df
)

left, right = st.columns(
    [1.3, 1]
)

with left:
    st.plotly_chart(
        fig_market,
        width="stretch"
    )

with right:
    st.plotly_chart(
        fig_sector,
        width="stretch"
    )

st.markdown("---")

# ---------------------------------------------------
# Company Explorer
# ---------------------------------------------------

st.subheader("🔍 Company Explorer")

st.caption(
    "Explore financial metrics for individual companies."
)

company_df = run_query(
    queries.COMPANIES
)

selected_company = st.selectbox(
    "Select Company",
    options=company_df["id"],
    format_func=lambda x: company_df.loc[
        company_df["id"] == x,
        "company_name"
    ].iloc[0]
)

snapshot = run_query(
    queries.COMPANY_SNAPSHOT.format(selected_company)
)

components.company_snapshot(snapshot)
history = run_query(
    queries.COMPANY_FINANCIAL_HISTORY.format(selected_company)
)

components.financial_history(history)

stock_df = run_query(
    queries.COMPANY_STOCK_HISTORY.format(selected_company)
)

stock_fig = charts.stock_price_chart(stock_df)

st.plotly_chart(
    stock_fig,
    width="stretch"
)