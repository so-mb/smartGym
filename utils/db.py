import os
import pyodbc
from config import DB_FILE, ODBC_CONNECTION_STRING


def _strip_sql_comments(sql: str) -> str:
    """
    Modification needed for Access ODBC.
    We primarily use '--' comments in our .sql files; strip full-line and trailing '--' comments.
    """
    out_lines: list[str] = []
    for line in sql.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        if stripped.startswith("--"):
            continue
        # Remove trailing -- comments (best-effort; assumes no string literals contain --)
        if "--" in line:
            line = line.split("--", 1)[0]
        if line.strip():
            out_lines.append(line)
    return "\n".join(out_lines)


def connect():
    # Prefer dynamic driver selection so this works across machines/runners
    db_path = os.path.abspath(DB_FILE)

    drivers = pyodbc.drivers()
    # Prefer an ACCDB-capable driver (if building .accdb)
    preferred = None
    lower_db = DB_FILE.lower()
    if lower_db.endswith(".accdb"):
        for d in drivers:
            if "accdb" in d.lower():
                preferred = d
                break
    elif lower_db.endswith(".mdb"):
        # GitHub runners often only have the older Access/Jet *.mdb driver (sometimes localized)
        for d in drivers:
            dl = d.lower()
            if "access" in dl and "mdb" in dl:
                preferred = d
                break

    # Fall back to the configured connection string if it matches the environment
    if preferred is None:
        try:
            return pyodbc.connect(ODBC_CONNECTION_STRING, autocommit=True)
        except Exception as e:
            raise RuntimeError(
                "No suitable Access ODBC driver found for "
                + DB_FILE
                + ". pyodbc.drivers() = "
                + repr(drivers)
                + "\nOriginal error: "
                + str(e)
            )

    conn_str = f"DRIVER={{{preferred}}};DBQ={db_path};"
    return pyodbc.connect(conn_str, autocommit=True)


def execute_sql(conn, sql: str):
    sql = _strip_sql_comments(sql)
    cursor = conn.cursor()
    for statement in sql.split(";"):
        stmt = statement.strip()
        if stmt:
            cursor.execute(stmt)


def run_sql_file(conn, path: str):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    execute_sql(conn, sql)
