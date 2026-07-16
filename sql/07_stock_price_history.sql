SELECT
    company_id,
    date,
    open_price,
    close_price,
    volume
FROM stock_prices
WHERE company_id='ABB'
ORDER BY date;