# MSFS2024 Knowledge Cache

A distilled cache of **verified** MSFS2024 development knowledge, gathered from
the official SDK & docs, DevSupport, the local SDK, and community sources.
Consult this **before** searching the web again. Every entry carries a
**Status** and a **Source** so you always know what to trust.

This file is exposed to sessions as the `msfs2024-knowledge` reference
(project `.opencode/opencode.json` + global `~/.config/opencode/opencode.jsonc`)
and backs up to an external drive.

## Using & contributing

- For any MSFS2024-specific question, `/read` this file first. If it answers
  with a solid `Status`, stop — no web research needed.
- Adding knowledge: verify first via the fallback chain (local SDK →
  official docs/DevSupport → community), then append a dated entry. Never bulk
  paste docs — keep entries atomic, snippet-sized.
- User-typed claims (maintainer statements) are taken as true exactly as
  stated — status `user-typed (authoritative)`; additions from external files
  (dumps, pastes) go through the full verification chain first.
- Every entry MUST carry `Status`, `Source`, `Added`. Status values:
  - `fact (cited)` — official docs / SDK / shipped sim assets
  - `fact (memory)` — confident from recent use, not re-verified
  - `empirical` — community-tested in the sim, confirmed by multiple users
  - `inferred` — derived from cited facts, not directly confirmed
  - `unknown` — flagged, needs verification before building on it
  - `user-typed (authoritative)` — stated by the user, taken as true
- **Categories** are the numbered `## N.` sections; **entries** are the `###`
  blocks. An entry that fits more than one category lives **once** in its home
  category and is listed elsewhere as a title + anchor link under a
  `#### Cross-references` block. Categories with no primary entries say
  `*(no entries yet — reserved for …)*` so agents know the gap is deliberate,
  not missing.

## Contents

1. [Scenery Objects](#1-scenery-objects)
2. [Scenery SimObjects](#2-scenery-simobjects)
3. [Aircraft Simobjects](#3-aircraft-simobjects)
4. [Blender Pipeline for Modeling and Animations](#4-blender-pipeline-for-modeling-and-animations)
5. [Blender Third Parties (Addons / Plugins)](#5-blender-third-parties-addons--plugins)
6. [Adobe 3D Painter Pipeline for Texturing](#6-adobe-3d-painter-pipeline-for-texturing)
7. [Terrain Edition (Satellite and CGL)](#7-terrain-edition-satellite-and-cgl)
8. [Projected Meshes](#8-projected-meshes)
9. [RPN Schematics and Quirks](#9-rpn-schematics-and-quirks)
10. [DevMode - Texturing (Polygons and Aprons)](#10-devmode---texturing-polygons-and-aprons)
11. [DevMode - Workarounds](#11-devmode---workarounds)
12. [DevMode - Runways](#12-devmode---runways)
13. [DevMode - Various](#13-devmode---various)
14. [DevMode - Light Presets](#14-devmode---light-presets)
15. [Open Questions (Unknowns)](#15-open-questions-unknowns)
16. [MSFS Programmability Gotchas](#16-msfs-programmability-gotchas)
17. [Edition trail](#17-edition-trail)

## INDEX — categories → starting line

Kept current on every edition (maintained by the cache updater). Categories = all `##` headings.

- **Using & contributing** — 12
- **Contents** — 36
- **1. Scenery Objects** — 82
- **2. Scenery SimObjects** — 93
- **3. Aircraft Simobjects** — 253
- **4. Blender Pipeline for Modeling and Animations** — 272
- **5. Blender Third Parties (Addons / Plugins)** — 534
- **6. Adobe 3D Painter Pipeline for Texturing** — 548
- **7. Terrain Edition (Satellite and CGL)** — 554
- **8. Projected Meshes** — 560
- **9. RPN Schematics and Quirks** — 599
- **10. DevMode - Texturing (Polygons and Aprons)** — 632
- **11. DevMode - Workarounds** — 638
- **12. DevMode - Runways** — 665
- **13. DevMode - Various** — 671
- **14. DevMode - Light Presets** — 678
- **15. Open Questions (Unknowns)** — 684
- **16. MSFS Programmability Gotchas** — 707
- **17. Edition trail** — 771

---

## 1. Scenery Objects

*(no entries yet — reserved for static, non-simulated Scenery Editor objects.)*

#### Cross-references

- [2024 animation parity note (scenery objects vs SimObjects)](#2024-animation-parity-note-scenery-objects-vs-simobjects)
  — the 2024 scenery-object animation regression (full entry in [§16](#16-msfs-programmability-gotchas)).

---

## 2. Scenery SimObjects

### Scenery SimObjects read only *global-scope* variables — never the user aircraft's A: state

**Claim:** RPN code on a scenery (non-aircraft) SimObject — animated hangar
door, gate, windsock, character — **cannot read the user aircraft's A: SimVars**
(`A:LIGHT LANDING`, `A:PLANE LATITUDE`, …). Aircraft-scoped A: variables have
"no effect at all" there. What DOES evaluate:

- **L:** — cross-object channel (an aircraft or WorldScript writes, the
  scenery SimObject reads).
- **E:** — global environment/time vars (`E:LOCAL TIME`, `E:SIMULATION TIME`).
- **A:** — but only *own-object* or *global/environmental* state:
  `A:AMBIENT WIND *`, `A:AMBIENT TEMPERATURE`, `A:SEA LEVEL PRESSURE`,
  `A:AMBIENT PRECIP STATE`, `A:ANIMATION DELTA TIME` (confirmed working); one
  poster found "(A:SEA LEVEL PRESSURE…) is reading the pressure on the
  simobject, not on the aircraft".

**Consequence:** an "interactable hangar door opened because *my plane* is
near/parked" can NOT condition directly on `(A:PLANE *)` inside the door's
animation — the plane's state must be *injected* (see Pattern A / Pattern B
below).

**Status:** `empirical` (multiple community posters, MSFS2020-confirmed,
consistent with MSFS2024 behavior).
**Source:** FSDeveloper "Visibility" thread p.10 —
https://www.fsdeveloper.com/forum/threads/visibility.449781/page-10
**Added:** 2026-09-20.

### Official corroboration — environment A: vars power SimObject animations

The shipped Asobo behavior template (`Asobo/Misc/SimObjects`, windmill /
windsock) animates from `(A:AMBIENT WIND VELOCITY,feet per second)` and
`(A:AMBIENT WIND DIRECTION,degrees)` (+ `(A:ANIMATION DELTA TIME, seconds)`),
and references `(A:PLANE HEADING DEGREES TRUE, degrees)` in the orientation
formula — how that aircraft-var resolves in a world-SimObject's context is
unverified (likely own-object/constant → wind relative to object; see the
`A:PLANE HEADING DEGREES TRUE` open question in [§15](#15-open-questions-unknowns)).

**Status:** `fact (cited)` (template exists as shipped).
**Source:** official ModelBehaviors template source —
https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/Models/ModelBehaviors/TemplateExplorer/Asobo/Misc/SimObjects.html
**Added:** 2026-09-20.

### Multiplayer Near/Far SimVar propagation — aircraft ↔ aircraft only (RESOLVED 2026-09-20)

Official wording (docs, Simulation Variables → "Note On SimVars In Multiplayer"):

> "Microsoft Flight Simulator 2024 does not have the same concept of shared
> cockpit as previous versions, as such only a small number of variables are
> communicated between **all aircraft** … **Near**: these SimVars are
> transmitted to all aircraft within a 500m radius. **Far**: these SimVars are
> transmitted to all aircraft up to a maximum radius of 10,000m."

**Resolution:** the propagation is scoped to **"all aircraft"** — it exists so
other *aircraft* instances can reproduce your lights/gear/surfaces. There is
**no official path** for a scenery SimObject's RPN to read these (or any
user-aircraft A:) values; the empirical record agrees (aircraft A: vars have
"no effect at all" on scenery SimObjects — first entry). A scenery object that
must react to the user plane has to use the Pattern A / Pattern B entries
below (aircraft-written L: mirrors / WorldScript scenario trigger).

Near list (≤500 m): `GEAR_ANIMATION_POSITION`, `GEAR_POSITION`,
`GEAR_*_STEER_ANGLE`, control-surface PCTs, `SIM ON GROUND`, `GENERAL ENG
STARTER ACTIVE`, prop/turbofan animation vars (`PROP ROTATION ANGLE`,
`TURB_ENG_N1`, `TURB_ENG_AFTERBURNER*`, …). Far list (≤10 km): `LIGHT_*`
(nav/taxi/landing/strobe/beacon/logo/wing/states), `GENERAL ENG RPM` /
`COMBUSTION` (+ sound PCT), `GROUND_VELOCITY`, rotor/disk vars, `SIM ON GROUND`.

**Status:** `fact (cited)` (official wording) → resolution `inferred` (official
scoping + empirical "no effect" record; the docs never mention scenery
SimObjects explicitly, so treat as "no" with high, not absolute, confidence).
**Source:** MSFS2024 docs Simulation Variables index, "Note On SimVars In
Multiplayer" — https://docs.flightsimulator.com/msfs2024/html/6_Programming_APIs/SimVars/Simulation_Variables.htm
**Added/Resolved:** 2026-09-20.

### Non-aircraft SimObjects are simulated and SimVar-controllable

"SimObjects are objects that are 'simulated' … can be controlled using
SimVars, and usually have animations — contrary to the 'static' objects that
can be created as Scenery Editor Objects." Non-aircraft kinds: boats, wildlife,
humans, vehicles. Main file: `sim.cfg` or `container.cfg`.

**Status:** `fact (cited)`.
**Source:** https://docs.flightsimulator.com/msfs2024/html/5_Content_Configuration/Modular_SimObjects/SimObjects/SimObjects.htm
**Added:** 2026-09-20.

### The `CATEGORY` SimVar — full sim.cfg category list

`Airplane|Airship|Helicopter|HotAirBalloon` (aircraft.cfg) or, from sim.cfg:
`AircraftPilot, Animal, Boat, CharacterSim, Container, ControlTower,
FlyingAnimal, GroundVehicle, GroundVehiclePilot, Human, Liquid, Parachute,
ProceduralCharacter, PylonSim, SimpleObject, SimpleObjectSim, StaticObject,
Train, VDGS, Viewer, VR, Winch`.

**Status:** `fact (cited)`.
**Source:** https://docs.flightsimulator.com/msfs2024/retail/programming-apis/simvars/miscellaneous-variables/
**Added:** 2026-09-20.

### SimObject package folders (2024)

Main `sim.cfg` / `container.cfg`; allowed folders at same root:
`animation > .xml`, `effects > .xml`, `interaction > <name>.loc` (2024
interaction system — semantics unverified, see the Open Questions entry in
[§15](#15-open-questions-unknowns)), `localization > <name>.loc`, `model > model.cfg/.xml`, `rtc > .xml`,
`sound > sound.xml`, `soundai > soundai.xml`, `texture > texture.cfg/.xml`.

**Status:** `fact (cited)`.
**Source:** same Non-Aircraft SimObjects page (above).
**Added:** 2026-09-20.

### 2020 → 2024 SimObject conversion quirks

Conversion-relevant differences (2024 docs, "Using The SDK" → SimObjects):

- **`.air` file removed:** "`.air` files (FSX flight model configuration files)
  have been removed in favor of exposing all flight model parameters in plain
  text `.cfg` files" (`aircraft.cfg` / `sim.cfg` cover everything).
- **ModelBehaviors XML named after the glTF:** "this link is done through an
  `*.xml` file which is named after the name of its accompanying `*.gltf`
  file" — `MODEL.gltf` ↔ `MODEL.xml`.
- **≥1 asset group per package:** "Each package will require one or more asset
  group to be a valid package"; an aircraft typically has several
  (SimObject + ModelLib + MaterialLib asset groups).
- **"One SimObject per package" (2020-era) superseded:** 2024 packages can
  hold any content mix — "a single project will have one or more independent
  packages… A package can contain any type of content supported by the
  simulation… defined by adding one or more Asset Groups". (Docs never state
  the supersession explicitly — `inferred` from the cited structure.)

**Status:** `fact (cited)` (docs) for the first three; 2020-claim supersession
`inferred` (derived from the cited 2024 package structure).
**Source:** https://docs.flightsimulator.com/msfs2024/flighting/introduction/using-the-sdk/
(SimObjects → Structure / Model Behaviors; Creating Your First Package)
**Added:** 2026-09-20.

### Pattern A — Scenario proximity trigger (reacts to the *user* by design)

WorldScript `SimMission.RectangleArea` + `ProximityTrigger`
(`ObjectFilter>User`), `OnEnter`/`OnExit` → `PlayBlendTreeStateAction` driving
the door blend-tree animation. This is the pattern Asobo shipped in the NZTL
hangar (`NZTL_Hangar3Door.spb`).

**Status:** `empirical` (community-mined from shipped sim assets).
**Source:** FSDeveloper — https://www.fsdeveloper.com/forum/threads/triggering-hangar-door-animation-in-simobject-by-distance.451392/
**Added:** 2026-09-20.

### Pattern B — Aircraft writes `L:` mirrors

The aircraft (WASM/ModelBehaviors) computes proximity or toggles and writes
`L:` vars; the door animation reads them. Works because `L:` is the verified
cross-object channel (see [§2](#2-scenery-simobjects), first entry). Live example: parallel42
msfs-keyfob (aircraft WASM → global vars consumed by a scenery keyfob
SimObject) — https://github.com/parallel42/msfs-keyfob

**Status:** `empirical` (shipped product).
**Added:** 2026-09-20.

---

## 3. Aircraft Simobjects

*(no entries yet — reserved for `aircraft.cfg` / aircraft SimObject specifics.)*

#### Cross-references

- [The `CATEGORY` SimVar — full sim.cfg category list](#the-category-simvar--full-simcfg-category-list)
  — includes the `aircraft.cfg` categories (`Airplane|Airship|Helicopter|HotAirBalloon`).
- [SimObject package folders (2024)](#simobject-package-folders-2024)
  — the same folder layout applies to aircraft SimObjects.
- [2020 → 2024 SimObject conversion quirks](#2020--2024-simobject-conversion-quirks)
  — covers `aircraft.cfg` and the ModelBehaviors XML link.
- [Pattern B — Aircraft writes `L:` mirrors](#pattern-b--aircraft-writes-l-mirrors)
  — the aircraft-side half of the cross-object pattern.
- [Multiplayer Near/Far SimVar propagation — aircraft ↔ aircraft only](#multiplayer-nearfar-simvar-propagation--aircraft--aircraft-only-resolved-2026-09-20)
  — propagation scope is "all aircraft".

---

## 4. Blender Pipeline for Modeling and Animations

### Blender glTF exporter line-up (2020 → 2024)

Official **MSFS2020** Asobo exporter — `io_scene_gltf2_msfs_2020` — distributed
on https://github.com/AsoboStudio/glTF-Blender-IO-MSFS. Supports Blender
3.3.x / 3.6.x / 4.2.x / 4.5.x LTS; requires the Khronos `io_scene_gltf2`
add-on; cannot import package-built glTF; not compatible with the FSX legacy
exporter.

Official **MSFS2024** exporter — `io_scene_gltf2_msfs_2024` — ships in the SDK
under `Tools\Blender\addons\` (local install) alongside
`wipermask_generator_msfs_2024`; the same folder also carries
`lod_tools_msfs_2024` and `max_bridge_msfs_2024`. Docs: "The Blender Plugin" /
"The Blender Exporter" (Models And Textures → Plugins).

The 2020 and 2024 plugins can be *installed* side by side, but **never enable
both at the same time**. The 2024 exporter has an **"Enable Auto LOD"** option
in its Lod Group Settings: the export emits LOD0 only; the remaining LODs are
generated at build time via Simplygon (see the AutoLOD entry).

Community forks exist: Krajken / flybywiresim ports, KJA1582
`io_scene_gltf2_msfs_kh_2024`.

**Status:** `fact (cited)` — official repo README + SDK-bundled add-on source;
fork list `empirical`.
**Source:** https://github.com/AsoboStudio/glTF-Blender-IO-MSFS ; local SDK
`Tools\Blender\addons\io_scene_gltf2_msfs_2024` ;
https://docs.flightsimulator.com/msfs2024/html/3_Models_And_Textures/Plugins/Blender_Plugin/The_Blender_Plugin.htm
**Added:** 2026-09-20.

### AutoLOD — Simplygon integrated LOD generation (2024)

The 2024 build pipeline integrates the **Simplygon** SDK for automatic LOD
generation ("AutoLOD"), applied per ModelLib asset group. Requirements and
behavior:

- Licensed Simplygon SDK installed under
  `C:\Users\<user>\AppData\Local\Microsoft\SimplygonSDK`; Asobo ships
  `LodProcessingPresets\*.xmlod` preset files with the SDK (selectable in
  Simplygon Options → Preferences → General → Preset Directories).
- Source files must be named `[MODEL]_LOD0.gltf` / `.bin`; the model XML
  declares `<LODS autoGenerate="true"></LODS>` and must **not** contain
  `<LOD/>` entries (remove them all).
- Build generates 7 LODs: LOD1 70% / LOD2 50% / LOD3 35% / LOD4 20% /
  LOD5 10% / LOD6 5% / LOD7 minSize ≤ 1%.
- DevMode: "Debug LODs" window + "Enable Force Active LOD" to preview LODs.
- Docs note **manually authored LODs generally give better results** — use
  AutoLOD as the convenience path (exporter-side: 2024 Blender exporter
  "Enable Auto LOD" exports LOD0 only — see exporter entry above).

**Status:** `fact (cited)` (official docs + SDK-bundled presets).
**Source:** https://docs.flightsimulator.com/msfs2024/html/3_Models_And_Textures/Modeling/Landscape/Using_Simplygon_To_Generate_LODs.htm ;
local SDK `LodProcessingPresets\`
**Added:** 2026-09-20.

### KTX2 / KTX2P — marketplace vs community texture compile (2024)

The Package Tool (in-sim build automation) compiles `*.gltf → *.glb`,
`*.png → *.ktx2` and `*.xml → *.bgl` at build. Texture facts (official):

- **Marketplace-ingested builds produce non-standard KTX2**: "there are
  circumstances where these files are *non-standard* and use a **propriety**
  format … This happens when a project is built for ingestion into the
  *Marketplace* specifically" — not editable/viewable like normal KTX2.
- **Community KTX2 are standard compliant** ("as they do not go through
  marketplace ingestion"); ingested packages become standard compliant via the
  **VFS Projector**.
- **Pixel values are not directly comparable to the source PNG/JPG after
  build** ("pixel data is modified for consumption by the games shaders") —
  for community *and* marketplace builds.
- **KTX2P** is purely a streaming optimization: packs several related KTX2
  files (e.g. albedo/norm/comp/emissive) so they stream in a single HTTP
  request; if absent, the sim falls back to the regular KTX2. **If you modify
  KTX2 post-build but leave the KTX2P, the sim may use the old data — remove
  the KTX2P** (post-build KTX2 edits are strongly discouraged).

Channel observation (Feb 2025, fs-sdk, single poster): marketplace builds came
out roughly **2× the size**, textures left uncompressed for streaming —
`empirical`, not doc-confirmed (docs attribute streaming to KTX2P instead).

**Status:** `fact (cited)` (official docs quotes) + `empirical` (channel size
observation).
**Source:** https://docs.flightsimulator.com/msfs2024/flighting/introduction/using-the-sdk/ ("KTX2 And KTX2P Files");
channel: fs-sdk dump (Feb 2025).
**Added:** 2026-09-20.

### Alpha & transparency flicker — alphaMode=BLEND bug + glass-on-glass in 2024

- **DevSupport report (Jun 2024, exporter 3.3.1 on Blender 4.2):** export
  always defaulted to `"alphaMode": "BLEND"` regardless of the shader setup
  (`gather_alpha_info` in `gltf2_blender_search_node_tree.py` falls through to
  BLEND) → **flickering in the MSFS engine** (materials blending with
  background textures). Same 3.3.1 exporter on Blender 3.6 LTS exports correct
  modes. Community temp fix: patch `gather_material_hook` in the exporter to
  force the MSFS alpha-mode setting into the glTF.
- **Channel report (fs-sdk, 20/03/2025, single poster):** in MSFS 2024 alpha
  problems persist — notably **glass-on-glass** with certain light
  combinations, "less than in 2020" but still present. Workaround applied:
  textures without an alpha channel; transparency expressed via base-color
  alpha only.
- 2020-era docs (Materials, 3ds Max plugin) document the underlying mechanic:
  overlapping transparent/Decal materials sort by mesh center, causing
  flicker; the **Draw Order** parameter offsets the render sorting distance.

**Status:** `empirical` (DevSupport bug-report thread + single-poster channel
report) + `fact (cited)` (2020-era docs Draw Order paragraph, labeled).
**Source:** https://devsupport.flightsimulator.com/t/blender-4-2-exporter-3-3-1-alphamode-blend-always/17564 ;
channel: fs-sdk dump (20/03/2025) ;
https://docs.flightsimulator.com/html/Asset_Creation/3DS_Max_Plugin/Materials.htm (2020-era docs)
**Added:** 2026-09-20.

### Mixamo FBX import — fix the location animation after applying the 0.01 scale

Mixamo rigs import with the **armature object scaled to `0.01`** (Mixamo works in
centimetres; the importer keeps the unit conversion on the object instead of
rewriting bone/keyframe values). Applying Rotation & Scale to get an identity
transform leaves the *rotation* keys correct but the *location* keys in the old
units, so the hips (master) bone ends up ~100× out and the character drifts.

**Procedure (fix the location F-curves):**
1. Import the Mixamo rig / animation. **Note the scale it comes in at** — usually
   `0.01`, but always confirm (N-panel → Item → Scale).
2. Apply rotation and scale (`Ctrl+A` → *Apply* → *Rotation & Scale*).
3. Open the **Graph Editor**. Set the **2D cursor to frame 0**, and the pivot to
   **2D Cursor Relative** (top-right of the Graph Editor — the same control as
   the 3D View pivot menu).
4. **Pose Mode** → select all bones; in the Graph Editor filter box type
   `Location`.
5. Scale the location keys on the **Y axis** (in the Graph Editor, Y = the value
   axis), confirm, then set the operator's **Y value to the original scale you
   noted** (e.g. `0.01`) and confirm. *(Keyboard path: `S`, `Y`, `0.01`,
   `Enter`, pointer over the Graph Editor.)*

For FK-only rigs like Mixamo only the **hips/master bone** location curves
actually matter (the rest are rotation-driven), so "select all + filter
Location" is safe.

**Notes** (`fact (cited)` unless marked otherwise):
- Root cause: applying the object scale changes the skeleton↔unit ratio by 100×
  without touching the stored location values (Blender SE Q309202).
- Alternative: **don't apply the scale at all** — leave the armature at `0.01`
  (engines handle it); only bake it in if you do it consistently to *every*
  armature in the file, else clips "fly" 100× (Cinevva 2026).
- Some authors set the scene to Metric / Unit Scale `0.01` / Length `cm` before
  importing from Mixamo to avoid the mismatch (dev.btro.jp, 2025-07-09).
- Mixamo bones import in **Quaternion** rotation mode (Blender defaults to XYZ
  Euler) — relevant when hand-keying on top of a clip (jMonkeyEngine wiki).
- **MSFS relevance:** fix the location curves *before* the glTF export, or the
  exported clip carries the wrong translation and drifts in-sim. *(inferred)*

**Status:** `user-typed (authoritative)` (procedure stated by the maintainer);
the Notes are cited corroboration.
**Source:** maintainer (user-typed), 2026-09-21; Blender StackExchange Q309202
(https://blender.stackexchange.com/questions/309202/) and Q268280
(https://blender.stackexchange.com/questions/268280/); Cinevva "Mixamo to
Blender 2026" — https://app.cinevva.com/guides/mixamo-to-blender-2026 ;
https://dev.btro.jp/2025/07/09/blender-mixamo-import-to-blender-scale-fix
**Added:** 2026-09-21.

### Cascadeur animations — importing into Blender and the MSFS-compliant glTF export

**Import (Cascadeur → Blender).** Cascadeur cannot emit glTF; export **FBX**
(`File → Export → Export FBX/DAE`, preset *Scene* = model+animation or
*Animation* = motion+skeleton only), with **`Type fbx ascii` = Binary**. In
Blender use `File → Import → FBX` with defaults, but **do NOT enable "Automatic
Bone Orientation"** (it corrupts the joints' rotations → broken animation).
Collada is deprecated since Blender 4.5. Cascadeur uses centimetres, Blender
metres (a Blender scale-1 model arrives at 100 in Cascadeur); Cascadeur's own
advice to avoid scale/rotation drift is `Blender → target engine → Cascadeur →
target engine`. If bones ignore the animation after applying the action, check
each bone's **Rotation mode** in Pose Mode (Euler vs Quaternion). Cascadeur
stores data on every frame, so curves arrive already dense/baked.

**MSFS compliance (export from Blender).** MSFS 2024 stores animations as
**glTF** (`.gltf`, not `.glb`-with-embedded-textures); use the SDK
**Multi-Exporter** `io_scene_gltf2_msfs_2024` — supported only on Blender
**3.3 / 3.6 / 4.2 / 4.5 LTS**. Key rules + the options that enforce them:
- **Negative keyframes are rejected** — the sim does not support them and the
  plugin errors on export; set `Negative Frames = Slide` or `Crop`.
- **Bake** constraints/drivers/IK with `Bake All Objects Animations`.
- `Always Sample Animations` (default on) + `Sampling Rate` (1–120).
- One clip per **action** (Blender 4.5, advised) or per **NLA track** (≤4.2) —
  each becomes a named glTF animation referenced by the **ModelBehaviors XML**.
- `Reset pose bones between actions` (default on) when clips do not key every
  bone; `Set all glTF Animation starting at 0` for loops.
- For **SimObjects** also: `Use Asobo Unique ID Extension` + `Remove LOD Prefix`
  + `Generate TextureLib` + `Optimise Animation Size`.

**Status:** `fact (cited)` (SDK docs + SDK source + Cascadeur help).
**Source:** MSFS SDK — *The Blender Exporter* / *The Blender Plugins* / *Model
Exporting* (docs.flightsimulator.com/msfs2024) ; SDK source
`Tools\Blender\addons\io_scene_gltf2_msfs_2024\io\exp\export_settings.py`
(animation options, lines 745-853) ; Cascadeur help — *Export to Blender* /
*Import from Blender* (cascadeur.com/help).
**Related:** the [Mixamo FBX import entry](#mixamo-fbx-import--fix-the-location-animation-after-applying-the-001-scale) — same "foreign clip → Blender → MSFS" shape.
**Added:** 2026-09-21.

### Parallax Window material — fake "behind glass" interiors (Blender workflow)

The **Parallax Window** FlightSim material renders a *fake interior* behind
window geometry with a parallax shader + a special texture layout — no interior
geometry needed. In MSFS 2024 it's a dedicated material type (Blender panel
material type `msfs_parallax_window`; glTF extension
`ASOBO_material_parallax_window`) and the successor of the older 2020-era
parallax tricks. It can be applied to any surface (building / airport /
porthole windows).

**How it works:** the shader tiles the fake rooms using the **second UV set**
(`UVMap2` in Blender, `UV2` in 3ds Max); Room Scale X/Y act on that UV set, so
the fake-room layout is only as good as the UVMap2.

**Texture slots (ParallaxWindow set, in order):** Base Color (Front Glass
Color) · Occlusion(R) Roughness(G) Metallic(B) · Normal (Front Glass Normal) ·
Emissive Ins Window (RGB) offset Time (A) · Behind Glass Color (RGB) Alpha (A)
· Occlusion (UV2).

**Room-grid rule (critical):** *Emissive Ins Window* and *Behind Glass Color*
must each be subdivided into a grid matching **Room Count**, each cell holding
one room image sized relative to the cell's UV as: vertically floor 1/4, roof
1/2, walls 1/4; horizontally left wall 1/4, back wall 1/2, right wall 1/4.
"Behind Glass Color (RGB) A" = interior albedo, "Emissive Ins Window (RGB) A" =
interior emissive — both respect the same grid.

**Parallax parameters (Blender panel):**
- Room Scale X / Y — multiplier on the UVMap2 size of the fake room (horizontal /
  vertical); Room Scale Z — depth multiplier of the fake rooms.
- Room Count — number of rooms available on the two grid textures.
- Corridor — toggle: left/right walls are not rendered → rooms connect on the
  horizontal axis → corridor look from an angle.

**Blender addon specifics (SDK source):** Alpha mode forced to `MASK`
(`msfs_material_parallax.py:87-89`); defaults Room Scale X/Y/Z = 0.5/0.5/0.5,
Room Count = 5, Corridor = off (`blender\utils\msfs_material_utils.py:157-162`);
material type `msfs_parallax_window` (`io\com\extensions\material\asobo_material_common.py:358`);
extension/export `ASOBO_material_parallax_window` (`asobo_material_parallax_window.py`);
glTF schema: `parallaxScale`, `roomSizeXScale`, `roomSizeYScale`, `roomNumberXY`,
`behindWindowMapTexture` (`Schemas\ASOBO_material_parallax_window\gltf.ASOBO_material_parallax_window.schema.json`).
Shader techs: `Tech_Parallax` / `Tech_Parallax_TwoSide` (`Fx\MSFS2024Material_ParallaxWindow.fx`).
Parallax Window excluded from detail-map slots (no detail maps, 3ds Max UI).

**Porthole material (same trick, aircraft):** albedo alpha encodes depth —
glass 0.8–1, frame 0.5–0.75, invisible 0; normals only on the frame exterior,
never the interior (else applied to the glass); emissive = interior projection,
tileable horizontally, opposing windows at alpha 0 (becomes transparent and
receives global lighting); mesh normals must be oriented horizontally (e.g.
Edit Normals); the effect degrades at extreme angles — keep albedo alpha
consistent and set occlusion (R) white on the exterior side of the window.

**Status:** `fact (cited)` — official MSFS2024 SDK docs + SDK addon source +
schema.
**Source:** docs.flightsimulator.com/msfs2024 — *FlightSim Material Textures*
(§ParallaxWindow), *FlightSim Material Parameters* (§Parallax Parameters),
*Parallax Windows* (models-and-textures/modeling/aircraft/airframe/parallax-windows/)
; SDK source `Tools\Blender\addons\io_scene_gltf2_msfs_2024\blender\material\msfs_material_parallax.py`
+ `blender\utils\msfs_material_utils.py` + `io\com\extensions\material\asobo_material_parallax_window.py`
; `Schemas\ASOBO_material_parallax_window\gltf.ASOBO_material_parallax_window.schema.json`.
**Related:** [Alpha & transparency flicker entry](#alpha--transparency-flicker--alphamodeblend-bug--glass-on-glass-in-2024) — window/glass materials share the alphaMode pitfalls.
**Added:** 2026-09-21.

---

## 5. Blender Third Parties (Addons / Plugins)

*(no entries yet — reserved for third-party Blender add-ons / plugins used
alongside the official exporter.)*

#### Cross-references

- [Blender glTF exporter line-up (2020 → 2024)](#blender-gltf-exporter-line-up-2020--2024)
  — community forks (Krajken / flybywiresim, KJA1582 `io_scene_gltf2_msfs_kh_2024`).
- [AutoLOD — Simplygon integrated LOD generation (2024)](#autolod--simplygon-integrated-lod-generation-2024)
  — Simplygon SDK is the third-party LOD middleware integrated into the build.

---

## 6. Adobe 3D Painter Pipeline for Texturing

*(no entries yet — reserved for the Substance 3D Painter texturing pipeline.)*

---

## 7. Terrain Edition (Satellite and CGL)

*(no entries yet — reserved for satellite imagery and CGL terrain editing.)*

---

## 8. Projected Meshes

### Projected Mesh objects — independent placement outside airports

A Projected Mesh renders a scenery model **projected flat onto terrain (2D)**
instead of in 3D — used in airports to add terrain detail.

- **Independent placement (2024):** "By default, Projected Mesh objects
  require one or more Airport Objects to be present in the scene… If no
  airport is present and you still require a Projected Mesh, then you should
  check the box labelled **Independent Object** before adding it to the scene"
  — the group is then created in the scenery root instead of inside an airport
  group. (This confirms the community technique for non-airport areas; fs-sdk
  channel, mamu82, 15/05/2024.)
- **Overlap & draw order:** overlapping meshes must have **different
  priorities** (higher = rendered over lower; same-priority order is not
  guaranteed). **Draw Before** slots the mesh into the render hierarchy (e.g.
  before MARKINGS → over aprons/taxiways/runways, under markings/marking
  text). Placed outside the airport **Object Test Radius** → **not rendered**.
- **Rendering:** meshes are **baked into the terrain textures** (polycount
  savings, terraformable) — quality capped by terrain resolution (~4mm/px at
  the equator; best LODs reserved for airports; increases with the "Terrain
  level of detail" setting). The source object itself is not required in the
  final package (baked into the glTF).
- **Authoring constraints:** export models **without translation/rotation/
  scale** (transforms are dropped — use the Scenery Editor Gizmo instead);
  only albedo, metal-rough-AO, normal maps + detail counterparts are allowed —
  metal and AO components are **not used**. **Ground Merging** blends terrain
  with the material textures; **Surface Type** has no visual effect (choose it
  for correct VFX/audio); snow coverage is automatic (darker areas less snow;
  asphalt/cement/paint materials and roads reduce it).

**Status:** `fact (cited)` (2024 docs; channel report corroborated).
**Source:** https://docs.flightsimulator.com/msfs2024/flighting/devmode/editors/scenery-editor/objects/projectedmesh-objects/ ;
channel: fs-sdk dump (mamu82, 15/05/2024).
**Added:** 2026-09-20.

---

## 9. RPN Schematics and Quirks

### Variable types reference — RPN variable prefixes (A: L: E: Z: O: P: H: K: B:)

| Prefix | Meaning | Scope / notes |
|---|---|---|
| `A:` | SimVar — sim state read/write | Scenery context: own-object + global-sim/env only; user-aircraft state readable only from the aircraft itself |
| `L:` | Custom variable | Per-SimObject, but the reliable cross-object channel in practice; saved with flight |
| `E:` | Environment variable (time, …) | Global |
| `Z:` | Script-scope temporary | Community-observed in RPN scripts; formally unverified |
| `O:` | ModelBehaviors runtime scratch (`O:XMLVAR_*` — jetway hoods, etc.) | Used in official templates; formal scope unverified |
| `P:` | FSX-era panel/param vars; Asobo gauge code seen using `P:LOCAL TIME` | Legacy context; not needed for scenery work |
| `H:` / `K:` | Key / input events | Client-side input events, not read-back variables |
| `B:` | B-events (custom events) | Not readable as variables (MobiFlight wiki, SU9-era) |

A:/L:/E: = confirmed; Z:/O:/P:/H:/K:/B: = empirical/legacy, marked per cell.

**Status:** `user-typed (authoritative)` (maintainer-marked 2026-09-21; per-prefix confidence still noted per row).
**Source:** maintainer (user-typed), 2026-09-21.
**Added:** 2026-09-20.

#### Cross-references

- [Scenery SimObjects read only *global-scope* variables — never the user aircraft's A: state](#scenery-simobjects-read-only-global-scope-variables--never-the-user-aircrafts-a-state)
  — the core RPN scoping quirk (full entry in [§2](#2-scenery-simobjects)).
- [Pattern A — Scenario proximity trigger (reacts to the *user* by design)](#pattern-a--scenario-proximity-trigger-reacts-to-the-user-by-design)
  and [Pattern B — Aircraft writes `L:` mirrors](#pattern-b--aircraft-writes-l-mirrors)
  — cross-object RPN schematics ([§2](#2-scenery-simobjects)).
- [ModelBehaviors `Update` components unreliable on Landmark SimObjects in 2024](#modelbehaviors-update-components-unreliable-on-landmark-simobjects-in-2024)
  — RPN fix via WorldScript `SimMission.Calculator` ([§16](#16-msfs-programmability-gotchas)).

---

## 10. DevMode - Texturing (Polygons and Aprons)

*(no entries yet — reserved for DevMode polygon/apron texturing.)*

---

## 11. DevMode - Workarounds

### SU1-beta asset-display bug — project opens, assets invisible (single report)

Channel report (fs-sdk, **salvuz, 13/02/2025**, single poster, 1 👍): on the
**SU1 Beta** (1.3.x line), opening a project works but **no assets are
displayed** in the editors — scenery objects, SimObjects and projected meshes
all missing. Building still succeeds with **no errors**; the same project
reopened on the current stable has no problem. The project was originally
2020-era, worked on in 2024 pre-SU1, all assets re-exported with the 2024
Blender exporter at the time.

**Workaround** (confirmed same day by the poster): create a **new project**
and use the **Import** function — assets re-import in one pass and everything
works.

No DevSupport thread corroborating this exact SU1-beta symptom was found
during verification (adjacent threads exist: 2020-SimObject auto-convert
prompts, generic "assets not loading") → **low confidence**, single-user
record.

**Status:** `empirical` (single-user report + same-day fix; low confidence).
**Source:** fs-sdk dump (salvuz, 13/02/2025, declog 83153-83180).
**Added:** 2026-09-20.

---

## 12. DevMode - Runways

*(no entries yet — reserved for DevMode runway editing.)*

---

## 13. DevMode - Various

*(no entries yet — reserved for DevMode topics not covered by the other
DevMode categories: ILS, custom frequencies, etc.)*

---

## 14. DevMode - Light Presets

*(no entries yet — reserved for DevMode light presets.)*

---

## 15. Open Questions (Unknowns)

- **Near/Far propagated aircraft vars vs scenery SimObject RPN — RESOLVED
  2026-09-20:** official "Note On SimVars In Multiplayer" scopes propagation to
  "all aircraft" (Near ≤500 m / Far ≤10 km — full lists in [§2](#2-scenery-simobjects)); no
  scenery-SimObject read path documented, empirical record consistent.
  Confidence: high, not absolute (docs never mention scenery objects).
  → [Multiplayer Near/Far SimVar propagation](#multiplayer-nearfar-simvar-propagation--aircraft--aircraft-only-resolved-2026-09-20) ([§2](#2-scenery-simobjects)).
- **`A:PLANE HEADING DEGREES TRUE` inside the official windmill template:**
  does it resolve the user plane or the SimObject itself? (affects the
  orientation formula's meaning).
  → [Official corroboration — environment A: vars power SimObject animations](#official-corroboration--environment-a-vars-power-simobject-animations) ([§2](#2-scenery-simobjects)).
- **`interaction/<name>.loc` package folder:** candidate for the 2024
  player/aircraft interaction system (the "interact with your plane" door
  idea) — structure and semantics not yet documented here.
  → [SimObject package folders (2024)](#simobject-package-folders-2024) ([§2](#2-scenery-simobjects)).
- **L: var cross-aircraft reading in MSFS2024:** community is split on whether
  a scenery SimObject reads *any* aircraft's L:vars or only globals; keyfob
  proves at least the aircraft→scenery direction.
  → [Pattern B — Aircraft writes `L:` mirrors](#pattern-b--aircraft-writes-l-mirrors) ([§2](#2-scenery-simobjects)).

---

## 16. MSFS Programmability Gotchas

### ModelBehaviors `Update` components unreliable on Landmark SimObjects in 2024

DevSupport report: `ASOBO_GT_Update` / `Asobo_Update_Template` on a Landmark
SimObject did **not** run — an L:var it was meant to write stayed `0` (checked
in DevMode Behaviors tool). Verified fix: drive the object from a **WorldScript
`SimMission.Calculator`** that computes and writes `L:` vars, consumed by
`animations.xml` / `soundai.xml`. Example (resolved thread):

```
(E:TIME OF DAY, Enum) 2 <= (A:AMBIENT PRECIP STATE, mask) 2 ==
and d (L:ESD_DawnDuskNoWX) != if{ (>L:ESD_DawnDuskNoWX) }
```

**Status:** `empirical` (user-confirmed failure + fix).
**Source:** https://devsupport.flightsimulator.com/t/using-the-update-component-in-a-non-aircraft-simobject-trigger-sound-using-lvar/16902
**Added:** 2026-09-20.

### 2024 animation parity note (scenery objects vs SimObjects)

At 2024 launch, MSFS2020 scenery-object animations regressed (runway people
t-pose, flags not animating) while the same setups as **SimObjects** worked.
Rule of thumb: use the SimObject animation path for reliable animation in
2024. Status: `empirical` (DevSupport bug-report thread).
**Source:** https://devsupport.flightsimulator.com/t/animation-problem/10323
**Added:** 2026-09-20.

### Jetway IK constraints — `<IKConstraint>` in model XML (2020-era; 2024 applicability unknown)

- **Channel tip (fs-sdk, mamu82, 20/03/2025 23:20):** when a jetway won't
  extend/move correctly at its parking position, the jetway model XML can
  carry an IK constraint block:
  ```
  <IKConstraint>
  <Node>Empty01</Node>
  <X min="0.54" max="15.5"/>
  </IKConstraint>
  ```
  — raise `max` / lower `min` (**X only**) to widen the allowed extension.
- **2024 SDK check (local grep, `C:\MSFS 2024 SDK`):** `IKConstraint` matches
  **zero** files. The 2024 `ModelBehaviorDefs\Asobo\Misc\SimObjects.xml`
  ships only `ASOBO_Jetway_Hood_Left/Right_Bend/Deployment`,
  `ASOBO_Jetway_Hood_Top_Horizontal/Vertical`, `ASOBO_Jetway_Wheel_Roll` and
  `ASOBO_Jetway_Wheel_Orientation` templates (lines 77–186) — no IK element.
- **2020-era docs** (Jetway sample page, labeled): "…by seeing the
  `<IKChain>` and `<IKConstraint>` sections of the [model].xml file" — the
  element is documented for the **2020** SDK. Whether 2024 jetway models still
  honor it is **unknown** (SDK silent, no counter-evidence).

**Status:** `empirical` (channel tip on 2020-style jetway XML) + `unknown`
(2024 applicability — 2024 SDK contains no `IKConstraint`).
**Source:** fs-sdk dump (mamu82, 20/03/2025, declog 83334-83341) ;
local SDK `ModelBehaviorDefs\Asobo\Misc\SimObjects.xml` ;
https://docs.flightsimulator.com/html/Samples_And_Tutorials/Samples/SimObjects_Other/Jetway.htm (2020-era docs)
**Added:** 2026-09-20.

#### Cross-references

- [SU1-beta asset-display bug — project opens, assets invisible (single report)](#su1-beta-asset-display-bug--project-opens-assets-invisible-single-report)
  — DevMode editor bug + workaround (full entry in [§11](#11-devmode---workarounds)).

---

## 17. Edition trail

One row per edition, newest first. Recorded by the **MSFS Cache Updater**
agent; rows are never removed. (Section numbers cited in rows before
2026-09-21 refer to the pre-reorg layout.)

| Date | Summary |
|---|---|
| 2026-09-21 | Added §4 entry "Parallax Window material — fake behind-glass interiors (Blender workflow)" (`fact (cited)`, research request C: official MSFS2024 docs FlightSim Material Textures/Parameters + Parallax Windows page + local SDK addon source `msfs_material_parallax.py`/`msfs_material_utils.py`/`asobo_material_parallax_window.py` + glTF schema). Entry-level insert — no renumber. |
| 2026-09-21 | Added §4 entry "Cascadeur animations — importing into Blender and the MSFS-compliant glTF export" (`fact (cited)`, research request C: SDK docs + SDK source + Cascadeur help). Entry-level insert — no renumber. |
| 2026-09-21 | Added §4 entry "Mixamo FBX import — fix the location animation after applying the 0.01 scale" (`user-typed (authoritative)` + cited corroboration). Entry-level insert — no renumber. |
| 2026-09-21 | Spec-alignment edition: §9 RPN variable-prefix table marked `user-typed (authoritative)` (adds mandatory Status/Source/Added); cross-reference blocks demoted from `###` to `####` so the inventory gate's `^### ` scan sees entries only; every bare `§N` in entry bodies/cross-refs converted to anchor links; the dated snapshot `MSFS2024_informations_2026-09-21_pre_category_reorg.md` removed (only `.bak` kept). Companion: `custom agent\msfs-cache-updater.md` updated (canonical 16-category list, cross-reference/reserved rules, structural-edition protocol, anchor link-check, INDEX bullet set, open-questions lifecycle, grep clarification). |
| 2026-09-21 | Structural reorg: 10 topic sections → 16 categories (1 Scenery Objects, 2 Scenery SimObjects, 3 Aircraft Simobjects, 4 Blender Pipeline for Modeling and Animations, 5 Blender Third Parties, 6 Adobe 3D Painter Pipeline for Texturing, 7 Terrain Edition (Satellite and CGL), 8 Projected Meshes, 9 RPN Schematics and Quirks, 10 DevMode - Texturing (Polygons and Aprons), 11 DevMode - Workarounds, 12 DevMode - Runways, 13 DevMode - Various, 14 DevMode - Light Presets, 15 Open Questions (Unknowns), 16 MSFS Programmability Gotchas). Every entry preserved; multi-category entries now cross-referenced by anchor; empty categories marked reserved. Moves: old §5 Variable types → new §9 RPN; old §7 KTX2/KTX2P + Alpha flicker → §4 Blender Pipeline; old §8 Projected Mesh → §8 Projected Meshes; old §3 SU1-beta → §11 DevMode - Workarounds. Internal `§` refs remapped to new numbering; Contents + INDEX refreshed. Backups: `MSFS2024_informations.md.bak` + `MSFS2024_informations_2026-09-21_pre_category_reorg.md`. |
| 2026-09-20 | Ingest 8/8 (fs-sdk dump): §3 SU1-beta asset-display bug entry (single-user report salvuz 13/02/2025; workaround new project + Import; no DevSupport corroboration → `empirical`, low confidence). Dump ingestion complete. |
| 2026-09-20 | Ingest 7/8 (fs-sdk dump): §3 Jetway IK constraint entry (`<IKConstraint><Node>…</Node><X min max/>` — channel tip `empirical`; 2024 SDK grep: zero matches → 2024 applicability `unknown`). |
| 2026-09-20 | Ingest 6/8 (fs-sdk dump): §2 2020→2024 SimObject conversion quirks (.air removed → .cfg; behavior XML named after .gltf; ≥1 asset group; one-SimObject-per-package superseded) (`fact (cited)` + `inferred`). |
| 2026-09-20 | Ingest 5/8 (fs-sdk dump): §8 Projected Mesh entry — Independent Object placement, bake-to-terrain, priorities/Draw Before, authoring constraints (`fact (cited)`). |
| 2026-09-20 | Ingest 4/8 (fs-sdk dump): §7 Alpha & transparency flicker entry (`empirical` DevSupport + channel; `fact (cited)` 2020-era docs note). |
| 2026-09-20 | Ingest 3/8 (fs-sdk dump): §7 KTX2/KTX2P texture-compile entry (`fact (cited)` + channel `empirical` note). |
| 2026-09-20 | Indexed the cache: new `INDEX — categories → starting line` block (after Contents) listing all `## N. Topic` headings + starting line numbers (verified exact post-insert). Future editions must keep it current. |
| 2026-09-20 | Ingest 2/8 (fs-sdk dump): §6 AutoLOD/Simplygon entry (`fact (cited)`). |
| 2026-09-20 | Ingest 1/8 (fs-sdk dump): §6 Blender exporter lineage entry (`fact (cited)`). Structural: added §6 Blender pipeline: exporters & LODs, §7 Textures & materials (2024), §8 Scenery Editor object types → Open questions §9, Edition trail §10; Contents updated. Backup: `MSFS2024_informations.md.bak`. |
| 2026-09-20 | Scaffold: added the `user-typed (authoritative)` status, §7 Edition trail, and wired the global `msfs2024-knowledge` reference (global `opencode.jsonc`). |

---

*Cache created 2026-09-20. Seed content = facts verified in the plan-msfs
research session on SimVars / SimObject variable scope. Kept at the project's
fallback-chain "rung 0" (consult before web research). Maintained by
`msfs-cache-updater` (global agent); staging workspace: `.cache_staging\`.*
