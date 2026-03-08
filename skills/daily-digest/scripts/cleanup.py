#!/usr/bin/env python3
"""Tiered retention cleanup for daily-digest-workspace.

Retention policy:
  - This week:  keep everything (audio, transcripts, summaries, JSON)
  - This month: delete audio files
  - This quarter: delete audio + transcripts
  - 6 months:  keep only summary MD + merged monthly digest
  - 1 year:    keep only yearly digest
  - Older:     delete everything

Usage:
    python cleanup.py --workspace daily-digest-workspace/ [--dry-run] [--verbose]
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_date_from_path(path: Path) -> datetime | None:
    """Extract date from a YYYY-MM-DD filename or directory."""
    name = path.stem
    for part in [name, path.parent.name]:
        try:
            return datetime.strptime(part[:10], "%Y-%m-%d")
        except (ValueError, IndexError):
            continue
    return None


def get_age_tier(file_date: datetime, now: datetime) -> str:
    """Determine retention tier based on age."""
    delta = now - file_date
    week_start = now - timedelta(days=now.weekday())

    if file_date >= week_start:
        return "week"
    elif delta.days <= 30:
        return "month"
    elif delta.days <= 90:
        return "quarter"
    elif delta.days <= 180:
        return "half_year"
    elif delta.days <= 365:
        return "year"
    else:
        return "archive"


def cleanup_workspace(
    workspace: Path,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict:
    """Apply tiered retention policy to workspace files."""
    now = datetime.now()
    stats = {
        "deleted_files": 0,
        "deleted_bytes": 0,
        "kept_files": 0,
        "errors": [],
    }

    fetched_dir = workspace / "fetched"
    transcripts_dir = workspace / "transcripts"
    summaries_dir = workspace / "summaries"

    # --- Clean fetched/ (audio + episode JSON) ---
    if fetched_dir.exists():
        for item in sorted(fetched_dir.rglob("*")):
            if not item.is_file():
                continue

            file_date = get_date_from_path(item)
            if not file_date:
                # Check parent dirs or use mtime
                file_date = datetime.fromtimestamp(item.stat().st_mtime)

            tier = get_age_tier(file_date, now)

            # Audio files: keep only this week
            is_audio = item.suffix in (".mp3", ".m4a", ".wav", ".ogg", ".opus")
            if is_audio and tier != "week":
                _delete(item, dry_run, verbose, stats)
                continue

            # Episode JSON: keep through quarter
            if item.suffix == ".json" and tier in ("half_year", "year", "archive"):
                _delete(item, dry_run, verbose, stats)
                continue

            stats["kept_files"] += 1

    # --- Clean transcripts/ ---
    if transcripts_dir.exists():
        for item in sorted(transcripts_dir.rglob("*")):
            if not item.is_file():
                continue

            file_date = get_date_from_path(item)
            if not file_date:
                file_date = datetime.fromtimestamp(item.stat().st_mtime)

            tier = get_age_tier(file_date, now)

            # Transcripts: keep through month, delete after
            if tier in ("quarter", "half_year", "year", "archive"):
                _delete(item, dry_run, verbose, stats)
                continue

            stats["kept_files"] += 1

    # --- Clean summaries/ ---
    if summaries_dir.exists():
        for item in sorted(summaries_dir.rglob("*")):
            if not item.is_file():
                continue

            file_date = get_date_from_path(item)
            if not file_date:
                file_date = datetime.fromtimestamp(item.stat().st_mtime)

            tier = get_age_tier(file_date, now)

            # Summaries MD: always keep (they're small)
            if item.suffix == ".md":
                stats["kept_files"] += 1
                continue

            # Summary JSON: keep through half year
            if item.suffix == ".json" and tier in ("year", "archive"):
                _delete(item, dry_run, verbose, stats)
                continue

            stats["kept_files"] += 1

    # --- Clean up empty directories ---
    if not dry_run:
        for dirpath in sorted(workspace.rglob("*"), reverse=True):
            if dirpath.is_dir() and not any(dirpath.iterdir()):
                dirpath.rmdir()
                if verbose:
                    print(f"  rmdir: {dirpath}", file=sys.stderr)

    return stats


def _delete(path: Path, dry_run: bool, verbose: bool, stats: dict):
    """Delete a file and update stats."""
    size = path.stat().st_size
    if verbose or dry_run:
        prefix = "[DRY RUN] " if dry_run else ""
        print(f"  {prefix}delete: {path} ({_fmt_size(size)})", file=sys.stderr)

    if not dry_run:
        try:
            path.unlink()
            stats["deleted_files"] += 1
            stats["deleted_bytes"] += size
        except OSError as e:
            stats["errors"].append(f"{path}: {e}")
    else:
        stats["deleted_files"] += 1
        stats["deleted_bytes"] += size


def _fmt_size(size_bytes: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def main():
    parser = argparse.ArgumentParser(description="Clean up daily-digest workspace")
    parser.add_argument(
        "--workspace",
        required=True,
        help="Path to daily-digest-workspace/",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print each file being processed",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace)
    if not workspace.exists():
        print(f"Workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)

    stats = cleanup_workspace(workspace, args.dry_run, args.verbose)

    # Output summary as JSON
    result = {
        "deleted_files": stats["deleted_files"],
        "freed_space": _fmt_size(stats["deleted_bytes"]),
        "freed_bytes": stats["deleted_bytes"],
        "kept_files": stats["kept_files"],
        "errors": stats["errors"],
        "dry_run": args.dry_run,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
