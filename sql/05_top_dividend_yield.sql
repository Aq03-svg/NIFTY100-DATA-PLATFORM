SELECT
    company_id,
    year,
    dividend_yield_pct AS dividend_yield
FROM market_cap
ORDER BY dividend_yield_pct DESC
LIMIT 10;