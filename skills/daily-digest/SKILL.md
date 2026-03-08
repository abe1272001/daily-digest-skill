---
name: daily-digest
description: >
  Run a daily content digest pipeline that fetches Podcast RSS feeds and YouTube
  channels, transcribes audio, generates AI summaries in Traditional Chinese, and
  sends notifications via Telegram. Use this skill whenever the user wants to:
  set up or run a daily digest, summarize podcasts or YouTube videos, create a
  content briefing, aggregate RSS/YouTube content, or build an automated summary
  system. Also triggers for: "daily digest", "每日摘要", "podcast 摘要",
  "YouTube 整理", "跑摘要", "內容彙整", "幫我整理今天的 podcast",
  "summarize my subscriptions", or any request to periodically collect and
  summarize media content. Even if the user just says "digest" or "摘要",
  check if this skill applies.
metadata:
  author: ray870211
  version: 0.1.0
  license: MIT
compatibility: >
  Requires: Python 3.10+, yt-dlp, faster-whisper, feedparser, httpx, pyyaml.
  macOS/Linux. Claude CLI authenticated.
---

# Daily Digest — Execution Skill

You are an autonomous content digest operator. When triggered, you execute a full
pipeline: fetch → transcribe → summarize → cross-analyze → notify.

## Important: You ARE the summarizer

Do NOT shell out to `claude -p` for summarization. You are already an LLM — summarize
and analyze content directly in your reasoning. This saves tokens, is faster, and
produces better results since you have full pipeline context.

## First-Time Setup

If no `daily-digest-config/` directory exists in the project root, guide the user
through setup step by step:

1. Run the setup script:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/setup.py" --check
   ```
   This checks which dependencies are installed and which are missing.

2. If dependencies are missing, install them:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/setup.py" --install
   ```

3. Ask the user for their content sources and create `daily-digest-config/sources.yaml`:
   ```yaml
   sources:
     - name: "來源名稱"
       type: podcast        # or "youtube"
       url: "https://..."   # RSS feed URL or YouTube channel handle
       limit: 5             # max items per run
       # YouTube-specific options:
       # filter: livestream   # skip livestreams
       # transcript: both     # try subs first, fallback whisper
   ```

4. Ask for Telegram bot credentials and save to `daily-digest-config/telegram.yaml`:
   ```yaml
   bot_token: "your-bot-token"
   chat_id: 123456789
   ```
   Guide them: BotFather → /newbot → get token → send /start to bot → get chat_id.

5. Confirm setup by running:
   ```bash
   python "${CLAUDE_SKILL_DIR}/scripts/notify_telegram.py" \
     --config daily-digest-config/telegram.yaml \
     --test
   ```

## Pipeline Execution

Run the pipeline in this exact order. Verify each step before proceeding.

### Step 1: Load Config & State

```bash
python "${CLAUDE_SKILL_DIR}/scripts/config_loader.py" \
  --sources daily-digest-config/sources.yaml \
  --state daily-digest-config/state.json
```

This outputs JSON with sources list and already-processed item keys.

### Step 2: Fetch Content

For each source, run the appropriate fetcher:

**Podcast sources:**
```bash
python "${CLAUDE_SKILL_DIR}/scripts/fetch_podcast.py" \
  --url "RSS_FEED_URL" \
  --limit 5 \
  --output-dir daily-digest-workspace/fetched/
```

**YouTube sources:**
```bash
python "${CLAUDE_SKILL_DIR}/scripts/fetch_youtube.py" \
  --channel "CHANNEL_HANDLE_OR_URL" \
  --limit 5 \
  --output-dir daily-digest-workspace/fetched/
```

Both output JSON files with: `{id, title, description, published, source_name, transcript?, audio_path?}`

### Step 3: Deduplicate

Compare fetched item IDs against state. Skip already-processed items.
Use the config_loader output from Step 1 to check.

### Step 4: Transcribe (if needed)

For items that have `audio_path` but no `transcript`:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/transcribe.py" \
  --audio "path/to/audio.wav" \
  --model tiny \
  --language zh
```

Outputs the transcript text to stdout.

### Step 5: Summarize (YOU do this)

For each new item, read the transcript and produce a summary **directly in your response**.
Follow these guidelines:

- Write in **繁體中文**
- Be detailed and faithful to the source — preserve key arguments, data points, quotes
- Structure each summary with:  來源名稱、標題、發布日期、重點摘要、關鍵觀點
- Keep each summary 300-800 characters

### Step 6: Cross-Source Analysis (YOU do this)

After all individual summaries, analyze across sources:

1. **共同主題** — What themes appear across multiple sources?
2. **不同觀點** — Where do sources disagree or offer different angles?
3. **獨立洞察** — Your synthesis and what the user should pay attention to

### Step 7: Write Output

Save the full digest to `daily-digest-workspace/summaries/YYYY-MM-DD.md` with:
- Date header
- Individual summaries
- Cross-analysis section

Also save raw transcripts to `daily-digest-workspace/transcripts/` for reference.

### Step 8: Notify via Telegram

```bash
python "${CLAUDE_SKILL_DIR}/scripts/notify_telegram.py" \
  --config daily-digest-config/telegram.yaml \
  --file daily-digest-workspace/summaries/YYYY-MM-DD.md
```

### Step 9: Update State

```bash
python "${CLAUDE_SKILL_DIR}/scripts/update_state.py" \
  --state daily-digest-config/state.json \
  --processed-ids "id1,id2,id3"
```

## Error Handling

- If a fetch fails for one source, log it and continue with other sources
- If transcription fails, skip the item and note it in the digest
- If Telegram notification fails, the digest is still saved locally — tell the user
- Never let one failure abort the entire pipeline

## Adding Sources

When the user wants to add a new source, edit `daily-digest-config/sources.yaml` directly.
Validate the source by doing a test fetch:

```bash
python "${CLAUDE_SKILL_DIR}/scripts/fetch_podcast.py" --url "NEW_URL" --limit 1 --output-dir /tmp/digest-test/
```

## Scheduling

Read `${CLAUDE_SKILL_DIR}/references/scheduling.md` for launchd/cron setup instructions.
