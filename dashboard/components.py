import streamlit as st


def show_kpis(companies, sectors, market_cap):

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("🏢 Companies", companies)

    with c2:
        st.metric("📂 Sectors", sectors)

    with c3:
        st.metric(
            "💰 Highest Market Cap (Cr)",
            f"{market_cap:,.0f}",
        )
def company_snapshot(df):

    if df.empty:
        st.warning("No financial data available.")
        return

    row = df.iloc[0]

    st.markdown("### 📊 Latest Financial Snapshot")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Sales",
            f"₹ {row['sales']:,}"
        )

    with c2:
        st.metric(
            "Operating Profit",
            f"₹ {row['operating_profit']:,}"
        )

    with c3:
        st.metric(
            "Net Profit",
            f"₹ {row['net_profit']:,}"
        )

    with c4:
        st.metric(
            "Total Assets",
            f"₹ {row['total_assets']:,}"
        )
def financial_history(df):

    st.subheader("📑 Financial History")

    if df.empty:
        st.warning("No financial history available.")
        return

    st.dataframe(
    df,
    width="stretch",
    height=300,
    hide_index=True
)