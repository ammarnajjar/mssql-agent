"""Utility helpers for building ODBC connection strings and loading env files.

This centralizes logic used by multiple scripts so passwords and settings come
from the environment or a single .env file (no hardcoded secrets in code).
"""
from pathlib import Path
import os


# Try to load .env from the project root when available (best-effort)
def _maybe_load_dotenv():
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).resolve().parents[1] / '.env'
        if env_path.exists():
            load_dotenv(env_path)
    except Exception:
        # Fallback simple loader
        env_path = Path(__file__).resolve().parents[1] / '.env'
        if env_path.exists():
            with env_path.open() as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())


_maybe_load_dotenv()


def build_conn_from_env() -> str | None:
    """Build an ODBC connection string from DB_* environment variables.

    Returns a connection string ending with ';' or None if insufficient data.
    """
    drv = os.environ.get('DB_DRIVER')
    host = os.environ.get('DB_HOST', 'localhost')
    port = os.environ.get('DB_PORT')
    db = os.environ.get('DB_NAME')
    user = os.environ.get('DB_USER')
    pwd = os.environ.get('DB_PASS')
    # Try Docker secret file fallback when DB_PASS not set
    if not pwd:
        secret_path = Path('/run/secrets/db_pass')
        if secret_path.exists():
            try:
                pwd = secret_path.read_text(encoding='utf-8').strip()
            except Exception:
                pwd = None
    trust = os.environ.get('TRUST_SERVER_CERT') or os.environ.get('TrustServerCertificate')

    if not drv:
        return None

    server = f"{host},{port}" if port else host
    parts = [f"Driver={{{drv}}}", f"Server={server}"]
    if db:
        parts.append(f"Database={db}")
    if user:
        parts.append(f"Uid={user}")
    if pwd:
        parts.append(f"Pwd={pwd}")
    if trust:
        parts.append(f"TrustServerCertificate={trust}")

    return ";".join(parts) + ";"


def sqlalchemy_to_odbc(conn: str) -> str:
    """Convert a SQLAlchemy-style mssql+pyodbc URL into an ODBC connection string.

    If the input doesn't look like a SQLAlchemy URL it is returned unchanged.
    """
    from urllib.parse import urlparse, parse_qs, unquote

    if not conn or not conn.startswith("mssql+pyodbc://"):
        return conn

    parsed = urlparse(conn)
    user = unquote(parsed.username) if parsed.username else ""
    pwd = unquote(parsed.password) if parsed.password else ""
    host = parsed.hostname or "localhost"
    port = parsed.port
    db = parsed.path.lstrip("/") if parsed.path else ""
    qs = parse_qs(parsed.query)

    driver = qs.get("driver", [None])[0]
    extras = {k: v[0] for k, v in qs.items() if k != "driver"}

    parts = []
    if driver:
        parts.append(f"Driver={{{driver}}}")
    server = f"{host},{port}" if port else host
    parts.append(f"Server={server}")
    if db:
        parts.append(f"Database={db}")
    if user:
        parts.append(f"Uid={user}")
    if pwd:
        parts.append(f"Pwd={pwd}")
    for k, v in extras.items():
        parts.append(f"{k}={v}")

    return ";".join(parts) + ";"
