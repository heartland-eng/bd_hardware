"""End-to-end geometry verification.

Builds a real part (a mounting plate with clearance holes and one
counterbore), exports STL, then reloads the mesh with trimesh and asserts it
is watertight with positive volume — the acceptance gate for a CAD feature.

This test touches the OCP kernel, so it is slower than the pure-data tests.
"""

import sys
import os
import tempfile

import build123d as bd
import numpy as np
import trimesh

from bd_hardware import through_hole, counterbore_hole


def _export_stl(part: bd.Part, path: str) -> None:
    bd.export_stl(part, path)


def test_plate_with_clearance_holes_is_watertight():
    plate = bd.Box(40.0, 40.0, 5.0)
    for x in (-15.0, 15.0):
        for y in (-15.0, 15.0):
            plate -= through_hole(3.0, 5.0).move(bd.Location((x, y, 0.0)))

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "plate.stl")
        bd.export_stl(plate, path)
        mesh = trimesh.load(path)

    assert mesh.is_watertight, "plate STL is not watertight"
    assert mesh.volume > 0, "plate volume must be positive"
    # 40x40x5 = 8000 mm^3 minus four M3-normal (d=3.4) holes through 5 mm.
    hole_vol = 4 * np.pi * (3.4 / 2) ** 2 * 5.0
    assert np.isclose(mesh.volume, 8000.0 - hole_vol, rtol=0.01)


def test_counterbore_plate_is_watertight():
    plate = bd.Box(20.0, 20.0, 5.0)
    tool = counterbore_hole(
        3.0, 5.0, head_diameter=6.0, head_depth=3.0
    ).move(bd.Location((0.0, 0.0, 0.0)))
    plate -= tool

    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "cb_plate.stl")
        bd.export_stl(plate, path)
        mesh = trimesh.load(path)

    assert mesh.is_watertight, "counterbore plate STL is not watertight"
    assert mesh.volume > 0, "counterbore plate volume must be positive"
