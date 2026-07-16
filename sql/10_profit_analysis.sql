SELECT
    company_id,
    year,
    sales,
    operating_profit,
    net_profit
FROM profit_loss
ORDER BY net_profit DESC
LIMIT 20;