from normaliser import normalize_year, normalize_ticker

print("Year Tests")
print(normalize_year("FY24"))
print(normalize_year("FY2025"))
print(normalize_year("2026"))
print(normalize_year("FY 2023"))

print()

print("Ticker Tests")
print(normalize_ticker("tcs.ns"))
print(normalize_ticker(" INFY "))
print(normalize_ticker("reliance.ns"))
print(normalize_ticker("HDFCBANK"))