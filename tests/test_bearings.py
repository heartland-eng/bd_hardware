"""Acceptance: press-fit bearing pockets are generated from the ``bearings``
size chart and match the press-fit interference classes from ``_sizes``.

Pocket diameter = nominal OD + 2 * interference (light 0.00 / medium -0.02 /
heavy -0.04 on the radius). Default depth = bearing width (the seat). With
``bore_through=True`` the shaft bore is pierced at the shaft-clearance class.
"""

import math

import pytest
from build123d import Part, Solid

from bd_hardware import bearings
from bd_hardware._sizes import BEARING_INTERFERENCE, SizeChart

# bearings._SHAFT_CLEARANCE (mm, on the diameter) by clearance class.
SHAFT_CLEARANCE = {"close": 0.05, "normal": 0.15, "loose": 0.30}


def _diam(solid: Solid) -> float:
    return solid.bounding_box().size.X


def _height(solid: Solid) -> float:
    return solid.bounding_box().size.Z


def _dims(size: str):
    return SizeChart("bearings").get(size)


# -- pocket ----------------------------------------------------------------


def test_pocket_returns_solid():
    assert isinstance(bearings.bearing_pocket("608"), Solid)


@pytest.mark.parametrize("fit,interference", sorted(BEARING_INTERFERENCE.items()))
def test_pocket_pressfit_diameter(fit, interference):
    d = _dims("608")
    pocket = bearings.bearing_pocket("608", fit=fit)
    assert _diam(pocket) == pytest.approx(d["od"] + 2.0 * interference)


def test_pocket_default_depth_is_bearing_width():
    d = _dims("608")
    pocket = bearings.bearing_pocket("608")
    assert _height(pocket) == pytest.approx(d["width"])


def test_pocket_explicit_depth():
    pocket = bearings.bearing_pocket("608", depth=10.0)
    assert _height(pocket) == pytest.approx(10.0)


def test_pocket_shoulder_is_blind():
    # Without bore_through, the pocket is a single blind cylinder (flat shoulder).
    pocket = bearings.bearing_pocket("608")
    assert pocket.volume == pytest.approx(
        math.pi * (_diam(pocket) / 2.0) ** 2 * _height(pocket), rel=1e-6
    )


def test_pocket_every_chart_size_is_generated_from_data():
    chart = SizeChart("bearings")
    for nominal in chart.sizes():
        dims = chart.get(nominal)
        for fit in BEARING_INTERFERENCE:
            pocket = bearings.bearing_pocket(nominal, fit=fit)
            assert _diam(pocket) == pytest.approx(
                dims["od"] + 2.0 * BEARING_INTERFERENCE[fit]
            )
            assert _height(pocket) == pytest.approx(dims["width"])


def test_pocket_pressfit_is_tighter_than_light():
    light = _diam(bearings.bearing_pocket("608", fit="light"))
    medium = _diam(bearings.bearing_pocket("608", fit="medium"))
    heavy = _diam(bearings.bearing_pocket("608", fit="heavy"))
    assert light > medium > heavy  # heavier press-fit -> smaller pocket


# -- bore through ----------------------------------------------------------


def test_bore_through_pierces_shaft_hole():
    pocket = bearings.bearing_pocket("608", bore_through=True)
    d = _dims("608")
    # bore extends one OD past the seat -> total height > seat depth.
    assert _height(pocket) == pytest.approx(d["width"] + d["od"])


@pytest.mark.parametrize("bore_class,clearance", sorted(SHAFT_CLEARANCE.items()))
def test_bore_through_clearance_class(bore_class, clearance):
    d = _dims("608")
    pocket = bearings.bearing_pocket("608", bore_through=True, bore_class=bore_class)
    # the through-bore diameter is the narrowest in-plane feature of the cutter,
    # but the cutter's max diameter is still the pocket. Check the bore radius
    # directly via the stepped-solid geometry: the bore diameter equals
    # bore + shaft clearance.
    bore_d = d["bore"] + clearance
    # the cutter is the union of pocket (big) + bore (small); its min Z-section
    # radius (below the seat) is the bore radius. Verify via the volume relation:
    seat = d["width"]
    bore_h = seat + d["od"]
    vol = (
        math.pi * (d["od"] / 2.0 + BEARING_INTERFERENCE["medium"]) ** 2 * seat
        + math.pi * (bore_d / 2.0) ** 2 * (bore_h - seat)
    )
    assert pocket.volume == pytest.approx(vol, rel=1e-6)


def test_bore_through_is_subtractable():
    from build123d import Box

    block = Box(40, 40, 30)
    before = block.volume
    block -= bearings.bearing_pocket("608", bore_through=True)
    assert block.volume < before


# -- positive bearing body -------------------------------------------------


def test_bearing_simple_is_part():
    assert isinstance(bearings.bearing("608"), Part)


def test_bearing_simple_dimensions():
    d = _dims("608")
    b = bearings.bearing("608")
    bb = b.bounding_box()
    assert bb.size.X == pytest.approx(d["od"])
    assert bb.size.Z == pytest.approx(d["width"])


def test_bearing_full_has_multiple_solids():
    d = _dims("608")
    b = bearings.bearing("608", simple=False)
    assert isinstance(b, Part)
    assert len(b.solids()) >= 3  # outer race + inner race + balls


# -- validation ------------------------------------------------------------


def test_invalid_size_raises():
    with pytest.raises(ValueError):
        bearings.bearing_pocket("9999")


def test_invalid_fit_raises():
    with pytest.raises(ValueError):
        bearings.bearing_pocket("608", fit="banana")


def test_invalid_bore_class_raises():
    with pytest.raises(ValueError):
        bearings.bearing_pocket("608", bore_through=True, bore_class="banana")


def test_nonpositive_depth_raises():
    with pytest.raises(ValueError):
        bearings.bearing_pocket("608", depth=0.0)


# -- quick_ref -------------------------------------------------------------


def test_quick_ref_lists_sizes_and_usage():
    chart = SizeChart("bearings")
    text = bearings.quick_ref()
    assert "USAGE" in text and "SIZES" in text
    assert "bearing_pocket" in text
    for nominal in chart.sizes():
        assert nominal in text
    for header in ("Size", "Bore", "OD", "Width", "Light", "Medium", "Heavy"):
        assert header in text
