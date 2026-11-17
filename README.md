# bd_hardware

Function-first hardware feature library for
[build123d](https://github.com/gumyr/build123d) — clearance holes, insert
pockets, nut traps, bosses, snap fits, bearing pockets.

Each feature is a small, parametric function that returns a `build123d.Part`.
Every dimension is a named variable with a source comment, so sizing a feature
for a new part or a different fit is a one-line change — never geometry surgery.

## Features

| Feature | Module | Status |
|---|---|---|
| Bearing pocket block (press/slip-fit bore + shaft hole) | `bd_hardware.bearing_pocket` | shipped |

## Install

From source (requires Python >= 3.10):

```bash
git clone https://github.com/heartland-eng/bd_hardware.git
cd bd_hardware
uv venv .venv --python 3.11 && source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

`build123d` pulls a large OCCT wheel (~300 MB) on first install.

## Quick start

```python
from bd_hardware import bearing_pocket_block

part = bearing_pocket_block()            # default 608 bearing
part.export_step("block.step")           # editable master
part.export_stl("block.stl")             # slice-ready mesh
```

The default builds a block for a 608 ball bearing (22 mm OD × 8 mm bore × 7 mm
wide). Override anything with the spec:

```python
from bd_hardware.bearing_pocket import BearingPocketSpec

spec = BearingPocketSpec(bearing_od=10.0, bearing_id=3.0, bearing_w=4.0)
part = bearing_pocket_block(spec)
```

### BearingPocketSpec parameters (all mm)

| Parameter | Default | Meaning |
|---|---|---|
| `bearing_od` | 22.0 | Bearing outer diameter |
| `bearing_id` | 8.0 | Bearing bore diameter |
| `bearing_w` | 7.0 | Bearing width |
| `pocket_clearance` | 0.20 | Diametral clearance for an FDM slip fit |
| `shaft_clearance` | 0.40 | Diametral clearance on the shaft hole |
| `boss_wall` | 3.0 | Minimum boss wall around the bearing |
| `base_margin` | 8.0 | Base extends past the boss on each side |
| `base_h` | 4.0 | Base plate thickness |
| `overlap` | 0.5 | Boolean overlap that keeps unions manifold |

## Example

```bash
python examples/bearing_pocket.py   # writes bearing_pocket_block.step + .stl
```

## Verify

```bash
python scripts/verify_mesh.py bearing_pocket_block.stl   # watertight + volume check
python scripts/render_preview.py bearing_pocket_block.stl preview.png
pytest -q                                                 # end-to-end test
```

The library's acceptance gate is a **watertight STL with positive volume** —
verified with trimesh after degenerate-face removal. "The script ran" is not
done; a manifold mesh is.

## License

MIT — see [LICENSE](LICENSE).
