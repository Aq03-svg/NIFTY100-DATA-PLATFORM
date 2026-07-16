from src.etl.sqlite_loader import SQLiteLoader


db = SQLiteLoader("db/nifty100.db")

db.create_schema()

db.close()