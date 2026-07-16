SELECT
    company_id,
    year,
    pe_ratio AS pe_ratio
FROM market_cap
ORDER BY pe_ratio DESC
LIMIT 10;