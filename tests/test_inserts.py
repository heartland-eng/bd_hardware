"""Tests for the heat-set insert boss feature."""

import build123d as bd
import pytest
import trimesh

from bd_hardware import InsertSpec, STANDARD_INSERTS, insert_boss


@pytest.mark.parametrize("key", list(STANDARD_INSERTS))
def test_standard_insert_boss_is_manifold(key):
    boss = insert_boss(STANDARD_INSERTS[key])
    assert boss.is_manifold
    assert boss.volume > 0


def test_m3_boss_stl_is_watertight(tmp_path):
    boss = insert_boss(STANDARD_INSERTS["M3"])
    stl = tmp_path / "m3_boss.stl"
    bd.export_stl(boss, str(stl))

    mesh = trimesh.load(str(stl), force="mesh")
    assert mesh.is_watertight
    assert mesh.is_winding_consistent
    assert mesh.volume > 0


def test_boss_diameter_validation():
    spec = STANDARD_INSERTS["M3"]
    with pytest.raises(ValueError):
        insert_boss(spec, boss_od=spec.pilot)  # wall collapses


def test_boss_height_validation():
    spec = STANDARD_INSERTS["M3"]
    with pytest.raises(ValueError):
        insert_boss(spec, boss_height=spec.length - 0.5)


def test_insert_spec_validation():
    with pytest.raises(ValueError):
        InsertSpec(od=4.0, length=4.0, screw_clearance=5.0, pilot=4.0, pilot_depth=1.0)
