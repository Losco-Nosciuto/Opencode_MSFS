#!/usr/bin/env python3
"""declog_chat.py — de-clog exported Discord chat dumps for MSFS knowledge ingestion.

Reads an exported Discord channel dump (.txt/.md) and writes a de-clogged copy
that keeps every message's timestamp, author and genuine text (plus "(pinned)"
markers) while stripping the noise that makes raw exports hard to digest:

  * standalone "Pinned a message." / "Pinned multiple messages." notices
  * {Attachments} blocks            -> dropped entirely (CDN URL noise)
  * {Embed} blocks                  -> collapsed to one "[embed] title" line
  * CDN / thumbnail URLs            -> cdn.discordapp.com, media.discordapp.net,
                                        images-ext-*.discordapp.net, i.ytimg.com,
                                        cdn.flightsim.to/images, play-lh.googleusercontent.com
  * empty messages and the footer  -> "<...> Exported N message(s) <...>"

Message-body URLs that are real references (YouTube, flightsim.to, forum/docs
links, ...) are KEPT — they are sources for the knowledge cache. Pass
--drop-links to strip every body URL too.

Pure stdlib (Python 3.8+), no dependencies. UTF-8 (BOM-tolerant) in/out.

Usage:
    python declog_chat.py export.txt
    python declog_chat.py export.txt -o cleaned.txt
    python declog_chat.py export.txt --drop-links
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Message header: [DD/MM/YYYY HH:MM] <user + optional "(flag)" markers>
HEADER_RE = re.compile(
    r"^\[(?P<ts>\d{1,2}/\d{1,2}/\d{4}),? (?P<time>\d{1,2}:\d{2})\] ?(?P<rest>.*)$"
)

PINNED_NOTICE_RE = re.compile(r"^Pinned (a|multiple) messages?\.?$", re.I)

# Hosts that only carry image/thumbnail noise (never a primary link).
CDN_RE = re.compile(
    r"https?://("
    r"cdn\.discordapp\.com|media\.discordapp\.net|"
    r"images-ext-(\d+)\.discordapp\.net|"
    r"(?:[a-z0-9-]+\.)*i\.ytimg\.com|"
    r"cdn\.flightsim\.to/images/|play-lh\.googleusercontent\.com"
    r")",
    re.I,
)

URL_RE = re.compile(r"https?://\S+")

EMBED_MAX_LINES = 2      # keep at most 2 meaningful lines per embed
EMBED_LINE_CAP = 200     # truncate each kept embed line


def is_media_url_line(line: str) -> bool:
    """True when a line is (almost) only one CDN/thumbnail URL -> pure noise."""
    s = line.strip().strip(".,;:!?…()")
    m = URL_RE.match(s)
    if not m:
        return False
    return bool(CDN_RE.match(m.group(0))) and URL_RE.sub("", s) == ""


def scrub_body_line(line: str, drop_links: bool = False) -> str:
    """Remove CDN/media URLs from a text line; keep informative URLs unless
    --drop-links is set."""

    def repl(match: re.Match) -> str:
        url = match.group(0)
        if drop_links or CDN_RE.search(url):
            return ""
        return url

    return URL_RE.sub(repl, line).strip()


def collapse_embed(embed_lines: list[str]) -> list[str]:
    """Turn the raw {Embed} block into a single '[embed] <title>' summary line.

    Skips URL/thumbnail lines, keeps at most EMBED_MAX_LINES meaningful lines
    (the two first — typically channel/author and title), truncated to
    EMBED_LINE_CAP chars. Returns [] when the embed carries no text.
    """
    kept: list[str] = []
    for raw in embed_lines:
        s = raw.strip()
        if not s or is_media_url_line(s) or URL_RE.fullmatch(s):
            continue  # url / thumbnail noise
        s = scrub_body_line(s)
        if not s:
            continue
        kept.append(s[:EMBED_LINE_CAP])
        if len(kept) >= EMBED_MAX_LINES:
            break
    if not kept:
        return []
    label = " — ".join(kept)
    return [f"[embed] {label}"]


def _is_chrome(s: str) -> bool:
    """Export footer / chrome lines (e.g. the '==== Exported N message(s) ====' block)."""
    return s.startswith("=") or bool(re.fullmatch(r"Exported \d+ message\(s\)", s, re.I))


def declog_message(raw_body: list[str], drop_links: bool) -> tuple[list[str], dict]:
    """Split a message body into text / embeds / attachments and clean it.

    Returns (out_lines, stats). out_lines == [] means the message is pure noise
    (dropped by the caller).
    """
    text: list[str] = []
    embed_lines: list[str] = []
    in_embed = False
    attachments = 0

    for raw in raw_body:
        s = raw.strip()
        if s == "{Embed}":
            in_embed = True
            continue
        if s == "{Attachments}":
            in_embed = False
            attachments += 1
            continue
        if not s:
            if in_embed:
                continue  # blank inside an embed block: ignore
            text.append("")
            continue
        if in_embed:
            embed_lines.append(s)
            continue
        text.append(s)

    out: list[str] = []
    for raw in text:
        s = scrub_body_line(raw, drop_links)
        if not s or PINNED_NOTICE_RE.fullmatch(s) or _is_chrome(s):
            continue
        out.append(s)

    out.extend(collapse_embed(embed_lines))

    if not out:
        return [], {"attachments": attachments, "embeds": bool(embed_lines)}
    return out, {"attachments": attachments, "embeds": bool(embed_lines)}


def parse_chat(text: str, drop_links: bool) -> tuple[list[str], list[tuple[str, list[str]]], dict]:
    """Split the dump into (context, messages, stats). messages = [(header, cleaned_body), ...]."""
    lines = text.splitlines()
    stats = {"messages": 0, "kept": 0, "dropped": 0, "pins": 0,
             "embeds": 0, "attachments": 0, "context_lines": 0}

    context: list[str] = []
    messages: list[tuple[str, list[str]]] = []
    cur_header: str | None = None
    cur_body: list[str] = []

    def flush() -> None:
        nonlocal cur_header, cur_body
        if cur_header is None:
            return
        stats["messages"] += 1
        body, msg_stats = declog_message(cur_body, drop_links)
        stats["embeds"] += msg_stats["embeds"]
        stats["attachments"] += msg_stats["attachments"]
        if body:
            messages.append((cur_header, body))
            stats["kept"] += 1
            if cur_header.endswith(" (pinned)"):
                stats["pins"] += 1
        else:
            stats["dropped"] += 1
        cur_header = None
        cur_body = []

    for raw in lines:
        m = HEADER_RE.match(raw)
        if m:
            flush()
            cur_header = raw.strip()
            continue
        if cur_header is None:
            if raw.strip():
                context.append(raw.strip())  # pre-header chrome / channel context
            continue
        cur_body.append(raw)
    flush()

    stats["context_lines"] = len(context)
    return context, messages, stats


def render(context: list[str], messages: list[tuple[str, list[str]]],
           stats: dict, src_name: str) -> str:
    out: list[str] = []
    if context:
        out.append("## Channel context")
        out.extend(context)
        out.append("")
    out.append(
        f"# Declogged from: {src_name} — {stats['messages']} messages → "
        f"{stats['kept']} kept, {stats['dropped']} dropped · {stats['pins']} pinned · "
        f"{stats['embeds']} embeds collapsed · {stats['attachments']} attachment blocks removed"
    )
    out.append("")
    for header, body in messages:
        out.append(header)
        out.extend(body)
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="declog_chat.py",
        description="De-clog an exported Discord chat dump for easier ingestion.",
    )
    ap.add_argument("input", help="exported chat file (.txt/.md)")
    ap.add_argument("-o", "--output", help="output path (default: <input>_declog.txt)")
    ap.add_argument("--drop-links", action="store_true",
                    help="also strip informative URLs from message bodies (default: keep them)")
    args = ap.parse_args(argv)

    src = Path(args.input)
    if not src.is_file():
        print(f"error: not a file: {src}", file=sys.stderr)
        return 2
    try:
        text = src.read_text(encoding="utf-8-sig", errors="replace")
    except OSError as exc:
        print(f"error: cannot read {src}: {exc}", file=sys.stderr)
        return 2

    context, messages, stats = parse_chat(text, args.drop_links)
    out_text = render(context, messages, stats, src.name)

    dst = Path(args.output) if args.output else src.with_name(src.stem + "_declog.txt")
    try:
        dst.write_text(out_text, encoding="utf-8", newline="\n")
    except OSError as exc:
        print(f"error: cannot write {dst}: {exc}", file=sys.stderr)
        return 2

    print(f"de-clogged {src} -> {dst}")
    print(f"  {stats['messages']} messages read: {stats['kept']} kept, "
          f"{stats['dropped']} dropped ({stats['pins']} pinned kept, "
          f"{stats['embeds']} embeds collapsed, {stats['attachments']} attachment blocks removed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())