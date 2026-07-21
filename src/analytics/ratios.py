"""
Financial Ratio Engine

Sprint 2 – Financial Ratio Engine

This module contains reusable functions for computing
financial ratios for NIFTY100 companies.

Each function:

• accepts raw financial values
• handles edge cases
• returns None where computation is invalid
• contains no database logic

Author: Aqeeb Javeed Shaikh
"""


def net_profit_margin(net_profit, sales):
    """
    Net Profit Margin (%)

    Formula:
        (Net Profit / Sales) * 100

    Returns:
        float | None
    """
    if sales is None or net_profit is None:
        return None
    
    if sales == 0:
        return None

    return round((net_profit / sales) * 100, 2)



def operating_profit_margin(operating_profit, sales):
    """
    Operating Profit Margin (%)

    Formula:
        (Operating Profit / Sales) * 100

    Returns:
        float | None
    """
    if operating_profit is None or sales is None:
        return None

    if sales == 0:
        return None

    return round((operating_profit / sales) * 100, 2)


def return_on_equity(net_profit, shareholder_equity):
    """
    Return on Equity (ROE)

    Formula:
        (Net Profit / Shareholder Equity) * 100

    Returns:
        float | None
    """

    if net_profit is None or shareholder_equity is None:
        return None

    if shareholder_equity == 0:
        return None

    return round((net_profit / shareholder_equity) * 100, 2)


def return_on_capital_employed(ebit, capital_employed):
    """
    Return on Capital Employed (ROCE)

    Formula:
        (EBIT / Capital Employed) * 100

    Returns:
        float | None
    """

    if ebit is None or capital_employed is None:
        return None

    if capital_employed == 0:
        return None

    return round((ebit / capital_employed) * 100, 2)


def return_on_assets(net_profit, total_assets):
    """
    Return on Assets (ROA)

    Formula:
        (Net Profit / Total Assets) * 100

    Returns:
        float | None
    """

    if net_profit is None or total_assets is None:
        return None

    if total_assets == 0:
        return None

    return round((net_profit / total_assets) * 100, 2)