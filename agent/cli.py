"""Simple CLI for the MSSQL Query Example Agent."""
import argparse
import json
from . import db_client, generator


def main(argv=None):
    p = argparse.ArgumentParser(description="Generate example SQL queries for a table")
    p.add_argument("--conn", required=True, help="ODBC connection string for MSSQL")
    p.add_argument("--table", required=True, help="Table name, optionally schema.table")
    p.add_argument("--json", action="store_true", help="Output JSON")
    args = p.parse_args(argv)

        cols = db_client.get_table_schema(args.conn, args.table)
        pk_cols = db_client.get_table_primary_key(args.conn, args.table)
        queries = generator.generate_examples(args.table, cols, pk_columns=pk_cols)

    if args.json:
        print(json.dumps(queries, indent=2))
    else:
        for k, v in queries.items():
            print(f"-- {k.upper()}")
                print(v['sql'])
                if v.get('params'):
                    print("Params:", v['params'])
            print()


if __name__ == "__main__":
    main()
