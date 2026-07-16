import sqlite3
from pathlib import Path


class SQLiteLoader:

    def __init__(self, db_path):

        self.db_path = Path(db_path)

        self.connection = sqlite3.connect(self.db_path)

        self.cursor = self.connection.cursor()

    def create_schema(self):

        with open("db/schema.sql", "r") as file:

            schema = file.read()

        self.cursor.executescript(schema)

        self.connection.commit()

        print("Database Schema Created Successfully.")

    def close(self):

        self.connection.close()