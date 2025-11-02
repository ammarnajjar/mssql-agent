"""Generate example SQL queries given a table schema."""
from typing import List, Dict


def _sample_value_for_type(data_type: str) -> str:
    t = data_type.lower()
    if t.startswith("int") or t in ("bigint", "smallint", "tinyint"):
        return "1"
    if t.startswith("decimal") or t in ("numeric", "money", "float", "real"):
        return "1.23"
    if t in ("bit",):
        return "1"
    if t.startswith("char") or t.startswith("varchar") or t in ("text", "nchar", "nvarchar", "ntext"):
        return "'example'"
    if t in ("date",):
        return "'2025-01-01'"
    if t.startswith("datetime") or t.startswith("smalldatetime") or t.startswith("datetime2"):
        return "'2025-01-01 12:00:00'"
    if t in ("uniqueidentifier",):
        return "'00000000-0000-0000-0000-000000000000'"
    # Fallback to string
    return "'example'"


def generate_examples(table_name: str, columns: List[Dict[str, str]], pk_columns: List[str] | None = None) -> Dict[str, object]:
    """Given a table name and columns, return parameterized SQL and example params.

    Returns a dict with keys: select, insert, update, delete. Each value is a dict with
    'sql' and 'params' (list) suitable for pyodbc (use '?' placeholders).
    """
    if not columns:
        raise ValueError("No columns provided")

    col_names = [c["column_name"] for c in columns]
    if pk_columns:
        pk = pk_columns
    else:
        # fallback to first column as pk
        pk = [columns[0]["column_name"]]

    # SELECT (no params by default, but show WHERE pk = ? example)
    # SELECT with PK equality on all PK columns
    select_where = " AND ".join([f"{c} = ?" for c in pk])
    select_sql = f"SELECT {', '.join(col_names)} FROM {table_name} WHERE {select_where};"
    # sample params for pk columns in same order
    select_params = [
        _sample_value_for_type(next((col["data_type"] for col in columns if col["column_name"] == pkc), "int"))
        for pkc in pk
    ]

    # INSERT: placeholders for all columns
    placeholders = ", ".join(["?" for _ in col_names])
    insert_sql = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders});"
    insert_params = [_sample_value_for_type(c.get("data_type", "varchar")) for c in columns]

    # UPDATE: set all non-PK columns, WHERE pk = ?
    non_pk_cols = [c for c in col_names if c not in pk]
    update_set = ", ".join([f"{name} = ?" for name in non_pk_cols])
    update_sql = f"UPDATE {table_name} SET {update_set} WHERE {select_where};"
    update_params = [_sample_value_for_type(next(col['data_type'] for col in columns if col['column_name'] == name)) for name in non_pk_cols]
    # append pk params
    update_params.extend(select_params)

    # DELETE: WHERE pk = ?
    delete_sql = f"DELETE FROM {table_name} WHERE {select_where};"
    delete_params = select_params

    return {
        "select": {"sql": select_sql, "params": select_params},
        "insert": {"sql": insert_sql, "params": insert_params},
        "update": {"sql": update_sql, "params": update_params},
        "delete": {"sql": delete_sql, "params": delete_params},
    }
