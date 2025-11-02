AI MSSQL Query Example Agent

This small Python project connects to an MSSQL database and generates example SQL queries for a given table.

Quick start

1. Create a virtual environment and install dependencies.

If you use the `uv` helper (a small virtualenv manager), you can create the environment with it. This project includes a helper script that prefers `uv` if it's installed and falls back to the standard venv.

Using the included script:

```bash
# make executable once
chmod +x scripts/setup_venv.sh
# create and activate venv (zsh)
./scripts/setup_venv.sh
source .venv/bin/activate
pip install -r requirements.txt
```

Or, manually with venv:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run tests with pytest after activating the venv:

```bash
pytest -q
```

Example: executing parameterized queries with pyodbc

See `examples/execute_pyodbc.py` for a minimal demonstration. Update the `CONNECTION_STRING` in the file, then run:

```bash
source .venv/bin/activate
python examples/execute_pyodbc.py
```

Environment file

Copy `.env.example` to `.env` and update values. Docker Compose will pick up `.env` automatically. Example:

```bash
cp .env.example .env
# edit .env to set DB_HOST/DB_USER/DB_PASS etc.
docker-compose up --build --abort-on-container-exit
```

Optional: use python-dotenv for richer .env parsing

If you want to use `python-dotenv` to parse `.env` files (supports quotes and multiline values), install it in your venv:

```bash
pip install python-dotenv
```

The scripts will prefer `python-dotenv` if available, otherwise they'll use a simple `.env` loader.


2. Install an ODBC driver for MSSQL on macOS (Homebrew example):

```bash
brew install --cask microsoft-odbc-driver-mssql
```

3. Run the CLI (example):

```bash
python -m agent.cli --conn "Driver={ODBC Driver 18 for SQL Server};Server=tcp:myserver.database.windows.net,1433;Database=mydb;Uid=myuser;Pwd=mypassword;Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;" --table dbo.MyTable
```

Notes
- The project uses pyodbc to connect. The library must be able to load an ODBC driver on your machine.
- Tests mock schema data and don't require a live DB.

Secure secrets and Docker
------------------------

For security, avoid committing real passwords to the repository. Options:

- Local development with a secrets file (recommended for compose):

```bash
# create a secrets directory and store your DB password in secrets/db_pass (file contains only the password)
mkdir -p ./secrets
echo "my_db_password_here" > ./secrets/db_pass
chmod 600 ./secrets/db_pass
docker-compose up --build --abort-on-container-exit
```

- Export DB_PASS in your shell before running loader scripts:

```bash
export DB_PASS="my_db_password_here"
./scripts/load_chinook.sh <container-name>
```

- For production, prefer Docker secrets or a secrets manager and map the secret into `/run/secrets/db_pass` for the service.

The project already supports reading a Docker secret from `/run/secrets/db_pass` (used by `agent.utils`) and `./secrets/db_pass` for the loader script.
