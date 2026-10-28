"""Acceptance: clearance holes are generated from the ``fastener_clearance``
size chart and match the shared conventions.

``clearance_hole`` shank diameter = chart clearance column for the class
(close/normal/loose). Default depth = 4x the clearance diameter. ``head="none"``
is a plain through-bore; ``head="counterbore"`` adds a coaxial socket-head
recess (diameter ``cbore + head_clearance``, depth ``0.5 x cbore``);
``head="countersink"`` adds a 90-degree conical recess (top diameter
``csink + head_clearance``).
"""

import pytest
from build123d import Box, Solid

from bd_hardware import fastener
from bd_hardware._sizes import SizeChart

CLEARANCE_CLASSES = ("close", "normal", "loose")
HEADS = ("none", "counterbore", "countersink")

# fastener._THROUGH_DEPTH_FACTOR and _CBORE_DEPTH_FACTOR.
THROUGH_DEPTH_FACTOR = 4.0
CBORE_DEPTH_FACTOR = 0.5


def _size(solid: Solid):
    return solid.bounding_box().size


def _dims(size: str):
    return SizeChart("fastener_clearance").get(size)


# -- clearance_hole: geometry ----------------------------------------------

def test_clearance_hole_returns_solid():
    assert isinstance(fastener.clearance_hole("M3-0.5"), Solid)


def test_default_is_normal_clearance():
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5")
    assert _size(hole).X == pytest.approx(d["normal"])


@pytest.mark.parametrize("cls", CLEARANCE_CLASSES)
def test_clearance_class_diameter(cls):
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5", clearance_class=cls)
    assert _size(hole).X == pytest.approx(d[cls])


def test_default_depth_is_through_factor():
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5")
    assert _size(hole).Z == pytest.approx(THROUGH_DEPTH_FACTOR * d["normal"])


def test_explicit_depth():
    hole = fastener.clearance_hole("M3-0.5", depth=12.0)
    assert _size(hole).Z == pytest.approx(12.0)


def test_head_none_is_plain_through_bore():
    # a plain through-bore: X extent == clearance diameter (no head feature).
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5", head="none")
    assert _size(hole).X == pytest.approx(d["normal"])


def test_counterbore_diameter():
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5", head="counterbore")
    assert _size(hole).X == pytest.approx(d["cbore"])


def test_counterbore_head_clearance_adds_diameter():
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5", head="counterbore", head_clearance=0.4)
    assert _size(hole).X == pytest.approx(d["cbore"] + 0.4)


def test_countersink_diameter():
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5", head="countersink")
    assert _size(hole).X == pytest.approx(d["csink"])


def test_countersink_head_clearance_adds_diameter():
    d = _dims("M3-0.5")
    hole = fastener.clearance_hole("M3-0.5", head="countersink", head_clearance=0.4)
    assert _size(hole).X == pytest.approx(d["csink"] + 0.4)


@pytest.mark.parametrize("head", HEADS)
def test_every_chart_size_generates(head):
    chart = SizeChart("fastener_clearance")
    for nominal in chart.sizes():
        dims = chart.get(nominal)
        hole = fastener.clearance_hole(nominal, head=head)
        assert isinstance(hole, Solid)
        # in-plane extent equals the head feature when present, else the shank.
        if head == "counterbore":
            expected = dims["cbore"]
        elif head == "countersink":
            expected = dims["csink"]
        else:
            expected = dims["normal"]
        assert _size(hole).X == pytest.approx(expected)


# -- clearance_hole: subtractability ----------------------------------------

@pytest.mark.parametrize("head", HEADS)
def test_clearance_hole_is_subtractable(head):
    block = Box(20, 20, 20)
    before = block.volume
    block -= fastener.clearance_hole("M4-0.7", head=head)
    assert block.volume < before


# -- clearance_hole: validation ---------------------------------------------

def test_invalid_size_raises():
    with pytest.raises(ValueError):
        fastener.clearance_hole("M99")


def test_invalid_clearance_class_raises():
    with pytest.raises(ValueError):
        fastener.clearance_hole("M3-0.5", clearance_class="banana")


def test_invalid_head_raises():
    with pytest.raises(ValueError):
        fastener.clearance_hole("M3-0.5", head="oval")


def test_negative_head_clearance_raises():
    with pytest.raises(ValueError):
        fastener.clearance_hole("M3-0.5", head="counterbore", head_clearance=-0.1)


def test_nonpositive_depth_raises():
    with pytest.raises(ValueError):
        fastener.clearance_hole("M3-0.5", depth=0.0)


# -- quick_ref ---------------------------------------------------------------

def test_quick_ref_lists_sizes_and_usage():
    text = fastener.quick_ref()
    assert "USAGE" in text and "SIZES" in text
    assert "clearance_hole" in text
    for header in ("Size", "Close", "Normal", "Loose", "CBoreØ", "CSinkØ"):
        assert header in text
    for nominal in SizeChart("fastener_clearance").sizes():
        assert nominal in text
