#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""split_extracts.py — shape a declogged digest into extract files (Fase 0).

Canonical shaping tool for the MSFS Cache Updater. Pure stdlib, deterministic,
offline, write-scoped to the output directory. This is the ONLY sanctioned way
to build extract files — hand-written read->write splits are forbidden.

Usage:
    python split_extracts.py <input> -o <outdir>
                            [--lines N] [--prefix PREFIX] [--force]
                            [--dry-run]

Behavior
--------
- <input> is opened read-only (UTF-8, a leading BOM is tolerated).
- A message starts at a header line like "[01/08/2024 03:03] username" and
  spans until the line before the next header.
- Extracts are cut ONLY at message boundaries: a message is never split
  across two files. A single message larger than --lines is kept whole in its
  own extract (integrity wins over the cap) with a warning.
- The digest context header (everything before the first message header) is
  repeated at the top of every extract, so each slice is self-contained.
- Each extract holds at most --lines lines (default 300), counting every line
  including blank separators — i.e. what the read tool will show.
- Existing files are NEVER overwritten unless --force is given. Nothing is
  written outside <outdir> (created if missing).
- Prints a summary: digest marker, message count, extract count, and per-file
  coverage (declog line range, message count, date span) — the numbers the
  CP1 report needs.

Exit codes: 0 ok · 1 usage/input error · 2 overwrite refused / no messages.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADER_RE = re.compile(r"^\[(\d{2}/\d{2}/\d{4} \d{2}:\d{2})\] ")


def die(message: str, code: int = 1) -> int:
    print(f"split_extracts.py: {message}", file=sys.stderr)
    return code


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Split a declogged digest into ≤N-line extract files at message boundaries."
    )
    parser.add_argument("input", help="declogged digest file (read-only)")
    parser.add_argument("-o", "--outdir", required=True, help="output directory for the extracts")
    parser.add_argument("--lines", type=int, default=300, help="max lines per extract (default 300)")
    parser.add_argument("--prefix", default="cord_extract", help="extract file prefix (default cord_extract)")
    parser.add_argument("--force", action="store_true", help="overwrite existing extract files")
    parser.add_argument("--dry-run", action="store_true", help="print the plan only; write nothing")
    args = parser.parse_args()

    if args.lines < 1:
        return die("--lines must be >= 1", 1)

    src = Path(args.input)
    if not src.is_file():
        return die(f"input file not found: {src}", 1)

    try:
        text = src.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        text = src.read_text(encoding="utf-8", errors="replace")
    # splitlines() drops line-ending characters; blank lines are preserved as "".
    lines = text.splitlines()
    if not lines:
        return die(f"input is empty: {src}", 2)

    # ---- isolate the context header -------------------------------------
    first_header = next((i for i, ln in enumerate(lines) if HEADER_RE.match(ln)), None)
    if first_header is None:
        return die(f"no message headers found (pattern {HEADER_RE.pattern!r})", 2)
    context: list[str] = lines[:first_header]

    # ---- split the body into message blocks (with 1-based input ranges) --
    blocks: list[list[str]] = []
    ranges: list[tuple[int, int]] = []  # (start_line, end_line) in the input, 1-based
    cur: list[str] = []
    start = first_header + 1  # 1-based line of the (current) first message header
    for idx, ln in enumerate(lines[first_header:], start=first_header + 1):
        if HEADER_RE.match(ln) and cur:
            blocks.append(cur)
            ranges.append((start, idx - 1))
            cur = [ln]
            start = idx
        else:
            cur.append(ln)
    if cur:
        blocks.append(cur)
        ranges.append((start, len(lines)))
    n_blocks = len(blocks)

    # ---- digest marker ----------------------------------------------------
    marker_line = next((ln for ln in lines if ln.startswith("# Declogged from:")), "")
    if "pre-cutoff removed" in marker_line:
        marker = "2024-only digest"
    elif marker_line:
        marker = "full-history digest"
    else:
        marker = "n/a"

    # ---- pack blocks into extracts -----------------------------------------
    max_lines = args.lines
    preamble = len(context)
    packs: list[list[int]] = []  # each pack = list of block indices
    cur_pack: list[int] = []
    cur_size = preamble
    warnings = 0
    for i, blk in enumerate(blocks):
        blk_size = len(blk)
        if cur_pack and cur_size + blk_size > max_lines:
            packs.append(cur_pack)
            cur_pack = []
            cur_size = preamble
        if blk_size > max_lines:
            if cur_pack:
                packs.append(cur_pack)
                cur_pack = []
                cur_size = preamble
            packs.append([i])
            warnings += 1
            print(
                f"  ! {args.prefix}: a single message is {blk_size} lines "
                f"(> {max_lines}); kept whole in its own extract"
            )
        else:
            cur_pack.append(i)
            cur_size += blk_size
    if cur_pack:
        packs.append(cur_pack)

    width = max(2, len(str(len(packs))))
    name_of = lambda idx: f"{args.prefix}_{idx:0{width}d}.md"
    outdir = Path(args.outdir)

    # ---- per-file planned info (shared by dry-run and real run) ------------
    def file_info(i: int, blk_idx: list[int]) -> tuple[str, str, int, int, int, int, str, str]:
        chunk: list[str] = list(context)
        for bi in blk_idx:
            chunk.extend(blocks[bi])
        content = "\n".join(chunk).rstrip() + "\n"
        return (
            name_of(i),
            content,
            content.rstrip("\n").count("\n") + 1,       # n_lines
            ranges[blk_idx[0]][0],                        # bl_lo
            ranges[blk_idx[-1]][1],                       # bl_hi
            len(blk_idx),                                 # msgs
            HEADER_RE.match(blocks[blk_idx[0]][0]).group(1),  # type: ignore[union-attr]
            HEADER_RE.match(blocks[blk_idx[-1]][0]).group(1),  # type: ignore[union-attr]
        )

    infos = [file_info(i, blk_idx) for i, blk_idx in enumerate(packs, start=1)]
    header = (
        f"input        : {src}\n"
        f"digest marker: {marker}\n"
        f"messages     : {n_blocks}\n"
        f"extracts     : {len(packs)} -> {outdir} (max {max_lines} lines each)"
    )

    def print_files() -> int:
        written = 0
        for name, _c, n_lines, bl_lo, bl_hi, msgs, first, last in infos:
            print(
                f"  {name}  {n_lines:4d} lines  declog {bl_lo}-{bl_hi} "
                f"({bl_hi - bl_lo + 1})  msgs {msgs:4d}  [{first}] -> [{last}]"
            )
            written += n_lines
        return written

    if args.dry_run:
        print(header)
        total = print_files()
        print(
            f"total planned: {total} lines in {len(packs)} files"
            f" (context {preamble} lines x {len(packs)} repeated) — dry-run, nothing written"
        )
        return 0

    targets = [(info, outdir / info[0]) for info in infos]
    existing = [str(p) for _info, p in targets if p.exists()]
    if existing and not args.force:
        print("overwrite refused — these extract files already exist (use --force to replace):")
        for e in existing:
            print(f"  {e}")
        return 2

    outdir.mkdir(parents=True, exist_ok=True)
    print(header)
    total = print_files()
    for info, dest in targets:
        with open(dest, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(info[1])
    print(
        f"total written: {total} lines in {len(packs)} files"
        f" (context {preamble} lines x {len(packs)} repeated)"
    )
    if warnings:
        print(f"warnings: {warnings} over-cap message(s) kept whole")
    return 0


if __name__ == "__main__":
    sys.exit(main())