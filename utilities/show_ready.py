#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print a research-ready file for the cache writer, with long strings chunked.

Why this exists: `read` and `grep` shorten every line after 2,000 characters,
and a ready-file / cache entry stores each long text as one single-line JSON
string. A truncated claim cannot be copied verbatim — reconstructing it from
the visible prefix would invent text in a "verified" cache.

This tool prints the same content with every long string split into fixed
pieces, each on its own line, with an exact reassembly instruction:

    entry.claim  [JOIN 17 pieces: concatenate the text after '|' exactly]
      0000|<first 200 chars>
      0001|<next 200 chars>
      ...

Reading those pieces and joining them in order reproduces the original string
byte for byte — no spaces added, no word-boundary guessing.

Read-only: this utility never writes anything.

Usage:
    python utilities/show_ready.py <ready-file.json>
    python utilities/show_ready.py <ready-file.json> --chunk 100
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PIECE = 200  # characters per chunk; well under the 2,000-char line limit
FLAT_LIMIT = 160  # escaped strings shorter than this are printed on one line


def as_json_body(value) -> str:
    """The exact ASCII-safe text that must sit in the JSON file for this value.

    For strings this is the body between the quotes; for numbers/null/objects it
    is the full JSON literal. `ensure_ascii=True` keeps the output pure ASCII, so
    it survives any Windows console code page on its way to the writer, and the
    escapes are still valid JSON.
    """
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)[1:-1]
    return json.dumps(value, ensure_ascii=True)


def emit_pieces(label: str, body: str, chunk: int) -> None:
    pieces = [body[i:i + chunk] for i in range(0, len(body), chunk)]
    print(
        f"{label}  [JOIN {len(pieces)} pieces: concatenate the text after '|' exactly; "
        "already JSON-escaped]"
    )
    for i, piece in enumerate(pieces):
        print(f"  {i:04d}|{piece}")


def emit_value(label: str, value, chunk: int) -> None:
    body = as_json_body(value)
    if len(body) <= FLAT_LIMIT:
        print(f"{label}: {body}")
        return
    emit_pieces(label, body, chunk)


def walk(prefix: str, value, chunk: int) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            walk(f"{prefix}.{key}" if prefix else str(key), child, chunk)
        return
    if isinstance(value, list) and any(isinstance(x, (dict, list)) for x in value):
        for i, child in enumerate(value):
            walk(f"{prefix}[{i}]", child, chunk)
        return
    emit_value(prefix, value, chunk)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Print a research-ready file with long strings chunked for verbatim retrieval."
    )
    p.add_argument("path", help="research_ready_<inv>.json (or any JSON cache file)")
    p.add_argument("--chunk", type=int, default=PIECE,
                   help=f"characters per piece (default: {PIECE})")
    args = p.parse_args(argv)

    path = Path(args.path)
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    if args.chunk < 40:
        print("error: --chunk must be >= 40", file=sys.stderr)
        return 2

    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        print(f"error: {path} is not valid JSON: {e}", file=sys.stderr)
        return 1

    print(f"ready-file: {path}")
    walk("", data, args.chunk)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
