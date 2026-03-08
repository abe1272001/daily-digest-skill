# Pipeline Architecture Reference

## Design Philosophy

This skill follows the **hybrid execution pattern** recommended by Anthropic's skill best practices:

- **Deterministic steps** (fetch, transcribe, notify, cleanup) → bundled Python scripts
- **Judgment steps** (summarize, cross-analyze) → Claude does it directly
- **Orchestration** → SKILL.md workflow checklist

This is more efficient than shelling out to `claude -p` because:
1. Claude is already running — no subprocess overhead
2. Full pipeline context available for better summaries
3. Fewer tokens consumed (no duplicate context loading)

## Script Interface Contract

All scripts follow a consistent interface:

- Input via CLI arguments (not stdin)
- Structured output to stdout (JSON where applicable)
- Progress/errors to stderr
- Non-zero exit code on failure
- No interactive prompts

## Data Flow

```
sources.yaml
    │
    ▼
┌─────────────┐     ┌─────────────────┐
│ fetch_podcast│     │  fetch_youtube   │
│    .py       │     │     .py          │
└──────┬───────┘     └────────┬─────────┘
       │                      │
       ▼                      ▼
   episodes.json          videos.json
       │                      │
       ├──────────┬───────────┘
       ▼          ▼
   ┌─────────────────┐
   │ config_loader.py │ ← state.json (dedup)
   └────────┬─────────┘
            │ new items only
            ▼
   ┌─────────────────┐
   │  transcribe.py   │ ← only items without transcript
   └────────┬─────────┘
            │
            ▼
   ┌─────────────────────┐
   │  Claude summarizes   │ ← YOU do this, not a script
   │  + cross-analyzes    │
   └────────┬─────────────┘
            │
            ├────────────┬──────────────┐
            ▼            ▼              ▼
   YYYY-MM-DD.md   YYYY-MM-DD.json   notify_telegram.py
   (for humans)    (for machines)       │
                                        ▼
                                   Telegram message
            │
            ▼
   update_state.py → state.json
            │
            ▼
   cleanup.py → remove old audio/transcripts
```

## Summarization Guidelines

When Claude summarizes content, follow these principles:

### Individual Summary Structure

```markdown
### [來源名稱] — [標題]
📅 [發布日期]

**重點摘要：**
[3-5 bullet points covering the main content]

**關鍵觀點：**
[1-2 paragraphs with notable quotes, data, or arguments]

**關鍵數字：**
[Specific data points, stats, metrics mentioned — if any]
```

### Cross-Analysis Structure (6 Dimensions)

```markdown
## 跨來源分析

### 共同主題
Themes that appear in 2+ sources.

### 不同觀點
Where sources disagree or offer different angles.

### 情緒觀感
Per-source tone on each major topic (bullish/bearish, optimistic/cautious).

### 關鍵數字
Most important data points aggregated across all sources.

### 行動建議
- 🔍 [Research] — topics worth digging deeper
- 👁 [Monitor] — trends or events to keep watching
- 🚀 [Try] — tools, techniques, or ideas to experiment with

### 優先閱讀
Rank today's items by relevance — help the user decide what to read in full.
```

### Quality Standards

- Be faithful to the source — don't inject opinions into individual summaries
- Preserve specific numbers, quotes, and data points
- Cross-analysis is where you add analytical value
- Keep individual summaries 300-800 chars; cross-analysis can be longer
- Language follows settings.yaml (default: en)

## Dual Output Format

Each digest produces two files:

- **Markdown** (`YYYY-MM-DD.md`) — human-readable, sent via Telegram
- **JSON** (`YYYY-MM-DD.json`) — machine-readable, enables trending analysis

The JSON schema enables future features like weekly trend reports by allowing
programmatic access to historical digest data.

### JSON Schema

```json
{
  "date": "YYYY-MM-DD",
  "items": [
    {
      "source": "Source Name",
      "source_type": "podcast|youtube",
      "title": "Episode/Video title",
      "summary": "3-5 bullet point summary",
      "key_insights": "Notable analysis, quotes, data points",
      "key_numbers": ["stat 1", "stat 2"]
    }
  ],
  "cross_analysis": {
    "themes": "Common themes across sources",
    "contrasts": "Different perspectives",
    "sentiment": {"Source A": "bullish", "Source B": "cautious"},
    "key_numbers": ["aggregated stat 1"],
    "action_items": [
      {"category": "Research", "text": "Topic to dig into"},
      {"category": "Monitor", "text": "Trend to watch"},
      {"category": "Try", "text": "Tool to experiment with"}
    ],
    "priority_reading": ["Most relevant item", "Second most relevant"]
  },
  "metadata": {
    "total_items": 5,
    "podcast_count": 2,
    "youtube_count": 3,
    "language": "zh-TW"
  }
}
```

### TUI digest-preview data format

The `tui.py digest-preview --data` expects JSON with these fields:

```json
{
  "date": "2026-03-08",
  "summaries": [{"type": "podcast", "source": "Source", "title": "Title", "preview": "..."}],
  "cross_analysis": {"themes": "...", "contrasts": "..."},
  "key_numbers": ["stat 1", "stat 2"],
  "sentiment": {"Source A": "bullish"},
  "action_items": [{"category": "Research", "text": "..."}],
  "priority_reading": ["Item 1", "Item 2"],
  "digest_path": "daily-digest-workspace/summaries/2026-03-08.md"
}
```

## Workspace Retention

The `cleanup.py` script implements tiered retention to keep workspace size
manageable. Audio files are the largest (tens of MB each) and are cleaned
first. Summaries are tiny and kept indefinitely.

| Age | Keep | Delete |
|-----|------|--------|
| This week | Everything | — |
| This month | Summaries, transcripts, JSON | Audio |
| This quarter | Summaries, JSON | Audio, transcripts |
| 6 months | Summaries MD | JSON, transcripts |
| 1 year+ | Summaries MD | Everything else |

Can be automated with `/loop 1d /daily-digest cleanup`.
