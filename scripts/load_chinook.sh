#!/usr/bin/env bash
set -euo pipefail

echo "Downloading Chinook SQL (v3) and loading into SQL Server..."
SQL_URL="https://raw.githubusercontent.com/lerocha/chinook-database/master/ChinookDatabase/DataSources/Chinook_MSSQL_Create.sql"
curl -sL "$SQL_URL" -o /tmp/chinook.sql

echo "Copying to container and executing..."
CONTAINER_NAME=$1
docker cp /tmp/chinook.sql "$CONTAINER_NAME":/tmp/chinook.sql

# Allow DB_PASS from env or from ./secrets/db_pass file (for local Compose secrets)
if [ -z "${DB_PASS:-}" ]; then
	if [ -f ./secrets/db_pass ]; then
		DB_PASS=$(cat ./secrets/db_pass)
	else
		echo "ERROR: DB_PASS not set in the environment and ./secrets/db_pass not found. Please export DB_PASS or provide ./secrets/db_pass." >&2
		exit 1
	fi
fi

# Pass the password into the container command securely
docker exec -u 0 "$CONTAINER_NAME" /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P "$DB_PASS" -i /tmp/chinook.sql

echo "Chinook loaded"
