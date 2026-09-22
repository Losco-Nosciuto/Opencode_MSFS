#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate the MSFS2024 knowledge cache (`MSFS2024_informations.json`).

Pure stdlib. This is the JSON-native replacement for the old markdown
"inventory gate" + "anchor link-check" of the cache updater workflow.

Checks (each failure is reported as `ERROR:` and exits 1):
  1. valid JSON and the expected top-level keys
  2. `categories` numbered sequentially 1..N; `editionTrail.number` == N + 1
  3. every entry carries the 16 documented fields and a well-formed UUIDv5 id
  4. ids are unique across the whole cache
  5. `kind` in {entry, openQuestion}; `openQuestion` only in the Open Questions
     category — located by title, never by hardcoded number
  6. every `statusValues` item is a known status-ladder value
  7. a category with a non-null `reserved` note has an empty `entries` array,
     and a category with entries keeps `reserved` null
  8. every `crossReferences` / `related` / `supersedes` entryId resolves to an
     existing entry; cross-references never point at an entry of their own
     category

Usage:
    python utilities/validate_cache.py [--file MSFS2024_informations.json]
    python utilities/validate_cache.py --ids   # print every entry id, one per line
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

DEFAULT_FILE = "MSFS2024_informations.json"

STATUS_VALUES = {
    "fact (cited)",
    "fact (memory)",
    "empirical",
    "inferred",
    "unknown",
    "user-typed (authoritative)",
}

KINDS = {"entry", "openQuestion"}

REQUIRED_FIELDS = (
    "id", "title", "kind", "claim", "status", "statusValues", "confidence",
    "sources", "user", "added", "updated", "resolved", "supersedes", "related",
    "tags", "_notes",
)


def load(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class Checker:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def check_id(self, raw: str, where: str) -> None:
        """A cache entry id must be a well-formed UUIDv5."""
        try:
            u = uuid.UUID(raw)
        except (ValueError, AttributeError, TypeError):
            self.error(f"{where}: id {raw!r} is not a valid UUID")
            return
        if u.version != 5:
            self.error(f"{where}: id {raw!r} is not a UUIDv5 (version {u.version})")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Validate the MSFS2024 knowledge cache JSON.")
    p.add_argument("--file", default=DEFAULT_FILE, help="cache file (default: %(default)s)")
    p.add_argument("--ids", action="store_true", help="print every entry id, one per line, and exit")
    args = p.parse_args(argv)

    path = Path(args.file)
    if not path.is_file():
        print(f"error: cache file not found: {path}", file=sys.stderr)
        return 2

    try:
        data = load(path)
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} is not valid JSON: {e}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("ERROR: top level is not a JSON object", file=sys.stderr)
        return 1

    categories = data.get("categories")
    if not isinstance(categories, list):
        print("ERROR: missing `categories` array", file=sys.stderr)
        return 1

    # --ids mode: dump ids in document order, done.
    if args.ids:
        for cat in categories:
            for entry in cat.get("entries", []):
                if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                    print(entry["id"])
        return 0

    c = Checker()

    # 1. top-level keys
    for key in ("formatVersion", "title", "description", "created", "usage",
                "categories", "editionTrail", "footer"):
        if key not in data:
            c.error(f"top level: missing key `{key}`")

    # 2. category numbering + editionTrail
    for i, cat in enumerate(categories):
        if not isinstance(cat, dict):
            c.error(f"categories[{i}]: not an object")
            continue
        number = cat.get("number")
        if number != i + 1:
            c.error(
                f"categories[{i}]: number {number!r} — expected {i + 1} "
                "(sequential 1..N)"
            )
        if not cat.get("title"):
            c.error(f"categories[{i}]: missing title")

    trail = data.get("editionTrail")
    if isinstance(trail, dict):
        if trail.get("number") != len(categories) + 1:
            c.error(
                f"editionTrail: number {trail.get('number')!r} — expected "
                f"{len(categories) + 1} (meta section after the categories)"
            )
        if not isinstance(trail.get("rows"), list):
            c.error("editionTrail: `rows` must be an array")

    # 2b. locate the Open Questions category by title — never hardcode its
    # number (renumberings must not break this rule)
    oq_numbers = {
        cat["number"] for cat in categories
        if isinstance(cat, dict)
        and cat.get("title") == "Open Questions (Unknowns)"
        and cat.get("number") is not None
    }
    if len(oq_numbers) != 1:
        c.error(
            "Open Questions category: expected exactly one category titled "
            f"'Open Questions (Unknowns)', found numbers {sorted(oq_numbers) or 'none'}"
        )

    all_ids: set[str] = set()
    seen: set[str] = set()

    for cat in categories:
        if not isinstance(cat, dict):
            continue
        number = cat.get("number")
        reserved = cat.get("reserved")
        entries = cat.get("entries")
        if not isinstance(entries, list):
            c.error(f"category {number}: `entries` must be an array")
            continue

        # 7. reserved <-> empty coupling
        if reserved is not None and entries:
            c.error(
                f"category {number}: has a `reserved` note but also "
                f"{len(entries)} entries — reserved must be null once filled"
            )
        if reserved is None and not entries:
            pass  # a plain empty category is allowed to exist

        # 3. per-entry fields + 4. id uniqueness
        for j, entry in enumerate(entries):
            if not isinstance(entry, dict):
                c.error(f"category {number} entries[{j}]: not an object")
                continue
            where = f"category {number} entries[{j}] ({entry.get('title', '?')!r})"
            for field in REQUIRED_FIELDS:
                if field not in entry:
                    c.error(f"{where}: missing required field `{field}`")
            eid = entry.get("id")
            if isinstance(eid, str):
                c.check_id(eid, where)
                if eid in seen:
                    c.error(f"{where}: duplicate id {eid}")
                seen.add(eid)
                all_ids.add(eid)
            else:
                c.error(f"{where}: missing `id`")

            # 5. kind rules
            kind = entry.get("kind")
            if kind not in KINDS:
                c.error(f"{where}: kind {kind!r} — expected entry|openQuestion")
            if kind == "openQuestion" and number not in oq_numbers:
                c.error(
                    f"{where}: openQuestion outside the Open Questions category "
                    f"({number})"
                )

            # 6. statusValues
            sv = entry.get("statusValues")
            if isinstance(sv, list):
                for v in sv:
                    if v not in STATUS_VALUES:
                        c.error(f"{where}: unknown statusValue {v!r}")
            elif sv is not None:
                c.error(f"{where}: statusValues must be an array")

    counts = {"crossReferences": 0, "related": 0, "supersedes": 0, "missing": 0}

    # 8. reference resolution
    for cat in categories:
        if not isinstance(cat, dict):
            continue
        number = cat.get("number")
        local_ids = {e.get("id") for e in cat.get("entries", []) if isinstance(e, dict)}
        xrefs = cat.get("crossReferences")
        if xrefs:
            if not isinstance(xrefs, list):
                c.error(f"category {number}: crossReferences must be an array")
                continue
            for idx, x in enumerate(xrefs):
                counts["crossReferences"] += 1
                if not isinstance(x, dict) or not isinstance(x.get("entryId"), str):
                    c.error(
                        f"category {number} crossReferences[{idx}]: must be "
                        "{title, entryId}"
                    )
                    continue
                eid = x["entryId"]
                if eid not in all_ids:
                    counts["missing"] += 1
                    c.error(
                        f"category {number} crossReferences[{idx}]: entryId "
                        f"{eid!r} does not resolve to any entry"
                    )
                elif eid in local_ids:
                    c.error(
                        f"category {number} crossReferences[{idx}]: points at an "
                        "entry of its own category — cross-references are for "
                        "secondary categories only"
                    )
                if not isinstance(x.get("title"), str) or not x["title"].strip():
                    c.error(
                        f"category {number} crossReferences[{idx}]: missing title"
                    )

    for cat in categories:
        if not isinstance(cat, dict):
            continue
        number = cat.get("number")
        for entry in cat.get("entries", []):
            if not isinstance(entry, dict):
                continue
            where = f"category {number} ({entry.get('title', '?')!r})"
            for rid in entry.get("related", []):
                counts["related"] += 1
                if not isinstance(rid, dict) or not isinstance(rid.get("entryId"), str):
                    c.error(f"{where} related: must be {{entryId, note}}")
                    continue
                if rid["entryId"] not in all_ids:
                    counts["missing"] += 1
                    c.error(f"{where} related: entryId {rid['entryId']!r} does not resolve")
            for sid in entry.get("supersedes", []):
                counts["supersedes"] += 1
                if not isinstance(sid, str):
                    c.error(f"{where} supersedes: entries must be id strings")
                    continue
                if sid not in all_ids:
                    counts["missing"] += 1
                    c.error(f"{where} supersedes: id {sid!r} does not resolve")

    print(f"validated: {path}")
    print(f"  categories : {len(categories)} (edition trail = meta #{len(categories) + 1})")
    print(f"  entries    : {len(seen)}")
    print(f"  refs       : {counts['crossReferences']} cross-references, "
          f"{counts['related']} related, {counts['supersedes']} supersedes, "
          f"{counts['missing']} unresolved")
    if c.errors:
        for e in c.errors:
            print(f"  ERROR: {e}")
        print(f"FAILED — {len(c.errors)} error(s)")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())