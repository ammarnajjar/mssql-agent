"""Example: execute parameterized queries produced by the agent using pyodbc.

This script demonstrates connecting to MSSQL via an ODBC connection string,
preparing a parameterized SQL statement returned by the agent, and executing it.

Adjust CONNECTION_STRING to your environment.
"""
import pyodbc

# Example connection string (ODBC Driver 18). Adjust as needed.
import os
from pathlib import Path

from agent.utils import build_conn_from_env

# Build connection string from env or fall back to a default
CONNECTION_STRING = os.environ.get('CONNECTION_STRING') or build_conn_from_env()

# Warn if no password is provided: many SQL Server instances require authentication
if not os.environ.get('DB_PASS') and not CONNECTION_STRING:
    import sys
    print("WARNING: DB_PASS is not set in the environment; authentication may fail.", file=sys.stderr)
    # Warn if no password is provided: many SQL Server instances require authentication
    if not pwd:
        import sys
        print("WARNING: DB_PASS is not set in the environment; authentication may fail.", file=sys.stderr)


def execute_example(select_query, select_params):
    # Use a context manager for the connection and a cursor
    with pyodbc.connect(CONNECTION_STRING, autocommit=True) as cnxn:
        with cnxn.cursor() as cur:
            # Execute a parameterized query. Use '?' placeholders in the SQL and
            # pass parameters as a tuple or list in the second argument to execute().
            cur.execute(select_query, select_params)
            # Fetch rows
            rows = cur.fetchall()
            for row in rows[:10]:  # print first 10 rows
                print(row)


if __name__ == "__main__":
    # Example usage — suppose the agent returned this:
    select_sql = "SELECT AlbumId, Title, ArtistId FROM dbo.Album WHERE AlbumId = ?;"
    select_params = [1]

    execute_example(select_sql, select_params)
