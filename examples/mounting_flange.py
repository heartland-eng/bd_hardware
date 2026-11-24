"""Example: a mounting flange with clearance holes and a counterbore.

Run from the repo root:

    python examples/mounting_flange.py

Exports ``examples/out/flange.step`` and ``examples/out/flange.stl`` and
prints a watertight/volume check. Demonstrates the function-first pattern:
the library returns cut tools, the caller positions and booleans them.
"""

import os
import sys

import build123d as bd
import trimesh

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bd_hardware import through_hole, counterbore_hole  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "out")
os.makedirs(OUT, exist_ok=True)

# --- Parametric spec (edit these, re-run) -------------------------------
FLANGE_W, FLANGE_H, FLANGE_T = 60.0, 40.0, 6.0       # flange envelope, mm
SCREW = 3.0                                          # M3 fasteners
FIT = "normal"                                       # ISO 273 medium
CORNER_OFFSET = (12.0, 8.0)                           # hole pattern inset
COUNTERBORE_HEAD_D, COUNTERBORE_HEAD_T = 6.0, 3.0    # socket cap head
# ------------------------------------------------------------------------

flange = bd.Box(FLANGE_W, FLANGE_H, FLANGE_T)

# Four plain clearance holes at the corners.
for sx in (-1, 1):
    for sy in (-1, 1):
        x = sx * (FLANGE_W / 2 - CORNER_OFFSET[0])
        y = sy * (FLANGE_H / 2 - CORNER_OFFSET[1])
        flange -= through_hole(SCREW, FLANGE_T, fit=FIT).move(
            bd.Location((x, y, 0.0))
        )

# One counterbored hole dead-centre (for a locating screw).
flange -= counterbore_hole(
    SCREW,
    FLANGE_T,
    head_diameter=COUNTERBORE_HEAD_D,
    head_depth=COUNTERBORE_HEAD_T,
).move(bd.Location((0.0, 0.0, 0.0)))

step_path = os.path.join(OUT, "flange.step")
stl_path = os.path.join(OUT, "flange.stl")
bd.export_step(flange, step_path)
bd.export_stl(flange, stl_path)

mesh = trimesh.load(stl_path, force="mesh")
print(f"STEP    -> {step_path}")
print(f"STL     -> {stl_path}")
print(f"watertight: {mesh.is_watertight}")
print(f"volume    : {mesh.volume:.2f} mm^3")
