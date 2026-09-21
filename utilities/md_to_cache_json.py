#!/usr/bin/env python3
"""Convert MSFS2024_informations.md -> MSFS2024_informations.json (+ guide)  [v2]

Simplified, uniform schema: every entry is
    id (deterministic UUIDv5 of the title) + title + claim (the whole body,
    words verbatim, block layout preserved, formatting stripped) + a uniform
    metadata envelope (status, sources, user, added, updated, resolved,
    supersedes, related, tags, _notes).

No per-body label classification: Claim:, Consequence:, L:, E:, A:, Procedure:,
Notes (...), etc. all become plain text inside `claim`. The .md file is the
canonical source and is never modified.

Deterministic and re-runnable. Which fields exist and why is documented in
MSFS2024_informations.guide.json (one field = one purpose; a new field is added
only when no existing one can hold the content).

Run:  python utilities/md_to_cache_json.py
"""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "MSFS2024_informations.md"
OUT = REPO / "MSFS2024_informations.json"
GUIDE = REPO / "MSFS2024_informations.guide.json"

# Fixed namespace so ids are deterministic across machines and re-runs.
ID_NAMESPACE = uuid.UUID("7c4f6e2a-9d61-4f31-b2c8-3e5a9d0f1c35")

# One-time seed (2026-09-21): poster handles for entries already ingested from
# Discord chat dumps. The updater agent extracts/parses handles from dump text
# on FUTURE updates automatically; this table seeds the current cache only.
USER_SEED = {
    "MSFS 2024 material texture naming — `OcclusionRoughnessMetallicTex` (ORM), not \"COMP\"": "614nlv, mamu82",
    "Projected Mesh objects — independent placement outside airports": "mamu82",
    "SU1-beta asset-display bug — project opens, assets invisible (single report)": "salvuz",
    "Jetway IK constraints — `<IKConstraint>` in model XML (2020-era; 2024 applicability unknown)": "mamu82",
}

STATUS_VALUES = [
    "fact (cited)",
    "fact (memory)",
    "empirical",
    "inferred",
    "unknown",
    "user-typed (authoritative)",
]

CAT_RE = re.compile(r"^##\s+(\d+)\.\s+(.*)$")
ENTRY_RE = re.compile(r"^###\s+(.*)$")
XREF_RE = re.compile(r"^####\s+Cross-references\s*$")
LIST_RE = re.compile(r"^\s*([-*+]|\d+\.)\s+")
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
META_RE = re.compile(
    r"^\*\*(Status|Source|Added/Resolved|Added|Related|Updated|Supersedes):\*\*\s*(.*)$"
)


# --------------------------------------------------------------------------- #
# small text helpers (words are always preserved verbatim)
# --------------------------------------------------------------------------- #
def fold(lines: list[str]) -> str:
    return " ".join(x.strip() for x in lines if x.strip())


def strip_links(text: str) -> str:
    return LINK_RE.sub(lambda m: m.group(1), text)


def clean_text(text: str) -> str:
    """Drop **bold**; drop *italic* only OUTSIDE backtick spans (so code
    wildcards like `A:AMBIENT WIND *` or `GEAR_*_STEER_ANGLE` survive)."""
    text = text.replace("**", "")
    parts = text.split("`")
    for i in range(0, len(parts), 2):  # even segments are outside code
        parts[i] = parts[i].replace("*", "")
    return "`".join(parts)


def gh_slug(title: str) -> str:
    """GitHub heading anchor algorithm — matches the anchors used in the .md."""
    s = title.strip().lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    return re.sub(r"\s", "-", s)


def entry_id(title: str) -> str:
    return str(uuid.uuid5(ID_NAMESPACE, title))


# --------------------------------------------------------------------------- #
# claim construction — body -> one string, blocks kept as lines
# --------------------------------------------------------------------------- #
def parse_list_block(lines: list[str], i: int) -> tuple[str, int]:
    n = len(lines)
    items = []
    while i < n:
        line = lines[i]
        if not line.strip():
            j = i + 1
            while j < n and not lines[j].strip():
                j += 1
            if j < n and (
                lines[j].startswith("  ") or LIST_RE.match(lines[j])
            ):
                i += 1
                continue
            break
        m = re.match(r"^\s*([-*+]|\d+\.)\s+(.*)$", line)
        if not m:
            break
        marker = m.group(1)
        i += 1
        # ordered segments so prose -> code -> trailing prose stays in order
        segments: list[tuple[str, list[str]]] = [("prose", [m.group(2)])]
        in_code = False
        while i < n and lines[i].strip():
            cont = lines[i]
            if not in_code and LIST_RE.match(cont):
                break
            if cont.strip().startswith("```"):
                in_code = not in_code
                segments.append(("code" if in_code else "prose", []))
                i += 1
                continue
            if in_code:
                segments[-1][1].append(cont.rstrip())
                i += 1
                continue
            if cont.startswith("  ") or cont.startswith("\t"):
                segments[-1][1].append(cont.strip())
                i += 1
                continue
            break
        rendered = []
        for kind, seg in segments:
            if not seg:
                continue
            if kind == "prose":
                rendered.append(clean_text(" ".join(seg)))
            else:
                rendered.append("\n".join("    " + c for c in seg))
        items.append(marker + " " + "\n\n".join(rendered))
    return "\n".join(items), i


def build_claim(lines: list[str]) -> str:
    i, n = 0, len(lines)
    blocks = []
    while i < n:
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        s = line.strip()
        if s.startswith("```"):  # fenced code -> own block, fences dropped
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i].rstrip())
                i += 1
            i += 1
            blocks.append(clean_text("\n".join(code)))
            continue
        if s.startswith(">"):  # blockquote -> own line(s)
            q = []
            while i < n and lines[i].lstrip().startswith(">"):
                q.append(re.sub(r"^\s*>\s?", "", lines[i]).strip())
                i += 1
            blocks.append(clean_text(fold(q)))
            continue
        if s.startswith("|"):  # table -> one line per row
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(" | ".join(clean_text(c) for c in cells))
                i += 1
            kept = [
                r
                for r in rows
                if not all(
                    re.fullmatch(r"-{2,}|:?-+:?", c.strip()) for c in r.split(" | ")
                )
            ]
            blocks.append("\n".join(kept))
            continue
        if LIST_RE.match(line):  # bullet / numbered list
            text, i = parse_list_block(lines, i)
            blocks.append(text)
            continue
        para = []
        while (
            i < n
            and lines[i].strip()
            and not LIST_RE.match(lines[i])
            and not lines[i].strip().startswith(("```", ">", "|"))
        ):
            para.append(lines[i])
            i += 1
        blocks.append(clean_text(fold(para)))
    return "\n\n".join(b for b in blocks if b).rstrip()


# --------------------------------------------------------------------------- #
# metadata
# --------------------------------------------------------------------------- #
def split_sources(value: str) -> list[str]:
    """Split verbatim Source text on top-level ';' only (a ';' inside
    parentheses does not split)."""
    parts, buf, depth = [], [], 0
    for ch in value:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            parts.append("".join(buf).strip())
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf).strip())
    return [p for p in parts if p.strip()]


def text_tokens(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_]+", text.lower()))


def derive_status_values(status: str | None) -> list[str]:
    if not status:
        return []
    found = []
    for tok in re.findall(r"`([^`]+)`", status):
        t = tok.strip()
        if t in STATUS_VALUES and t not in found:
            found.append(t)
    return found


def derive_confidence(status: str | None) -> str | None:
    if not status:
        return None
    low = status.lower()
    if "low confidence" in low or "single-user" in low:
        return "low"
    if "high, not absolute" in low:
        return "high"
    return None


def parse_metadata(meta_lines: list[str], collect: dict) -> dict:
    fields: dict[str, str] = {}
    cur = None
    for line in meta_lines:
        m = META_RE.match(line)
        if m:
            cur = m.group(1)
            fields[cur] = m.group(2).strip()
        elif cur is not None and line.strip():
            fields[cur] = (fields[cur] + " " + line.strip()).strip()

    added_raw = fields.get("Added") or fields.get("Added/Resolved")
    related = []
    raw_related = fields.get("Related", "")
    for lbl, href in LINK_RE.findall(raw_related):
        collect["href"].update(text_tokens(href))
        link = f"[{lbl}]({href})"
        after = raw_related[raw_related.find(link) + len(link):]
        after = re.sub(r"^\s*[—-]\s*", "", after).strip()
        related.append({"title": clean_text(lbl), "href": href, "note": clean_text(after)})

    return {
        "status": fields.get("Status"),
        "sources": [clean_text(s) for s in split_sources(fields["Source"])]
        if "Source" in fields
        else [],
        "added": added_raw.rstrip(".").strip() if added_raw else None,
        "resolved": fields["Added/Resolved"].rstrip(".").strip()
        if "Added/Resolved" in fields
        else None,
        "related": related,
    }


# --------------------------------------------------------------------------- #
# entries
# --------------------------------------------------------------------------- #
def parse_entry(title: str, raw: list[str], collect: dict) -> dict:
    while raw and (not raw[-1].strip() or raw[-1].strip() == "---"):
        raw.pop()
    meta_start = next((i for i, l in enumerate(raw) if META_RE.match(l)), None)
    body = raw[:meta_start] if meta_start is not None else raw
    meta_lines = raw[meta_start:] if meta_start is not None else []
    meta = parse_metadata(meta_lines, collect)
    status = meta["status"]

    # outlier (§16 parity note): `Status:` sentence embedded in the body
    if status is None and body:
        joined = " ".join(body)
        m = re.search(r"\bStatus:\s*(`.+?`[^.]*\.)", joined)
        if m:
            status = m.group(1).strip()
            joined = re.sub(r"\s{2,}", " ", (joined[: m.start()] + joined[m.end():]).strip())
            body = [joined]

    entry = {
        "id": entry_id(title),
        "title": clean_text(title),
        "kind": "entry",
        "claim": build_claim(body),
        "status": status,
        "statusValues": derive_status_values(status),
        "confidence": derive_confidence(status),
        "sources": meta["sources"],
        "user": None,
        "added": meta["added"],
        "updated": None,
        "resolved": meta["resolved"],
        "supersedes": [],
        "related": meta["related"],
        "tags": [],
        "_notes": None,
    }
    if entry["title"] in USER_SEED:
        entry["user"] = USER_SEED[entry["title"]]
    return entry


def parse_open_questions(lines: list[str], collect: dict) -> list[dict]:
    items, cur = [], None
    for l in lines:
        if l.strip() == "---":
            continue
        if re.match(r"^-", l.lstrip()):
            if cur:
                items.append(cur)
            cur = [l]
        elif cur is not None:
            cur.append(l)
    if cur:
        items.append(cur)

    out = []
    for it in items:
        text = re.sub(r"^\s*-\s*", "", fold(it))
        m = re.match(r"^\*\*(?P<b>[^*]+)\*\*\s*(?P<rest>.*)$", text)
        title, rest = text, ""
        if m:
            title = m.group("b").strip()
            rest = re.sub(r"^[:—-]\s*", "", m.group("rest").strip())
        resolved = None
        rm = re.search(r"RESOLVED\s+(\d{4}-\d{2}-\d{2})", text)
        if rm:
            resolved = rm.group(1)
        claim = build_claim(strip_links(rest).split("\n")) if rest else ""
        links = LINK_RE.findall(rest)
        for _, href in links:
            collect["href"].update(text_tokens(href))
        out.append(
            {
                "id": entry_id(title),
                "title": clean_text(title),
                "kind": "openQuestion",
                "claim": claim,
                "status": None,
                "statusValues": [],
                "confidence": None,
                "sources": [],
                "user": None,
                "added": None,
                "updated": None,
                "resolved": resolved,
                "supersedes": [],
                "related": [{"title": clean_text(l), "href": h, "note": ""} for l, h in links],
                "tags": [],
                "_notes": None,
            }
        )
    return out


def parse_xrefs(lines: list[str], collect: dict) -> list[dict]:
    items, cur = [], None
    for l in lines:
        if l.strip() == "---":
            continue
        if re.match(r"^-", l.lstrip()):
            if cur:
                items.append(cur)
            cur = [l]
        elif cur is not None:
            cur.append(l)
    if cur:
        items.append(cur)

    out = []
    for it in items:
        text = re.sub(r"^\s*-\s*", "", fold(it))
        for lbl, href in LINK_RE.findall(text):
            if href.startswith("#"):
                out.append({"title": clean_text(lbl), "href": href})
                collect["href"].update(text_tokens(href))
        # the .md may carry a short note after the link ("— the aircraft-side
        # half of the cross-object pattern"). Per spec, crossReferences store
        # title + entryId ONLY — the note is intentionally dropped, so its
        # words join the allow-drop set of the word-preservation gate.
        collect["xref_notes"].update(text_tokens(LINK_RE.sub(" ", text)))
    return out


# --------------------------------------------------------------------------- #
# usage + edition trail
# --------------------------------------------------------------------------- #
def parse_usage(lines: list[str]) -> dict:
    rules, legend = [], []
    cur = None
    i, n = 0, len(lines)
    while i < n:
        m = re.match(r"^-\s+(.*)$", lines[i])
        if m:
            cur = {"text": m.group(1).strip(), "nested": []}
            i += 1
            while (
                i < n
                and lines[i].strip()
                and not re.match(r"^-\s+", lines[i])
                and not re.match(r"^\s+-\s+", lines[i])
            ):
                cur["text"] += " " + lines[i].strip()
                i += 1
            while i < n and re.match(r"^\s+-\s+", lines[i]):
                item = re.sub(r"^\s+-\s+", "", lines[i]).strip()
                i += 1
                while (
                    i < n
                    and lines[i].strip()
                    and not re.match(r"^\s+-\s+", lines[i])
                    and not re.match(r"^-\s+", lines[i])
                ):
                    item += " " + lines[i].strip()
                    i += 1
                cur["nested"].append(item)
            rules.append(cur)
            continue
        i += 1
    for r in rules:
        for it in r["nested"]:
            it = clean_text(it)
            v, mean = (it.split(" — ", 1) + [""])[:2]
            legend.append({"value": v.strip().strip("`"), "meaning": mean.strip()})
    return {
        "title": "Using & contributing",
        "rules": [clean_text(r["text"]) for r in rules],
        "statusLegend": legend,
    }


def parse_trail(lines: list[str]) -> tuple[str, list[dict], str]:
    intro, footer = [], []
    raw_rows = []
    seen_rows = False
    for l in lines:
        if l.strip().startswith("|"):
            seen_rows = True
            raw_rows.append([c.strip() for c in l.strip().strip("|").split("|")])
        elif not seen_rows:
            if l.strip() and l.strip() != "---":
                intro.append(l.strip())
        else:
            if l.strip() and l.strip() != "---":
                footer.append(l.strip())
    sep = next(
        (
            k
            for k, cells in enumerate(raw_rows)
            if all(re.fullmatch(r"-{2,}|:?-+:?", c) for c in cells)
        ),
        None,
    )
    rows = [
        {"date": c[0], "summary": clean_text(c[1])}
        for c in (raw_rows[sep + 1 :] if sep is not None else raw_rows[1:])
        if len(c) >= 2 and c[0]
    ]
    footer_text = re.sub(r"^\*|\*$", "", " ".join(footer)).strip()
    return fold(intro), rows, footer_text


# --------------------------------------------------------------------------- #
# main conversion
# --------------------------------------------------------------------------- #
def convert(text: str) -> tuple[dict, set[str]]:
    lines = text.replace("\r\n", "\n").split("\n")

    # words that v2 intentionally drops (already re-stored elsewhere or not
    # part of the data model): anchor slugs (`#...` hrefs -> entryIds) and the
    # explanatory notes on cross-reference lines (title + entryId only).
    collect = {"href": set(), "xref_notes": set()}

    cat_idx = [i for i, l in enumerate(lines) if CAT_RE.match(l)]
    first = cat_idx[0] if cat_idx else len(lines)
    preamble = lines[:first]

    title = ""
    desc = []
    first_h2 = next((i for i, l in enumerate(preamble) if l.startswith("## ")), len(preamble))
    for l in preamble[:first_h2]:
        if l.startswith("# "):
            title = l[2:].strip()
        else:
            desc.append(l)
    description = clean_text(
        "\n\n".join(
            fold(p.split("\n")) for p in re.split(r"\n\s*\n", "\n".join(desc)) if p.strip()
        )
    )

    categories, usage, trail = [], None, None
    for k, i in enumerate(cat_idx):
        end = cat_idx[k + 1] if k + 1 < len(cat_idx) else len(lines)
        body = lines[i + 1 : end]
        m = CAT_RE.match(lines[i])
        number, name = int(m.group(1)), m.group(2).strip()

        if name == "Edition trail":
            intro, rows, footer = parse_trail(body)
            trail = {
                "number": 17,
                "title": "Edition trail",
                "intro": intro,
                "rows": rows,
            }
            continue

        xstart = next((j for j, l in enumerate(body) if XREF_RE.match(l)), None)
        core = body[:xstart] if xstart is not None else body
        xref_lines = body[xstart + 1 :] if xstart is not None else None

        reserved = None
        res_buf = []
        for l in core:
            if l.strip().startswith("*("):
                res_buf.append(l.strip())
            elif res_buf and l.strip() and not l.strip().startswith("#") and l.strip() != "---":
                res_buf.append(l.strip())
        if res_buf:
            reserved = clean_text(re.sub(r"^\*\(|\)\*$", "", " ".join(res_buf)).strip())

        if name.startswith("Open Questions"):
            entries = parse_open_questions(core, collect)
        else:
            ent_idx = [j for j, l in enumerate(core) if ENTRY_RE.match(l)]
            entries = []
            for e, j in enumerate(ent_idx):
                eend = ent_idx[e + 1] if e + 1 < len(ent_idx) else len(core)
                h = ENTRY_RE.match(core[j])
                entries.append(parse_entry(h.group(1).strip(), core[j + 1 : eend], collect))

        categories.append(
            {
                "number": number,
                "title": clean_text(name),
                "reserved": reserved,
                "entries": entries,
                "crossReferences": parse_xrefs(xref_lines, collect) if xref_lines else [],
            }
        )

    data = {
        "formatVersion": 2,
        "title": clean_text(title),
        "description": description,
        "created": "2026-09-20",
        "usage": usage if usage is not None else {"rules": [], "statusLegend": []},
        "categories": categories,
        "editionTrail": trail,
        "omittedMetaSections": ["Contents", "INDEX — categories → starting line"],
    }
    if trail is not None:
        data["footer"] = footer if "footer" in dir() else ""
    resolve_all(data)
    return data, collect["href"] | collect["xref_notes"]


def resolve_all(data: dict) -> None:
    """Replace #anchor links with UUIDs once every entry id exists."""
    entry_of = {gh_slug(e["title"]): e["id"] for c in data["categories"] for e in c["entries"]}

    def resolve(href: str) -> str | None:
        slug = href[1:] if href.startswith("#") else href
        return entry_of.get(slug)

    for cat in data["categories"]:
        for e in cat["entries"]:
            fixed = []
            for r in e["related"]:
                eid = resolve(r["href"])
                if eid is None:  # non-entry targets (e.g. a §N category) are dropped
                    continue
                fixed.append({"entryId": eid, "note": r["note"]})
            e["related"] = fixed
        fixed_x = []
        for x in cat["crossReferences"]:
            eid = resolve(x["href"])
            if eid is None:
                continue
            fixed_x.append({"title": x["title"], "entryId": eid})
        cat["crossReferences"] = fixed_x


# --------------------------------------------------------------------------- #
# guide (vital: teaches the agent how to maintain the JSON)
# --------------------------------------------------------------------------- #
def build_guide(data: dict) -> dict:
    fields = [
        {
            "name": "id",
            "type": "string (UUIDv5)",
            "required": True,
            "values": None,
            "purpose": "Stable, unique identifier for the entry.",
            "usage": "Never change it. related, crossReferences and open questions point at it. Deterministic UUIDv5 of the title, so it survives re-runs.",
        },
        {
            "name": "title",
            "type": "string",
            "required": True,
            "values": None,
            "purpose": "Verbatim heading of the entry.",
            "usage": "Copy the `###` heading word-for-word. Changing a title changes the id -> treat as a structural edition.",
        },
        {
            "name": "kind",
            "type": "enum",
            "required": True,
            "values": ["entry", "openQuestion"],
            "purpose": "Subtype of the entry.",
            "usage": "openQuestion is used only for category-15 unknowns that are still unresolved. Everything else is entry. Once answered, an open question stays put and gains status + sources + resolved (it does not change kind on its own).",
        },
        {
            "name": "claim",
            "type": "string",
            "required": True,
            "values": None,
            "purpose": "THE ENTRY BODY. The main part presented to the user on retrieval.",
            "usage": "Always present; words verbatim; never paraphrase. Layout: paragraphs on one line each, blank line between blocks, bullets on their own '- ' lines, code/table rows on their own lines, inline code kept in backticks. Stored without bold/italic markers.",
        },
        {
            "name": "status",
            "type": "string|null",
            "required": True,
            "values": None,
            "purpose": "Veracity of the entry.",
            "usage": "One or more ladder values, verbatim text in backticks. May be compound: `fact (cited)` + `inferred`, `empirical` + `unknown`, etc. The first value is the leading one.",
        },
        {
            "name": "statusValues",
            "type": "array<enum>",
            "required": True,
            "values": STATUS_VALUES,
            "purpose": "Normalized status list for filtering.",
            "usage": "Automatically extracted from status; keep in sync when status changes.",
        },
        {
            "name": "confidence",
            "type": "enum|null",
            "required": True,
            "values": ["low", "high"],
            "purpose": "Certainty as stated by the source.",
            "usage": "Set ONLY when the source states it explicitly: 'low confidence' or 'single-user' -> low; 'high, not absolute' -> high. Otherwise null. Never invent it.",
        },
        {
            "name": "sources",
            "type": "array<string>",
            "required": True,
            "values": None,
            "purpose": "Where the fact comes from.",
            "usage": "Verbatim Source text, one string per source (split on top-level ';' only). Keep URLs, doc names, SDK file:line, Discord channels and timestamps.",
        },
        {
            "name": "user",
            "type": "string|null",
            "required": True,
            "values": None,
            "purpose": "Author attribution for facts extracted from Discord chats / chat dumps.",
            "usage": "One or more poster handles, comma-separated (e.g. \"614nlv, mamu82\"), when the fact came from a chat dump that credits them; null for every other source type. Always present so every entry conforms. On future updates the agent extracts the handle(s) from the dump text itself.",
        },
        {
            "name": "added",
            "type": "date|null",
            "required": True,
            "values": None,
            "purpose": "Creation date of the entry.",
            "usage": "Always set on real entries (YYYY-MM-DD). Mandatory.",
        },
        {
            "name": "updated",
            "type": "object|null",
            "required": True,
            "values": None,
            "purpose": "Last in-place edit of an existing entry (same fact clarified/corrected).",
            "usage": "Shape: {\"date\": \"YYYY-MM-DD\", \"note\": \"one-sentence what changed\"}. Set only when an entry is edited after it was added; full history belongs in the edition trail. Only the latest update is kept here.",
        },
        {
            "name": "resolved",
            "type": "date|null",
            "required": True,
            "values": None,
            "purpose": "Marks an entry that was BORN from an open question or an `unknown` and has since been answered.",
            "usage": "Set ONLY when the reason we researched this was an open question or an unknown entry. Once resolved the entry carries a real status + sources (no longer open/unknown), plus this date. Provenance stays checkable: open questions live in category 15; unknowns have 'unknown' in statusValues.",
        },
        {
            "name": "supersedes",
            "type": "array<id>",
            "required": True,
            "values": None,
            "purpose": "Entry ids (UUIDs) this entry renders obsolete after new verification.",
            "usage": "The superseded entries are NOT deleted — kept on file for history; this field marks the link. Rarely used; only for verified-change replacements.",
        },
        {
            "name": "related",
            "type": "array<{entryId, note}>",
            "required": True,
            "values": None,
            "purpose": "Neighbour entries sharing the same mechanism / shape / fix-family.",
            "usage": "Each item: entryId (UUID) + note saying why they are related. Not for cross-category placement - that is crossReferences.",
        },
        {
            "name": "tags",
            "type": "array<string>",
            "required": True,
            "values": None,
            "purpose": "Global, cross-category keywords.",
            "usage": "Short lowercase keywords that help retrieval across categories (e.g. blender, gltf, rpn, simvar, ktx, workaround, devmode, parallax). Categories are the home; tags are the global index. Add only when they genuinely help retrieval.",
        },
        {
            "name": "_notes",
            "type": "string|null",
            "required": True,
            "values": None,
            "purpose": "Maintainer-only caveats.",
            "usage": "Free text NOT shown in normal retrieval: next verification step, flagged conflicts, doubts, open sub-questions. Keep null unless needed.",
        },
    ]

    template = {
        "_example": True,
        "id": "3f2b8b4a-0000-0000-0000-000000000000",
        "title": "Example entry — verbatim title",
        "kind": "entry",
        "claim": "First paragraph of the claim, folded to one line.\n\n- L: — a bullet inside the claim, own line.\n\nA code block, on its own lines:\n\n    (E:TIME OF DAY, Enum) 2 <=",
        "status": "`fact (cited)` + `inferred` (…)",
        "statusValues": ["fact (cited)", "inferred"],
        "confidence": "high",
        "sources": ["official docs — https://…", "local SDK `C:\\MSFS 2024 SDK\\…\\file.py:54`"],
        "user": "mamu82",
        "added": "2026-09-21",
        "updated": {"date": "2026-09-22", "note": "Clarified the Near/Far radius wording."},
        "resolved": "2026-09-22",
        "supersedes": [],
        "related": [{"entryId": "00000000-0000-0000-0000-000000000001", "note": "same export path"}],
        "tags": ["blender", "gltf"],
        "_notes": "Not yet checked against SU2.",
    }

    rules = [
        "One field = one purpose. Add a new field ONLY if its content cannot fit into an existing one.",
        "claim is the entry body - the main text shown to the user on retrieval. Verbatim, never paraphrased.",
        "crossReferences is used ONLY when one entry fits more than one category. It is placed in SECONDARY categories and stores ONLY title + entryId (UUID of the home-category entry). If a cross-reference exists, store nothing else there — the short note the .md may carry after the link (e.g. \"the aircraft-side half of the cross-object pattern\") is intentionally dropped from the JSON.",
        "An entry lives once, in its home category. Categories are the home; tags are the global cross-cutting index.",
        "One fact, one entry. Never merge distinct facts; never split one fact.",
        "Verify through the fallback chain before writing a factual status: local SDK -> official docs/DevSupport -> community. Never fabricate a source, channel, date, or doc.",
        "Never delete an entry. Correct in place: set updated {date, note} (or supersedes for verified replacements) and log it in the edition trail.",
        "status escalates with evidence: unknown -> inferred -> empirical -> fact (cited / memory). Never downgrade without a dated rationale.",
        "resolved applies ONLY to entries born from an open question or an unknown (now answered). Fresh research entries never use it.",
        "added is mandatory; ids are immutable; the .md file stays the canonical source behind this JSON.",
    ]

    return {
        "formatVersion": 2,
        "purpose": "Field catalog + maintenance manual for MSFS2024_informations.json. Teach the updater agent from this file: the schema, what every field is FOR, how to use it, and the cache rules.",
        "companion": "MSFS2024_informations.json",
        "source": "MSFS2024_informations.md",
        "statusLadder": ["unknown", "inferred", "empirical", "fact (memory)", "fact (cited)"],
        "statusLegend": data["usage"]["statusLegend"],
        "kinds": ["entry", "openQuestion"],
        "fields": fields,
        "rules": rules,
        "templateEntry": template,
    }


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #
def token_report(
    original: str, data: dict, drop: tuple[int, int], allow_drop: set[str]
) -> list[str]:
    """Every word of the .md (outside Contents/INDEX and the v2 intentional
    drops: anchor slugs and cross-reference notes) must survive in the JSON.

    IMPORTANT: tokens are read from the PARSED string values, never from a
    json.dumps() dump — the escaped `\\n`/`\\` sequences glue letters together
    (`\\nnPractical` tokenizes as `npractical`) and produce false positives.
    """
    src = original.replace("\r\n", "\n").split("\n")
    kept = [l for i, l in enumerate(src) if not (drop[0] <= i + 1 <= drop[1])]
    orig = text_tokens("\n".join(kept))

    js = set()
    buf: list[str] = []

    def walk(o):
        if isinstance(o, str):
            buf.append(o)
        elif isinstance(o, dict):
            for k, v in o.items():
                buf.append(str(k))
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif o is not None:
            buf.append(str(o))

    walk(data)
    js = text_tokens("\n".join(buf))
    return sorted((orig - allow_drop) - js)


def summarize(data: dict) -> dict:
    entries = sum(len(c["entries"]) for c in data["categories"])
    xrefs = sum(len(c["crossReferences"]) for c in data["categories"])
    reserved = sum(1 for c in data["categories"] if c["reserved"])
    openq = sum(
        1 for c in data["categories"] for e in c["entries"] if e["kind"] == "openQuestion"
    )
    return {
        "categories": len(data["categories"]),
        "entries": entries,
        "openQuestions": openq,
        "crossReferences": xrefs,
        "reserved": reserved,
        "editionTrailRows": len(data["editionTrail"]["rows"]),
    }


def main() -> int:
    original = SRC.read_text(encoding="utf-8")
    lines = original.replace("\r\n", "\n").split("\n")
    ui = next(i for i, l in enumerate(lines) if l.strip().startswith("## Using & contributing"))
    ue = next(i for i, l in enumerate(lines) if l.strip().startswith("## Contents"))
    usage = parse_usage(lines[ui + 1 : ue])

    data, allow_drop = convert(original)
    data["usage"] = usage

    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    GUIDE.write_text(
        json.dumps(build_guide(data), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    all_ids = {e["id"] for c in data["categories"] for e in c["entries"]}
    dead_x = [
        x
        for c in data["categories"]
        for x in c["crossReferences"]
        if x["entryId"] not in all_ids
    ]
    dead_r = [
        (e["title"], r)
        for c in data["categories"]
        for e in c["entries"]
        for r in e["related"]
        if r["entryId"] not in all_ids
    ]

    missing = token_report(original, data, (36, 79), allow_drop)
    print("wrote: MSFS2024_informations.json + MSFS2024_informations.guide.json [v2]")
    print("counts:", json.dumps(summarize(data)))
    print("dangling cross-ref ids:", dead_x)
    print("dangling related ids:", dead_r)
    print("tokens missing from JSON (should be []):", missing[:60])
    return 0 if not missing and not dead_x and not dead_r else 1


if __name__ == "__main__":
    sys.exit(main())