FROM python:3.11-slim

# Install system deps for unixODBC and FreeTDS (tdsodbc)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    curl ca-certificates build-essential unixodbc unixodbc-dev freetds-dev tdsodbc \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt /app/requirements.txt
# Install Python dependencies (pyodbc will build against unixODBC)
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

ENTRYPOINT ["python", "scripts/run_local_agent.py"]
