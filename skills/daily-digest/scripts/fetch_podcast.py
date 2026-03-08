#!/usr/bin/env python3
"""Fetch podcast episodes from RSS feeds, download audio for transcription."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import feedparser


def get_feed_title(url: str) -> str:
    """Get the podcast name from the RSS feed title."""
    feed = feedparser.parse(url)
    return feed.feed.get("title", "Unknown Podcast")


def fetch_feed(url: str, limit: int = 5) -> list[dict]:
    """Parse RSS feed and extract episode metadata."""
    feed = feedparser.parse(url)

    if feed.bozo and not feed.entries:
        print(f"Error: Failed to parse feed: {url}", file=sys.stderr)
        print(f"  Reason: {feed.bozo_exception}", file=sys.stderr)
        return []

    episodes = []
    for entry in feed.entries[:limit]:
        # Find audio enclosure
        audio_url = None
        for link in entry.get("links", []):
            if link.get("type", "").startswith("audio/"):
                audio_url = link.get("href")
                break
        # Fallback: check enclosures
        if not audio_url:
            for enc in entry.get("enclosures", []):
                if enc.get("type", "").startswith("audio/"):
                    audio_url = enc.get("href")
                    break

        episode = {
            "id": entry.get("id", entry.get("link", entry.get("title", ""))),
            "title": entry.get("title", "Untitled"),
            "description": entry.get("summary", ""),
            "published": entry.get("published", ""),
            "audio_url": audio_url,
            "source_type": "podcast",
        }
        episodes.append(episode)

    return episodes


def download_audio(audio_url: str, output_dir: Path) -> str | None:
    """Download audio file via curl."""
    if not audio_url:
        return None

    # Generate filename from URL
    suffix = ".mp3"
    if ".m4a" in audio_url:
        suffix = ".m4a"
    elif ".wav" in audio_url:
        suffix = ".wav"

    output_file = output_dir / f"audio_{hash(audio_url) % 10**8}{suffix}"

    try:
        subprocess.run(
            ["curl", "-L", "-s", "-o", str(output_file), audio_url],
            check=True,
            timeout=300,
        )
        return str(output_file)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Warning: Failed to download audio: {e}", file=sys.stderr)
        return None


def main():
    parser = argparse.ArgumentParser(description="Fetch podcast episodes from RSS")
    parser.add_argument("--url", required=True, help="RSS feed URL")
    parser.add_argument("--limit", type=int, default=5, help="Max episodes to fetch")
    parser.add_argument(
        "--output-dir", required=True, help="Directory to save fetched data"
    )
    parser.add_argument(
        "--source-name", default="podcast", help="Name of this source"
    )
    parser.add_argument(
        "--download-audio", action="store_true", help="Also download audio files"
    )
    parser.add_argument(
        "--get-feed-title", action="store_true", help="Output feed title and exit"
    )
    args = parser.parse_args()

    # Feed title lookup mode
    if args.get_feed_title:
        title = get_feed_title(args.url)
        print(title)
        return

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching RSS feed: {args.url}", file=sys.stderr)
    episodes = fetch_feed(args.url, args.limit)
    print(f"Found {len(episodes)} episodes", file=sys.stderr)

    if args.download_audio:
        audio_dir = output_dir / "audio"
        audio_dir.mkdir(exist_ok=True)
        for ep in episodes:
            if ep.get("audio_url"):
                print(f"  Downloading: {ep['title'][:50]}...", file=sys.stderr)
                audio_path = download_audio(ep["audio_url"], audio_dir)
                ep["audio_path"] = audio_path

    # Add source name
    for ep in episodes:
        ep["source_name"] = args.source_name

    # Output JSON
    output_file = output_dir / f"{args.source_name.replace(' ', '_')}_episodes.json"
    with open(output_file, "w") as f:
        json.dump(episodes, f, ensure_ascii=False, indent=2)

    print(json.dumps(episodes, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
