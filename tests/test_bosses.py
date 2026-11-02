"""Acceptance: self-tapping screw bosses are generated from the ``thread_forming``
size chart and match the shared conventions.

``screw_boss`` is a positive post (base at Z=0, rising +Z) with a coaxial pilot
hole. Post OD = chart ``boss_od`` (override via ``boss_od=``); pilot diameter =
``pilot_soft``/``pilot_hard`` by ``material``; default height = ``boss_od``; the
pilot extends one pilot diameter below the base by default. ``countersink=True``
adds a 45-degree conical lead-in at the mouth.
"""

import math

import pytest
from build123d import Box, Solid

from bd_hardware import bosses
from bd_hardware._sizes import SizeChart

MATERIALS = ("soft", "hard")


def _size(solid: Solid):
    return solid.bounding_box().size


def _dims(size: str):
    return SizeChart("thread_forming").get(size)


# -- screw_boss: geometry ----------------------------------------------------

def test_screw_boss_returns_solid():
    assert isinstance(bosses.screw_boss("M3-0.5"), Solid)


def test_screw_boss_default_boss_od():
    d = _dims("M3-0.5")
    boss = bosses.screw_boss("M3-0.5")
    assert _size(boss).X == pytest.approx(d["boss_od"])


def test_screw_boss_default_height_is_boss_od():
    d = _dims("M3-0.5")
    boss = bosses.screw_boss("M3-0.5")
    assert _size(boss).Z == pytest.approx(d["boss_od"])


def test_screw_boss_boss_od_override():
    boss = bosses.screw_boss("M3-0.5", boss_od=8.0)
    assert _size(boss).X == pytest.approx(8.0)


def test_screw_boss_height_override():
    boss = bosses.screw_boss("M3-0.5", height=12.0)
    assert _size(boss).Z == pytest.approx(12.0)


def test_screw_boss_soft_has_more_material_than_hard():
    # hard pilot (2.6) > soft pilot (2.5) -> more material removed -> smaller volume
    soft = bosses.screw_boss("M3-0.5", material="soft")
    hard = bosses.screw_boss("M3-0.5", material="hard")
    assert soft.volume > hard.volume


def test_screw_boss_default_pilot_is_through_bore():
    # default pilot depth = height + pilot_d; within the boss the pilot is a full
    # through-bore, so boss volume == post volume minus the full pilot cylinder.
    d = _dims("M3-0.5")
    od, pilot_d = d["boss_od"], d["pilot_soft"]
    boss = bosses.screw_boss("M3-0.5")
    expected = math.pi * od * ((od / 2.0) ** 2 - (pilot_d / 2.0) ** 2)
    assert boss.volume == pytest.approx(expected, rel=1e-3)


def test_screw_boss_countersink_adds_lead_in():
    plain = bosses.screw_boss("M3-0.5")
    csink = bosses.screw_boss("M3-0.5", countersink=True)
    assert isinstance(csink, Solid)
    # the conical mouth removes a little extra material at the top
    assert csink.volume < plain.volume


@pytest.mark.parametrize("material", MATERIALS)
def test_screw_boss_every_chart_size_generates(material):
    chart = SizeChart("thread_forming")
    for nominal in chart.sizes():
        dims = chart.get(nominal)
        boss = bosses.screw_boss(nominal, material=material)
        assert isinstance(boss, Solid)
        assert _size(boss).X == pytest.approx(dims["boss_od"])
        assert _size(boss).Z == pytest.approx(dims["boss_od"])


# -- screw_boss: additivity (it's a positive feature) ------------------------

def test_screw_boss_is_additive():
    plate = Box(20, 20, 5)
    before = plate.volume
    plate = plate.fuse(bosses.screw_boss("M3-0.5"))
    assert plate.volume > before


# -- screw_boss: validation ---------------------------------------------------

def test_invalid_size_raises():
    with pytest.raises(ValueError):
        bosses.screw_boss("M99")


def test_invalid_material_raises():
    with pytest.raises(ValueError):
        bosses.screw_boss("M3-0.5", material="wood")


def test_nonpositive_boss_od_raises():
    with pytest.raises(ValueError):
        bosses.screw_boss("M3-0.5", boss_od=0.0)


def test_boss_od_below_pilot_raises():
    with pytest.raises(ValueError):
        bosses.screw_boss("M3-0.5", boss_od=2.0)  # <= pilot_soft 2.5


def test_nonpositive_height_raises():
    with pytest.raises(ValueError):
        bosses.screw_boss("M3-0.5", height=0.0)


def test_nonpositive_pilot_depth_raises():
    with pytest.raises(ValueError):
        bosses.screw_boss("M3-0.5", pilot_depth=0.0)


# -- quick_ref ----------------------------------------------------------------

def test_quick_ref_lists_sizes_and_usage():
    text = bosses.quick_ref()
    assert "USAGE" in text and "SIZES" in text
    assert "screw_boss" in text
    for header in ("Size", "BossOD", "PilotSoft", "PilotHard"):
        assert header in text
    for nominal in SizeChart("thread_forming").sizes():
        assert nominal in text
