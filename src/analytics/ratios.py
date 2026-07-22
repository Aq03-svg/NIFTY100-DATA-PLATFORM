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

def debt_to_equity(total_debt, shareholder_equity):
    """
    Debt-to-Equity Ratio

    Formula:
        Total Debt / Shareholder Equity

    Returns:
        float | None
    """

    if total_debt is None or shareholder_equity is None:
        return None

    if shareholder_equity == 0:
        return None

    return round(total_debt / shareholder_equity, 2)

def interest_coverage_ratio(ebit, interest_expense):
    """
    Interest Coverage Ratio

    Formula:
        EBIT / Interest Expense

    Returns:
        float | None
    """

    if ebit is None or interest_expense is None:
        return None

    if interest_expense == 0:
        return None

    return round(ebit / interest_expense, 2)

def net_debt(total_debt, cash_and_equivalents):
    """
    Net Debt

    Formula:
        Total Debt - Cash & Cash Equivalents

    Returns:
        float | None
    """

    if total_debt is None or cash_and_equivalents is None:
        return None

    return round(total_debt - cash_and_equivalents, 2)

def asset_turnover_ratio(revenue, average_total_assets):
    """
    Asset Turnover Ratio

    Formula:
        Revenue / Average Total Assets

    Returns:
        float | None
    """

    if revenue is None or average_total_assets is None:
        return None

    if average_total_assets == 0:
        return None

    return round(revenue / average_total_assets, 2)