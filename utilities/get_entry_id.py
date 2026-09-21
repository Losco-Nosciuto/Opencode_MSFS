#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compute the canonical UUIDv5 id for a knowledge-cache entry title.

`MSFS2024_informations.json` entries carry a stable, unique `id`. Ids are a
deterministic **UUIDv5 of the verbatim entry title** over the canonical
namespace pinned below — the SAME namespace used by `md_to_cache_json.py`, so
an id computed here is byte-identical to a re-conversion of the source .md.

Two pre-existing ids were generated from earlier title wording and therefore
do not reproduce (they are immutable and stay exactly as they are):

  - "Scenery SimObjects read only global-scope variables — never the
    user aircraft's A: state"
  - "Pattern A — Scenario proximity trigger (reacts to the user by design)"

Usage:
    python utilities/get_entry_id.py "<verbatim entry title>"
    echo "some title" | python utilities/get_entry_id.py

Pure stdlib — no dependencies.
"""

import sys
import uuid

# Canonical namespace (matches md_to_cache_json.py).
ID_NAMESPACE = uuid.UUID("7c4f6e2a-9d61-4f31-b2c8-3e5a9d0f1c35")


def entry_id(title: str) -> str:
    """UUIDv5 over the canonical namespace for the verbatim title."""
    return str(uuid.uuid5(ID_NAMESPACE, title))


def main(argv: list[str]) -> int:
    if not argv:
        title = sys.stdin.read().strip()
    elif len(argv) == 1:
        title = argv[0]
    else:
        print(
            f'usage: python {__file__} "<verbatim entry title>" '
            f"or pipe one title via stdin",
            file=sys.stderr,
        )
        return 2
    if not title:
        print("error: empty title", file=sys.stderr)
        return 2
    print(entry_id(title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))