# API Contract — bd_hardware (Hardware Integration Library for build123d)

Version 1.0 · Author: researcher · AGENTS.md v— (n/a; OSS project, not JARVIS)

This document is the binding API contract for the pip-installable build123d hardware
library. It is the input to the scaffold task (t_11fbda75) and the four implementation
tasks. Everything below is a decision, not a suggestion — implementers treat it as the
single source of truth. Where the root pitch or a task body is ambiguous, this document
resolves the ambiguity.

---

## 1. Purpose and scope

A lightweight, beginner-friendly, function-first Python library of hardware *features*
(holes, pockets, bosses, snap features) keyed to standard metric and imperial sizes,
built natively on build123d. It is deliberately simpler than bd_warehouse: one import,
one function call per feature, plain string sizes, and a `quick_ref()` cheatsheet for
discovery. No class hierarchy, no CSV internals, no eval-based parsing.

Six feature families, mapped to five modules (module names are fixed by the root pitch;
the mapping of the six families onto five modules is fixed here to prevent ownership
collisions):

| Feature family                 | Module file          | Owner task    |
|--------------------------------|----------------------|---------------|
| Screw clearance / cbore / csk  | `fastener.py`        | t_a2320a26    |
| Heat-set insert pockets        | `inserts.py`         | t_dc036f54    |
| Nut traps + thread-forming     | `nuts.py`            | t_dc036f54    |
| Snap-fits                      | `snap_fit.py`        | t_fbd4e557    |
| Press-fit bearing pockets      | `bearings.py`        | t_fbd4e557    |

The sixth family, "threaded plastic holes" (thread-forming screws), lives in `nuts.py`
under the names `thread_forming_boss()` / `thread_forming_hole()`. Rationale: `nuts.py`
is owned by t_dc036f54 (which also owns thread-forming per its task body), and placing
them in `fastener.py` would put two developers on one file.

---

## 2. Survey findings (what already exists — evidence)

### 2.1 Catch'n'Hole (OpenSCAD) — github.com/mmalecki/catchnhole, MIT
Nutcatches, screw holes, countersinks. Ergonomic but OpenSCAD-only, requires the nightly
build + JSON `import`. API is module-based with a `name` string ("M3") and `kind`
("headless" / "socket_head" / "countersunk" / "hex_head"). Uses BOLTS data. Good ergonomics,
wrong ecosystem.

### 2.2 cq-queryabolt (CadQuery) — github.com/mmalecki/cq-queryabolt, MIT
CadQuery port of Catch'n'Hole. `WorkplaneMixin` adds `boltHole()`, `cboreBoltHole()`,
`cskBoltHole()`, `nutcatchParallel()`, `nutcatchSidecut()`. Data from BOLTS JSON. Author
explicitly notes cqparts_fasteners and cq_warehouse were "too verbose" — that is the same
ergonomic bar this library targets.

### 2.3 threads.scad (OpenSCAD) — github.com/rcolyer/threads-scad, CC0-1.0
Mature threading library (metric internal/external threads, clearance/countersunk/recessed
holes, bolts, nuts, washers). Frozen since ~2021. Metric-first with numeric-diameter API
(`ScrewHole(outer_diam, height, ...)`), not size-keyed. Excellent thread geometry reference,
not a size-chart library.

### 2.4 bd_warehouse (build123d) — github.com/gumyr/bd_warehouse, Apache-2.0
The incumbent. Active (commit 2026-09-21, build123d v0.13). Modules: fastener, bearing,
bushing, flange, gear, o_rings, pipe, retaining_ring, shaft_key, sprocket, thread. Already
covers most of this library's surface:
- `HeatSetNut` (types McMaster-Carr / Hilitchi / ruthex / CNCKitchen / AE-SamZhihui) + `InsertHole`
- `Nut` subclasses (HexNut, SquareNut, DomedCapNut, …) + `ClearanceHole(captive_nut=…)`
- `ClearanceHole` / `TapHole` / `ThreadedHole` with `fit ∈ {Close, Normal, Loose}`
- `bearing.Bearing` + `PressFitHole(bearing, interference, fit, depth)`

### 2.5 Where the existing APIs are awkward / undocumented (the gaps this library closes)

1. **Stringly-typed, unvalidated sizes.** `"M6-1"`, `"#6-32"`, `"M8-22-7"` are parsed with
   ad-hoc `.split("-")` and an `eval()` call (`metric_str_to_float`) on CSV strings. No
   single parser, no validation that pitch matches diameter, no `Size` object.
2. **Hole classes require a fully-built fastener instance**, not a size. `ClearanceHole`
   takes `fastener: Union[Nut, Screw]` — you must know which screw class to instantiate
   just to cut a clearance hole. Heavyweight and confusing for beginners.
3. **Inconsistent enums.** Clearance fits are `Close/Normal/Loose` but tap material is
   `Soft/Hard`; cq_warehouse used `Close/Medium/Loose`. Three vocabularies across two libs.
4. **No discovery surface.** `types()`/`sizes()`/`select_by_size()` exist but the underlying
   CSVs are opaque; there is no one-call cheatsheet. Beginners can't learn the API without
   reading source. (The root pitch's #1 r/cadquery question is literally "how do I add a
   screw hole?" — discoverability is the whole point.)
5. **No snap-fit primitive anywhere** in the surveyed set. Snap-fits have no size chart;
   they are pure geometry — a greenfield module.
6. **No thread-forming-screw primitive.** `TapHole` is for cutting metal threads, not for
   thread-forming screws in plastic (different pilot/engagement diameters, boss walls).
7. **Bearing fit classes are reused from clearance holes** (`Close/Normal/Loose`) rather
   than real press-fit interference classes (light/medium/heavy).

---

## 3. Package name

**`bd_hardware`** — import as `import bd_hardware as bdh`. Provisional; if a name conflict
surfaces at publish time, rename once in the scaffold (a single find/replace in `pyproject.toml`
and `__init__.py`) before any implementation lands. Do not invent a second name downstream.

Layout on disk:

```
bd_hardware/
  __init__.py        # re-exports the 5 modules + quick_ref; OWNED BY SCAFFOLD ONLY
  _sizes.py          # shared size model: Size, SizeChart, ClearanceClass, parse()
  _quick_ref.py      # shared formatter: quick_ref dispatch + table/usage renderers
  fastener.py
  inserts.py
  nuts.py
  snap_fit.py
  bearings.py
  data/
    fastener_clearance.json
    inserts.json
    nuts.json
    thread_forming.json
    bearings.json
```

Underscore-prefixed `_sizes.py` and `_quick_ref.py` are shared infrastructure. They are
written ONCE by the scaffold task and are NOT edited by the module implementers — this is
the primary non-conflict guarantee (see §8).

---

## 4. Common size-data model

Every feature is resolved through a single shared `Size` + `SizeChart`. Module implementers
MUST NOT parse size strings or load JSON themselves; they call `_sizes`.

### 4.1 `Size` dataclass

```python
from dataclasses import dataclass
from typing import Literal

Units = Literal["metric", "imperial"]
ClearanceClass = Literal["close", "normal", "loose"]   # lowercase, normalized
Material = Literal["soft", "hard"]                     # tap / thread-forming substrate

@dataclass(frozen=True)
class Size:
    nominal: str          # canonical id, e.g. "M3-0.5", "#6-32", "608"
    units: Units          # "metric" | "imperial"
    clearance_class: ClearanceClass = "normal"
    source: str = ""      # chart key, e.g. "iso273", "cnc-kitchen", "iso4032"
```

The four required fields from the task — nominal size, units, clearance class, source
chart — are exactly these four dataclass fields. `source` is the chart key (§7).

### 4.2 `parse()` and constructors

```python
def parse(spec: str, *, clearance_class: ClearanceClass = "normal") -> Size
def metric(diameter_mm: float, pitch_mm: float) -> str      # -> "M3-0.5"
def imperial(major: str, tpi: int) -> str                   # -> "#6-32"
def bearing_608(size: str) -> str                           # normalize "608" -> "608"
```

`parse("M3")` must resolve to nominal `"M3-0.5"` (coarse pitch assumed) — accept the bare
diameter form; pitch is filled from the coarse-pitch table. `parse("#6-32")` keeps `#6-32`.
Invalid sizes raise `ValueError` with the list of valid nominals for that chart.

### 4.3 `SizeChart` loader

```python
class SizeChart:
    name: str                                   # chart key, e.g. "inserts"
    def __init__(self, name: str): ...          # loads data/<name>.json
    def sizes(self) -> list[str]: ...           # nominal ids, sorted ascending
    def get(self, nominal: str) -> dict[str, float]: ...  # key dims, KeyError -> ValueError
    def quick_ref(self) -> str: ...             # formatted table (see §6)
```

Data files are **JSON** (not CSV) with a fixed schema so the scaffold can validate them:

```json
{
  "chart": "inserts",
  "units": "metric",
  "source": "cnc-kitchen",
  "columns": ["od", "length", "pilot", "pitch"],
  "sizes": {
    "M3-0.5":  {"od": 4.6, "length": 5.7, "pilot": 4.0, "pitch": 0.5}
  }
}
```

All dimensions are **millimetres** in data files. Imperial inputs are converted to mm on
parse (the module never does its own unit math). `Units` is recorded for display/rounding
only.

### 4.4 Units

`MM = 1`, `IN = 25.4` are re-exported from `build123d` (or defined in `_sizes.py`).
Functions accept and return mm floats; `quick_ref()` prints mm for metric charts and
both mm and inch for imperial charts.

---

## 5. Conventions (apply to every module — do not deviate)

1. **Return types.** Every *cutter* (a negative feature you subtract) returns a build123d
   `Solid` when it is a single body, or a `Part` when it is compound (e.g. a threaded hole
   with a separate thread helix). Every *positive* part (insert body, nut, bearing, snap
   hook) returns a `Solid` (or `Part` for a bearing race pair). Type is stated per signature.
   Subtraction is `workpiece -= cutter` (build123d native); a helper `bdh.cut(part, *cutters)`
   may be provided by the scaffold but is NOT required of modules.
2. **Origin / axis convention.** A hole/pocket cutter is modeled opening at `Z=0` and
   cutting along `+Z` (depth increases +Z). Positive parts are modeled axis-aligned with
   their reference face at `Z=0` and their axis on `+Z`. No function translates/rotates a
   result into a caller location — callers position with `Location`/`Pos` themselves. This
   keeps module outputs composable and testable at the origin.
3. **Depth default.** `depth=None` means "through the part" for holes. In builder mode the
   scaffold wrapper may default to `2 * max_dimension`; the pure function contract stays
   `None = through`.
4. **Validation.** All size strings go through `_sizes.parse()`. Invalid size/chart/class →
   `ValueError` (never `KeyError` leaking to the user). Errors name the valid options.
5. **Tolerances.** A global module-level default for FFF printing clearance is provided via
   `_sizes` (e.g. `MANUFACTURING_COMPENSATION = 0.0`), overridable per-call by a
   `compensation` kwarg. Do not hard-code printer fudge factors into size data; keep data
   nominal and apply compensation at generation time.
6. **No hard-coded geometry.** Every dimension comes from `SizeChart.get()`. A literal mm
   value in a module body is only allowed for angles and non-size geometry (csk angle,
   snap retention angle) — never for a size dimension.

---

## 6. `quick_ref()` contract

One `quick_ref()` per module, plus a package-level dispatcher. Output is a **plain string**
(markdown-style), deterministic, and identical in shape across modules so tests can diff it.

```python
# per module
def quick_ref() -> str: ...

# package level
def quick_ref(module: str | None = None) -> str: ...   # None -> all modules concatenated
```

### 6.1 Exact format

```
== <module> ==
USAGE
  <example line>
  <example line>
SIZES
| <col1> | <col2> | ... |
|--------|--------|-----|
| <row>  | <row>  | ... |
```

Rules:
- Header line is exactly `== <module> ==` (module = file stem, e.g. `fastener`).
- `USAGE` section: 1–3 lines, each prefixed with two spaces, showing a real import + call
  with a representative size and a short `# comment`.
- `SIZES` section: a GitHub-flavored Markdown table. First column is always `Size`.
  Column set is module-specific but stable per module (§7 lists the exact columns).
  Rows sorted ascending by nominal size. A trailing count line is NOT included (count is
  derivable); the table is the source of truth.
- Sections separated by a single blank line; the block ends with a trailing newline.

### 6.2 Example (`inserts.quick_ref()`)

```
== inserts ==
USAGE
  from bd_hardware import inserts
  insert_hole("M3-0.5", clearance_class="normal")   # heat-set pilot pocket
SIZES
| Size     | OD   | Length | Pilot | Source      |
|----------|------|--------|-------|-------------|
| M2-0.4   | 3.6  | 3.0    | 2.8   | cnc-kitchen |
| M3-0.5   | 4.6  | 5.7    | 4.0   | cnc-kitchen |
```

The scaffold provides `_quick_ref.render(module, usage_lines, headers, rows) -> str` that
builds the above exactly; modules call it and do not hand-format strings.

---

## 7. Function signatures (per module)

### 7.1 `fastener.py` — screw clearance holes, counterbores, countersinks

```python
def clearance_hole(
    size: str,                              # "M3", "M4-0.7", "#6-32"
    *,
    clearance_class: ClearanceClass = "normal",   # close | normal | loose
    head: Literal["none", "counterbore", "countersink"] = "none",
    head_clearance: float = 0.0,            # extra radial clearance on the head recess
    depth: float | None = None,             # None = through
) -> Solid
```

- `head="counterbore"` cuts a socket-head-cap-screw counterbore; `head="countersink"` cuts
  a flat-head countersink (metric 90°, imperial 82°). `head_clearance` adds to the recess
  diameter only (mirrors `head_diameter_clearance` in Catch'n'Hole).
- Return: single `Solid` cutter, opening at Z=0, +Z depth.
- quick_ref columns: `Size | Close | Normal | Loose | CBoreØ | CSinkØ`

### 7.2 `inserts.py` — heat-set insert pockets

```python
def insert_hole(
    size: str,                              # "M3-0.5"
    *,
    clearance_class: ClearanceClass = "normal",
    depth: float | None = None,
    compensation: float = 0.0,              # add to hole diameter for over-extrusion
    lead_in: bool = True,                   # top chamfer/taper for the insert body
) -> Solid

def heat_set_insert(
    size: str,
    *,
    simple: bool = True,                    # True = no thread (fast preview)
) -> Solid                                  # positive insert body for viz / BOM
```

- `insert_hole` models the recommended pilot hole (straight bore + optional lead-in taper)
  and the counterbore lip where the insert shoulder sits. `depth` is the insert seating
  depth, not the screw clearance depth (which is `fastener.clearance_hole` on top).
- quick_ref columns: `Size | OD | Length | Pilot | Source`

### 7.3 `nuts.py` — nut traps + thread-forming bosses

```python
def nut_trap(
    size: str,                              # "M3", "M4-0.7", "#6-32"
    *,
    nut_type: Literal["hexagon", "square", "hexagon_thin", "hexagon_lock"] = "hexagon",
    clearance_class: ClearanceClass = "normal",
    depth: float | None = None,
    sidecut: bool = False,                  # True = slot from the side; False = end-on trap
    capture: bool = False,                  # True = add screw relief beyond the nut seat
) -> Solid

def thread_forming_boss(
    size: str,                              # "M3", "#6-32"
    *,
    material: Material = "soft",            # soft (PLA/ABS) | hard (PC/glass-filled)
    boss_od: float | None = None,           # None = recommended min wall OD
    depth: float | None = None,
) -> Solid                                  # cutter: pilot hole + boss OD outer pocket
```

- `nut_trap` covers hex (ISO 4032), square (DIN 562), thin (ISO 4035), lock (ISO 7040).
  `sidecut=True` is the side-entry slot; `capture=True` extends a relief for the screw
  tip past the nut. Return: `Solid` cutter (trap) — the nut itself is NOT required to be
  generated for v1.
- `thread_forming_boss` is the plastic counterpart for a thread-forming screw: pilot hole
  diameter per `material`, plus the outer boss wall (a ring pocket so the printed boss has
  the correct wall thickness). Return: `Solid` cutter (pilot + boss pocket, compound).
- quick_ref columns (nut_trap): `Size | AF | Height | Type`
- quick_ref columns (thread_forming_boss): `Size | PilotSoft | PilotHard | BossOD`

### 7.4 `snap_fit.py` — cantilever + annular snap-fits (no size chart)

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class CantileverSpec:
    length: float          # beam length (mm)
    width: float           # beam width (mm)
    thickness: float       # beam thickness at root (mm)
    retention: float       # engagement/undercut depth (mm)
    angle: float = 45.0    # retention ramp angle (deg)
    root_fillet: float = 0.5   # fillet radius at root (mm)

def cantilever_hook(spec: CantileverSpec) -> Solid        # positive hook feature
def cantilever_catch(spec: CantileverSpec) -> Solid       # mating undercut cutter
def annular_snap(
    radius: float,         # nominal radius (mm)
    *,
    thickness: float,
    retention: float,
    angle: float = 45.0,
) -> Solid                                                # revolved annular snap feature
```

- Snap-fits have **no size chart**. `quick_ref()` lists the recommended parameter set (a
  small table of typical `CantileverSpec` values keyed by beam length) plus a usage example.
  Implementers add a plain-language design note (retention ≈ deflection, keep undercut
  shallow for FFF) but NO dimension data files.
- quick_ref columns: `Config | Length | Width | Thickness | Retention`

### 7.5 `bearings.py` — press-fit bearing pockets

```python
def bearing_pocket(
    size: str,                              # "608", "625", "6900"
    *,
    fit: Literal["light", "medium", "heavy"] = "medium",  # press-fit interference class
    depth: float | None = None,             # None = bearing width (seat depth)
    bore_through: bool = False,             # True = also cut the shaft bore
    bore_class: ClearanceClass = "normal",  # shaft-bore fit (reuses clearance vocab)
) -> Solid

def bearing(
    size: str,
    *,
    simple: bool = True,                    # True = no balls/races detail
) -> Part                                    # positive bearing for viz
```

- `fit` selects the interference applied to the pocket OD: `light/medium/heavy` map to a
  fixed set of mm interferences (e.g. 0.00 / -0.02 / -0.04 on the radius) defined in
  `_sizes`. `bore_through=True` also cuts the axial bore at `bore_class` (reuses the
  `ClearanceClass` vocabulary for the shaft hole, which is a clearance feature, not a
  press-fit). Return: `Solid` cutter (pocket, optional bore).
- quick_ref columns: `Size | Bore | OD | Width | Light | Medium | Heavy`

---

## 8. Non-conflict guarantees (how two devs build in parallel)

1. **Shared files are written once, by the scaffold, and never touched by implementers:**
   `__init__.py`, `_sizes.py`, `_quick_ref.py`. Implementers import from them only.
2. **Each implementer owns exactly one or two whole module files** (fastener / inserts+nuts /
   snap_fit+bearings) and **one data JSON per file**. No two tasks write the same file.
3. **`__init__.py` import list is fixed** by this contract; a module implementer never edits
   it, so no merge collision on the package entry point.
4. **Data schema is fixed** (§4.3); the scaffold ships a JSON-schema validator + a test that
   loads every `data/*.json`. A malformed chart fails CI before it reaches another module.
5. **All size strings funnel through `_sizes.parse()`** and all dims through `SizeChart.get()`,
   so two modules cannot invent divergent parsing/units.
6. **Origin/axis and return-type conventions (§5) are identical across modules**, so a part
   composed of features from different modules subtracts cleanly with no coordinate fixes.

Conflicts are therefore structurally impossible except by two people editing a shared file
they are told not to touch.

---

## 9. Initial size charts (first release — manageable, ~30 profiles)

Metric-first; imperial for fastener + nut where standard charts exist.

| Module | Sizes (v1) | Source chart | Approx profiles |
|--------|-----------|--------------|-----------------|
| fastener | metric M2, M2.5, M3, M4, M5, M6, M8 · imperial #2, #4, #6, #8, #10, 1/4" | ISO 273 (metric clearance), Machinery's Handbook / ASME B18.2.8 (imperial) | 13 |
| inserts | M2, M2.5, M3, M4, M5, M6, M8 (1–2 lengths each: standard + short for M3/M4) | CNC Kitchen / ruthex / McMaster-Carr | 9 |
| nuts (nut_trap) | hex M2–M8 (ISO 4032), square M3–M6 (DIN 562); imperial hex #4-40, #6-32, #8-32, #10-24, 1/4-20 | ISO 4032 / DIN 562 | ~12 |
| nuts (thread_forming) | M2, M2.5, M3, M4, M5, M6 (soft + hard pilot) | EJOT/Bossard-style, genericized | 6 |
| snap_fit | n/a — parametric, 3 recommended CantileverSpec configs | n/a (design guideline) | 3 (configs, not sizes) |
| bearings | 623, 624, 625, 626, 627, 608, 686, 688, 695, 6900, 6901, 6902 | ISO 15 / SKF | 12 |

Total ≈ 43 profiles incl. the imperial nut set; ≈ 25–30 if imperial nut types are deferred
to v1.1. **Recommendation: ship metric-only for inserts/thread-forming/bearings in v1,
metric+imperial for fastener and nut traps.** Defer imperial inserts (M-gauge heat-set in
inch sizes) to v1.1 — they are a small, rare set and add chart maintenance for little
beginner demand.

---

## 10. Open questions (Chuck / Chief of Staff to confirm)

1. **Package name `bd_hardware`** — accept, or prefer another (e.g. `bd_fasteners`,
   `bd_joinery`)? One rename decision, made now, costs nothing.
2. **build123d minimum version.** Target latest stable (v0.10+ per build123d docs; bd_warehouse
   tracks v0.13). Pin at scaffold time — confirm v0.10 floor is acceptable so the lib runs on
   the widest installs.
3. **Builder-mode wrappers.** The contract is function-first (pure `Solid`/`Part` returns).
   Should the scaffold ALSO ship `BuildPart` context-manager conveniences (`.insert_hole(...)`
   style) in v1, or defer? Recommendation: defer to v1.1; keep v1 pure and simple.
4. **License.** bd_warehouse is Apache-2.0, threads.scad CC0, Catch'n'Hole MIT. Propose MIT
   for this library (simplest for a beginner-facing utility). Confirm.
5. **Data provenance.** Size charts above are from public standard references (ISO 4032,
   ISO 273, SKF, CNC Kitchen/ruthex published dims). If the library will be distributed,
   confirm we're comfortable shipping dimension tables derived from these (all are either
   open standards or vendor-published spec sheets) rather than licensing a proprietary chart.

---

## Appendix A — quick summary for the scaffold task

- Package: `bd_hardware`, 5 modules + 2 shared (`_sizes`, `_quick_ref`).
- Shared model: frozen `Size(nominal, units, clearance_class, source)` + `SizeChart` JSON loader.
- Size strings: `"M3"`, `"M3-0.5"`, `"#6-32"`, `"608"`; single `parse()` entry point.
- Every module: `quick_ref() -> str` with the fixed `== module == / USAGE / SIZES` format.
- Cutters return `Solid` (or `Part` for compound), opening at Z=0, +Z depth, `depth=None = through`.
- Non-conflict: shared files written once; each dev owns whole files; fixed `__init__` and JSON schema.
