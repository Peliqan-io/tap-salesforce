import sys
sys.path.insert(1, '..')
import tap_salesforce

tap_salesforce.main()

# Run discovery mode: python3 tap-salesforce.py --discover --config config.json > catalog.json
# Run sync mode: python3 tap-salesforce.py --config config.json --catalog catalog.json --state state.json
# Sync to target: python3 tap-salesforce.py --config config.json --catalog catalog.json --state state.json | target-postgres --config target_config.json
