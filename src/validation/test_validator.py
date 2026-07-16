from src.etl.loader import ExcelLoader
from src.validation.validator import DataValidator

loader = ExcelLoader("data/raw")

datasets = loader.load_all()

validator = DataValidator()

for name, df in datasets.items():

    validator.check_missing_values(df, name)

    validator.check_duplicate_rows(df, name)

    validator.check_empty_columns(df, name)

    validator.check_year(df, name)

    validator.check_negative_values(df, name)

validator.generate_report()