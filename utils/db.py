import os
import pyodbc
from config import DB_FILE, ODBC_CONNECTION_STRING


def connect():
    # Prefer dynamic driver selection so this works across machines/runners
    db_path = os.path.abspath(DB_FILE)

    drivers = pyodbc.drivers()
    # Prefer an ACCDB-capable driver
    preferred = None
    for d in drivers:
        if "accdb" in d.lower():
            preferred = d
            break

    # Fall back to the configured connection string if it matches the environment
    if preferred is None:
        try:
            return pyodbc.connect(ODBC_CONNECTION_STRING, autocommit=True)
        except Exception as e:
            raise RuntimeError(
                "No ACCDB-capable ODBC driver found. pyodbc.drivers() = "
                + repr(drivers)
                + "\nOriginal error: "
                + str(e)
            )

    conn_str = f"DRIVER={{{preferred}}};DBQ={db_path};"
    return pyodbc.connect(conn_str, autocommit=True)


def execute_sql(conn, sql: str):
    cursor = conn.cursor()
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            cursor.execute(stmt)


def run_sql_file(conn, path: str):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    execute_sql(conn, sql)
