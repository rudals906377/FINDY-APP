#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -d ".venv_findy_server" ]; then
  python3 -m venv .venv_findy_server
fi

source .venv_findy_server/bin/activate
pip install -r findy_server/requirements.txt

if [ -f "findy_server/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source findy_server/.env
  set +a
fi

uvicorn findy_server.main:app --host 0.0.0.0 --port 8790 --reload

