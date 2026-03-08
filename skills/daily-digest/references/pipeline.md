# Pipeline Architecture Reference

## Design Philosophy

This skill follows the **hybrid execution pattern** recommended by Anthropic's skill best practices:

- **Deterministic steps** (fetch, transcribe, notify) → bundled Python scripts
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
            ├──────────────────┐
            ▼                  ▼
   summaries/YYYY-MM-DD.md   notify_telegram.py
                               │
                               ▼
                          Telegram message
            │
            ▼
   update_state.py → state.json
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
```

### Cross-Analysis Structure

```markdown
## 跨來源分析

### 共同主題
[Themes that appear in 2+ sources]

### 不同觀點
[Where sources disagree or offer different angles]

### 今日洞察
[Your synthesis — what the user should pay attention to]
```

### Quality Standards

- Be faithful to the source — don't inject opinions into individual summaries
- Preserve specific numbers, quotes, and data points
- Cross-analysis is where you add analytical value
- Keep individual summaries 300-800 chars; cross-analysis can be longer
- Always write in 繁體中文
