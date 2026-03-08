#!/usr/bin/env python3
"""Fetch YouTube videos from channels, extract subtitles or download audio."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def list_videos(channel: str, limit: int = 5) -> list[dict]:
    """List recent videos from a YouTube channel using yt-dlp."""
    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--flat-playlist",
                "--print",
                "%(id)s\t%(title)s\t%(upload_date)s\t%(duration)s",
                "--playlist-end",
                str(limit),
                f"https://www.youtube.com/{channel}/videos",
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        print(f"Error: Timeout listing videos for {channel}", file=sys.stderr)
        return []

    if result.returncode != 0:
        print(f"Error listing videos: {result.stderr[:500]}", file=sys.stderr)
        return []

    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        video = {
            "id": parts[0],
            "title": parts[1],
            "published": parts[2] if len(parts) > 2 else "",
            "duration": parts[3] if len(parts) > 3 else "",
            "url": f"https://www.youtube.com/watch?v={parts[0]}",
            "source_type": "youtube",
        }
        videos.append(video)

    return videos


def is_livestream(video: dict) -> bool:
    """Heuristic check if a video is a livestream (very long duration)."""
    try:
        duration = int(video.get("duration", 0))
        # Videos longer than 4 hours are likely livestreams
        return duration > 14400
    except (ValueError, TypeError):
        return False


def fetch_subtitles(video_id: str, output_dir: Path) -> str | None:
    """Try to download subtitles (zh-TW preferred, en fallback)."""
    sub_path = output_dir / f"{video_id}"

    try:
        result = subprocess.run(
            [
                "yt-dlp",
                "--write-subs",
                "--write-auto-subs",
                "--sub-lang",
                "zh-TW,zh-Hant,zh,en",
                "--sub-format",
                "vtt",
                "--skip-download",
                "--no-warnings",
                "-o",
                str(sub_path),
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        return None

    # Find the downloaded subtitle file
    for lang in ["zh-TW", "zh-Hant", "zh", "en"]:
        vtt_file = output_dir / f"{video_id}.{lang}.vtt"
        if vtt_file.exists():
            return parse_vtt(vtt_file)

    return None


def parse_vtt(vtt_path: Path) -> str:
    """Parse VTT subtitle file, strip timestamps, deduplicate lines."""
    text = vtt_path.read_text(encoding="utf-8")

    # Remove VTT header
    lines = text.split("\n")
    content_lines = []
    prev_line = ""

    for line in lines:
        line = line.strip()
        # Skip empty lines, timestamps, WEBVTT header, NOTE lines
        if not line:
            continue
        if line.startswith("WEBVTT"):
            continue
        if line.startswith("NOTE"):
            continue
        if re.match(r"\d{2}:\d{2}", line):
            continue
        # Remove HTML tags
        line = re.sub(r"<[^>]+>", "", line)
        # Deduplicate consecutive identical lines
        if line != prev_line:
            content_lines.append(line)
            prev_line = line

    return " ".join(content_lines)


def download_audio(video_id: str, output_dir: Path) -> str | None:
    """Download audio for transcription when no subtitles available."""
    audio_path = output_dir / f"{video_id}.wav"

    try:
        subprocess.run(
            [
                "yt-dlp",
                "-x",
                "--audio-format",
                "wav",
                "--audio-quality",
                "0",
                "-o",
                str(output_dir / f"{video_id}.%(ext)s"),
                f"https://www.youtube.com/watch?v={video_id}",
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"Warning: Failed to download audio for {video_id}: {e}", file=sys.stderr)
        return None

    if audio_path.exists():
        return str(audio_path)
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch YouTube channel videos")
    parser.add_argument(
        "--channel", required=True, help="YouTube channel handle (e.g. @username)"
    )
    parser.add_argument("--limit", type=int, default=5, help="Max videos to fetch")
    parser.add_argument(
        "--output-dir", required=True, help="Directory to save fetched data"
    )
    parser.add_argument(
        "--source-name", default="youtube", help="Name of this source"
    )
    parser.add_argument(
        "--filter-livestream", action="store_true", help="Skip livestream videos"
    )
    parser.add_argument(
        "--transcript",
        choices=["subs", "whisper", "both"],
        default="both",
        help="Transcript strategy: subs only, whisper only, or try subs then whisper",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    subs_dir = output_dir / "subs"
    subs_dir.mkdir(exist_ok=True)
    audio_dir = output_dir / "audio"
    audio_dir.mkdir(exist_ok=True)

    print(f"Listing videos from: {args.channel}", file=sys.stderr)
    videos = list_videos(args.channel, args.limit)
    print(f"Found {len(videos)} videos", file=sys.stderr)

    if args.filter_livestream:
        before = len(videos)
        videos = [v for v in videos if not is_livestream(v)]
        filtered = before - len(videos)
        if filtered:
            print(f"Filtered {filtered} livestreams", file=sys.stderr)

    for video in videos:
        video["source_name"] = args.source_name
        video_id = video["id"]
        print(f"  Processing: {video['title'][:50]}...", file=sys.stderr)

        transcript = None

        # Try subtitles first
        if args.transcript in ("subs", "both"):
            transcript = fetch_subtitles(video_id, subs_dir)
            if transcript:
                video["transcript"] = transcript
                video["transcript_source"] = "subtitles"
                print(f"    Got subtitles ({len(transcript)} chars)", file=sys.stderr)

        # Fallback to audio download for whisper
        if not transcript and args.transcript in ("whisper", "both"):
            audio_path = download_audio(video_id, audio_dir)
            if audio_path:
                video["audio_path"] = audio_path
                print(f"    Downloaded audio for whisper", file=sys.stderr)

        if not transcript and "audio_path" not in video:
            print(f"    Warning: No transcript or audio available", file=sys.stderr)

    # Output JSON
    output_file = output_dir / f"{args.source_name.replace(' ', '_')}_videos.json"
    with open(output_file, "w") as f:
        json.dump(videos, f, ensure_ascii=False, indent=2)

    print(json.dumps(videos, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
