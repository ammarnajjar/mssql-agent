"""Interactive AI agent that accepts natural-language requests and uses an LLM to produce SQL.

This is intentionally minimal: the LLM is used to propose SQL from a short schema summary.
The agent will show the proposed SQL and will only execute if the user passes --execute (and only SELECTs
are allowed by default).
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from typing import List

from . import generator, db_client
from .llm import call_llm, LLMError
from .prompts import SYSTEM_PROMPT, USER_PROMPT_PATTERN


def summarize_schema(columns: List[dict]) -> str:
    parts = []
    for c in columns:
        parts.append(f"{c['column_name']} {c['data_type']}")
    return ", ".join(parts)


def parse_sql_from_llm(resp: dict) -> str:
    # Try to extract assistant content
    try:
        msg = resp["choices"][0]["message"]["content"]
    except Exception:
        raise LLMError("unexpected LLM response format")
    # Try to parse JSON out of it
    m = re.search(r"\{.*\}", msg, flags=re.S)
    if not m:
        # fallback: return whole message
        return msg.strip()
    j = m.group(0)
    try:
        parsed = json.loads(j)
        return parsed.get("sql", msg).strip()
    except Exception:
        return msg.strip()


def is_select(sql: str) -> bool:
    return sql.strip().lower().startswith("select")


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--table", required=True, help="schema-qualified table name (e.g., dbo.Track)")
    p.add_argument("--ask", required=True, help="Natural-language request (e.g., 'top 10 tracks by sales')")
    p.add_argument("--execute", action="store_true", help="If set, execute permitted queries against DB")
    p.add_argument("--model", default="gpt-3.5-turbo")
    args = p.parse_args(argv)

    # If debugging DB issues, dump environment early so we capture what the entrypoint sees
    if os.environ.get("DEBUG_DB"):
        try:
            out_dir = os.environ.get("OUTPUT_DIR", "/output")
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            env_path = Path(out_dir) / "agent-env-debug.log"
            with env_path.open("a", encoding="utf-8") as fh:
                fh.write("---\n")
                fh.write(datetime.utcnow().isoformat() + "Z\n")
                for k, v in sorted(os.environ.items()):
                    fh.write(f"{k}={v}\n")
        except Exception:
            pass

    # fetch schema
    try:
        cols = db_client.get_table_schema(build_conn_from_env(), args.table)
    except Exception as exc:
        print("Failed to fetch schema:", exc, file=sys.stderr)
        return 2

    schema_summary = summarize_schema(cols)
    user_prompt = USER_PROMPT_PATTERN.format(schema=schema_summary, request=args.ask)

    try:
        resp = call_llm(SYSTEM_PROMPT, user_prompt, model=args.model)
    except LLMError as e:
        print("LLM call failed:", e, file=sys.stderr)
        return 2

    sql = parse_sql_from_llm(resp)
    print("Proposed SQL:\n", sql)
    if not is_select(sql) and not args.execute:
        print("Refusing to execute non-SELECT query without --execute flag.")
        return 0

    if args.execute:
        # execute using pyodbc via db_client helper
        try:
            rows = db_client.execute_query(build_conn_from_env(), sql)
            print(json.dumps({"rows": rows}, indent=2, default=str))
        except Exception as e:
            print("Execution failed:", e, file=sys.stderr)
            return 3

    return 0


def build_conn_from_env():
    # Lazy import to avoid circular import at module import time
    from .utils import build_conn_from_env as _b
    return _b()


if __name__ == "__main__":
    raise SystemExit(main())
