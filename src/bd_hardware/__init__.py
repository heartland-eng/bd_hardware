"""bd_hardware — function-first hardware features for build123d.

The library ships individual, parametric hardware features (clearance holes,
insert pockets, nut traps, bosses, snap fits, bearing pockets) as small,
composable functions that each return a build123d ``Part``.
"""

from bd_hardware.bearing_pocket import bearing_pocket_block

__all__ = ["bearing_pocket_block"]
__version__ = "0.1.0"
