import sqlite3
from pathlib import Path
import pandas as pd

DB_PATH = "db/nifty100.db"

SQL_FOLDER = Path("sql")
REPORT_FOLDER = Path("reports")

REPORT_FOLDER.mkdir(exist_ok=True)

connection = sqlite3.connect(DB_PATH)

print("=" * 70)
print("RUNNING SQL REPORTS")
print("=" * 70)

sql_files = sorted(SQL_FOLDER.glob("*.sql"))

for sql_file in sql_files:

    print(f"\nRunning: {sql_file.name}")

    with open(sql_file, "r") as f:
        query = f.read()

    try:
        result = pd.read_sql_query(query, connection)

        print(result)

        output = REPORT_FOLDER / f"{sql_file.stem}.csv"
        result.to_csv(output, index=False)

        print(f"Saved: {output}")

    except Exception as e:
        print(f"Error in {sql_file.name}")
        print(e)

connection.close()

print("\nAll SQL reports generated successfully.")