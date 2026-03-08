#!/usr/bin/env python3
"""Send digest notifications via Telegram Bot API using HTML formatting."""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx
import yaml

MAX_MESSAGE_LENGTH = 4096
# Telegram rate limit: ~1 msg/sec per chat
SEND_DELAY = 1.1


def load_config(config_path: str) -> dict:
    """Load Telegram bot config (bot_token, chat_id)."""
    path = Path(config_path)
    if not path.exists():
        print(f"Error: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        config = yaml.safe_load(f)

    if "bot_token" not in config or "chat_id" not in config:
        print("Error: Config must contain 'bot_token' and 'chat_id'", file=sys.stderr)
        sys.exit(1)

    return config


def escape_html(text: str) -> str:
    """Escape special HTML characters for Telegram."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def markdown_to_telegram_html(text: str) -> str:
    """Convert basic Markdown to Telegram-compatible HTML.

    Handles: headers, bold, italic, code blocks, inline code, links.
    Keeps it simple — complex Markdown should be pre-processed.
    """
    import re

    lines = text.split("\n")
    result = []

    in_code_block = False
    code_block_lines = []

    for line in lines:
        # Code block toggle
        if line.strip().startswith("```"):
            if in_code_block:
                code_content = "\n".join(code_block_lines)
                result.append(f"<pre>{escape_html(code_content)}</pre>")
                code_block_lines = []
                in_code_block = False
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        # Headers → bold
        if line.startswith("# "):
            result.append(f"\n<b>{escape_html(line[2:].strip())}</b>\n")
            continue
        if line.startswith("## "):
            result.append(f"\n<b>{escape_html(line[3:].strip())}</b>")
            continue
        if line.startswith("### "):
            result.append(f"<b>{escape_html(line[4:].strip())}</b>")
            continue

        # Escape HTML first for non-special content
        processed = escape_html(line)

        # Inline code (must be before bold/italic to avoid conflicts)
        processed = re.sub(r"`([^`]+)`", r"<code>\1</code>", processed)

        # Bold **text** or __text__
        processed = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", processed)
        processed = re.sub(r"__(.+?)__", r"<b>\1</b>", processed)

        # Italic *text* or _text_
        processed = re.sub(r"\*(.+?)\*", r"<i>\1</i>", processed)
        processed = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<i>\1</i>", processed)

        # Links [text](url)
        processed = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', processed
        )

        result.append(processed)

    return "\n".join(result)


def split_message(text: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
    """Split long message into chunks, preferring paragraph breaks."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        # Try splitting at double newline (paragraph break)
        split_pos = text.rfind("\n\n", 0, max_length)
        if split_pos == -1:
            # Try single newline
            split_pos = text.rfind("\n", 0, max_length)
        if split_pos == -1:
            # Hard split at limit
            split_pos = max_length

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip("\n")

    return chunks


def send_message(
    bot_token: str,
    chat_id: int | str,
    text: str,
    parse_mode: str = "HTML",
) -> dict:
    """Send a single message via Telegram Bot API."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    with httpx.Client(timeout=30) as client:
        resp = client.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            },
        )
        data = resp.json()

        if not data.get("ok"):
            error_desc = data.get("description", "Unknown error")
            # If HTML parsing fails, retry without formatting
            if "can't parse entities" in error_desc.lower():
                print(
                    "  Warning: HTML parse failed, sending as plain text",
                    file=sys.stderr,
                )
                resp = client.post(
                    url,
                    json={
                        "chat_id": chat_id,
                        "text": text,
                        "disable_web_page_preview": True,
                    },
                )
                data = resp.json()
                if not data.get("ok"):
                    raise RuntimeError(f"Telegram API error: {data.get('description')}")
            else:
                raise RuntimeError(f"Telegram API error: {error_desc}")

        return data["result"]


def send_digest(config: dict, content: str, use_html: bool = True) -> int:
    """Send a full digest, splitting if necessary. Returns message count."""
    if use_html:
        formatted = markdown_to_telegram_html(content)
    else:
        formatted = content

    chunks = split_message(formatted)
    sent = 0

    for i, chunk in enumerate(chunks):
        if i > 0:
            time.sleep(SEND_DELAY)

        print(
            f"  Sending message {i + 1}/{len(chunks)} ({len(chunk)} chars)...",
            file=sys.stderr,
        )
        send_message(
            config["bot_token"],
            config["chat_id"],
            chunk,
            parse_mode="HTML" if use_html else None,
        )
        sent += 1

    return sent


def send_test(config: dict):
    """Send a test message to verify configuration."""
    test_msg = (
        "<b>Daily Digest — Test Message</b>\n\n"
        "Configuration is working!\n"
        "Bot token: ...{}\n"
        "Chat ID: {}"
    ).format(config["bot_token"][-6:], config["chat_id"])

    send_message(config["bot_token"], config["chat_id"], test_msg)
    print("Test message sent successfully!", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Send digest via Telegram")
    parser.add_argument("--config", required=True, help="Path to telegram.yaml")
    parser.add_argument("--file", help="Markdown file to send")
    parser.add_argument("--text", help="Direct text to send")
    parser.add_argument("--test", action="store_true", help="Send test message")
    parser.add_argument(
        "--plain", action="store_true", help="Send as plain text (no HTML)"
    )
    args = parser.parse_args()

    config = load_config(args.config)

    if args.test:
        send_test(config)
        return

    content = None
    if args.file:
        content = Path(args.file).read_text(encoding="utf-8")
    elif args.text:
        content = args.text
    else:
        print("Error: Provide --file, --text, or --test", file=sys.stderr)
        sys.exit(1)

    count = send_digest(config, content, use_html=not args.plain)
    print(f"Sent {count} message(s) to Telegram", file=sys.stderr)


if __name__ == "__main__":
    main()
