import pytest

from src.analytics.ratios import (
    net_profit_margin,
    operating_profit_margin,
    return_on_equity,
    return_on_capital_employed,
    return_on_assets,
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