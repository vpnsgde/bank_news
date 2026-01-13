#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR/gui"
source .venv/bin/activate
exec streamlit run app.py
deactivate
 