SELECT
    p.company_id,
    p.year,
    p.sales,
    p.net_profit,
    b.total_assets,
    b.total_liabilities
FROM profit_loss p
JOIN balance_sheet b
ON p.company_id = b.company_id
AND p.year = b.year
LIMIT 20;