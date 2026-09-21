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

### Usage

```text
python declog_chat.py export.txt                 → export_declog.txt
python declog_chat.py export.txt -o clean.txt    → custom output
python declog_chat.py export.txt --drop-links    → also strip body URLs
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
it runs this script into `.cache_staging\` before the normal scan workflow.
De-clogged content is still **source B** for the updater: every claim still
gets verified through the fallback chain.

## `validate_cache.py`

Integrity gate for the knowledge cache (`MSFS2024_informations.json`) — pure
stdlib. Checks: valid JSON + expected top-level keys; `categories` numbered
sequentially 1..N with a meta `editionTrail` at N+1 (17); the 16 mandatory
entry fields with UUIDv5 ids, unique across the cache; `kind` rules
(`openQuestion` only in the Open Questions category, 15); `statusValues`
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