import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
    debt_to_equity,
    interest_coverage_ratio,
    net_debt,
    asset_turnover_ratio,
    compound_annual_growth_rate,
    operating_cash_flow,
    free_cash_flow,
    cash_conversion_ratio,
    operating_cash_flow_margin,
)


# ==========================================================
# Net Profit Margin Tests
# ==========================================================

def test_net_profit_margin_normal():
    assert net_profit_margin(200, 1000) == 20.00


def test_net_profit_margin_zero_sales():
    assert net_profit_margin(200, 0) is None


def test_net_profit_margin_none_sales():
    assert net_profit_margin(200, None) is None


def test_net_profit_margin_none_profit():
    assert net_profit_margin(None, 1000) is None


def test_net_profit_margin_negative_profit():
    assert net_profit_margin(-100, 1000) == -10.00


# ==========================================================
# Operating Profit Margin Tests
# ==========================================================

def test_operating_profit_margin_normal():
    assert operating_profit_margin(300, 1000) == 30.00


def test_operating_profit_margin_zero_sales():
    assert operating_profit_margin(300, 0) is None


def test_operating_profit_margin_none_sales():
    assert operating_profit_margin(300, None) is None


def test_operating_profit_margin_none_profit():
    assert operating_profit_margin(None, 1000) is None


def test_operating_profit_margin_negative_profit():
    assert operating_profit_margin(-200, 1000) == -20.00

# ==========================================================
# Return on Equity Tests
# ==========================================================

def test_return_on_equity_normal():
    assert return_on_equity(500, 2500) == 20.00


def test_return_on_equity_zero_equity():
    assert return_on_equity(500, 0) is None


def test_return_on_equity_none_equity():
    assert return_on_equity(500, None) is None


def test_return_on_equity_none_profit():
    assert return_on_equity(None, 2500) is None


def test_return_on_equity_negative_profit():
    assert return_on_equity(-200, 2500) == -8.00

# ==========================================================
# Return on Capital Employed (ROCE) Tests
# ==========================================================

def test_return_on_capital_employed_normal():
    assert return_on_capital_employed(800, 4000) == 20.00


def test_return_on_capital_employed_zero_capital():
    assert return_on_capital_employed(800, 0) is None


def test_return_on_capital_employed_none_capital():
    assert return_on_capital_employed(800, None) is None


def test_return_on_capital_employed_none_ebit():
    assert return_on_capital_employed(None, 4000) is None


def test_return_on_capital_employed_negative_ebit():
    assert return_on_capital_employed(-400, 4000) == -10.00

# ==========================================================
# Return on Assets (ROA) Tests
# ==========================================================

def test_return_on_assets_normal():
    assert return_on_assets(400, 2000) == 20.00


def test_return_on_assets_zero_assets():
    assert return_on_assets(400, 0) is None


def test_return_on_assets_none_assets():
    assert return_on_assets(400, None) is None


def test_return_on_assets_none_profit():
    assert return_on_assets(None, 2000) is None


def test_return_on_assets_negative_profit():
    assert return_on_assets(-100, 2000) == -5.00

# ==========================================================
# Debt-to-Equity Ratio Tests
# ==========================================================

def test_debt_to_equity_normal():
    assert debt_to_equity(2000, 1000) == 2.00


def test_debt_to_equity_zero_equity():
    assert debt_to_equity(2000, 0) is None


def test_debt_to_equity_none_equity():
    assert debt_to_equity(2000, None) is None


def test_debt_to_equity_none_debt():
    assert debt_to_equity(None, 1000) is None


def test_debt_to_equity_zero_debt():
    assert debt_to_equity(0, 1000) == 0.00

# ==========================================================
# Interest Coverage Ratio Tests
# ==========================================================

def test_interest_coverage_ratio_normal():
    assert interest_coverage_ratio(1000, 200) == 5.00


def test_interest_coverage_ratio_zero_interest():
    assert interest_coverage_ratio(1000, 0) is None


def test_interest_coverage_ratio_none_interest():
    assert interest_coverage_ratio(1000, None) is None


def test_interest_coverage_ratio_none_ebit():
    assert interest_coverage_ratio(None, 200) is None


def test_interest_coverage_ratio_negative_ebit():
    assert interest_coverage_ratio(-500, 200) == -2.50

# ==========================================================
# Net Debt Tests
# ==========================================================

def test_net_debt_normal():
    assert net_debt(5000, 1200) == 3800.00


def test_net_debt_zero_cash():
    assert net_debt(5000, 0) == 5000.00


def test_net_debt_more_cash_than_debt():
    assert net_debt(3000, 5000) == -2000.00


def test_net_debt_none_debt():
    assert net_debt(None, 1000) is None


def test_net_debt_none_cash():
    assert net_debt(5000, None) is None

# ==========================================================
# Asset Turnover Ratio Tests
# ==========================================================

def test_asset_turnover_ratio_normal():
    assert asset_turnover_ratio(10000, 5000) == 2.00


def test_asset_turnover_ratio_zero_assets():
    assert asset_turnover_ratio(10000, 0) is None


def test_asset_turnover_ratio_none_assets():
    assert asset_turnover_ratio(10000, None) is None


def test_asset_turnover_ratio_none_revenue():
    assert asset_turnover_ratio(None, 5000) is None


def test_asset_turnover_ratio_zero_revenue():
    assert asset_turnover_ratio(0, 5000) == 0.00

# ==========================================================
# Compound Annual Growth Rate (CAGR) Tests
# ==========================================================

def test_cagr_normal():
    assert compound_annual_growth_rate(100, 200, 5) == 14.87


def test_cagr_same_value():
    assert compound_annual_growth_rate(100, 100, 5) == 0.00


def test_cagr_zero_beginning():
    assert compound_annual_growth_rate(0, 200, 5) is None


def test_cagr_negative_beginning():
    assert compound_annual_growth_rate(-100, 200, 5) is None


def test_cagr_zero_years():
    assert compound_annual_growth_rate(100, 200, 0) is None


def test_cagr_none_beginning():
    assert compound_annual_growth_rate(None, 200, 5) is None


def test_cagr_none_ending():
    assert compound_annual_growth_rate(100, None, 5) is None


def test_cagr_none_years():
    assert compound_annual_growth_rate(100, 200, None) is None

# ==========================================================
# Operating Cash Flow (OCF) Tests
# ==========================================================

def test_operating_cash_flow_normal():
    assert operating_cash_flow(2500) == 2500.00


def test_operating_cash_flow_zero():
    assert operating_cash_flow(0) == 0.00


def test_operating_cash_flow_negative():
    assert operating_cash_flow(-500) == -500.00


def test_operating_cash_flow_none():
    assert operating_cash_flow(None) is None


def test_operating_cash_flow_decimal():
    assert operating_cash_flow(1234.567) == 1234.57

# ==========================================================
# Free Cash Flow (FCF) Tests
# ==========================================================

def test_free_cash_flow_normal():
    assert free_cash_flow(5000, 1200) == 3800.00


def test_free_cash_flow_zero_capex():
    assert free_cash_flow(5000, 0) == 5000.00


def test_free_cash_flow_negative_result():
    assert free_cash_flow(1000, 2000) == -1000.00


def test_free_cash_flow_none_ocf():
    assert free_cash_flow(None, 500) is None


def test_free_cash_flow_none_capex():
    assert free_cash_flow(5000, None) is None

# ==========================================================
# Cash Conversion Ratio (CCR) Tests
# ==========================================================

def test_cash_conversion_ratio_normal():
    assert cash_conversion_ratio(3000, 2000) == 1.50


def test_cash_conversion_ratio_zero_profit():
    assert cash_conversion_ratio(3000, 0) is None


def test_cash_conversion_ratio_none_ocf():
    assert cash_conversion_ratio(None, 2000) is None


def test_cash_conversion_ratio_none_profit():
    assert cash_conversion_ratio(3000, None) is None


def test_cash_conversion_ratio_negative_profit():
    assert cash_conversion_ratio(3000, -1500) == -2.00

# ==========================================================
# Operating Cash Flow Margin Tests
# ==========================================================

def test_operating_cash_flow_margin_normal():
    assert operating_cash_flow_margin(2500, 10000) == 25.00


def test_operating_cash_flow_margin_zero_revenue():
    assert operating_cash_flow_margin(2500, 0) is None


def test_operating_cash_flow_margin_none_ocf():
    assert operating_cash_flow_margin(None, 10000) is None


def test_operating_cash_flow_margin_none_revenue():
    assert operating_cash_flow_margin(2500, None) is None


def test_operating_cash_flow_margin_negative_ocf():
    assert operating_cash_flow_margin(-1000, 10000) == -10.00