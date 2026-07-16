from pathlib import Path

from src.etl.loader import ExcelLoader

loader = ExcelLoader("data/raw")

datasets = loader.load_all()

for name, df in datasets.items():

    print("=" * 80)
    print(f"FILE: {name}")
    print("=" * 80)

    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    print("\nColumns:")

    for column in df.columns:
        print(f" - {column}")

    print("\nFirst 3 Rows:\n")

    print(df.head(3))

    print("\n\n")