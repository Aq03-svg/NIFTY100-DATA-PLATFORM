SELECT
    company_id,
    year,
    total_assets,
    total_liabilities
FROM balance_sheet
ORDER BY total_assets DESC
LIMIT 20;