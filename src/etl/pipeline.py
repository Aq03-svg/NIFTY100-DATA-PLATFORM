from src.etl.loader import ExcelLoader
from src.validation.validator import DataValidator
from src.etl.sqlite_loader import SQLiteLoader
from src.etl.db_loader import DatabaseLoader


def main():

    print("=" * 70)
    print("NIFTY100 DATA PLATFORM ETL PIPELINE")
    print("=" * 70)

    # 1. Load Excel Files
    loader = ExcelLoader("data/raw")
    datasets = loader.load_all()
    companies = datasets["companies"]["id"]
    

    # 2. Validate Data
    validator = DataValidator()

    for name, df in datasets.items():
        

        validator.check_missing_values(df, name)
        validator.check_duplicate_rows(df, name)
        validator.check_empty_columns(df, name)
        validator.check_year(df, name)
        validator.check_negative_values(df, name)
        validator.check_primary_key_duplicates(df, name)

        validator.check_company_id(
            df,
            name,
            companies
        )

        validator.check_positive_sales(df, name)

        validator.check_stock_prices(df, name)

    validator.generate_report()

    # 3. Create Database
    sqlite = SQLiteLoader("db/nifty100.db")
    sqlite.create_schema()
    sqlite.close()

    # 4. Load Database
    database = DatabaseLoader("db/nifty100.db")

    table_map = {

        "companies": "companies",
        "balancesheet": "balance_sheet",
        "cashflow": "cash_flow",
        "profitandloss": "profit_loss",
        "financial_ratios": "financial_ratios",
        "market_cap": "market_cap",
        "peer_groups": "peer_groups",
        "stock_prices": "stock_prices",
        "documents": "documents",
        "analysis": "analysis",
        "prosandcons": "prosandcons",
        "sectors": "sectors"

    }

    for dataset_name, dataframe in datasets.items():

        table = table_map[dataset_name]

        database.load_dataframe(dataframe, table)

    database.close()

    print("\nETL Pipeline Completed Successfully")


if __name__ == "__main__":
    main()