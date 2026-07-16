from src.utils.logger import logger
import pandas as pd


class DataValidator:

    def __init__(self):
        self.failures = []

    # ----------------------------
    # DQ Rule 1 - Missing Values
    # ----------------------------
    def check_missing_values(self, df, dataset_name):

        missing = df.isnull().sum()

        for column, count in missing.items():

            if count > 0:

                self.failures.append({
                    "dataset": dataset_name,
                    "rule": "Missing Values",
                    "column": column,
                    "failed_records": int(count)
                })

    # ----------------------------
    # DQ Rule 2 - Duplicate Rows
    # ----------------------------
    def check_duplicate_rows(self, df, dataset_name):

        duplicates = df.duplicated().sum()

        if duplicates > 0:

            self.failures.append({
                "dataset": dataset_name,
                "rule": "Duplicate Rows",
                "column": "-",
                "failed_records": int(duplicates)
            })

    # ----------------------------
    # DQ Rule 3 - Empty Columns
    # ----------------------------
    def check_empty_columns(self, df, dataset_name):

        for column in df.columns:

            if df[column].count() == 0:

                self.failures.append({
                    "dataset": dataset_name,
                    "rule": "Empty Column",
                    "column": column,
                    "failed_records": len(df)
                })

    # ----------------------------
    # DQ Rule 4 - Invalid Year
    # ----------------------------
    def check_year(self, df, dataset_name):
        if "year" not in df.columns:
            return

    # Extract a 4-digit year from strings like "Dec 2012", "Mar-13", "2024"
        years = (
            df["year"]
            .astype(str)
            .str.extract(r"(\d{4})")[0]
        )

        years = pd.to_numeric(years, errors="coerce")

        invalid = years[(years < 1990) | (years > 2035)]

        if not invalid.empty:

            self.failures.append({
                "dataset": dataset_name,
                "rule": "Invalid Year",
                "column": "year",
                "failed_records": len(invalid)
            })

    # ----------------------------
    # DQ Rule 5 - Negative Values
    # ----------------------------
    def check_negative_values(self, df, dataset_name):

        numeric = df.select_dtypes(include="number")

        for column in numeric.columns:

            count = (numeric[column] < 0).sum()

            if count:

                self.failures.append({
                    "dataset": dataset_name,
                    "rule": "Negative Values",
                    "column": column,
                    "failed_records": int(count)
                })

    # ----------------------------
    # Generate Validation Report
    # ----------------------------
    def generate_report(self):

        report = pd.DataFrame(self.failures)

        report.to_csv(
            "data/output/validation_failures.csv",
            index=False
        )
    def check_primary_key_duplicates(self, df, dataset_name):

        if "id" not in df.columns:
            return

        duplicates = df["id"].duplicated().sum()

        if duplicates:

            self.failures.append({
                "dataset": dataset_name,
                "rule": "Primary Key Duplicate",
                "column": "id",
                "failed_records": int(duplicates)
            })
    def check_company_id(self, df, dataset_name, companies):

        if "company_id" not in df.columns:
            return

        company_ids = (
            pd.Series(companies)
            .astype(str)
            .str.strip()
            .str.upper()
        )

        current_ids = (
            df["company_id"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        invalid = ~current_ids.isin(company_ids)

        count = int(invalid.sum())

        if count:

            self.failures.append({
                "dataset": dataset_name,
                "rule": "Foreign Key",
                "column": "company_id",
                "failed_records": count
            })
    def check_positive_sales(self, df, dataset_name):

        if "sales" not in df.columns:
            return

        sales = pd.to_numeric(df["sales"], errors="coerce")

        invalid = sales <= 0

        if invalid.sum():

            self.failures.append({
                "dataset": dataset_name,
                "rule": "Positive Sales",
                "column": "sales",
                "failed_records": int(invalid.sum())
            })
    def check_stock_prices(self, df, dataset_name):

        needed = [
            "open_price",
            "high_price",
            "low_price",
            "close_price"
        ]

        if not all(col in df.columns for col in needed):
            return

        invalid = (
            (df["high_price"] < df["low_price"]) |
            (df["high_price"] < df["open_price"]) |
            (df["high_price"] < df["close_price"])
        )

        if invalid.sum():

            self.failures.append({
                "dataset": dataset_name,
                "rule": "Stock Price Validation",
                "column": "high_price",
                "failed_records": int(invalid.sum())
            })

        logger.info("Validation Report Generated")