"""
Shared fixtures and utilities for tap-salesforce regression tests.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REGRESSION_DIR = Path(__file__).parent
BASELINE_DIR = REGRESSION_DIR / "baseline"
TAP_CMD = str(Path(sys.executable).parent / "tap-salesforce")

REQUIRED_ENV = [
    "TAP_SALESFORCE_REFRESH_TOKEN",
    "TAP_SALESFORCE_CLIENT_ID",
    "TAP_SALESFORCE_CLIENT_SECRET",
]


def build_config():
    missing = [v for v in REQUIRED_ENV if not os.getenv(v)]
    if missing:
        pytest.skip(f"Missing required env vars: {missing}")

    return {
        "refresh_token": os.environ["TAP_SALESFORCE_REFRESH_TOKEN"],
        "client_id": os.environ["TAP_SALESFORCE_CLIENT_ID"],
        "client_secret": os.environ["TAP_SALESFORCE_CLIENT_SECRET"],
        "start_date": os.getenv("TAP_SALESFORCE_START_DATE", "2024-01-01T00:00:00Z"),
        "api_type": os.getenv("TAP_SALESFORCE_API_TYPE", "REST"),
        "select_fields_by_default": os.getenv("TAP_SALESFORCE_SELECT_FIELDS_BY_DEFAULT", "true"),
        "is_sandbox": os.getenv("TAP_SALESFORCE_IS_SANDBOX", "false"),
    }


def _tap_env():
    env = os.environ.copy()
    env.setdefault("AES_SECRET_KEY", "peliqan-test-key")
    return env


def discover_catalog(config_path):
    """Run tap-salesforce in --discover mode and return the catalog dict."""
    result = subprocess.run(
        [TAP_CMD, "--config", config_path, "--discover"],
        capture_output=True, text=True, env=_tap_env()
    )
    if result.returncode != 0:
        raise RuntimeError(f"discover failed: {result.stderr[-2000:]}")
    return json.loads(result.stdout)


def select_streams(catalog, only_streams):
    """Mark only the specified streams (and their fields) as selected.

    tap-salesforce discovers ~600 SObjects. Without filtering, sync would take
    forever and may hit API limits. only_streams is a list of stream names.
    """
    only = set(only_streams)
    for stream in catalog.get("streams", []):
        sid = stream.get("tap_stream_id") or stream.get("stream")
        selected = sid in only
        for entry in stream.get("metadata", []):
            entry.setdefault("metadata", {})["selected"] = selected
    return catalog


def write_catalog(catalog):
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(catalog, tmp)
    tmp.close()
    return tmp.name


@pytest.fixture(scope="session")
def config_file():
    config = build_config()
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
    json.dump(config, tmp)
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture(scope="session")
def include_streams():
    raw = os.getenv("TAP_SALESFORCE_INCLUDE_STREAMS", "Account,Contact")
    return [s.strip() for s in raw.split(",") if s.strip()]


@pytest.fixture(scope="session")
def catalog_file(config_file, include_streams):
    catalog = discover_catalog(config_file)
    select_streams(catalog, include_streams)
    path = write_catalog(catalog)
    yield path
    os.unlink(path)


def run_tap(config_path, catalog_path=None, extra_args=None):
    cmd = [TAP_CMD, "--config", config_path]
    if catalog_path:
        cmd += ["--catalog", catalog_path]
    cmd += (extra_args or [])
    result = subprocess.run(cmd, capture_output=True, text=True, env=_tap_env())
    return result.stdout, result.stderr, result.returncode


def parse_messages(stdout):
    schemas, records, states = {}, {}, []
    for line in stdout.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = msg.get("type")
        if t == "SCHEMA":
            schemas[msg["stream"]] = msg["schema"]
            records.setdefault(msg["stream"], [])
        elif t == "RECORD":
            records.setdefault(msg["stream"], []).append(msg["record"])
        elif t == "STATE":
            states.append(msg["value"])
    return schemas, records, states
