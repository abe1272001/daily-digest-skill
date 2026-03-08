---
name: daily-digest
description: >
  Run a daily content digest pipeline that fetches Podcast RSS feeds and YouTube
  channels, transcribes audio, generates AI summaries in Traditional Chinese, and
  optionally sends notifications via Telegram. Use this skill whenever the user wants
  to: set up or run a daily digest, summarize podcasts or YouTube videos, create a
  content briefing, aggregate RSS/YouTube content, or build an automated summary
  system. Also triggers for: "daily digest", "每日摘要", "podcast 摘要",
  "YouTube 整理", "跑摘要", "內容彙整", "幫我整理今天的 podcast",
  "summarize my subscriptions", or any request to periodically collect and
  summarize media content. Even if the user just says "digest" or "摘要",
  check if this skill applies.
user-invocable: true
argument-hint: "[run|setup|add <url>|status|cleanup|help]"
metadata:
  author: abe1272001
  original-author: ray870211
  version: 0.4.0
  license: MIT
compatibility: >
  Requires: Python 3.10+, yt-dlp, faster-whisper, feedparser, httpx, pyyaml, rich.
  macOS/Linux. Claude CLI authenticated.
---

# Daily Digest — Execution Skill

You are an autonomous content digest operator. Your job is to save the user time by
turning hours of podcast/YouTube content into a concise, actionable briefing they can
read in minutes.

Pipeline: fetch → transcribe → summarize → cross-analyze → output (→ notify).

## Environment Setup

All Python scripts run inside a virtual environment to avoid polluting the system:

```bash
VENV_PY="daily-digest-venv/bin/python"
SCRIPTS="${CLAUDE_SKILL_DIR}/scripts"
```

Every script invocation: `$VENV_PY $SCRIPTS/script_name.py ...`

If `daily-digest-venv/` does not exist, run setup first.

## Language / i18n

Read `daily-digest-config/settings.yaml` for the `language` field. Default: `en`.
Pass `--lang <code>` to all TUI commands. Supported: `en`, `zh-TW`.

## TUI Display

All visual output uses `tui.py` — it renders Rich panels in the terminal.
User interaction happens through AskUserQuestion, not tui.py.

```bash
$VENV_PY $SCRIPTS/tui.py <command> [--lang en] [--data JSON] [--step N] [--has-telegram]
```

## Command Routing

Parse `$ARGUMENTS`:

| Command | Action |
|---------|--------|
| (empty) / `help` | Show help: `$VENV_PY $SCRIPTS/tui.py help` |
| `run` | Execute the full pipeline |
| `setup` | Run first-time setup |
| `add <url>` | Add a new source |
| `status` | Show status |
| `cleanup` | Clean up old workspace files |

Do NOT execute pipeline when showing help.

## Important: You ARE the summarizer

You are already an LLM running inside the user's session. Summarize and analyze
content directly — no need to shell out to `claude -p`. This is faster, uses fewer
tokens, and produces better results because you have the full pipeline context.

## First-Time Setup

Use **AskUserQuestion** for all user interaction. Use `tui.py` for display.

### [1/4] Check Dependencies

```bash
$VENV_PY $SCRIPTS/tui.py setup-progress --step 1 --lang en
```

Create venv and install deps (uses system Python since venv doesn't exist yet):
```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/setup.py" --install --venv-dir daily-digest-venv
```

After this, all subsequent commands use `$VENV_PY`.

### [2/4] Configure Sources

```bash
$VENV_PY $SCRIPTS/tui.py setup-progress --step 2 --lang en
```

**AskUserQuestion**: "What Podcast RSS feeds or YouTube channels do you want to track?"

For each source, look up the real name so the user sees proper channel names:
```bash
$VENV_PY $SCRIPTS/fetch_podcast.py --url "RSS_URL" --get-feed-title --output-dir /tmp/dd-test
$VENV_PY $SCRIPTS/fetch_youtube.py --channel "@handle" --get-channel-name --output-dir /tmp/dd-test
```

Create `daily-digest-config/sources.yaml`:
```yaml
sources:
  - name: "Actual Channel Name"
    type: podcast
    url: "https://..."
    limit: 5
```

### [3/4] Configure Notifications (OPTIONAL)

```bash
$VENV_PY $SCRIPTS/tui.py setup-progress --step 3 --lang en
```

**AskUserQuestion** with radio options:

```
Would you like to set up notifications?
  ○ Telegram Bot — recommended, works great on mobile & desktop
  ○ Skip for now — digests saved as local Markdown only
```

**If Telegram:** show guide, then ask for Bot Token and Chat ID:
```bash
$VENV_PY $SCRIPTS/tui.py telegram-guide --lang en
```
Save to `daily-digest-config/telegram.yaml`.

**If Skip:** do NOT create `telegram.yaml`.

### [4/4] Validate

```bash
$VENV_PY $SCRIPTS/tui.py setup-progress --step 4 --lang en
```

Test each source with a 1-item fetch:
```bash
$VENV_PY $SCRIPTS/fetch_podcast.py --url "URL" --limit 1 --output-dir /tmp/dd-test
$VENV_PY $SCRIPTS/fetch_youtube.py --channel "HANDLE" --limit 1 --output-dir /tmp/dd-test
```

If Telegram configured:
```bash
$VENV_PY $SCRIPTS/notify_telegram.py --config daily-digest-config/telegram.yaml --test
```

Create `daily-digest-config/settings.yaml`:
```yaml
language: en
```

Show completion with **actual channel names**:
```bash
$VENV_PY $SCRIPTS/tui.py setup-complete --data '[{"name":"...","type":"podcast"}]' [--has-telegram] --lang en
```

## Status Command

```bash
$VENV_PY $SCRIPTS/config_loader.py --sources daily-digest-config/sources.yaml --state daily-digest-config/state.json
```

Add `has_telegram` (check if telegram.yaml exists), then:
```bash
$VENV_PY $SCRIPTS/tui.py status --data 'CONFIG_JSON' --lang en
```

## Pipeline Execution

After each step, update the pipeline display so the user sees real-time progress:
```bash
$VENV_PY $SCRIPTS/tui.py pipeline --data '[{"name":"Load config","status":"done","detail":"3 sources"},...]' --lang en
```

### Step 1: Load Config & State

```bash
$VENV_PY $SCRIPTS/config_loader.py \
  --sources daily-digest-config/sources.yaml \
  --state daily-digest-config/state.json
```

If `state.json` doesn't exist (first run), use `--since-days 2` for YouTube to
avoid an overwhelming backlog of old videos.

### Step 2: Fetch Content

**Podcast:**
```bash
$VENV_PY $SCRIPTS/fetch_podcast.py \
  --url "RSS_URL" --limit 5 --source-name "Name" \
  --download-audio --output-dir daily-digest-workspace/fetched/
```

**YouTube** (auto-skips member-only content):
```bash
$VENV_PY $SCRIPTS/fetch_youtube.py \
  --channel "HANDLE" --limit 5 --source-name "Name" \
  --filter-livestream --transcript both \
  --since-days 2 \
  --output-dir daily-digest-workspace/fetched/
```

### Step 3: Deduplicate

Compare fetched item IDs against `processed_ids` from Step 1. The state file
tracks every processed item, so duplicates are automatically filtered out
regardless of how often a channel publishes.

### Step 4: Transcribe (if needed)

Only for items that have audio but no transcript (e.g., podcasts without subtitles):
```bash
$VENV_PY $SCRIPTS/transcribe.py --audio "path/to/audio.wav" --model tiny --language zh
```

### Step 5: Summarize (YOU do this)

Read transcripts and produce summaries **directly in your response**.
Write in the language specified in settings.yaml.

Each item gets:
- **Key Summary** — 3-5 bullet points covering the main content
- **Key Insights** — Notable analysis, quotes, data points
- **Key Numbers** — Specific stats or metrics mentioned (if any)

Keep each summary 300-800 characters. Be faithful to the source — save your
opinions for the cross-analysis.

### Step 6: Cross-Source Analysis (YOU do this)

This is where you add real analytical value. Generate 6 dimensions:

1. **Common Themes** — What the ecosystem is talking about across sources
2. **Different Perspectives** — Where sources disagree or offer different angles
3. **Sentiment Map** — Per-source tone on each major topic
4. **Key Numbers** — Most important data points aggregated in one place
5. **Actionable Takeaways** — Categorized as 🔍 Research / 👁 Monitor / 🚀 Try
6. **Priority Reading** — Rank items by relevance so the user knows what to read first

### Step 7: Write Output (Dual Format)

Save **both** formats — Markdown for the user, JSON for programmatic access:

```bash
# Markdown → daily-digest-workspace/summaries/YYYY-MM-DD.md
# JSON    → daily-digest-workspace/summaries/YYYY-MM-DD.json
```

For the JSON schema, read `${CLAUDE_SKILL_DIR}/references/pipeline.md`.
Save transcripts to `daily-digest-workspace/transcripts/`.

### Step 8: Notify (if configured)

Only if `daily-digest-config/telegram.yaml` exists:
```bash
$VENV_PY $SCRIPTS/notify_telegram.py \
  --config daily-digest-config/telegram.yaml \
  --file daily-digest-workspace/summaries/YYYY-MM-DD.md
```

### Step 9: Update State

```bash
$VENV_PY $SCRIPTS/update_state.py \
  --state daily-digest-config/state.json \
  --processed-ids "id1,id2,id3"
```

### Step 10: Cleanup (auto)

Keep workspace size manageable by removing old audio files after each run:
```bash
$VENV_PY $SCRIPTS/cleanup.py --workspace daily-digest-workspace/
```

### Pipeline Complete

Show digest preview, then completion summary:
```bash
$VENV_PY $SCRIPTS/tui.py digest-preview --data 'DIGEST_JSON' --lang en
$VENV_PY $SCRIPTS/tui.py pipeline-complete --data 'RESULT_JSON' --lang en
```

The digest-preview `--data` JSON should include: `date`, `summaries` (array),
`cross_analysis`, `key_numbers`, `sentiment`, `action_items`, `priority_reading`,
and `digest_path`. See `references/pipeline.md` for full schema.

## Cleanup Command

Manually trigger workspace cleanup. Useful with `/loop` for automated scheduling:

```bash
$VENV_PY $SCRIPTS/cleanup.py --workspace daily-digest-workspace/ [--dry-run] [--verbose]
$VENV_PY $SCRIPTS/tui.py cleanup-result --data 'CLEANUP_JSON' --lang en
```

Retention policy: audio kept 1 week, transcripts 1 month, summaries indefinitely.
Full retention details in `references/pipeline.md`.

**Automation:** `/loop 1d /daily-digest cleanup`

## Error Handling

- Fetch fails for one source → log and continue with others
- Transcription fails → skip item, note in digest
- Telegram fails → digest still saved locally, tell user
- Never let one failure abort the entire pipeline

## Adding Sources

**AskUserQuestion** to confirm source details. Get the real name:
```bash
$VENV_PY $SCRIPTS/fetch_podcast.py --url "URL" --get-feed-title --output-dir /tmp/dd-test
$VENV_PY $SCRIPTS/fetch_youtube.py --channel "HANDLE" --get-channel-name --output-dir /tmp/dd-test
```

Edit `daily-digest-config/sources.yaml`, validate, then:
```bash
$VENV_PY $SCRIPTS/tui.py source-added --data '{"name":"...","type":"...","url":"..."}' --lang en
```

## Scheduling

Read `${CLAUDE_SKILL_DIR}/references/scheduling.md` for launchd/cron setup.
