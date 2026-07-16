# NIFTY100 Data Platform - ETL Summary

## Pipeline Status
- ETL Pipeline: Completed Successfully
- Validation: Completed
- SQLite Database: Created
- Audit Report: Generated

## Datasets Processed

| Dataset | Rows |
|---------|------:|
| companies | 92 |
| sectors | 92 |
| peer_groups | 56 |
| market_cap | 552 |
| financial_ratios | 1184 |
| balance_sheet | 1312 |
| cash_flow | 1187 |
| stock_prices | 5520 |
| documents | 1585 |
| analysis | 20 |
| prosandcons | 16 |
| profit_loss | 1276 |

## Validation Summary

Validation identified:

- Missing values
- Duplicate checks
- Primary Key validation
- Foreign Key validation
- Negative numeric values
- Stock price validation
- Sales validation

## Foreign Key Findings

The validation detected references to company IDs that are absent from the provided `companies.xlsx` dataset.

Missing IDs include:

- AGTL
- ULTRACEMCO
- UNIONBANK
- UNITDSPR
- VBL
- VEDL
- WIPRO
- ZOMATO
- ZYDUSLIFE

These are retained as genuine data quality findings and have **not** been modified in the source data.

## Output Files

- data/output/load_audit.csv
- data/output/validation_failures.csv
- db/nifty100.db