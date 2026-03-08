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
argument-hint: "[run|setup|add <url>|status|help]"
metadata:
  author: abe1272001
  version: 0.2.0
  license: MIT
compatibility: >
  Requires: Python 3.10+, yt-dlp, faster-whisper, feedparser, httpx, pyyaml.
  macOS/Linux. Claude CLI authenticated.
---

# Daily Digest — Execution Skill

You are an autonomous content digest operator. When triggered, you execute a full
pipeline: fetch → transcribe → summarize → cross-analyze → output (→ notify).

## Command Routing

Parse `$ARGUMENTS` to determine what to do:

| Command | Example | Action |
|---------|---------|--------|
| (empty) | `/daily-digest` | Show usage guide below |
| `run` | `/daily-digest run` | Execute the full pipeline |
| `setup` | `/daily-digest setup` | Run first-time setup |
| `add <url>` | `/daily-digest add https://feeds...` | Add a new source |
| `status` | `/daily-digest status` | Show config, sources, and last run info |
| `help` | `/daily-digest help` | Show usage guide below |

### Usage Guide (show when no arguments or `help`)

When the user runs `/daily-digest` without arguments, output this exactly:

```
╔══════════════════════════════════════════════════╗
║           📰 Daily Digest v0.2.0                ║
║           每日內容摘要 Pipeline                   ║
╚══════════════════════════════════════════════════╝

  指令                          說明
  ──────────────────────────────────────────────
  /daily-digest setup           首次設定（來源 + 通知）
  /daily-digest run             執行一次完整摘要
  /daily-digest add <url>       新增 Podcast 或 YouTube 來源
  /daily-digest status          查看來源與執行狀態
  /daily-digest help            顯示此說明

  快速開始
  ──────────────────────────────────────────────
  Step 1 → /daily-digest setup     設定內容來源
  Step 2 → /daily-digest run       跑第一次摘要

  也可以直接說
  ──────────────────────────────────────────────
  「幫我整理今天的 podcast 和 YouTube」
  「跑一次每日摘要」
  「新增這個 RSS 到 daily digest: https://...」
```

Do NOT proceed with any pipeline execution when showing the usage guide.

## Important: You ARE the summarizer

Do NOT shell out to `claude -p` for summarization. You are already an LLM — summarize
and analyze content directly in your reasoning. This saves tokens, is faster, and
produces better results since you have full pipeline context.

## First-Time Setup

If no `daily-digest-config/` directory exists in the project root, guide the user
through setup. Display progress as you go:

```
── Daily Digest Setup ─────────────────────────────
  [1/4] 檢查依賴套件
  [2/4] 設定內容來源
  [3/4] 設定通知方式（可跳過）
  [4/4] 驗證設定
────────────────────────────────────────────────────
```

### [1/4] Check Dependencies

```bash
python "${CLAUDE_SKILL_DIR}/scripts/setup.py" --check
```

If missing, ask the user if they want to auto-install:
```bash
python "${CLAUDE_SKILL_DIR}/scripts/setup.py" --install
```

### [2/4] Configure Sources

Ask the user for their content sources. For each source, determine:
- Is it a Podcast RSS or YouTube channel?
- What's the URL / channel handle?
- Proactively search for the real RSS URL or channel handle if the user gives a name

Create `daily-digest-config/sources.yaml`:
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

### [3/4] Configure Notifications (OPTIONAL)

Ask the user:

```
要設定通知嗎？（可以之後再設定）

  [1] Telegram Bot — 推薦，手機/桌面都好讀
  [2] 先跳過 — 摘要只存本地 Markdown

選擇 (1/2):
```

If the user chooses Telegram, guide them step by step:

```
── Telegram Bot 設定 ──────────────────────────────
  Step 1: 在 Telegram 搜尋 @BotFather
  Step 2: 發送 /newbot，設定 bot 名稱和 username
  Step 3: 複製 BotFather 給你的 Bot Token
  Step 4: 對你的 bot 發送 /start
  Step 5: 取得 chat_id:
          curl https://api.telegram.org/bot<TOKEN>/getUpdates
          找到 "chat":{"id": 數字} 就是你的 chat_id
────────────────────────────────────────────────────
```

Save to `daily-digest-config/telegram.yaml`:
```yaml
bot_token: "your-bot-token"
chat_id: 123456789
```

If the user skips, do NOT create `telegram.yaml`. The pipeline will work fine
without it — digests are always saved as local Markdown files regardless.

### [4/4] Validate

Validate each source with a test fetch:
```bash
python "${CLAUDE_SKILL_DIR}/scripts/fetch_podcast.py" --url "URL" --limit 1 --output-dir /tmp/digest-test/
python "${CLAUDE_SKILL_DIR}/scripts/fetch_youtube.py" --channel "HANDLE" --limit 1 --output-dir /tmp/digest-test/
```

If Telegram is configured, send a test message:
```bash
python "${CLAUDE_SKILL_DIR}/scripts/notify_telegram.py" \
  --config daily-digest-config/telegram.yaml \
  --test
```

Show final summary:

```
── Setup Complete ─────────────────────────────────
  來源:   2 個（1 Podcast + 1 YouTube）
  通知:   Telegram ✓  /  未設定（本地 Markdown）
  下一步: /daily-digest run
────────────────────────────────────────────────────
```

## Status Command

When the user runs `/daily-digest status`, read config and state, then display:

```
── Daily Digest Status ────────────────────────────
  來源 (N 個):
    • [podcast] 來源名稱 — https://...
    • [youtube] 來源名稱 — @handle

  通知:
    • Telegram ✓  /  未設定

  上次執行: YYYY-MM-DD HH:MM
  已處理:   N 個項目
────────────────────────────────────────────────────
```

Read the data from:
```bash
python "${CLAUDE_SKILL_DIR}/scripts/config_loader.py" \
  --sources daily-digest-config/sources.yaml \
  --state daily-digest-config/state.json
```

## Pipeline Execution

Run the pipeline in this exact order. Verify each step before proceeding.
Display progress as a checklist — update after each step:

```
── Daily Digest Pipeline ──────────────────────────
  [v] Step 1: 載入設定與狀態
  [v] Step 2: 抓取內容 (3 sources → 5 items)
  [v] Step 3: 去重 (2 new, 3 skipped)
  [~] Step 4: 轉錄音訊...
  [ ] Step 5: 摘要各項目
  [ ] Step 6: 跨來源分析
  [ ] Step 7: 儲存摘要
  [ ] Step 8: 推送通知
  [ ] Step 9: 更新狀態
────────────────────────────────────────────────────
```

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
  --source-name "來源名稱" \
  --download-audio \
  --output-dir daily-digest-workspace/fetched/
```

**YouTube sources:**
```bash
python "${CLAUDE_SKILL_DIR}/scripts/fetch_youtube.py" \
  --channel "CHANNEL_HANDLE_OR_URL" \
  --limit 5 \
  --source-name "來源名稱" \
  --filter-livestream \
  --transcript both \
  --output-dir daily-digest-workspace/fetched/
```

Both output JSON with: `{id, title, description, published, source_name, transcript?, audio_path?}`

### Step 3: Deduplicate

Compare fetched item IDs against `processed_ids` from Step 1. Skip already-processed items.

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

- Write in **繁體中文**
- Be detailed and faithful — preserve key arguments, data points, quotes
- Structure:

```
### [來源名稱] — [標題]
📅 YYYY-MM-DD

**重點摘要：**
• point 1
• point 2
• point 3

**關鍵觀點：**
paragraph with notable insights, quotes, or data
```

- Keep each summary 300-800 characters

### Step 6: Cross-Source Analysis (YOU do this)

After all individual summaries, analyze across sources:

```
## 跨來源分析

### 共同主題
themes across 2+ sources

### 不同觀點
where sources disagree or differ

### 今日洞察
your synthesis and actionable takeaways
```

### Step 7: Write Output

Save the full digest to `daily-digest-workspace/summaries/YYYY-MM-DD.md`.
Save raw transcripts to `daily-digest-workspace/transcripts/`.

### Step 8: Notify (if configured)

**Only if `daily-digest-config/telegram.yaml` exists:**

```bash
python "${CLAUDE_SKILL_DIR}/scripts/notify_telegram.py" \
  --config daily-digest-config/telegram.yaml \
  --file daily-digest-workspace/summaries/YYYY-MM-DD.md
```

If telegram.yaml does not exist, skip this step and tell the user:
```
📄 摘要已儲存至 daily-digest-workspace/summaries/YYYY-MM-DD.md
💡 如需推送通知，執行 /daily-digest setup 設定 Telegram
```

### Step 9: Update State

```bash
python "${CLAUDE_SKILL_DIR}/scripts/update_state.py" \
  --state daily-digest-config/state.json \
  --processed-ids "id1,id2,id3"
```

### Pipeline Complete

Show final summary:

```
── Pipeline Complete ──────────────────────────────
  日期:     YYYY-MM-DD
  新項目:   N 篇（X Podcast + Y YouTube）
  摘要:     daily-digest-workspace/summaries/YYYY-MM-DD.md
  通知:     ✓ Telegram 已推送  /  ⏭ 跳過（未設定）
  耗時:     ~Xm Xs
────────────────────────────────────────────────────
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

For YouTube:
```bash
python "${CLAUDE_SKILL_DIR}/scripts/fetch_youtube.py" --channel "HANDLE" --limit 1 --output-dir /tmp/digest-test/
```

After adding, confirm:
```
── Source Added ────────────────────────────────────
  名稱:   新來源名稱
  類型:   podcast / youtube
  URL:    https://...
  驗證:   ✓ 成功抓取 1 筆測試資料
────────────────────────────────────────────────────
```

## Scheduling

Read `${CLAUDE_SKILL_DIR}/references/scheduling.md` for launchd/cron setup instructions.
