# NIFTY100 Data Platform

An end-to-end Data Engineering project that builds a production-style ETL pipeline for NIFTY100 company financial data.

---

## Project Overview

This project ingests multiple Excel datasets, validates data quality, loads the cleaned data into SQLite, and prepares it for analytics and dashboarding.

The pipeline performs automated validation, generates audit reports, and creates a centralized relational database for downstream analysis.

---

## Features

- Multi-file Excel ingestion
- Automated ETL pipeline
- Data validation framework
- SQLite database integration
- Audit report generation
- Foreign key validation
- Primary key validation
- Missing value detection
- Duplicate detection
- Stock price validation
- Sales validation

---

## Project Structure

```
NIFTY100-DATA-PLATFORM/

├── config/
├── data/
│   ├── raw/
│   ├── processed/
│   └── output/
│
├── db/
├── docs/
├── logs/
├── notebooks/
├── reports/
├── src/
│   ├── analytics/
│   ├── etl/
│   ├── utils/
│   └── validation/
│
├── tests/
├── README.md
├── requirements.txt
└── .gitignore
```

---

## ETL Workflow

```
Excel Files
      │
      ▼
Excel Loader
      │
      ▼
Data Validation
      │
      ▼
Validation Report
      │
      ▼
SQLite Schema
      │
      ▼
Database Loader
      │
      ▼
Analytics Ready Database
```

---

## Datasets

The project processes:

- Companies
- Balance Sheet
- Profit & Loss
- Cash Flow
- Financial Ratios
- Market Capitalization
- Stock Prices
- Documents
- Analysis
- Pros & Cons
- Sectors
- Peer Groups

---

## Data Quality Checks

The validation engine performs:

- Missing Values
- Duplicate Rows
- Empty Columns
- Invalid Years
- Negative Numeric Values
- Primary Key Validation
- Foreign Key Validation
- Stock Price Validation
- Positive Sales Validation

---

## Database

SQLite is used as the project database.

The pipeline automatically:

- Creates schema
- Loads all tables
- Preserves relational structure

---

## Output Files

```
data/output/load_audit.csv
data/output/validation_failures.csv
db/nifty100.db
```

---

## Technologies Used

- Python
- Pandas
- SQLite
- SQL
- VS Code
- Git
- GitHub

---

## Future Enhancements

- Interactive Streamlit dashboard
- SQL analytics
- Automated logging
- Scheduled ETL execution
- Cloud deployment

---

## Author

**Aqeeb Javeed Shaikh**

AI & Machine Learning Undergraduate

Data Science & Machine Learning Enthusiast