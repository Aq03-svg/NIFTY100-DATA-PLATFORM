import sqlite3

connection = sqlite3.connect("db/nifty100.db")

connection.execute("PRAGMA foreign_keys = ON")

cursor = connection.cursor()

cursor.execute("PRAGMA foreign_keys")

print("Foreign Keys Enabled:", cursor.fetchone()[0])

connection.close()