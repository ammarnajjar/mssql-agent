#!/usr/bin/env python3
"""Run the agent against a local MSSQL instance.

This script will:
- connect using pyodbc
- list user tables in the specified database
- fetch column schema for each table and write generated example queries to ./out
"""
import sys
import json
from typing import Optional
import os
from pathlib import Path
from urllib.parse import quote_plus
from datetime import datetime
try:
    from agent.utils import build_conn_from_env, sqlalchemy_to_odbc  # centralized helpers
except Exception:
    # Fallback: load utils directly from the agent package path
    import importlib.util
    import pathlib
    base = pathlib.Path(__file__).resolve().parents[1]
    utils_path = base / 'agent' / 'utils.py'
    if utils_path.exists():
        spec = importlib.util.spec_from_file_location('agent.utils', str(utils_path))
        utils_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utils_mod)  # type: ignore
        build_conn_from_env = utils_mod.build_conn_from_env
        sqlalchemy_to_odbc = utils_mod.sqlalchemy_to_odbc
    else:
        raise

# Prefer python-dotenv when available, otherwise fall back to simple .env loader
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parents[0].parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
except Exception:
    env_path = Path(__file__).resolve().parents[0].parent / '.env'
    if env_path.exists():
        with env_path.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip())


CONN_ARG = None
if len(sys.argv) > 1:
    CONN_ARG = sys.argv[1]

# allow CONNECTION_STRING from environment (used in Docker)
ENV_CONN = os.environ.get("CONNECTION_STRING")
if not CONN_ARG and ENV_CONN:
    CONN_ARG = ENV_CONN


# If still no connection string, build from individual env vars using helper
if not CONN_ARG:
    CONN_ARG = build_conn_from_env()


# The SQLAlchemy->ODBC helper is provided by agent.utils/sqlalchemy_to_odbc


def main(conn_str: Optional[str]):
    try:
        import pyodbc
    except Exception as e:
        print(f"ERROR: pyodbc is required: {e}")
        return 2

    if not conn_str:
        print("Please provide a full ODBC connection string as the first argument.")
        print("Example:\n  DRIVER={ODBC Driver 18 for SQL Server};SERVER=localhost,1433;DATABASE=master;UID=sa;PWD=<your_password>;TrustServerCertificate=yes;")
        print("Alternatively, set DB_* environment variables or a .env file (DB_PASS for password).")
        return 1

    # allow SQLAlchemy-style URL conversion
    conn_str = sqlalchemy_to_odbc(conn_str)

    try:
        cnxn = pyodbc.connect(conn_str, autocommit=True)
    except Exception as e:
        print(f"ERROR: failed to connect: {e}")
        return 3

    cursor = cnxn.cursor()
    try:
        cursor.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"ERROR: failed to list tables: {e}")
        cursor.close()
        cnxn.close()
        return 4

    if not rows:
        print("No base tables found in the connected database.")
        cursor.close()
        cnxn.close()
        return 0

    # iterate all base tables
    tables = [(r.TABLE_SCHEMA, r.TABLE_NAME) for r in rows]

    # Ensure generator is available (with a fallback loader)
    try:
        from agent import generator  # type: ignore
    except Exception as e:
        import importlib.util
        import pathlib
        print(f"WARN: import agent.generator failed: {e}; attempting fallback loader")
        base = pathlib.Path(__file__).resolve().parents[1]
        gen_path = base / "agent" / "generator.py"
        if gen_path.exists():
            spec = importlib.util.spec_from_file_location("agent.generator", str(gen_path))
            generator = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(generator)  # type: ignore
            except Exception as e2:
                print(f"ERROR: failed to exec module fallback: {e2}")
                return 6
        else:
            print(f"ERROR: fallback generator file not found at {gen_path}")
            return 6

    cursor.close()
    cnxn.close()

    output_dir = os.environ.get("OUTPUT_DIR") or str(Path(__file__).resolve().parents[0].parent / "out")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    for table_schema, table_name in tables:
        full_table = f"{table_schema}.{table_name}"
        print(f"Processing table: {full_table}")

        # fetch columns for this table
        try:
            cnx = pyodbc.connect(conn_str, autocommit=True)
            cur = cnx.cursor()
            cur.execute(
                "SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
                (table_schema, table_name),
            )
            cols = [
                {"column_name": r.COLUMN_NAME, "data_type": r.DATA_TYPE, "is_nullable": r.IS_NULLABLE}
                for r in cur.fetchall()
            ]
            cur.close()
            cnx.close()
        except Exception as e:
            print(f"ERROR: failed to fetch columns for {full_table}: {e}")
            continue

        # detect primary keys using db_client if available
        pk_cols = None
        try:
            from agent import db_client  # type: ignore
            try:
                pk_cols = db_client.get_table_primary_key(conn_str, full_table)
            except Exception:
                pk_cols = None
        except Exception:
            pk_cols = None

        # generate queries
        try:
            queries = generator.generate_examples(full_table, cols, pk_columns=pk_cols)
        except Exception as e:
            print(f"ERROR: generator failed for {full_table}: {e}")
            continue

        out = {"table": full_table, "columns": cols, "queries": queries}

        try:
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            fname = f"queries_{full_table.replace('.', '_')}_{ts}.json"
            out_path = Path(output_dir) / fname
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(out, f, indent=2)
            print(f"Wrote queries to {out_path}")
        except Exception as e:
            print("Failed to write output file for {full_table}, printing to stdout instead:", e)
            print(json.dumps(out, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main(CONN_ARG))
