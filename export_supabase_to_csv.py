import os
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import DictCursor

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------

# Recommended: put your password in an environment variable instead of hard-coding it
# Example:
#   export SUPABASE_DB_PASSWORD="your_real_password"
SUPABASE_PASSWORD = "polymarket2025"

# Connection string from your prompt, with password filled in
CONNECTION_URI = (
    f"postgresql://postgres:{SUPABASE_PASSWORD}"
    "@db.ugasofwlocyygkbtdtzn.supabase.co:5432/postgres"
)

# Output folder for CSV exports
OUTPUT_DIR = Path("supabase_exports")


# -------------------------------------------------------------------
# HELPER FUNCTIONS
# -------------------------------------------------------------------

def get_connection():
    """Create and return a new psycopg2 connection using the CONNECTION_URI."""
    return psycopg2.connect(CONNECTION_URI, cursor_factory=DictCursor)


def list_tables(conn):
    """
    List all non-system tables across user schemas.

    Returns a list of (schema_name, table_name) tuples.
    """
    query = """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_type = 'BASE TABLE'
          AND table_schema NOT IN ('pg_catalog', 'information_schema')
        ORDER BY table_schema, table_name;
    """
    with conn.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    return [(r["table_schema"], r["table_name"]) for r in rows]


def export_table_to_csv(conn, schema_name, table_name, output_dir: Path):
    """
    Export one table to a CSV file using pandas.
    Files are stored in per-schema folders:

      supabase_exports/<schema_name>/<table_name>.csv
    """
    # Create per-schema directory
    schema_dir = output_dir / schema_name
    schema_dir.mkdir(parents=True, exist_ok=True)

    # File name is just the table name
    file_name = f"{table_name}.csv"
    output_path = schema_dir / file_name

    # Use pandas to load the entire table
    sql = f'SELECT * FROM "{schema_name}"."{table_name}"'
    df = pd.read_sql(sql, conn)

    # Write to CSV
    df.to_csv(output_path, index=False)
    print(f"Exported {schema_name}.{table_name} -> {output_path}")


def export_all_tables(output_dir: Path = OUTPUT_DIR):
    """
    Connect to Supabase Postgres, enumerate all user tables, and export each to CSV.
    """
    print("Connecting to Supabase Postgres...")
    with get_connection() as conn:
        print("Connected.")

        print("Listing tables...")
        tables = list_tables(conn)
        print(f"Found {len(tables)} tables.")

        for schema_name, table_name in tables:
            try:
                export_table_to_csv(conn, schema_name, table_name, output_dir)
            except Exception as e:
                # Log and continue; you can make this stricter if desired
                print(f"ERROR exporting {schema_name}.{table_name}: {e}")


# -------------------------------------------------------------------
# ENTRY POINT
# -------------------------------------------------------------------

if __name__ == "__main__":
    export_all_tables()