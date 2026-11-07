# MSFS2024 OpenCode Workspace — Installation

This repo ships six OpenCode agents (`custom agent/`: the cache updater, the
planner, the three dump-pipeline sub-agents — triage, research, cache writer —
plus the planning source-scout) and a distilled MSFS 2024 development knowledge
cache (`MSFS2024_informations.json`). Setup takes ~2 minutes and requires
**no manual path editing**: the agent sources carry two placeholders
(`{{REPO}}`, `{{SDK}}`) and the installer resolves them for your machine.

## Prerequisites

- [OpenCode](https://opencode.ai) V2 (global agents live under
  `~/.config/opencode/agents/`; on Windows that is
  `%USERPROFILE%\.config\opencode\agents\`)
- Microsoft Flight Simulator **2024 SDK** installed at `C:\MSFS 2024 SDK`
  (the agents read it as a pre-approved reference — if yours lives elsewhere,
  pass `--sdk <path>` to the installer). The **SDK root must also hold its
  `Documentation` and `Samples` folders** — all three live under the same root,
  and the agents read all of them (local docs are preferred over online when
  the versions match; the installer's SDK prompt reminds you of this).

## Step 1 — Clone

```sh
git clone <this-repo-url>
cd <your-clone-path>
```

## Step 2 — Install the agents

Run the installer — it copies the agents into your global OpenCode config,
resolves `{{REPO}}` → this checkout and `{{SDK}}` → your SDK root, and backs up
anything it overwrites:

```sh
python utilities/install_agents.py --dry-run   # preview first
python utilities/install_agents.py             # or with --yes to skip prompts
```

Pure stdlib, safe to re-run (idempotent). `--help` documents all options
(`--repo`, `--agents-dir`, `--sdk`, `--yes`, `--dry-run`).

**Manual alternative** (no Python): copy the six files from `custom agent/` into
your global agents directory, then replace every `{{REPO}}` with your checkout
path and every `{{SDK}}` with your SDK root. Nothing else in the files needs
editing.

> Note: `custom agent/` is a **1:1 live backup** of the global agents — the
> same sources you install from. Keep the install step in your workflow after
> editing a global agent.

## Paths in the agent files (how they work)

Two kinds of path appear, and neither needs hand-editing:

1. **`{{REPO}}` / `{{SDK}}` placeholders** — resolved by the installer (see
   step 2). They cover the canonical shell commands, the permission rules for
   the cache workspace, the fallback-chain paths and the SDK examples.
2. **Relative `edit` rules** — `*.cache_staging/extracts/*`,
   `*.cache_staging/inventory/*`, `*.cache_staging/ingestion/*`,
   `*MSFS2024_informations.json`, `*MSFS2024_informations.json.bak` — are
   deliberately **relative**: OpenCode matches `edit`/`write`/`patch`
   resources as worktree-relative paths, so a leading `*` matches the `..\`
   prefix produced when the session runs outside the cache workspace, and the
   bare path when it runs inside it. The write zone is therefore honored from
   any working directory — **never convert these to absolute paths.**

No other configuration is required: the project-level `opencode.jsonc` in this
repo wires the `msfs2024-knowledge` reference (→ `MSFS2024_informations.json`)
**automatically** (relative path, resolved from the repo root) when OpenCode
opens this directory.

## Optional cleanup

If this repo is the only project that uses the knowledge-cache reference, you
can remove the `msfs2024-knowledge` entry from your *global*
`~/.config/opencode/opencode.jsonc` — the project file now covers it.
Keep it if you open OpenCode from other directories.