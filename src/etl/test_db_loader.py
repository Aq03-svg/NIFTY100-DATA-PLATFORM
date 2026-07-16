from src.etl.loader import ExcelLoader
from src.etl.db_loader import DatabaseLoader

loader = ExcelLoader("data/raw")

datasets = loader.load_all()

database = DatabaseLoader("db/nifty100.db")

for name, dataframe in datasets.items():

    table_map = {
    "companies": "companies",
    "balancesheet": "balance_sheet",
    "profitandloss": "profit_loss",
    "cashflow": "cash_flow",
    "financial_ratios": "financial_ratios",
    "market_cap": "market_cap",
    "peer_groups": "peer_groups",
    "stock_prices": "stock_prices",
    "documents": "documents",
    "analysis": "analysis",
    "prosandcons": "prosandcons",
    "sectors": "sectors"
}

table_name = table_map[name]

database.load_dataframe(dataframe, table_name)

database.close()

print("\nAll datasets loaded into SQLite.")