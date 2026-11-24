"""bd_hardware — a function-first hardware feature library for build123d.

Clearance holes, insert pockets, nut traps, bosses, snap fits, bearing
pockets — each feature is a plain function that returns build123d geometry
for you to position and boolean, rather than a class that owns your part.

Units are millimetres throughout.
"""

from ._standards import clearance_diameter
from .holes import counterbore_hole, through_hole

__version__ = "0.1.0"

__all__ = [
    "clearance_diameter",
    "through_hole",
    "counterbore_hole",
    "__version__",
]
