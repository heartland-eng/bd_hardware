"""Demo: a mounting plate with M3 heat-set inserts in each corner.

Run:    python examples/heat_set_insert_plate.py
Output: heat_set_insert_plate.step  (editable master)
        heat_set_insert_plate.stl   (printable mesh)
"""

import build123d as bd
from build123d import Align, Box, Pos

from bd_hardware import STANDARD_INSERTS, insert_boss

# Bosses are embedded into the plate by this much so the boolean union fuses
# cleanly (coplanar face-to-face unions can leave a non-manifold seam).
OVERLAP = 0.5

spec = STANDARD_INSERTS["M3"]

PLATE_L = 30.0  # plate length (X)
PLATE_W = 30.0  # plate width (Y)
PLATE_T = 3.0   # plate thickness (Z)
MARGIN = 4.0    # boss centre inset from each edge

plate = Box(PLATE_L, PLATE_W, PLATE_T, align=(Align.CENTER, Align.CENTER, Align.MIN))

boss = insert_boss(spec, boss_height=spec.length + 1.5)

for x in (MARGIN, PLATE_L - MARGIN):
    for y in (MARGIN, PLATE_W - MARGIN):
        plate += Pos(x, y, PLATE_T - OVERLAP) * boss

bd.export_step(plate, "heat_set_insert_plate.step")
bd.export_stl(plate, "heat_set_insert_plate.stl")

print(f"volume   = {plate.volume:.3f} mm^3")
print(f"manifold = {plate.is_manifold}")
print("wrote heat_set_insert_plate.step and heat_set_insert_plate.stl")
