# Changelog

Notable changes to the MSFS 2024 OpenCode Workspace. Newest first.

## 2026-11-07

### Agents and installer

- **Location-agnostic agent sources.** `custom agent/*.md` now carry two placeholders, `{{REPO}}` and `{{SDK}}`, instead of machine-specific paths. `utilities/install_agents.py` resolves them at install time, so the public repo ships no personal filesystem layout and there is no manual find/replace step (the old INSTALL.md "ONE path replace" is gone). The installer reports how many placeholders it resolved and warns if any survive.
- **Shell allowlist discipline (both cache agents).** `Permission denied: shell` means *that exact command string* is not allowlisted — not that shell is unavailable and not that the workspace is read-only. Canonical commands must be issued verbatim (no `cd`, `;`, `&&`, `|`, `python -c`, `Get-Content`); a denial is re-tried once and then reported as a permission bug. Scripts or alternative code paths written to route around a denial are explicitly forbidden — this is the failure mode that produced a 300-line "applier" script instead of a cache write.
- **IDs gate fixed.** The documented gate ran `validate_cache.py --ids | Set-Content …`; the shell scanner splits compound commands and `Set-Content` was never allowlisted, so the gate failed by construction. Replaced by `validate_cache.py --ids-write <path>` and `--ids-diff <before> <after>`, both covered by the existing `python "…/validate_cache.py"*` rule. `--ids-diff` prints `NEW`/`MISSING`/`DUPLICATE` and fails on loss or duplication.
- **Status snippet removed.** The `Get-Content`/`ConvertFrom-Json`/`Get-ChildItem` status one-liner was also unallowlisted; ready/flushed counts now come from `glob` plus one inventory `read`.
- **Stale backup guard.** `MSFS-Cache-Writer-Subagent` refreshes `.bak` when it is missing **or older than the cache**, instead of only when absent. A stale safety copy would silently discard the previous edition on restore.
- **`validate_cache.py` default file** resolves to the repo's `MSFS2024_informations.json` rather than the current working directory, so the canonical command works when the session is opened in another project.
- **Long values are readable again.** `read`/`grep` truncate every line after 2,000 characters and one-line JSON strings arrive cut — the writer was about to reconstruct claims "from the verified prefix". New `utilities/show_ready.py` prints any JSON file with long values split into numbered pieces (`JOIN n pieces`, already JSON-escaped) that concatenate byte-for-byte; both cache agents get the rule "never reconstruct a truncated string", and the research sub-agent now caps `claim` at ~1,200 characters (a longer claim is two facts).
- **Stale handoffs can no longer reintroduce retired commands.** The writer prompt states that its own canonical commands win over any command text quoted in the parent's handoff, and the parent is told to pass paths only — never `--ids`, `Set-Content`, pipes or scripts. Resumed sessions keep the prompt they were created with: a session started before an agent update must be restarted (new session), not resumed.

### Knowledge cache

- **Pending 2026-11-05 edition committed** (animation, weather and SimConnect entries) as a clean base before the next flush.
- **Ad-hoc batch of 2 applied** (LOD bounding-sphere + LOD screen-size math, category 15): 65 entries, `validate_cache.py` OK, ids diff clean. Applied across two writer runs because the step budget ran out mid-batch — see the agents entry below.

### Agents and installer

- **Step budgets raised:** `MSFS-Cache-Writer-Subagent` 40 → 80, `msfs-cache-updater` 60 → 80. A 2-item batch spent ~30 steps on orientation (guide, both ready-files, repeated paged reads of `editionTrail`) and died at the limit twice.
- **Orientation budget and anchor discipline** in both agents: read the guide once, each ready-file once, one cache slice; never read another agent file; never page the whole `editionTrail`; copy `oldString` from a read result stripping exactly the `NNNN: ` prefix; one failed edit → re-read, two failures on the same anchor → skip and report.
- **Close-out ownership:** only the writer renames `research_ready_*` (the parent has no `Rename-Item` rule, verified with a probe); the parent deletes `flushed_*` only, after `OK` and a clean ids diff, and **never** `research_ready_*`. A failed writer is not re-spawned blindly — the cache is grepped for the batch ids first.
- **No phantom edition bump:** `editionTrail.number` is the meta section's fixed index (N+1); routine insertions only prepend a `rows` entry. The handoff now says "edition date", not "edition bump".
- **Restore is a targeted edit**, never a whole-file `Copy-Item` from `.bak` (which would discard the rest of the batch). A denied command is permanent: no synonym retries (`python -c`, `powershell -Command`, `Get-Content`, pipes, `;` chains). `git` stays out of both allowlists.

## 2026-11-05

### plan-msfs

- **Project-agnostic planner.** It plans for the project the session is opened in: it reads the project's own documentation first, then cross-checks the code, which wins when the two disagree. No assumed filenames or standard layout, and no assumptions carried over from another project or from the knowledge cache.
- **Documentation handling matches the project.** Current docs get updated, stale docs are flagged and the user is asked whether to refresh them, and a project with no docs gets a minimal proposal (for example a short audit to track progress beyond git commits).
- **No `PLAN.md` unless asked.** Planning artifacts at the project root remain off-limits unless the user explicitly requests one.
- **Knowledge cache is facts, not context.** Cache entries never imply which project the session is about; the cache resolves from any project and says when it is unavailable.
- **Scope stated up front:** MSFS / MSFS 2024 development and Blender add-on development, including add-ons built around `io_scene_gltf2_msfs_2024`.

### MSFS Cache Updater

- **Step budget raised from 40 to 60.** Research, writes, validation and reporting all count against the same budget; the previous limit ran out during a research-heavy edition.
- **Source-C research is delegated.** One `MSFS-Research-SubAgent` per entry, in parallel (up to 8 live), instead of the parent researching inline. The parent reads the guide, runs the version gate, de-dups and coordinates.
- **Ad-hoc writer flush.** Source-C editions with 2 or more entries are applied by one `MSFS-Cache-Writer-Subagent` in a single batch; the ≥4-ready threshold remains specific to the dump-ingestion pipeline.
- **Live progress.** Short 1–2 line updates at phase boundaries and on notable findings (source contradictions, unsupported features, blocked paths). Updates are folded into the same turn as the next tool call; the full report comes at the end.
- **Budget guard and resume block.** At least 12 steps are reserved for finalization. If the remaining work does not fit, the run stops after staging and reports `Done / Applied / Staged / Remaining / Next / Gates` instead of half-applying an edition.
- **ID discipline.** Titles are frozen before ID generation; ASCII hyphens only (no em dashes, arrows, smart quotes or shell metacharacters); one `get_entry_id.py` call per final title.
- **UTF-8 inventory gate.** `ids_before.json` is written with `Set-Content -Encoding utf8`; PowerShell 5's `>` writes UTF-16 and breaks later reads.
- **Deep source fan-out (exception).** `MSFS-Source-Scout` may be used in parallel across sources only for a single high-stakes or conflicting claim — not for every entry.

### Sub-agents

- **`MSFS-Research-SubAgent`**: ready-files can carry an optional `crossReferences` array so the writer applies secondary-category links; independent lookups should be batched in the same turn; parallel sibling researchers stay self-contained.
- **`MSFS-Cache-Writer-Subagent`**: accepts ad-hoc batches of any size ≥1 when the parent requests them, applies `crossReferences` from the ready-file, keeps one edition row per ready-file, and writes the ID gate in UTF-8.

### Knowledge cache

- **Temporary product name neutralized.** The Bake-to-Vertex-Color entry now refers to "the author's upcoming add-on suite", with the suite name explicitly marked as not final. No verified facts changed.
- **Source-C edition completed** (character animation research, local SDK 1.7.3):
  - `38d8c6f1` — Scenery character SimObject: non-playable human placed as a Scenery SimObj under `SimObjects\Landmarks`, `model.cfg category=StaticObject`, hand-written model XML, `DistanceToNotAnimate` caveats, no instancing on animated objects.
  - `a788efd9` — three-state Arrival / Main / Exit AnimGraph driven by `E:LOCAL TIME` and `A:AMBIENT PRECIP STATE`; loop flag per `BlendTreeState`; Condition/ExitTime transition modes.
  - `acce152b` — open question: whether Condition/ExitTime transitions run on `category=StaticObject` scenery SimObjects, and whether a one-shot state restarts on re-entry.
  - Cross-reference added from Category 1 (Scenery Objects); edition trail updated; flagged conflict on the `E:TIME OF DAY` enum (2024 SimVars page vs older shipped template comments).
  - Validation: 58 entries, 21 cross-references, 0 unresolved references, `OK`. ID gate: 55 pre-existing IDs intact, 3 new IDs present exactly once.

### Docs

- **README:** the Fase 3 bullet now notes the ad-hoc source-C delegation and the ≥2 writer flush.
- **CHANGELOG:** added.
