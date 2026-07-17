import sqlite3
import pandas as pd

DB_PATH = "db/nifty100.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def run_query(query):
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df