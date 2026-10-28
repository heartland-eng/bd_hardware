"""Verify bd_hardware fastener module: generate clearance_hole cutters (through,
counterbore, countersink) and a combined demo plate, export STEP + STL, and
check the meshes are watertight with positive volume. This is the acceptance
gate for the part drop.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import trimesh
from build123d import Box, Pos, export_step, export_stl

from bd_hardware import fastener

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "verify_out")
os.makedirs(OUT, exist_ok=True)

results = []


def check(name, solid):
    step = os.path.join(OUT, name + ".step")
    stl = os.path.join(OUT, name + ".stl")
    export_step(solid, step)
    export_stl(solid, stl)
    m = trimesh.load(stl, force="mesh")
    ok = bool(m.is_watertight) and m.volume > 0.0
    results.append((name, ok, m.is_watertight, m.volume))
    print(f"{name}: watertight={m.is_watertight} volume={m.volume:.2f} mm^3  {'OK' if ok else 'FAIL'}")


# 1. through-bore clearance hole (M3, normal clearance)
check("clearance_hole_m3", fastener.clearance_hole("M3-0.5"))

# 2. SHCS counterbore cutter (M3)
check("counterbore_m3", fastener.clearance_hole("M3-0.5", head="counterbore"))

# 3. flat-head countersink cutter (M3, 90-deg)
check("countersink_m3", fastener.clearance_hole("M3-0.5", head="countersink"))

# 4. combined demo: plate with a through hole, a counterbore, and a countersink
plate = Box(50, 30, 8)
plate -= Pos(-16, 0, 0) * fastener.clearance_hole("M4-0.7")
plate -= Pos(0, 0, 0) * fastener.clearance_hole("M4-0.7", head="counterbore")
plate -= Pos(16, 0, 0) * fastener.clearance_hole("M4-0.7", head="countersink")
check("demo_plate", plate)

print()
print("=== SUMMARY ===")
all_ok = all(ok for _, ok, *_ in results)
for name, ok, wt, vol in results:
    print(f"  {name:20s} watertight={wt!s:5s} volume={vol:>10.2f} mm^3  {'OK' if ok else 'FAIL'}")
print(f"ALL PASS: {all_ok}")

sys.stdout.flush()
os._exit(0 if all_ok else 1)
