# daily-digest-skill

An agent skill that autonomously runs a daily content digest pipeline — fetching Podcasts and YouTube videos, transcribing audio, generating AI summaries in Traditional Chinese, and notifying via Telegram.

## Install

```bash
npx skills add ray870211/daily-digest-skill
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
    references/
      pipeline.md         # Architecture deep-dive
      scheduling.md       # Cron/launchd setup
```

## License

MIT
