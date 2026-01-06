from utils.db import connect, run_sql_file
from utils.seed_loader import load_seed_data
import os
import sys


def create_access_database(db_path):
    """Create a new Access database file using COM automation (Windows only)"""
    try:
        import win32com.client

        access = win32com.client.Dispatch("Access.Application")
        access.NewCurrentDatabase(db_path)
        access.Quit()
        print(f"Created new Access database: {db_path}")
        return True
    except ImportError:
        print("ERROR: win32com not available. Install pywin32: pip install pywin32")
        return False
    except Exception as e:
        print(f"ERROR creating database: {e}")
        print("\nAlternative: Create an empty Access database manually:")
        print(f"  1. Open Microsoft Access")
        print(f"  2. Create a new blank database")
        print(f"  3. Save it as '{db_path}' in the project directory")
        print(f"  4. Close Access and run this script again")
        return False


def main():
    db_path = "smart_gym.accdb"

    if os.path.exists(db_path):
        print(f"Removing existing database: {db_path}")
        os.remove(db_path)

    if not create_access_database(db_path):
        sys.exit(1)

    try:
        conn = connect()

        print("Creating tables...")
        run_sql_file(conn, "schema/tables.sql")

        print("Inserting seed data...")
        load_seed_data(conn)

        print("Creating relationships...")
        run_sql_file(conn, "schema/relationships.sql")

        print("Creating queries...")
        run_sql_file(conn, "schema/queries.sql")

        conn.close()
        print(f"✔ {db_path} successfully created and populated")
    except Exception as e:
        print(f"ERROR during database population: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
