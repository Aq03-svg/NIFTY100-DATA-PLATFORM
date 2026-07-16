import sqlite3
import pandas as pd


class DatabaseLoader:

    def __init__(self, db_path):
        self.connection = sqlite3.connect(db_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.connection.cursor()

    def load_dataframe(self, dataframe, table_name):

        dataframe.to_sql(
            table_name,
            self.connection,
            if_exists="replace",
            index=False
        )

        rows = len(dataframe)

        print(f"✓ {table_name:<20} {rows} rows loaded")

    def execute_sql(self, sql):

        self.cursor.executescript(sql)
        self.connection.commit()

    def commit(self):
        self.connection.commit()

    def close(self):
        self.connection.close()