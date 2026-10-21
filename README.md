# bd_hardware

A lightweight, function-first hardware **feature** library for
[build123d](https://build123d.readthedocs.io/): screw clearance holes, heat-set
insert pockets, nut traps, thread-forming bosses, snap fits, and press-fit
bearing pockets — keyed to standard metric and imperial sizes.

```python
import bd_hardware as bdh

bdh.quick_ref()            # every module's cheatsheet
bdh.quick_ref("inserts")   # just one module
```

Deliberately simpler than `bd_warehouse`: one import, one function call per
feature, plain string sizes (`"M3"`, `"#6-32"`, `"608"`), and a one-call
discovery surface. No class hierarchy, no CSV internals, no `eval()` parsing.

## Layout

```
bd_hardware/
  __init__.py     # re-exports the 5 modules + package-level quick_ref dispatcher
  _sizes.py       # shared size model: Size, SizeChart, parse()  (scaffold-owned)
  _quick_ref.py   # shared quick_ref formatter + dispatch       (scaffold-owned)
  fastener.py     # screw clearance / counterbore / countersink holes
  inserts.py      # heat-set insert pockets
  nuts.py         # nut traps + thread-forming bosses
  snap_fit.py     # cantilever + annular snap fits
  bearings.py     # press-fit bearing pockets
  data/           # JSON size charts (mm), one per chart, schema-validated
```

The underscore-prefixed `_sizes.py` and `_quick_ref.py` are shared
infrastructure, written once by the scaffold and **not** edited by module
implementers (see `API_CONTRACT.md` §8).

## Install

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"        # editable + pytest (build123d is a hard dep)
```

## Test

```bash
python -m pytest
```

The test suite verifies the package installs, every module imports, every
`quick_ref()` returns the fixed `== module == / USAGE / SIZES` format, and every
`data/*.json` chart loads through the schema-validating `SizeChart`.

## Status

Implemented modules (geometry lands via `build123d`):

- `snap_fit.py` — cantilever + annular snap fits
- `bearings.py` — press-fit bearing pockets
- `nuts.py` — nut traps + thread-forming bosses

Still stubbed (pending module-owner tasks): `fastener.py` (screw clearance /
counterbore / countersink) and `inserts.py` (heat-set insert pockets).

The size charts are **nominal starter data** derived from public standard
references (ISO 273 / ISO 4762 / ISO 10642, ISO 4032 / DIN 562, ISO 15 / SKF,
CNC Kitchen / ruthex published dims). Verify against the source before using for
production parts.

## Open questions (pending owner confirmation)

1. Package name `bd_hardware` — accept, or rename once in the scaffold.
2. `build123d` minimum version — `>=0.10` floor proposed.
3. Builder-mode (`BuildPart`) wrappers — deferred to v1.1 (v1 is pure functions).
4. Data provenance — confirm comfort shipping standard-derived dimension tables.
