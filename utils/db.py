import pyodbc
from config import ODBC_CONNECTION_STRING


def connect():
    return pyodbc.connect(ODBC_CONNECTION_STRING, autocommit=True)


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
