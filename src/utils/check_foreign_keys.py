from src.etl.loader import ExcelLoader

loader = ExcelLoader("data/raw")
datasets = loader.load_all()

companies = set(
    datasets["companies"]["id"]
    .astype(str)
    .str.strip()
    .str.upper()
)

for name, df in datasets.items():

    if "company_id" not in df.columns:
        continue

    ids = (
        df["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    missing = sorted(set(ids) - companies)

    print(f"\n{name}")
    print(f"Missing IDs: {len(missing)}")

    if missing:
        print(missing[:20])