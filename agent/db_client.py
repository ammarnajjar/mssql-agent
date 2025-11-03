"""Database client helper to fetch table schema from MSSQL using pyodbc.

This module keeps pyodbc import lazy so tests can run without the dependency or driver.
"""
from typing import List, Dict, Optional
from pathlib import Path
import os
from datetime import datetime
import re


class DBClientError(RuntimeError):
    pass


def parse_connection_string(conn_str: str) -> Dict[str, str]:
    # Very small parser for key=value; pairs separated by ;
    parts = [p for p in re.split(r";\s*", conn_str) if p]
    out = {}
    for p in parts:
        if "=" in p:
            k, v = p.split("=", 1)
            out[k.strip().lower()] = v.strip()
    return out


def get_table_schema(connection_string: str, table_name: str) -> List[Dict[str, Optional[str]]]:
    """Return list of columns for the table.

    Each column is a dict: {column_name, data_type, is_nullable}
    Requires pyodbc and a working ODBC driver.
    """
    try:
        import pyodbc
    except Exception as e:
        raise DBClientError("pyodbc is required to access a live database: %s" % e)

    # Connect using the connection string directly.
    try:
        # Optional debug info when DEBUG_DB env var is set (only in diagnostics)
        if os.environ.get("DEBUG_DB"):
            try:
                # Print to stdout for quick debugging
                print("DEBUG_DB: connection_string=", connection_string)
                print("DEBUG_DB: pyodbc.drivers()=", pyodbc.drivers())
                # Also append a timestamped log to /output/agent-db-debug.log when available
                out_dir = os.environ.get("OUTPUT_DIR", "/output")
                try:
                    Path(out_dir).mkdir(parents=True, exist_ok=True)
                    log_path = Path(out_dir) / "agent-db-debug.log"
                    with log_path.open("a", encoding="utf-8") as fh:
                        fh.write("---\n")
                        fh.write(datetime.utcnow().isoformat() + "Z\n")
                        fh.write("connection_string=" + (connection_string or "") + "\n")
                        fh.write("drivers=" + str(pyodbc.drivers()) + "\n")
                except Exception:
                    pass
            except Exception:
                pass
        cnxn = pyodbc.connect(connection_string, autocommit=True)
    except Exception as e:
        # If DEBUG_DB set try to write the full traceback to the log file for post-mortem
        if os.environ.get("DEBUG_DB"):
            try:
                import traceback as _tb
                out_dir = os.environ.get("OUTPUT_DIR", "/output")
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                log_path = Path(out_dir) / "agent-db-debug.log"
                with log_path.open("a", encoding="utf-8") as fh:
                    fh.write("EXCEPTION:\n")
                    fh.write(_tb.format_exc())
                    fh.write("\n---\n")
            except Exception:
                pass
        raise DBClientError(f"Failed to connect: {e}")

    # Normalize table into schema and table
    if "." in table_name:
        schema_part, table_part = table_name.split(".", 1)
    else:
        schema_part, table_part = "dbo", table_name

    cursor = cnxn.cursor()
    sql = ("SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE "
           "FROM INFORMATION_SCHEMA.COLUMNS "
           "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? "
           "ORDER BY ORDINAL_POSITION")
    try:
        cursor.execute(sql, (schema_part, table_part))
    except Exception as e:
        raise DBClientError(f"Failed to query schema: {e}")

    cols = []
    for row in cursor.fetchall():
        cols.append({
            "column_name": row.COLUMN_NAME,
            "data_type": row.DATA_TYPE,
            "is_nullable": row.IS_NULLABLE,
        })

    cursor.close()
    cnxn.close()
    return cols


def get_table_primary_key(connection_string: str, table_name: str) -> List[str]:
    """Return a list of primary key column names for the given table.

    Uses INFORMATION_SCHEMA.TABLE_CONSTRAINTS and KEY_COLUMN_USAGE.
    """
    try:
        import pyodbc
    except Exception as e:
        raise DBClientError("pyodbc is required to access a live database: %s" % e)

    try:
        cnxn = pyodbc.connect(connection_string, autocommit=True)
    except Exception as e:
        # write debug if requested
        if os.environ.get("DEBUG_DB"):
            try:
                out_dir = os.environ.get("OUTPUT_DIR", "/output")
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                log_path = Path(out_dir) / "agent-db-debug.log"
                import traceback as _tb
                with log_path.open("a", encoding="utf-8") as fh:
                    fh.write("EXCEPTION get_table_primary_key:\n")
                    fh.write(_tb.format_exc())
                    fh.write("\n---\n")
            except Exception:
                pass
        raise DBClientError(f"Failed to connect: {e}")

    if "." in table_name:
        schema_part, table_part = table_name.split(".", 1)
    else:
        schema_part, table_part = "dbo", table_name

    cursor = cnxn.cursor()
    sql = (
        "SELECT kcu.COLUMN_NAME "
        "FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc "
        "JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE kcu "
        "  ON tc.CONSTRAINT_NAME = kcu.CONSTRAINT_NAME AND tc.TABLE_SCHEMA = kcu.TABLE_SCHEMA "
        "WHERE tc.TABLE_SCHEMA = ? AND tc.TABLE_NAME = ? AND tc.CONSTRAINT_TYPE = 'PRIMARY KEY' "
        "ORDER BY kcu.ORDINAL_POSITION"
    )
    try:
        cursor.execute(sql, (schema_part, table_part))
    except Exception as e:
        raise DBClientError(f"Failed to query primary keys: {e}")

    pk_cols = [row.COLUMN_NAME for row in cursor.fetchall()]

    cursor.close()
    cnxn.close()
    return pk_cols


def execute_query(connection_string: str, sql: str):
    """Execute a SQL query and return rows as list of tuples.

    This is intentionally minimal: callers should format/serialize results.
    """
    try:
        import pyodbc
    except Exception as e:
        raise DBClientError("pyodbc is required to execute queries: %s" % e)

    try:
        cnxn = pyodbc.connect(connection_string, autocommit=True)
    except Exception as e:
        if os.environ.get("DEBUG_DB"):
            try:
                out_dir = os.environ.get("OUTPUT_DIR", "/output")
                Path(out_dir).mkdir(parents=True, exist_ok=True)
                log_path = Path(out_dir) / "agent-db-debug.log"
                import traceback as _tb
                with log_path.open("a", encoding="utf-8") as fh:
                    fh.write("EXCEPTION execute_query:\n")
                    fh.write(_tb.format_exc())
                    fh.write("\n---\n")
            except Exception:
                pass
        raise DBClientError(f"Failed to connect: {e}")

    cursor = cnxn.cursor()
    try:
        cursor.execute(sql)
        cols = [col[0] for col in cursor.description] if cursor.description else []
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()] if cols else [tuple(row) for row in cursor.fetchall()]
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        try:
            cnxn.close()
        except Exception:
            pass

    return rows
