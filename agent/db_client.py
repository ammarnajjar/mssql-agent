"""Database client helper to fetch table schema from MSSQL using pyodbc.

This module keeps pyodbc import lazy so tests can run without the dependency or driver.
"""
from typing import List, Dict, Optional
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
        cnxn = pyodbc.connect(connection_string, autocommit=True)
    except Exception as e:
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
