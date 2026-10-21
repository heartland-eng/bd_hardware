"""Acceptance: nut traps and thread-forming bosses are generated from the
``nuts`` and ``thread_forming`` size charts and match the shared conventions.

``nut_trap`` across-flats = chart AF + clearance class (close/normal/loose added
to the across-flats). Default depth = the nut height (the seat). ``sidecut=True``
opens the pocket on +X; ``capture=True`` adds a coaxial screw-tip relief past the
seat. ``thread_forming_boss`` is a ``boss_od`` boss cavity with a pilot hole
(diameter per material) drilled through its floor and one pilot diameter deeper.
"""

import math

import pytest
from build123d import Box, Solid

from bd_hardware import nuts
from bd_hardware._sizes import SizeChart

# nuts._NUT_CLEARANCE (mm, both sides) by clearance class.
NUT_CLEARANCE = {"close": 0.05, "normal": 0.2, "loose": 0.4}

# nuts._HEIGHT_FACTOR by nut type (relative to the ISO 4032 hexagon height).
HEIGHT_FACTOR = {"hexagon": 1.0, "square": 1.0, "hexagon_thin": 0.65, "hexagon_lock": 1.5}


def _size(solid: Solid):
    return solid.bounding_box().size


def _dims(size: str):
    return SizeChart("nuts").get(size)


def _tf_dims(size: str):
    return SizeChart("thread_forming").get(size)


# -- nut_trap: geometry ----------------------------------------------------

def test_nut_trap_returns_solid():
    assert isinstance(nuts.nut_trap("M3-0.5"), Solid)


def test_nut_trap_across_flats_default_normal():
    d = _dims("M3-0.5")
    trap = nuts.nut_trap("M3-0.5")
    assert _size(trap).X == pytest.approx(d["af"] + NUT_CLEARANCE["normal"])


@pytest.mark.parametrize("cls,clearance", sorted(NUT_CLEARANCE.items()))
def test_nut_trap_clearance_class(cls, clearance):
    d = _dims("M3-0.5")
    trap = nuts.nut_trap("M3-0.5", clearance_class=cls)
    assert _size(trap).X == pytest.approx(d["af"] + clearance)


def test_nut_trap_default_depth_is_nut_height():
    d = _dims("M3-0.5")
    trap = nuts.nut_trap("M3-0.5")
    assert _size(trap).Z == pytest.approx(d["height"])


def test_nut_trap_explicit_depth():
    trap = nuts.nut_trap("M3-0.5", depth=10.0)
    assert _size(trap).Z == pytest.approx(10.0)


@pytest.mark.parametrize("nut_type,factor", sorted(HEIGHT_FACTOR.items()))
def test_nut_trap_nut_type_height(nut_type, factor):
    d = _dims("M3-0.5")
    trap = nuts.nut_trap("M3-0.5", nut_type=nut_type)
    assert _size(trap).Z == pytest.approx(d["height"] * factor)


def test_nut_trap_square_is_square_section():
    trap = nuts.nut_trap("M3-0.5", nut_type="square")
    s = _size(trap)
    assert s.X == pytest.approx(s.Y)  # square cross-section
    assert s.X == pytest.approx(_dims("M3-0.5")["af"] + NUT_CLEARANCE["normal"])


def test_nut_trap_every_chart_size_generates():
    chart = SizeChart("nuts")
    for nominal in chart.sizes():
        dims = chart.get(nominal)
        trap = nuts.nut_trap(nominal)
        assert _size(trap).X == pytest.approx(dims["af"] + NUT_CLEARANCE["normal"])
        assert _size(trap).Z == pytest.approx(dims["height"] * HEIGHT_FACTOR["hexagon"])


# -- nut_trap: sidecut + capture ------------------------------------------

def test_sidecut_opens_plus_x():
    plain = nuts.nut_trap("M3-0.5")
    sidecut = nuts.nut_trap("M3-0.5", sidecut=True)
    assert isinstance(sidecut, Solid)
    assert _size(sidecut).X > _size(plain).X  # feed slot extends +X


def test_capture_adds_screw_relief_past_seat():
    d = _dims("M3-0.5")
    plain = nuts.nut_trap("M3-0.5")
    captured = nuts.nut_trap("M3-0.5", capture=True)
    assert isinstance(captured, Solid)
    # relief extends one nut height past the seat.
    assert _size(captured).Z == pytest.approx(d["height"] + d["height"])


def test_capture_uses_fastener_clearance_diameter():
    # the capture relief is a coaxial bore at the fastener normal clearance;
    # the cutter's in-plane extent still matches the pocket (relief is coaxial).
    captured = nuts.nut_trap("M3-0.5", capture=True)
    assert _size(captured).X == pytest.approx(
        _dims("M3-0.5")["af"] + NUT_CLEARANCE["normal"]
    )


def test_nut_trap_is_subtractable():
    block = Box(20, 20, 20)
    before = block.volume
    block -= nuts.nut_trap("M4-0.7")
    assert block.volume < before


# -- nut_trap: validation --------------------------------------------------

def test_invalid_size_raises():
    with pytest.raises(ValueError):
        nuts.nut_trap("M99")


def test_invalid_nut_type_raises():
    with pytest.raises(ValueError):
        nuts.nut_trap("M3-0.5", nut_type="triangle")


def test_invalid_clearance_class_raises():
    with pytest.raises(ValueError):
        nuts.nut_trap("M3-0.5", clearance_class="banana")


def test_nonpositive_depth_raises():
    with pytest.raises(ValueError):
        nuts.nut_trap("M3-0.5", depth=0.0)


# -- thread_forming_boss ---------------------------------------------------

def test_thread_forming_boss_returns_solid():
    assert isinstance(nuts.thread_forming_boss("M3-0.5"), Solid)


def test_thread_forming_boss_boss_od_diameter():
    d = _tf_dims("M3-0.5")
    boss = nuts.thread_forming_boss("M3-0.5")
    assert _size(boss).X == pytest.approx(d["boss_od"])


def test_thread_forming_boss_default_depth_is_boss_od():
    d = _tf_dims("M3-0.5")
    boss = nuts.thread_forming_boss("M3-0.5")
    # cavity depth = boss_od, pilot extends one pilot diameter deeper.
    assert _size(boss).Z == pytest.approx(d["boss_od"] + d["pilot_soft"])


def test_thread_forming_boss_material_changes_pilot():
    soft = nuts.thread_forming_boss("M3-0.5", material="soft")
    hard = nuts.thread_forming_boss("M3-0.5", material="hard")
    assert soft.volume < hard.volume  # soft pilot (2.5) is smaller than hard (2.6)


def test_thread_forming_boss_boss_od_override():
    boss = nuts.thread_forming_boss("M3-0.5", boss_od=8.0)
    assert _size(boss).X == pytest.approx(8.0)


def test_thread_forming_boss_every_chart_size_generates():
    chart = SizeChart("thread_forming")
    for nominal in chart.sizes():
        dims = chart.get(nominal)
        boss = nuts.thread_forming_boss(nominal)
        assert _size(boss).X == pytest.approx(dims["boss_od"])
        assert isinstance(boss, Solid)


def test_thread_forming_boss_is_subtractable():
    block = Box(30, 30, 30)
    before = block.volume
    block -= nuts.thread_forming_boss("M4-0.7")
    assert block.volume < before


# -- thread_forming_boss: validation --------------------------------------

def test_thread_forming_invalid_size_raises():
    with pytest.raises(ValueError):
        nuts.thread_forming_boss("#6-32")  # thread_forming chart is metric-only


def test_thread_forming_invalid_material_raises():
    with pytest.raises(ValueError):
        nuts.thread_forming_boss("M3-0.5", material="wood")


def test_thread_forming_nonpositive_boss_od_raises():
    with pytest.raises(ValueError):
        nuts.thread_forming_boss("M3-0.5", boss_od=0.0)


def test_thread_forming_boss_od_below_pilot_raises():
    with pytest.raises(ValueError):
        nuts.thread_forming_boss("M3-0.5", boss_od=2.0)  # <= pilot_soft 2.5


# -- quick_ref -------------------------------------------------------------

def test_quick_ref_lists_sizes_and_usage():
    text = nuts.quick_ref()
    assert "USAGE" in text and "SIZES" in text
    assert "nut_trap" in text and "thread_forming_boss" in text
    assert "THREAD-FORMING" in text
    for header in ("Size", "AF", "Height", "Type", "PilotSoft", "PilotHard", "BossOD"):
        assert header in text
    for nominal in SizeChart("nuts").sizes():
        assert nominal in text
