#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET="${1:-apk}"

cd "$ROOT_DIR"
python3 scripts/generate_release_assets.py
python3 python_files/smoke_test.py

case "$TARGET" in
  apk|aab|ipa|macos|web)
    ;;
  *)
    echo "Usage: $0 [apk|aab|ipa|macos|web]" >&2
    exit 2
    ;;
esac

exec flet build "$TARGET" . \
  --build-version 0.1.0 \
  --build-number 1 \
  --exclude .git build output tmp .pycache_smoke __pycache__ auth_gateway docs web
