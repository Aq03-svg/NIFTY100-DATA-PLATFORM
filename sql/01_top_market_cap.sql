SELECT
    company_id,
    year,
    market_cap_crore
FROM market_cap
ORDER BY market_cap_crore DESC
LIMIT 10;