#!/bin/sh
set -e

python - <<'PY'
import os, time
import psycopg2

host = os.getenv("POSTGRES_HOST", "postgres")
port = int(os.getenv("POSTGRES_PORT", "5432"))
db   = os.getenv("POSTGRES_DATABASE", "prod")
user = os.getenv("POSTGRES_USERNAME", "prod")
pwd  = os.getenv("POSTGRES_PASSWORD", "prod")

for i in range(60):
    try:
        conn = psycopg2.connect(host=host, port=port, dbname=db, user=user, password=pwd)
        conn.close()
        print("Postgres is ready")
        break
    except Exception as e:
        print(f"Waiting for Postgres... {i+1}/60: {e}")
        time.sleep(1)
else:
    raise SystemExit("Postgres is not ready")
PY


python -c "from database import init_db; init_db()"


alembic upgrade head


exec uvicorn main:app --host 0.0.0.0 --port 8080
