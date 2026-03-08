#!/usr/bin/env python3
"""Update digest state to track processed items."""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Update digest state")
    parser.add_argument("--state", required=True, help="Path to state.json")
    parser.add_argument(
        "--processed-ids",
        required=True,
        help="Comma-separated list of processed item IDs",
    )
    args = parser.parse_args()

    state_path = Path(args.state)

    # Load existing state
    if state_path.exists():
        with open(state_path) as f:
            state = json.load(f)
    else:
        state = {"processed": {}}
        state_path.parent.mkdir(parents=True, exist_ok=True)

    # Add new processed IDs
    now = datetime.now().isoformat()
    new_ids = [id.strip() for id in args.processed_ids.split(",") if id.strip()]

    for item_id in new_ids:
        state["processed"][item_id] = now

    state["last_run"] = now
    state["total_processed"] = len(state["processed"])

    # Save
    with open(state_path, "w") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

    print(f"Updated state: {len(new_ids)} new items, {state['total_processed']} total")


if __name__ == "__main__":
    main()
