"""Acceptance: cantilever + annular snap-fit geometry is generated from
:class:`CantileverSpec` and matches its parametric dimensions.

The hook is a beam (length x width x thickness) with a retention lip that rises
``retention`` above the beam top on a ramp of ``angle`` degrees; the catch is a
slot (beam + clearance) with an undercut ledge of ``retention``; the annular
snap is a revolved ring with an inward lip.
"""

import math

import pytest
from build123d import Solid

from bd_hardware import snap_fit

# snap_fit._SNAP_CLEARANCE (mm, both sides) -- the hook-to-catch allowance.
CLEARANCE = 0.2

SPEC = snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6)


def _size(solid: Solid):
    return solid.bounding_box().size


def _min_radial(solid: Solid) -> float:
    """Minimum distance of any vertex from the Z axis."""
    return min(
        math.hypot(v.X, v.Y)
        for v in solid.vertices()
    )


# -- cantilever hook -------------------------------------------------------


def test_hook_returns_solid():
    assert isinstance(snap_fit.cantilever_hook(SPEC), Solid)


def test_hook_dimensions():
    s = _size(snap_fit.cantilever_hook(SPEC))
    assert s.X == pytest.approx(SPEC.length)
    assert s.Y == pytest.approx(SPEC.width)
    assert s.Z == pytest.approx(SPEC.thickness + SPEC.retention)


def test_hook_retention_is_peak_height():
    hook = snap_fit.cantilever_hook(SPEC)
    assert _size(hook).Z == pytest.approx(SPEC.thickness + SPEC.retention)


def test_hook_root_fillet_reduces_stress_corner():
    # A filleted hook has strictly less volume than an un-filleted one.
    sharp = snap_fit.cantilever_hook(
        snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6, root_fillet=0.0)
    )
    filleted = snap_fit.cantilever_hook(
        snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6, root_fillet=0.5)
    )
    assert filleted.volume < sharp.volume


def test_recommended_configs_generate():
    for spec in (
        snap_fit.CantileverSpec(length=10.0, width=3.0, thickness=1.0, retention=0.4),
        snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6),
        snap_fit.CantileverSpec(length=25.0, width=8.0, thickness=2.5, retention=1.0),
    ):
        hook = snap_fit.cantilever_hook(spec)
        assert hook.volume > 0.0
        assert isinstance(hook, Solid)


# -- cantilever catch ------------------------------------------------------


def test_catch_returns_solid():
    assert isinstance(snap_fit.cantilever_catch(SPEC), Solid)


def test_catch_dimensions():
    s = _size(snap_fit.cantilever_catch(SPEC))
    # slot height = thickness + retention + clearance
    assert s.Z == pytest.approx(SPEC.thickness + SPEC.retention + CLEARANCE)
    # slot width = width + 2*clearance
    assert s.Y == pytest.approx(SPEC.width + 2.0 * CLEARANCE)


def test_catch_undercut_depth():
    # undercut ledge extends `retention + clearance` beyond the beam reach.
    s = _size(snap_fit.cantilever_catch(SPEC))
    assert s.X == pytest.approx(SPEC.length + SPEC.retention + CLEARANCE)


def test_catch_is_subtractable():
    from build123d import Box

    block = Box(30, 30, 10)
    before = block.volume
    block -= snap_fit.cantilever_catch(SPEC)
    assert block.volume < before


# -- annular snap ----------------------------------------------------------


def test_annular_returns_solid():
    assert isinstance(snap_fit.annular_snap(10.0, thickness=2.0, retention=1.0), Solid)


def test_annular_outer_and_height():
    ann = snap_fit.annular_snap(10.0, thickness=2.0, retention=1.0)
    s = _size(ann)
    assert s.X == pytest.approx(2.0 * (10.0 + 2.0))  # outer diameter
    assert s.Z == pytest.approx(2.0)  # axial height == thickness


def test_annular_retention_reaches_inward():
    ann = snap_fit.annular_snap(10.0, thickness=2.0, retention=1.0)
    assert _min_radial(ann) == pytest.approx(10.0 - 1.0)


# -- validation ------------------------------------------------------------


def test_hook_invalid_length_raises():
    with pytest.raises(ValueError):
        snap_fit.cantilever_hook(snap_fit.CantileverSpec(length=0.0, width=5.0, thickness=1.5, retention=0.6))


def test_hook_invalid_retention_raises():
    with pytest.raises(ValueError):
        snap_fit.cantilever_hook(snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.0))


def test_hook_invalid_angle_raises():
    with pytest.raises(ValueError):
        snap_fit.cantilever_hook(snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6, angle=90.0))


def test_hook_ramp_exceeding_length_raises():
    # retention 5 at 10 deg -> ramp ~28mm > length 10
    with pytest.raises(ValueError):
        snap_fit.cantilever_hook(
            snap_fit.CantileverSpec(length=10.0, width=5.0, thickness=1.5, retention=5.0, angle=10.0)
        )


def test_annular_retention_exceeding_radius_raises():
    with pytest.raises(ValueError):
        snap_fit.annular_snap(10.0, thickness=2.0, retention=10.0)


def test_annular_invalid_thickness_raises():
    with pytest.raises(ValueError):
        snap_fit.annular_snap(10.0, thickness=0.0, retention=1.0)


# -- quick_ref -------------------------------------------------------------


def test_quick_ref_lists_configs_and_usage():
    text = snap_fit.quick_ref()
    assert "USAGE" in text and "SIZES" in text
    assert "cantilever_hook" in text
    for config in ("small", "medium", "large"):
        assert config in text
    for header in ("Config", "Length", "Width", "Thickness", "Retention"):
        assert header in text
