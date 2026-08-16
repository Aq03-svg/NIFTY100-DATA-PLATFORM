"""
NIFTY 100 Analytics Dashboard

Main Streamlit application entry point.
"""

import streamlit as st


# ---------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# Application header
# ---------------------------------------------------------------------

st.title("Nifty 100 Analytics")

st.markdown(
    """
    ### Financial Intelligence Platform

    Explore company fundamentals, financial ratios, peer comparisons,
    trends, sector analysis, capital allocation patterns, and reports.
    """
)


# ---------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------

st.sidebar.title("Navigation")

st.sidebar.markdown(
    """
    Select a section below to explore the Nifty 100 universe.
    """
)


# ---------------------------------------------------------------------
# Dashboard home
# ---------------------------------------------------------------------

st.subheader("Dashboard")

st.write(
    "Use the navigation menu to explore the available analytics screens."
)


# ---------------------------------------------------------------------
# Available screens
# ---------------------------------------------------------------------

st.markdown("### Available Screens")

screens = [
    "Home",
    "Company Profile",
    "Screener",
    "Peer Comparison",
    "Trend Analysis",
    "Sector Analysis",
    "Capital Allocation",
    "Annual Reports",
]

for number, screen in enumerate(screens, start=1):
    st.write(f"{number}. {screen}")