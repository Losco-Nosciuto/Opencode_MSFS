# utilities

Small helper tools for the MSFS knowledge pipeline.

## `declog_chat.py`

De-clogs exported Discord chat dumps before they are fed to the
`msfs-cache-updater` agent, so the scan sees only the useful text.

**Keeps:** message timestamps + author (headers, including `(pinned)` markers)
and every message's genuine text and real reference URLs (YouTube, flightsim.to,
forum/docs links, ...).

**Removes:** `Pinned a message.` notices, `{Attachments}` blocks,
`{Embed}` blocks (collapsed to a single `[embed] …` title line),
image/CDN/thumbnail URLs (`cdn.discordapp.com`, `media.discordapp.net`,
`images-ext-*.discordapp.net`, `i.ytimg.com`, `cdn.flightsim.to/images`,
`play-lh.googleusercontent.com`), empty messages, and the
`Exported N message(s)` footer.

**2024-only policy (default):** messages dated strictly **before `--cutoff`
(DD/MM/YYYY, default `01/08/2024`** — ~3 months before the MSFS2024 beta)
are dropped from the output, so the cache updater ingests only 2024-relevant
content. The picked count is reported both in the console and in the
`# Declogged from:` header as
`+ N pre-cutoff removed (< 01/08/2024, 2024-only policy)` — the updater uses
that marker to attribute the file as an intentionally partial, 2024-only
digest. Pass `--cutoff off` (or `none`) to disable truncation. The raw input
dump is **never modified** — pre-cutoff (2020-era) recovery is done with the
sibling manual tool [`declogger_FS2020_manualonly.py`](#declogger_fs2020_manualonlypy)
on the untouched original.

### Usage

```text
python declog_chat.py export.txt                 → export_declog.txt (2024-only, < 01/08/2024)
python declog_chat.py export.txt -o clean.txt    → custom output
python declog_chat.py export.txt --drop-links    → also strip body URLs
python declog_chat.py export.txt --cutoff 01/08/2024   (default)
python declog_chat.py export.txt --cutoff off          → full history, no truncation
```

Pure stdlib, Python 3.8+. Try `py -3` if `python` is not on PATH.

### Pipeline

```text
raw export.txt ──► declog_chat.py ──► .txt declogged
                                    ──► msfs-cache-updater (verify → stage → merge)
```

The output's first line is a `# Declogged from: <file> — N messages …` summary
the cache updater uses for attribution. The updater now **auto-declogs**: on
receiving a dump it reads the first line, and if `# Declogged from:` is absent
it runs this script into `.cache_staging\extracts\` before the normal scan
workflow.
De-clogged content is still **source B** for the updater: every claim still
gets verified through the fallback chain.

## `declogger_FS2020_manualonly.py`

1:1 copy of the original (pre-cutoff) `declog_chat.py` — **manual 2020/2024
recovery tool**. No `--cutoff` flag, no policy: it emits the **full history**
de-clogged file from a raw dump.

Use it when pre-cutoff (2020-era) content must be ingested: run it manually on
the untouched raw dump and hand the output to the cache updater, which treats
it as a normal full-history source-B file:

```text
python declogger_FS2020_manualonly.py export.txt -o full_history.txt → complete 2020+2024 text
```

**Golden rule — raw dumps are never touched:** both tools only *write* their
output file. The downloaded dumps in
`C:\Lavoro\DiscordChatExporter\Unfiltered_MSFS_Chats\` are the only permanent
copy of the pre-2024 history and must never be deleted or overwritten. (Known
quirk carried over from the original: on files whose *name* contains emoji,
the final console summary line crashes — the output file is already written
and correct; ignore the traceback or rename the dump.)

## `validate_cache.py`

Integrity gate for the knowledge cache (`MSFS2024_informations.json`) — pure
stdlib. Checks: valid JSON + expected top-level keys; `categories` numbered
sequentially 1..N with a meta `editionTrail` at N+1 (locate it dynamically —
never by hardcoded number); the 16 mandatory entry fields with UUIDv5 ids,
unique across the cache; `kind` rules (`openQuestion` only in the Open
Questions category, located by title); `statusValues`
against the known ladder; the `reserved`-note / empty-entries coupling; and
that every `crossReferences` / `related` / `supersedes` entryId resolves to an
existing entry.

```text
python validate_cache.py                     → validate MSFS2024_informations.json
python validate_cache.py --file cache.json   → another file
python validate_cache.py --ids               → print every entry id, one per line
```

The cache updater uses `--ids` before/after an edition as its **inventory gate**
(pre-existing ids must survive, new ids appear exactly once), then runs the full
check before closing the edition. Exit code 0 = OK, 1 = validation failed.

## `get_entry_id.py`

Prints the canonical **UUIDv5 entry id** for a knowledge-cache entry title —
the same namespace `md_to_cache_json.py` uses, so ids are deterministic across
machines and re-runs. The cache updater runs this when staging a new entry and
never invents or hand-edits ids (ids are immutable).

```text
python get_entry_id.py "<verbatim entry title>"
echo "some title" | python get_entry_id.py
```

Two legacy ids (the Scenery-SimObjects variable-scope entry and the Pattern A
entry) were generated from earlier title wording and do not reproduce — they
stay exactly as they are.

## `split_extracts.py`

Canonical **Fase 0 (shaping)** tool: splits a declogged digest into numbered
extract files (`cord_extract_01.md`, …) of ≤ ~300 lines each, **cut only at
message boundaries** (never mid-message), with the channel context header
repeated at the top of every slice so each extract is self-contained. Writes
only into the `-o` directory, **never overwrites existing extracts** without
`--force`, and prints a summary (digest marker, message count, per-file declog
coverage + date span) that feeds the updater's checkpoint report.

```text
python split_extracts.py declogged.txt -o .cache_staging\extracts              → cord_extract_01.md, …
python split_extracts.py declogged.txt -o .cache_staging\extracts --lines 250  → re-slice size
python split_extracts.py declogged.txt -o .cache_staging\extracts --prefix scan_extract
python split_extracts.py declogged.txt -o .cache_staging\extracts --force      → replace existing
python split_extracts.py declogged.txt -o .cache_staging\extracts --dry-run    → verify: same summary, writes nothing
```

The cache updater runs this in Fase 0 **instead of building extracts by hand**:
extract files are shaping, not judgment, so no LLM context is spent slicing
and nothing is pre-filtered (the dev-relevance filter is Fase 1 triage's job).