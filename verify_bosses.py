"""Verify bd_hardware bosses module: generate screw_boss posts (soft, hard,
countersink) and a combined demo plate, export STEP + STL, and check the meshes
are watertight with positive volume. This is the acceptance gate for the part
drop.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import trimesh
from build123d import Box, Pos, export_step, export_stl

from bd_hardware import bosses

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


# 1. self-tapping screw boss (M3, soft material, plain pilot)
check("screw_boss_m3_soft", bosses.screw_boss("M3-0.5"))

# 2. self-tapping screw boss (M3, hard material)
check("screw_boss_m3_hard", bosses.screw_boss("M3-0.5", material="hard"))

# 3. self-tapping screw boss with countersunk pilot mouth
check("screw_boss_m3_csink", bosses.screw_boss("M3-0.5", countersink=True))

# 4. combined demo: plate with two bosses fused on top (additive feature)
plate = Box(40, 30, 4)
plate = plate.fuse(Pos(-12, 0, 0) * bosses.screw_boss("M4-0.7"))
plate = plate.fuse(Pos(12, 0, 0) * bosses.screw_boss("M4-0.7", countersink=True))
check("demo_plate", plate)

print()
print("=== SUMMARY ===")
all_ok = all(ok for _, ok, *_ in results)
for name, ok, wt, vol in results:
    print(f"  {name:24s} watertight={wt!s:5s} volume={vol:>10.2f} mm^3  {'OK' if ok else 'FAIL'}")
print(f"ALL PASS: {all_ok}")

sys.stdout.flush()
os._exit(0 if all_ok else 1)
