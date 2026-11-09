# bd_hardware

Function-first hardware feature library for [build123d](https://build123d.readthedocs.io/) —
clearance holes, insert pockets, nut traps, bosses, snap fits, bearing pockets.

Each feature is a plain function that returns a watertight `build123d.Part`, so
you can fuse it into your own designs with a single boolean union. Dimensions
are named parameters with sensible defaults; change a value, re-run, done.

## Features

| Module | Feature | Description |
| ------ | ------- | ----------- |
| `inserts` | `insert_boss()` | Cylindrical boss with a counterbored pocket for a heat-set threaded insert, plus a through hole for the screw |

## Install

```bash
pip install -e .
```

## Quick start

```python
import build123d as bd
from build123d import Pos

from bd_hardware import STANDARD_INSERTS, insert_boss

boss = insert_boss(STANDARD_INSERTS["M3"])

# Fuse onto a plate (overlap so the union stays manifold)
plate = bd.Box(30, 30, 3)
plate += Pos(0, 0, 3 - 0.5) * boss
bd.export_stl(plate, "plate.stl")
```

`STANDARD_INSERTS` carries typical brass-insert dimensions for M2, M2.5, M3,
M4 and M5. **Confirm them against your insert's datasheet** — these are
nominal and vary by manufacturer.

## Examples

```bash
python examples/heat_set_insert_plate.py
```

writes a corner-mounted M3 insert plate as both `.step` and `.stl`.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests build each standard insert and assert the result is manifold with
positive volume, and that the exported STL is watertight with consistent
winding.

## License

MIT — see [LICENSE](LICENSE).
