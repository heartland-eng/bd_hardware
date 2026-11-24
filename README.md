# bd_hardware

Function-first hardware feature library for
[build123d](https://build123d.readthedocs.io/) — clearance holes, insert
pockets, nut traps, bosses, snap fits, bearing pockets.

Every feature is a **plain function** that returns build123d geometry for
*you* to position and boolean. They never mutate or assume a specific part:
you bring the geometry, the library hands you the cut tool / boss / pocket.

Units are millimetres throughout.

## Install

```bash
pip install -e .
```

## Quick start

```python
import build123d as bd
from bd_hardware import through_hole

plate = bd.Box(40, 40, 5)                    # a 40x40x5 mounting plate
for x in (-15, 15):
    for y in (-15, 15):
        plate -= through_hole(3.0, 5.0).move(bd.Location((x, y, 0)))

bd.export_step(plate, "plate.step")
bd.export_stl(plate, "plate.stl")
```

## Features

### Clearance holes (`bd_hardware.holes`)

- `clearance_diameter(nominal, fit="normal")` — hole diameter for a metric
  screw size. Fits follow ISO 273: `"close"` (fine), `"normal"` (medium),
  `"loose"` (coarse).
- `through_hole(nominal, depth, fit="normal")` — a straight through-hole cut
  tool (rod).
- `counterbore_hole(nominal, depth, fit="normal", head_diameter, head_depth)`
  — a stepped through-hole + recessed counterbore cut tool.

```python
from bd_hardware import counterbore_hole

# M3 socket-head screw, 5 mm wall, recessed flush
tool = counterbore_hole(3.0, 5.0, head_diameter=6.0, head_depth=3.0)
```

## Developing

```bash
pip install -e ".[test]"
pytest
```

Tests exercise real parameter sets end-to-end, including exporting STL and
asserting the resulting mesh is watertight with positive volume.

## License

MIT — see [LICENSE](LICENSE).
