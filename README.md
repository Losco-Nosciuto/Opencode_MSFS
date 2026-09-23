<a name="top"></a>

# MSFS 2024 OpenCode Workspace

OpenCode agents plus a distilled, verified **MSFS 2024 development knowledge cache** — built to serve both you and the aviation-dev community. The workspace ships six [OpenCode](https://opencode.ai) agents (updater, planner, the dump-pipeline sub-agents, and a parallel source-scout) and a growing reference cache, with install automation so a fresh machine is minutes away from running.

- The knowledge cache: [`MSFS2024_informations.json`](MSFS2024_informations.json) (schema guide: [`utilities/MSFS2024_informations.guide.json`](utilities/MSFS2024_informations.guide.json); the old `.md` is history-only)
- The six agents under [`custom agent/`](custom%20agent/): the cache maintainer [`msfs-cache-updater.md`](custom%20agent/msfs-cache-updater.md), the planner [`plan-msfs.md`](custom%20agent/plan-msfs.md), and four sub-agents — dump triage [`triage-dump.md`](custom%20agent/triage-dump.md), research [`MSFS-Research-SubAgent.md`](custom%20agent/MSFS-Research-SubAgent.md), cache writer [`MSFS-Cache-Writer-Subagent.md`](custom%20agent/MSFS-Cache-Writer-Subagent.md), and the parallel source-scout [`MSFS-Source-Scout.md`](custom%20agent/MSFS-Source-Scout.md)
- The installer: [`utilities/install_agents.py`](utilities/install_agents.py)
- The DeClogger for Discord Chats (import and filter whole discord channels, **2024-only by default** — pre-`01/08/2024` removed): [`utilities/declog_chat.py`](utilities/declog_chat.py); manual 2020-recovery full-history variant: [`utilities/declogger_FS2020_manualonly.py`](utilities/declogger_FS2020_manualonly.py)
- The cache integrity gate + id helper: [`utilities/validate_cache.py`](utilities/validate_cache.py), [`utilities/get_entry_id.py`](utilities/get_entry_id.py)
---

## Table of Contents

1. [Installation](#installation)
2. [What's the Cache Updater Agent in Short](#whats-the-cache-updater-agent-in-short)
3. [What's the Planner Agent in Short](#whats-the-planner-agent-in-short)

---

## Installation

**Prerequisites:** [OpenCode]([https://opencode.ai/v2/docs/](https://opencode.ai/it/download)) V2, and the [MSFS 2024 SDK](https://docs.flightsimulator.com/msfs2024) at `C:\MSFS 2024 SDK` — the root must also hold its `Documentation` and `Samples` folders (same root: agents read SDK sources + local docs + real samples, preferring local docs over online when the versions match).

**Quick path (recommended):** run the [installer](utilities/install_agents.py) — it copies the agents into your global OpenCode config, re-points all hardcoded paths to this checkout (and your SDK), and backs up anything it overwrites:

```sh
python utilities/install_agents.py --dry-run   # preview, writes nothing
python utilities/install_agents.py             # or --yes to skip prompts
```

**Manual path:** copy [`custom agent/*.md`](custom%20agent/) into `~/.config/opencode/agents/`, then replace the single path prefix `C:\Lavoro\Programming\Opencode_MSFS` with your checkout path. The full step-by-step guide is in [`INSTALL.md`](INSTALL.md).

**Knowledge reference:** this repo's [`opencode.jsonc`](opencode.jsonc) wires the [`msfs2024-knowledge`](MSFS2024_informations.json) reference automatically via a relative path — no further setup needed after cloning.

[▲ Back to top](#top)

---

## What's the Cache Updater Agent in Short

**The [MSFS Cache Updater](custom%20agent/msfs-cache-updater.md)** maintains the knowledge cache — distilled, verified MSFS 2024 development facts organized into canonical categories (the file's live `categories` array defines count/order/titles — currently 18; additions and reorders are maintainer-confirmed structural editions). Think of it as a community-grade knowledge base with a strict quality gate.

What it does:

- **Three input contracts** — user-typed facts (taken as authoritative, always enriched with research), external files (Discord dumps / `.txt`, every claim verified), and on-demand research requests.
- **Verification fallback chain** — cache first, then the local [MSFS 2024 SDK](https://docs.flightsimulator.com/msfs2024) (sources **+ local `Documentation`** preferred over online when they match — version-gated — **+ real `Samples`**, incl. Wwise), then official docs ([docs.flightsimulator.com/msfs2024](https://docs.flightsimulator.com/msfs2024)), then community sources; everything labelled `fact (cited)` / `fact (memory)` / `empirical` / `inferred` / `unknown`.
- **Anti-bloat, anti-loss, anti-search-loop rules** — canonical categories, one fact per entry, mandatory metadata, de-dup before insert, entryId-based cross-references, and a structural-edition protocol that never silently renumbers.
- **Concurrent ingestion pipeline (Fase 3)** — decision-paced, sub-agent-worked: a live inventory (`<stem>_inventory.json` in `.cache_staging\inventory\`) drives up to **8 parallel `MSFS-Research-SubAgent`** verifications into `research_ready_<inv>.json` files, and a single **`MSFS-Cache-Writer-Subagent`** flushes batches of **≥ 4 ready items** to the cache (renaming consumed files to `flushed_<inv>.json` as the audit trail). One decision per run; research and writes never wait on the user.
- **Write-scoped** — edits only the cache workspace and the `.cache_staging\` staging area (phase folders: `extracts\`, `inventory\`, `ingestion\`); the raw-dump sanitizer lives in [`utilities/declog_chat.py`](utilities/declog_chat.py).

[▲ Back to top](#top)

---

## What's the Planner Agent in Short

**The [plan-msfs agent](custom%20agent/plan-msfs.md)** is a read-only planning partner for MSFS 2024 + Blender add-on development. It was originally built for the LoscoTools project, but it proved reliable in production and has been expanded to ship to whoever needs it — for planning Blender add-ons and MSFS / MSFS 2024 development-related tasks: risk-tiered research and build-ready plans, never implementation.

What it does:

- **Plans, never implements** — read-only except `~/.opencode/plan`; produces a structured plan (goal, constraints, research summary, architecture, phased steps) that a build agent can execute step-by-step without re-researching.
- **Same verification discipline, cache-first by default** — the knowledge cache is distilled research: a cache hit with a research-derived status (`fact (cited)` / `empirical` / `inferred` / `user-typed (authoritative)`) answers the question without sub-agents or fallback. Deeper verification (local SDK → official docs → community, ~5-consultation budget, snippet-only) runs only for cache-absent or `unknown`-status items — or on your explicit request.
- **Status-ladder honesty** — every claim labelled `fact (cited)` / `fact (memory)` / `inferred` / `unknown`; uncertainties and SDK gotchas called out explicitly.
- **Durable on request** — writes the plan to `~/.opencode/plan/` when you ask, and summarizes before handing off to build mode.

[▲ Back to top](#top)

---

*Small verified cache beats a big noisy one — [back to top](#top).*
