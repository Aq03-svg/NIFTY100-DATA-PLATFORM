# KPI Queries

TOTAL_COMPANIES = """
SELECT COUNT(*) AS total
FROM companies;
"""

TOTAL_SECTORS = """
SELECT COUNT(DISTINCT broad_sector) AS total
FROM sectors;
"""

MAX_MARKET_CAP = """
SELECT ROUND(MAX(market_cap_crore),2) AS max_cap
FROM market_cap;
"""

TOP_MARKET_CAP = """
SELECT
    company_id,
    MAX(market_cap_crore) AS market_cap
FROM market_cap
GROUP BY company_id
ORDER BY market_cap DESC
LIMIT 10;
"""

SECTOR_DISTRIBUTION = """
SELECT
    broad_sector,
    COUNT(*) AS companies
FROM sectors
GROUP BY broad_sector
ORDER BY companies DESC;
"""

COMPANIES = """
SELECT
    id,
    company_name
FROM companies
ORDER BY id;
"""
COMPANY_SNAPSHOT = """
SELECT
    p.year,
    p.sales,
    p.operating_profit,
    p.net_profit,
    b.total_assets,
    b.total_liabilities
FROM profit_loss p
JOIN balance_sheet b
ON p.company_id = b.company_id
AND p.year = b.year
WHERE p.company_id = '{}'
ORDER BY p.year DESC
LIMIT 1;
"""
COMPANY_FINANCIAL_HISTORY = """
SELECT
    year,
    sales,
    operating_profit,
    net_profit
FROM profit_loss
WHERE company_id = '{}'
ORDER BY year DESC;
"""
COMPANY_STOCK_HISTORY = """
SELECT
    date,
    close_price
FROM stock_prices
WHERE company_id = '{}'
ORDER BY date;
"""

print("LOADED NEW QUERIES FILE")

print(">>> queries.py loaded <<<")
print("Has COMPANY_SNAPSHOT:", "COMPANY_SNAPSHOT" in globals())