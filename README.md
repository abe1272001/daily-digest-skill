# daily-digest-skill

An agent skill that autonomously runs a daily content digest pipeline — fetching Podcasts and YouTube videos, transcribing audio, generating AI summaries in Traditional Chinese, and notifying via Telegram.

## Install

```bash
npx skills add abe1272001/daily-digest-skill
```

## What it does

```
RSS Feeds ──┐                    ┌── Summarize (Claude)
            ├── Fetch → Transcribe ──┤
YouTube ────┘                    └── Cross-analyze → Telegram
```

- **Fetch** latest content from Podcast RSS feeds and YouTube channels
- **Transcribe** audio using `faster-whisper` (YouTube subtitles preferred)
- **Summarize** each item in detailed Traditional Chinese (Claude does this directly)
- **Cross-analyze** themes across all sources
- **Notify** via Telegram with formatted messages

## Architecture

Follows Anthropic's recommended **hybrid execution pattern**:

| Step | Type | Handler |
|------|------|---------|
| Fetch | Deterministic | Bundled Python script |
| Transcribe | Deterministic | Bundled Python script |
| Summarize | Requires judgment | Claude directly |
| Cross-analyze | Requires judgment | Claude directly |
| Notify | Deterministic | Bundled Python script |

## Requirements

- Python 3.10+
- `claude` CLI (authenticated)
- `yt-dlp`, `faster-whisper`, `feedparser`, `httpx`, `pyyaml`
- `ffmpeg`, `curl`

## Usage

After installing the skill, ask Claude:

```
幫我設定 daily digest
跑一次每日摘要
新增這個 podcast 到 daily digest: https://...
整理一下今天的 YouTube 和 podcast
```

## Data Directory

All runtime data is stored in a fixed home directory (`~/.daily-digest/`), independent of your current working directory:

```
~/.daily-digest/
  venv/                   # Python virtual environment (yt-dlp, faster-whisper, etc.)
  config/
    sources.yaml          # RSS feeds & YouTube channels
    settings.yaml         # Language preference
    state.json            # Processed item tracking (dedup)
    telegram.yaml         # Telegram bot credentials (optional)
  workspace/
    fetched/              # Downloaded episodes & video metadata
    transcripts/          # Transcribed text
    summaries/            # Daily digest output (YYYY-MM-DD.md / .json)
```

The directory is created automatically on first run — no manual setup needed.

## Project Structure

```
skills/
  daily-digest/
    SKILL.md              # Main skill definition
    scripts/
      setup.py            # Dependency checker & installer
      config_loader.py    # Load sources + state
      fetch_podcast.py    # RSS feed fetcher
      fetch_youtube.py    # YouTube channel fetcher
      transcribe.py       # Whisper audio transcription
      notify_telegram.py  # Telegram bot notifications
      update_state.py     # Dedup state management
      cleanup.py          # Workspace cleanup (retention policy)
    references/
      pipeline.md         # Architecture deep-dive
      scheduling.md       # Cron/launchd setup
```

## Credits

Inspired by [ray870211/daily-digest](https://github.com/ray870211/daily-digest) — the original Python CLI tool for aggregating podcast and YouTube content. This skill reimplements the concept as an agent skill following Anthropic's hybrid execution pattern.

## License

MIT
