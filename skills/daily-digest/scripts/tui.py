#!/usr/bin/env python3
"""Rich TUI display components for Daily Digest. Display-only — no user prompts.

Usage:
    python tui.py help [--lang en|zh-TW]
    python tui.py setup-progress --step N [--lang ...]
    python tui.py setup-complete --data JSON [--has-telegram] [--lang ...]
    python tui.py status --data JSON [--lang ...]
    python tui.py pipeline --data JSON [--lang ...]
    python tui.py pipeline-complete --data JSON [--lang ...]
    python tui.py source-added --data JSON [--lang ...]
    python tui.py telegram-guide [--lang ...]
    python tui.py digest-preview --data JSON [--lang ...]
"""

import argparse
import json
import sys
import os

# Allow importing i18n from the same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from i18n import t

console = Console()


def show_help(lang: str = "en"):
    """Display the help/usage guide."""
    title_text = Text()
    title_text.append(f"📰 {t('app_title', lang)}\n", style="bold cyan")
    title_text.append(f"   {t('app_subtitle', lang)}", style="dim")

    console.print(Panel(title_text, box=box.ROUNDED, border_style="cyan", padding=(1, 2)))

    cmd_table = Table(box=None, show_header=False, padding=(0, 2), expand=False)
    cmd_table.add_column("cmd", style="bold green", min_width=30)
    cmd_table.add_column("desc")
    cmd_table.add_row("/daily-digest setup", t("cmd_setup", lang))
    cmd_table.add_row("/daily-digest run", t("cmd_run", lang))
    cmd_table.add_row("/daily-digest add <url>", t("cmd_add", lang))
    cmd_table.add_row("/daily-digest status", t("cmd_status", lang))
    cmd_table.add_row("/daily-digest help", t("cmd_help", lang))

    console.print(Panel(cmd_table, title=t("commands_title", lang), box=box.ROUNDED, border_style="blue"))

    qs_table = Table(box=None, show_header=False, padding=(0, 2))
    qs_table.add_column("step", style="bold yellow")
    qs_table.add_column("cmd", style="green")
    qs_table.add_column("desc")
    qs_table.add_row("Step 1 →", "/daily-digest setup", t("quick_step1", lang))
    qs_table.add_row("Step 2 →", "/daily-digest run", t("quick_step2", lang))

    console.print(Panel(qs_table, title=t("quick_start", lang), box=box.ROUNDED, border_style="yellow"))

    nl = Text()
    nl.append(f"  {t('nl_example1', lang)}\n", style="italic")
    nl.append(f"  {t('nl_example2', lang)}\n", style="italic")
    nl.append(f"  {t('nl_example3', lang)}", style="italic")

    console.print(Panel(nl, title=t("natural_lang", lang), box=box.ROUNDED, border_style="dim"))


def show_setup_progress(current_step: int, lang: str = "en"):
    """Display setup wizard progress. current_step: 1-4."""
    steps = [
        t("step_check_deps", lang),
        t("step_config_sources", lang),
        t("step_config_notify", lang),
        t("step_validate", lang),
    ]

    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column("icon", width=3)
    table.add_column("step")
    table.add_column("status", justify="right")

    for i, step in enumerate(steps):
        step_num = i + 1
        if step_num < current_step:
            icon = "[green]✓[/green]"
            status = f"[green]{t('done', lang)}[/green]"
            style = ""
        elif step_num == current_step:
            icon = "[yellow]●[/yellow]"
            status = f"[yellow]{t('running', lang)}[/yellow]"
            style = "bold"
        else:
            icon = "[dim]○[/dim]"
            status = f"[dim]{t('pending', lang)}[/dim]"
            style = "dim"

        label = f"[{style}][{step_num}/4] {step}[/{style}]" if style else f"[{step_num}/4] {step}"
        table.add_row(icon, label, status)

    console.print(Panel(table, title=t("setup_title", lang), box=box.ROUNDED, border_style="cyan"))


def show_setup_complete(sources_json: str, has_telegram: bool, lang: str = "en"):
    """Display setup completion summary with actual source names."""
    sources = json.loads(sources_json)

    content = Table(box=None, show_header=False, padding=(0, 2))
    content.add_column("label", style="bold", min_width=14)
    content.add_column("value")

    source_lines = []
    for src in sources:
        src_type = src.get("type", "unknown")
        src_name = src.get("name", "Unknown")
        emoji = "🎙" if src_type == "podcast" else "📺"
        source_lines.append(f"{emoji} [{src_type}] {src_name}")

    content.add_row(t("sources_label", lang), "\n".join(source_lines))
    content.add_row(
        t("notify_label", lang),
        t("notify_configured", lang) if has_telegram else t("notify_not_configured", lang),
    )
    content.add_row(t("next_step", lang), "[bold green]/daily-digest run[/bold green]")

    console.print(Panel(
        content,
        title=f"[bold green]{t('setup_complete_title', lang)}[/bold green]",
        box=box.ROUNDED,
        border_style="green",
    ))


def show_status(config_json: str, lang: str = "en"):
    """Display current digest status."""
    data = json.loads(config_json)
    sources = data.get("sources", [])
    processed_count = data.get("processed_count", 0)
    last_run = data.get("last_run", t("never", lang))
    has_telegram = data.get("has_telegram", False)

    src_table = Table(box=box.SIMPLE, show_header=True, padding=(0, 1))
    src_table.add_column("#", justify="right", style="dim", width=3)
    src_table.add_column(t("type_label", lang), style="cyan", width=10)
    src_table.add_column(t("name_label", lang), style="bold")
    src_table.add_column(t("url_label", lang), style="dim")

    for i, src in enumerate(sources, 1):
        src_table.add_row(str(i), src.get("type", "?"), src.get("name", "?"), src.get("url", "?"))

    info = Table(box=None, show_header=False, padding=(0, 2))
    info.add_column("label", style="bold", min_width=14)
    info.add_column("value")
    info.add_row(
        t("notify_label", lang),
        t("notify_configured", lang) if has_telegram else t("notify_not_configured", lang),
    )
    info.add_row(t("last_run", lang), str(last_run))
    info.add_row(t("total_processed", lang), f"{processed_count} {t('items', lang)}")

    console.print(Panel(
        Group(src_table, "", info),
        title=t("status_title", lang),
        box=box.ROUNDED,
        border_style="blue",
    ))


def show_pipeline(steps_json: str, lang: str = "en"):
    """Display pipeline progress."""
    steps = json.loads(steps_json)

    table = Table(box=None, show_header=False, padding=(0, 2))
    table.add_column("icon", width=3)
    table.add_column("step")
    table.add_column("detail", justify="right", style="dim")

    for step in steps:
        status = step.get("status", "pending")
        detail = step.get("detail", "")
        name = step.get("name", "")

        if status == "done":
            icon = "[green]✓[/green]"
            style = ""
            detail = f"[dim]{detail}[/dim]" if detail else ""
        elif status == "running":
            icon = "[yellow]●[/yellow]"
            style = "bold"
            detail = f"[yellow]{detail or t('running', lang)}[/yellow]"
        elif status == "skipped":
            icon = "[dim]⏭[/dim]"
            style = "dim"
            detail = f"[dim]{t('skipped', lang)}[/dim]"
        else:
            icon = "[dim]○[/dim]"
            style = "dim"
            detail = ""

        name_str = f"[{style}]{name}[/{style}]" if style else name
        table.add_row(icon, name_str, detail)

    console.print(Panel(table, title=t("pipeline_title", lang), box=box.ROUNDED, border_style="blue"))


def show_pipeline_complete(result_json: str, lang: str = "en"):
    """Display pipeline completion summary."""
    result = json.loads(result_json)

    info = Table(box=None, show_header=False, padding=(0, 2))
    info.add_column("label", style="bold", min_width=14)
    info.add_column("value")

    info.add_row(t("date_label", lang), result.get("date", "?"))

    new_items = result.get("new_items", 0)
    podcasts = result.get("podcast_count", 0)
    youtubes = result.get("youtube_count", 0)
    info.add_row(
        t("new_items", lang),
        f"{new_items} ({podcasts} {t('podcast', lang)} + {youtubes} {t('youtube', lang)})",
    )
    info.add_row(t("digest_file", lang), result.get("digest_path", "?"))

    has_tg = result.get("telegram_sent", False)
    info.add_row(
        t("notify_status", lang),
        t("telegram_sent", lang) if has_tg else t("skipped_not_configured", lang),
    )
    info.add_row(t("duration_label", lang), result.get("duration", "?"))

    console.print(Panel(
        info,
        title=f"[bold green]{t('pipeline_complete_title', lang)}[/bold green]",
        box=box.ROUNDED,
        border_style="green",
    ))


def show_digest_preview(digest_json: str, lang: str = "en"):
    """Display a preview of the generated digest with summaries."""
    data = json.loads(digest_json)
    summaries = data.get("summaries", [])
    cross_analysis = data.get("cross_analysis", {})
    digest_path = data.get("digest_path", "")
    date = data.get("date", "")

    content_parts = []

    for s in summaries:
        src_type = s.get("type", "podcast")
        emoji = "🎙" if src_type == "podcast" else "📺"
        source = s.get("source", "")
        title = s.get("title", "")
        preview = s.get("preview", "")

        item_text = Text()
        item_text.append(f"  {emoji} ", style="bold")
        item_text.append(f"{source}", style="bold cyan")
        item_text.append(f" — {title}\n", style="bold")
        item_text.append(f"     {preview}\n", style="dim")
        content_parts.append(item_text)

    # Cross analysis section
    if cross_analysis:
        separator = Text("  ── " + t("cross_analysis", lang) + " ", style="yellow")
        separator.append("─" * 30, style="yellow dim")
        content_parts.append(separator)

        ca_text = Text()
        themes = cross_analysis.get("themes", "")
        contrasts = cross_analysis.get("contrasts", "")
        if themes:
            ca_text.append(f"  {t('common_themes', lang)}: ", style="bold")
            ca_text.append(f"{themes}\n")
        if contrasts:
            ca_text.append(f"  {t('diff_views', lang)}: ", style="bold")
            ca_text.append(f"{contrasts}\n")
        content_parts.append(ca_text)

    # Footer
    footer = Text()
    footer.append(f"\n  📄 {t('full_file', lang)}: ", style="dim")
    footer.append(digest_path, style="bold green")
    content_parts.append(footer)

    console.print(Panel(
        Group(*content_parts),
        title=f"{t('digest_preview_title', lang)} — {date}",
        box=box.ROUNDED,
        border_style="cyan",
    ))


def show_source_added(source_json: str, lang: str = "en"):
    """Display source addition confirmation."""
    source = json.loads(source_json)

    info = Table(box=None, show_header=False, padding=(0, 2))
    info.add_column("label", style="bold", min_width=12)
    info.add_column("value")
    info.add_row(t("name_label", lang), source.get("name", "?"))
    info.add_row(t("type_label", lang), source.get("type", "?"))
    info.add_row(t("url_label", lang), source.get("url", "?"))
    info.add_row(t("validation_label", lang), f"[green]{t('validation_ok', lang)}[/green]")

    console.print(Panel(
        info,
        title=f"[bold green]{t('source_added_title', lang)}[/bold green]",
        box=box.ROUNDED,
        border_style="green",
    ))


def show_telegram_guide(lang: str = "en"):
    """Display Telegram setup instructions."""
    steps = [
        t("telegram_step1", lang),
        t("telegram_step2", lang),
        t("telegram_step3", lang),
        t("telegram_step4", lang),
        t("telegram_step5", lang),
    ]

    content = Text()
    for i, step in enumerate(steps, 1):
        content.append(f"  Step {i}: ", style="bold yellow")
        content.append(f"{step}\n")

    console.print(Panel(
        content,
        title=t("telegram_guide_title", lang),
        box=box.ROUNDED,
        border_style="yellow",
    ))


def main():
    parser = argparse.ArgumentParser(description="Daily Digest TUI")
    parser.add_argument("command", choices=[
        "help", "setup-progress", "setup-complete", "status",
        "pipeline", "pipeline-complete", "source-added",
        "telegram-guide", "digest-preview",
    ])
    parser.add_argument("--lang", default="en", choices=["en", "zh-TW"])
    parser.add_argument("--step", type=int, default=1, help="Current step (for setup-progress)")
    parser.add_argument("--data", default="{}", help="JSON data for the display")
    parser.add_argument("--has-telegram", action="store_true")

    args = parser.parse_args()

    dispatch = {
        "help": lambda: show_help(args.lang),
        "setup-progress": lambda: show_setup_progress(args.step, args.lang),
        "setup-complete": lambda: show_setup_complete(args.data, args.has_telegram, args.lang),
        "status": lambda: show_status(args.data, args.lang),
        "pipeline": lambda: show_pipeline(args.data, args.lang),
        "pipeline-complete": lambda: show_pipeline_complete(args.data, args.lang),
        "source-added": lambda: show_source_added(args.data, args.lang),
        "telegram-guide": lambda: show_telegram_guide(args.lang),
        "digest-preview": lambda: show_digest_preview(args.data, args.lang),
    }

    dispatch[args.command]()


if __name__ == "__main__":
    main()
