from utils.db import connect, run_sql_file
from utils.seed_loader import load_seed_data
import os
import sys


def create_access_database(db_path):
    """Create a new Access database file.

    Important: GitHub-hosted runners often *do not* have Microsoft Access installed,
    so Access.Application COM automation is not available. Prefer pure-Python creation
    (msaccessdb) or ADOX if ACE components are installed.
    """

    try:
        import os

        abs_path = os.path.abspath(db_path)

        # For .mdb builds, the ODBC driver typically CANNOT create the file.
        # Create an empty .mdb first using ADOX + Jet OLEDB provider (32-bit).
        if abs_path.lower().endswith(".mdb"):
            try:
                import win32com.client  # type: ignore

                catalog = win32com.client.Dispatch("ADOX.Catalog")
                # Jet OLEDB provider for .mdb
                # Engine Type=5 => Access 2000 format (widely compatible)
                conn_str = (
                    "Provider=Microsoft.Jet.OLEDB.4.0;"
                    f"Data Source={abs_path};"
                    "Jet OLEDB:Engine Type=5;"
                )
                catalog.Create(conn_str)
                print(f"Created new Access database using Jet ADOX: {db_path}")
                return True
            except Exception as jet_err:
                print(f"Jet ADOX method failed for .mdb: {jet_err}")
                # Fall through to other methods (may still work on some machines)

        # Method 1: pure Python (no COM). Requires `msaccessdb` (accdb).
        try:
            import msaccessdb  # type: ignore

            msaccessdb.create(abs_path)
            print(f"Created new Access database using msaccessdb: {db_path}")
            return True
        except Exception as ms_err:
            print(f"msaccessdb method failed (will try COM-based methods): {ms_err}")

        # Method 2: Try using ADOX.Catalog (works with Access Database Engine, no full Access needed)
        try:
            import win32com.client  # type: ignore

            catalog = win32com.client.Dispatch("ADOX.Catalog")
            # Use ACE OLEDB provider (comes with Access Database Engine)
            # Try both 12.0 and 16.0 providers
            providers = [
                "Provider=Microsoft.ACE.OLEDB.16.0;Data Source={};",
                "Provider=Microsoft.ACE.OLEDB.12.0;Data Source={};",
            ]

            for provider_template in providers:
                try:
                    conn_str = provider_template.format(abs_path)
                    catalog.Create(conn_str)
                    print(f"Created new Access database using ADOX: {db_path}")
                    return True
                except Exception as provider_error:
                    print(f"Tried provider, failed: {provider_error}")
                    continue

            raise Exception("All ADOX providers failed")

        except Exception as adox_error:
            print(f"ADOX method failed: {adox_error}")
            # Method 3: Fallback to Access.Application (requires full Access, won't work on GitHub Actions)
            try:
                import win32com.client  # type: ignore

                access = win32com.client.Dispatch("Access.Application")
                access.NewCurrentDatabase(abs_path)
                access.Quit()
                print(
                    f"Created new Access database using Access.Application: {db_path}"
                )
                return True
            except Exception as access_error:
                print(f"Access.Application method also failed: {access_error}")
                raise adox_error

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
    # Use .mdb for CI compatibility (GitHub-hosted runners have 32-bit Jet/Access ODBC,
    # but often lack 64-bit ACCDB/ACE drivers).
    db_path = "smart_gym.mdb"

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

        # Relationships/queries creation via ODBC can be flaky across drivers and
        # Access versions. Keep the build resilient: try, but don't fail the CI artifact.
        try:
            print("Creating relationships...")
            run_sql_file(conn, "schema/relationships.sql")
        except Exception as rel_err:
            print(f"WARNING: relationships not created: {rel_err}")

        try:
            print("Creating queries...")
            run_sql_file(conn, "schema/queries.sql")
        except Exception as q_err:
            print(f"WARNING: queries not created: {q_err}")
            print(
                "You can copy/paste queries manually from schema/queries.sql in Access."
            )

        conn.close()
        print(f"OK: {db_path} successfully created and populated")
    except Exception as e:
        print(f"ERROR during database population: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
