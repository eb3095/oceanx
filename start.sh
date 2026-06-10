#!/bin/bash
# Run OceanX from the git tree without pip install.
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:${PATH}"

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

export PYTHONPATH="${ROOT}${PYTHONPATH:+:${PYTHONPATH}}"

if ! command -v hackrf_transfer >/dev/null 2>&1 && ! command -v rtl_sdr >/dev/null 2>&1; then
  echo "No SDR capture binary found. Install hackrf_transfer (brew install hackrf) or rtl_sdr (brew install rtl-sdr)." >&2
  exit 1
fi

if [[ ! -d .venv ]]; then
  echo "Run 'make dev-install' first." >&2
  exit 1
fi

source .venv/bin/activate
exec python3 -m oceanx "$@"
