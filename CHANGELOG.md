# Changelog

Notable changes to the MSFS 2024 OpenCode Workspace. Newest first.

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
