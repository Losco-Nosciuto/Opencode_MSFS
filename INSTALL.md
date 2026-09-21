# MSFS2024 OpenCode Workspace — Installation

This repo ships two OpenCode agents (`custom agent/`) plus a distilled MSFS 2024
development knowledge cache (`MSFS2024_informations.md`). Setup takes ~2
minutes and only requires changing **one path string**.

## Prerequisites

- [OpenCode](https://opencode.ai) V2 (global agents live under
  `~/.config/opencode/agents/`; on Windows that is
  `%USERPROFILE%\.config\opencode\agents\`)
- Microsoft Flight Simulator **2024 SDK** installed at `C:\MSFS 2024 SDK`
  (the agents read it as a pre-approved reference — without it, change that
  path in the agent files, see step 3)

## Step 1 — Clone

```sh
git clone <this-repo-url>
cd <your-clone-path>
```

## Step 2 — Install the agents

Copy the agent files from the repo into your global agents directory:

```sh
cp "custom agent/msfs-cache-updater.md" ~/.config/opencode/agents/
cp "custom agent/plan-msfs.md"          ~/.config/opencode/agents/
```

> Note: `custom agent/` is a **1:1 live backup** of the global agents — the
> same files you install from. Keep the copy step in your workflow after
> editing a global agent.

**Automatic alternative (recommended):** run the included installer instead of
steps 2–3 — it copies the agents, re-points the hardcoded paths to this
checkout, optionally re-points the SDK path, and backs up anything it
overwrites:

```sh
python utilities/install_agents.py --dry-run   # preview first
python utilities/install_agents.py             # or with --yes to skip prompts
```

Pure stdlib, safe to re-run (idempotent). `--help` documents all options.

## Step 3 — The ONE path replace

Absolute paths are hardcoded in the agents. Replace the single prefix string in
**both installed agent files** (frontmatter permission rules *and* the body
examples):

```
Find:    C:\Lavoro\Programming\Opencode_MSFS
Replace: <your-absolute-repo-path>
```

Keep the trailing `\*` wildcards in the permission rules intact
(e.g. `'C:\...\Opencode_MSFS\*'`). The SDK path `C:\MSFS 2024 SDK` also appears
in the files — leave it if you have the SDK there, otherwise replace that too.

> Note: the cache-updater's **write** rules (`edit` on `.cache_staging/*`,
> `MSFS2024_informations.md`, `MSFS2024_informations.md.bak`) are deliberately
> **relative** — OpenCode matches `edit` resources relative to the repo root, so
> these need no editing and must not be converted to absolute paths.

No other configuration is required: the project-level `opencode.jsonc` in this
repo wires the `msfs2024-knowledge` reference **automatically** (relative path,
resolved from the repo root) when OpenCode opens this directory. Nothing else
in this repo needs editing.

## Optional cleanup

If this repo is the only project that uses the knowledge-cache reference, you
can remove the `msfs2024-knowledge` entry from your *global*
`~/.config/opencode/opencode.jsonc` — the project file now covers it.
Keep it if you open OpenCode from other directories.