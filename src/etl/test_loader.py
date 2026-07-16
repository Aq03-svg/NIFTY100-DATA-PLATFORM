from loader import ExcelLoader

loader = ExcelLoader("data/raw")

datasets = loader.load_all()

loader.generate_audit_report()

print("\nLoaded datasets:")

for name in datasets:
    print(name)