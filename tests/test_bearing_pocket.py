"""End-to-end test: build the part, export an STL, and verify it is watertight.

Requires the dev extras (``pip install -e .[dev]``) so build123d and trimesh
are available. Run with::

    pytest -q
"""

import os
import sys
import tempfile

import pytest
from build123d import export_stl

from bd_hardware import bearing_pocket_block
from bd_hardware.bearing_pocket import BearingPocketSpec


def _mesh_properties(stl_path: str) -> dict:
    import trimesh

    mesh = trimesh.load(stl_path)
    return {
        "watertight": bool(mesh.is_watertight),
        "volume": float(mesh.volume),
        "bounds": [float(v) for v in mesh.bounds.reshape(-1).tolist()],
        "vertices": len(mesh.vertices),
        "faces": len(mesh.faces),
    }


def test_default_bearing_pocket_is_watertight():
    part = bearing_pocket_block()

    with tempfile.TemporaryDirectory() as tmp:
        stl = os.path.join(tmp, "part.stl")
        export_stl(part, stl)

        props = _mesh_properties(stl)

        assert props["watertight"], f"mesh not watertight: {props}"
        assert props["volume"] > 0, f"expected positive volume: {props}"
        # Bounds sanity check against the default 608 dimensions.
        assert props["bounds"][2] == pytest.approx(
            0.0, abs=0.1
        ), f"expected base floor near z=0: {props}"
        assert props["bounds"][5] == pytest.approx(
            4.0 + 7.0, abs=0.1
        ), f"expected total height ~11 mm: {props}"


def test_custom_spec_is_parametric():
    spec = BearingPocketSpec(bearing_od=10.0, bearing_id=3.0, bearing_w=4.0)
    part = bearing_pocket_block(spec)

    with tempfile.TemporaryDirectory() as tmp:
        stl = os.path.join(tmp, "part.stl")
        export_stl(part, stl)

        props = _mesh_properties(stl)
        assert props["watertight"]
        # Total height tracks base_h + bearing_w = 4 + 4 = 8 mm.
        assert props["bounds"][5] == pytest.approx(8.0, abs=0.1)


if __name__ == "__main__":
    sys.exit(pytest.main(["-q"]))
