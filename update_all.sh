#!/usr/bin/env bash
set -euo pipefail
pkill -f "airflow" || true

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
AIRFLOW_DIR="$ROOT_DIR/airflow"

cd "$AIRFLOW_DIR"
source .venv/bin/activate

export AIRFLOW_HOME="$AIRFLOW_DIR"
export AIRFLOW__CORE__LOAD_EXAMPLES=False

# Init DB if needed
if [ ! -f "$AIRFLOW_HOME/airflow.db" ]; then
    airflow db init
    airflow users create \
        --username admin \
        --firstname Admin \
        --lastname User \
        --role Admin \
        --email admin@example.com \
        --password admin
fi

# Clean example DAGs (idempotent)
# airflow dags list | grep example_ | awk '{print $1}' | xargs -r airflow dags delete -y

# Start Airflow
setsid airflow webserver -p 8080 > webserver.log 2>&1 < /dev/null &
setsid airflow scheduler > scheduler.log 2>&1 < /dev/null &
sleep 5

# Open GUI
xdg-open http://localhost:8080
sleep 3
airflow dags unpause update_all
airflow dags trigger update_all

deactivate