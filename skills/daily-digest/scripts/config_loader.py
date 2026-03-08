#!/usr/bin/env python3
"""Load sources config and digest state for the pipeline."""

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_sources(sources_path: str) -> list[dict]:
    """Load and validate sources.yaml."""
    path = Path(sources_path)
    if not path.exists():
        print(f"Error: Sources file not found: {sources_path}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        data = yaml.safe_load(f)

    sources = data.get("sources", [])
    for src in sources:
        if "name" not in src or "type" not in src or "url" not in src:
            print(
                f"Error: Source missing required fields (name, type, url): {src}",
                file=sys.stderr,
            )
            sys.exit(1)
        if src["type"] not in ("podcast", "youtube"):
            print(
                f"Error: Unknown source type '{src['type']}' for '{src['name']}'",
                file=sys.stderr,
            )
            sys.exit(1)

    return sources


def load_state(state_path: str) -> dict:
    """Load digest state (processed item tracking)."""
    path = Path(state_path)
    if not path.exists():
        return {"processed": {}}

    with open(path) as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Load daily-digest config")
    parser.add_argument("--sources", required=True, help="Path to sources.yaml")
    parser.add_argument("--state", required=True, help="Path to state.json")
    args = parser.parse_args()

    sources = load_sources(args.sources)
    state = load_state(args.state)

    output = {
        "sources": sources,
        "processed_ids": list(state.get("processed", {}).keys()),
        "source_count": len(sources),
        "processed_count": len(state.get("processed", {})),
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
