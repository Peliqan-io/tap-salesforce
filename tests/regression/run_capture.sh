#!/usr/bin/env bash
# Run baseline capture inside a Python 3.9 container.
# Usage: bash run_capture.sh

set -euo pipefail

TAP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "==> Running baseline capture in python:3.9-slim"
echo "    Tap dir: $TAP_DIR"

docker run --rm \
  -v "$TAP_DIR":/tap \
  -w /tap \
  -e TAP_SALESFORCE_REFRESH_TOKEN="${TAP_SALESFORCE_REFRESH_TOKEN:?}" \
  -e TAP_SALESFORCE_CLIENT_ID="${TAP_SALESFORCE_CLIENT_ID:?}" \
  -e TAP_SALESFORCE_CLIENT_SECRET="${TAP_SALESFORCE_CLIENT_SECRET:?}" \
  -e TAP_SALESFORCE_START_DATE="${TAP_SALESFORCE_START_DATE:-2024-01-01T00:00:00Z}" \
  -e TAP_SALESFORCE_API_TYPE="${TAP_SALESFORCE_API_TYPE:-REST}" \
  -e TAP_SALESFORCE_SELECT_FIELDS_BY_DEFAULT="${TAP_SALESFORCE_SELECT_FIELDS_BY_DEFAULT:-true}" \
  -e TAP_SALESFORCE_IS_SANDBOX="${TAP_SALESFORCE_IS_SANDBOX:-false}" \
  -e TAP_SALESFORCE_INCLUDE_STREAMS="${TAP_SALESFORCE_INCLUDE_STREAMS:-Account,Contact}" \
  -e AES_SECRET_KEY="peliqan-test-key" \
  python:3.9-slim \
  bash -c "
    apt-get update -qq && apt-get install -y -qq git > /dev/null
    python -m venv /venv
    /venv/bin/pip install -e . -q
    /venv/bin/python tests/regression/capture.py
  "

echo ""
echo "==> Baseline written to tests/regression/baseline/"
