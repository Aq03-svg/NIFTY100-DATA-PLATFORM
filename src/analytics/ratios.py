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

def compound_annual_growth_rate(beginning_value, ending_value, years):
    """
    Compound Annual Growth Rate (CAGR)

    Formula:
        ((Ending Value / Beginning Value) ** (1 / Years) - 1) * 100

    Returns:
        float | None
    """

    if (
        beginning_value is None
        or ending_value is None
        or years is None
    ):
        return None

    if beginning_value <= 0:
        return None

    if years <= 0:
        return None

    cagr = ((ending_value / beginning_value) ** (1 / years) - 1) * 100

    return round(cagr, 2)

def operating_cash_flow(cash_from_operations):
    """
    Operating Cash Flow (OCF)

    Returns:
        float | None
    """

    if cash_from_operations is None:
        return None

    return round(cash_from_operations, 2)

def free_cash_flow(operating_cash_flow, capital_expenditure):
    """
    Free Cash Flow (FCF)

    Formula:
        Operating Cash Flow - Capital Expenditure

    Returns:
        float | None
    """

    if operating_cash_flow is None or capital_expenditure is None:
        return None

    return round(operating_cash_flow - capital_expenditure, 2)

def cash_conversion_ratio(operating_cash_flow, net_profit):
    """
    Cash Conversion Ratio (CCR)

    Formula:
        Operating Cash Flow / Net Profit

    Returns:
        float | None
    """

    if operating_cash_flow is None or net_profit is None:
        return None

    if net_profit == 0:
        return None

    return round(operating_cash_flow / net_profit, 2)

def operating_cash_flow_margin(operating_cash_flow, revenue):
    """
    Operating Cash Flow Margin

    Formula:
        (Operating Cash Flow / Revenue) * 100

    Returns:
        float | None
    """

    if operating_cash_flow is None or revenue is None:
        return None

    if revenue == 0:
        return None

    return round((operating_cash_flow / revenue) * 100, 2)