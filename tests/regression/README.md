# tap-salesforce — Python 3.11 Regression Tests

Before/after parity test for the Python 3.9 → 3.11 migration.

## Strategy

1. **Capture** baseline on pre-migration `master` + Python 3.9: discover, select a subset of streams, sync, record schemas / state-key names / record field names.
2. **Compare** on migration branch + Python 3.11 — assert schemas unchanged, no streams dropped, all baseline fields still present.

Salesforce has ~1000 SObjects, so we filter to a small set via `TAP_SALESFORCE_INCLUDE_STREAMS` (default `Account,Contact`).

## Files

| File | Purpose |
| --- | --- |
| `conftest.py` | Shared fixtures: config builder, catalog filtering, sync runner, message parser |
| `capture.py` | Standalone — run once on Python 3.9 to write `baseline/` |
| `test_regression.py` | pytest suite — run on Python 3.11 to verify parity |
| `run_capture.sh` | Wrapper that runs `capture.py` in `python:3.9-slim` Docker |
| `run_tests.sh` | Wrapper that runs pytest in `python:3.11-slim` Docker |
| `get_refresh_token.py` | One-time OAuth helper to mint a Salesforce `refresh_token` (stdlib only — localhost callback version; if your Connected App's callback is hosted elsewhere, use the manual flow documented in the Notion Tests page) |
| `baseline/` | Committed reference output: schemas, state keys, record fields, catalog, meta |

## Usage

Required env vars:

```bash
export TAP_SALESFORCE_REFRESH_TOKEN=...
export TAP_SALESFORCE_CLIENT_ID=...
export TAP_SALESFORCE_CLIENT_SECRET=...
export TAP_SALESFORCE_API_TYPE=REST                 # or BULK
export TAP_SALESFORCE_INCLUDE_STREAMS=Account,Contact   # comma-separated
export TAP_SALESFORCE_IS_SANDBOX=false              # optional, default false
export TAP_SALESFORCE_START_DATE=2024-01-01T00:00:00Z
```

### Capture baseline (pre-migration code on Python 3.9)

```bash
git worktree add /tmp/tap-salesforce-master master
cp -r tests/regression /tmp/tap-salesforce-master/tests/regression
cd /tmp/tap-salesforce-master
bash tests/regression/run_capture.sh
cp -r tests/regression/baseline /path/to/migration-branch/tests/regression/
git worktree remove /tmp/tap-salesforce-master
```

### Run tests (migration branch on Python 3.11)

```bash
bash tests/regression/run_tests.sh
```

## Caveats

- Discover takes 30–60s because tap-salesforce describes all ~1000 SObjects in the org.
- BULK API has different error behavior than REST. The baseline must be captured with the same `api_type` used for the comparison.
- Records sync depends on data in the org. If your dev org's Accounts / Contacts change between capture and test runs, the record field union may differ — this is informational only; only **dropped** fields fail the test.
