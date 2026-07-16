SELECT
    company_id,
    year,
    ROUND(return_on_equity_pct / 100.0, 2) AS roe_percentage
FROM financial_ratios
ORDER BY roe_percentage DESC
LIMIT 10;