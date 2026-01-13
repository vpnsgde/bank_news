#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Airflow
cd "$ROOT_DIR/airflow"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
AIRFLOW_VERSION=2.9.1
PYTHON_VERSION=3.11
CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-${AIRFLOW_VERSION}/constraints-${PYTHON_VERSION}.txt"
pip install "apache-airflow==${AIRFLOW_VERSION}" --constraint "${CONSTRAINT_URL}"
deactivate

# ETL
cd "$ROOT_DIR/etl"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install requests bs4 lxml
deactivate

# GUI
cd "$ROOT_DIR/gui"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install streamlit unidecode
deactivate

echo "Setup completed."
