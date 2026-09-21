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