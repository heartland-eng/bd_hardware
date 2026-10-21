"""Verify bd_hardware nuts module: generate nut_trap + thread_forming_boss
cutters and a combined demo part, export STEP + STL, and check the meshes are
watertight with positive volume. This is the acceptance gate for the part drop.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import trimesh
from build123d import Box, Pos, export_step, export_stl

from bd_hardware import nuts

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
    results.append((name, ok, m.is_watertight, round(m.volume, 2), m.volume))
    print(f"{name}: watertight={m.is_watertight} volume={m.volume:.2f} mm^3  {'OK' if ok else 'FAIL'}")


# 1. nut trap cutter (hexagon M3, normal clearance)
check("nut_trap_m3", nuts.nut_trap("M3-0.5"))

# 2. thread-forming boss cutter (M3 soft)
check("thread_forming_boss_m3", nuts.thread_forming_boss("M3-0.5"))

# 3. combined demo: plate with a captured nut trap and a thread-forming boss
plate = Box(40, 30, 8)
plate -= Pos(15, 0, 0) * nuts.nut_trap("M4-0.7", capture=True)
plate -= Pos(-15, 0, 0) * nuts.thread_forming_boss("M4-0.7", material="soft")
check("demo_plate", plate)

print()
print("=== SUMMARY ===")
all_ok = all(ok for _, ok, *_ in results)
for name, ok, wt, vol, _ in results:
    print(f"  {name:28s} watertight={wt!s:5s} volume={vol:>10.2f} mm^3  {'OK' if ok else 'FAIL'}")
print(f"ALL PASS: {all_ok}")

sys.stdout.flush()
os._exit(0 if all_ok else 1)
