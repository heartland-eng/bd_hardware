"""Nut traps and thread-forming bosses (owner t_dc036f54).

Geometry follows API_CONTRACT.md §7.3 and the shared size model in ``_sizes``:
every dimension comes from the ``nuts`` and ``thread_forming`` JSON charts, and
every size string is validated through ``_sizes.parse()``.

Conventions (API_CONTRACT.md §5):
  * ``nut_trap`` and ``thread_forming_boss`` are cutters (``Solid``), opening at
    ``Z=0`` and cutting ``+Z``.

``nut_trap`` is the pocket that captures a nut — hexagon (ISO 4032), square
(DIN 562), thin (ISO 4035), or lock (ISO 7040). ``sidecut=True`` opens the
pocket on the ``+X`` side so the nut slides in sideways; ``capture=True`` adds a
coaxial screw-tip relief past the nut seat. ``thread_forming_boss`` is the
plastic counterpart for a thread-forming screw: a ``boss_od`` boss cavity with a
pilot hole (diameter per ``material``) drilled through its floor, giving the
boss its ``(boss_od - pilot) / 2`` wall thickness.

The v1 ``nuts`` chart ships hexagon (ISO 4032) data only. The other three nut
types are derived from it: ``square`` reuses the hexagon across-flats/height,
``hexagon_thin`` is 0.65× the hexagon height (ISO 4035), and ``hexagon_lock`` is
1.5× (ISO 7040). These are documented approximations, not independent charts.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Cylinder,
    Plane,
    Polygon,
    extrude,
)

from ._quick_ref import render, table
from ._sizes import SizeChart, parse

if TYPE_CHECKING:
    from build123d import Solid

__all__ = ["nut_trap", "thread_forming_boss", "quick_ref"]

# Nut-trap clearance added to the across-flats (mm, both sides) by clearance
# class. The pocket is oversized relative to the nominal nut so a printed part
# drops the nut in without binding. A global fit tolerance (like
# ``_sizes.BEARING_INTERFERENCE``); starter values, verify against your printer.
_NUT_CLEARANCE: dict[str, float] = {
    "close": 0.05,
    "normal": 0.2,
    "loose": 0.4,
}

# Height multiplier by nut type, relative to the ISO 4032 hexagon height in the
# ``nuts`` chart (see module docstring for provenance).
_HEIGHT_FACTOR: dict[str, float] = {
    "hexagon": 1.0,
    "square": 1.0,
    "hexagon_thin": 0.65,
    "hexagon_lock": 1.5,
}

_CHART_NAME = "nuts"
_TF_CHART_NAME = "thread_forming"


def _resolve(size: str) -> tuple[str, dict[str, float]]:
    """Validate/normalize a nut size and return (nominal, dims)."""
    chart = SizeChart(_CHART_NAME)
    nominal = parse(size).nominal  # parse() normalizes and rejects junk
    return nominal, chart.get(nominal)  # get() raises ValueError with valid sizes


def _resolve_tf(size: str) -> tuple[str, dict[str, float]]:
    """Validate/normalize a thread-forming size and return (nominal, dims)."""
    chart = SizeChart(_TF_CHART_NAME)
    nominal = parse(size).nominal
    return nominal, chart.get(nominal)


def _polygon_pts(af_clear: float, nut_type: str) -> list[tuple[float, float]]:
    """Closed (X, Y) vertex list for the nut pocket cross-section.

    Across-flats ``af_clear`` is measured along X. For the hexagon types the
    circumradius is ``af_clear / sqrt(3)``; a square nut uses ``af_clear`` as the
    side length (DIN 562 square-nut across-flats).
    """
    if nut_type == "square":
        half = af_clear / 2.0
        return [(-half, -half), (half, -half), (half, half), (-half, half)]
    radius = af_clear / math.sqrt(3.0)
    # Vertices at 30° + 60°·i put a flat pair along X, so bbox.X == af_clear.
    return [
        (
            radius * math.cos(math.radians(30.0 + 60.0 * i)),
            radius * math.sin(math.radians(30.0 + 60.0 * i)),
        )
        for i in range(6)
    ]


def _pocket(af_clear: float, nut_type: str, seat_depth: float) -> "Solid":
    """Extrude the nut pocket cross-section ``seat_depth`` along +Z (opens at Z=0)."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XY):
            Polygon(*_polygon_pts(af_clear, nut_type))
        extrude(amount=seat_depth)
    return bp.part.solid()


def nut_trap(
    size: str,
    *,
    nut_type: str = "hexagon",
    clearance_class: str = "normal",
    depth: float | None = None,
    sidecut: bool = False,
    capture: bool = False,
) -> "Solid":
    """Return a nut trap cutter (opens at Z=0, +Z depth).

    ``nut_type`` selects the nut profile (``hexagon``/``square``/
    ``hexagon_thin``/``hexagon_lock``). ``clearance_class`` (``close``/``normal``/
    ``loose``) adds to the across-flats so the nut drops in. ``depth`` defaults to
    the nut height (the seat depth). With ``sidecut=True`` the pocket is opened on
    the +X side (a feed slot the nut slides into sideways); with ``capture=True`` a
    coaxial screw-tip relief (fastener normal clearance) extends past the seat so a
    bolt threading into the captured nut has room.
    """
    nominal, dims = _resolve(size)
    af, height = dims["af"], dims["height"]

    if nut_type not in _HEIGHT_FACTOR:
        raise ValueError(
            f"Invalid nut_type {nut_type!r}; expected one of "
            f"{', '.join(_HEIGHT_FACTOR)}"
        )
    if clearance_class not in _NUT_CLEARANCE:
        raise ValueError(
            f"Invalid clearance_class {clearance_class!r}; expected one of "
            f"{', '.join(_NUT_CLEARANCE)}"
        )

    af_clear = af + _NUT_CLEARANCE[clearance_class]
    nut_height = height * _HEIGHT_FACTOR[nut_type]
    seat_depth = nut_height if depth is None else depth
    if seat_depth <= 0.0:
        raise ValueError(f"depth must be > 0, got {seat_depth:g}")

    trap = _pocket(af_clear, nut_type, seat_depth)

    if sidecut:
        # Side-entry feed slot: a rectangular channel opening on +X so the nut
        # slides in sideways. As wide as the across-flats (any rotation) and one
        # across-flats long; the caller places the trap so the mouth reaches the
        # part edge. min-X aligned to the origin, so it overlaps the pocket and
        # opens the +X flat.
        mouth = Box(
            af_clear,
            af_clear,
            seat_depth,
            align=(Align.MIN, Align.CENTER, Align.MIN),
        )
        trap = trap.fuse(mouth)

    if capture:
        # Screw-tip relief: coaxial bolt clearance past the seat. Diameter is the
        # fastener "normal" clearance hole (from the fastener_clearance chart);
        # depth extends one nut height past the seat for the bolt tip.
        relief_d = SizeChart("fastener_clearance").get(nominal)["normal"]
        relief = Cylinder(
            relief_d / 2.0,
            seat_depth + nut_height,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        trap = trap.fuse(relief)

    return trap


def thread_forming_boss(
    size: str,
    *,
    material: str = "soft",
    boss_od: float | None = None,
    depth: float | None = None,
) -> "Solid":
    """Return a thread-forming boss cutter (pilot + boss-wall ring pocket).

    The cutter is a boss cavity: a ``boss_od``-diameter recess whose center is the
    pilot hole, with the pilot bore extending one pilot diameter deeper than the
    boss wall. ``material`` selects the pilot diameter (``soft`` = smaller pilot
    for more thread engagement in PLA/ABS; ``hard`` = larger pilot for brittle
    PC/glass-filled). ``boss_od`` defaults to the recommended minimum wall OD from
    the chart; ``depth`` defaults to ``boss_od`` (a sensible boss height).
    """
    nominal, dims = _resolve_tf(size)

    if material not in ("soft", "hard"):
        raise ValueError(f"Invalid material {material!r}; expected 'soft' or 'hard'")

    pilot_d = dims["pilot_soft"] if material == "soft" else dims["pilot_hard"]
    od = dims["boss_od"] if boss_od is None else boss_od
    if od <= 0.0:
        raise ValueError(f"boss_od must be > 0, got {od:g}")
    if od <= pilot_d:
        raise ValueError(
            f"boss_od ({od:g}) must exceed the pilot diameter ({pilot_d:g})"
        )

    boss_depth = od if depth is None else depth
    if boss_depth <= 0.0:
        raise ValueError(f"depth must be > 0, got {boss_depth:g}")

    # Boss cavity (the boss outer wall, ``boss_od``) with the pilot hole drilled
    # through its floor and extending one pilot diameter deeper. The wall
    # thickness of the resulting boss is (boss_od - pilot) / 2.
    cavity = Cylinder(
        od / 2.0,
        boss_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    # Pilot hole: the threaded bore, deeper than the cavity floor.
    pilot = Cylinder(
        pilot_d / 2.0,
        boss_depth + pilot_d,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return cavity.fuse(pilot).solid()


_USAGE = [
    "from bd_hardware import nuts",
    'nut_trap("M3-0.5", nut_type="hexagon")             # hex nut pocket (ISO 4032)',
    'thread_forming_boss("M3-0.5", material="soft")    # plastic thread-forming boss',
]


def quick_ref() -> str:
    nuts = SizeChart(_CHART_NAME)
    tf = SizeChart(_TF_CHART_NAME)

    nut_rows = [
        [nom] + [f"{nuts.get(nom)[c]:g}" for c in ("af", "height")]
        + [str(nuts.get(nom)["type"])]
        for nom in nuts.sizes()
    ]
    tf_rows = [
        [nom] + [f"{tf.get(nom)[c]:g}" for c in ("pilot_soft", "pilot_hard", "boss_od")]
        for nom in tf.sizes()
    ]

    block = render("nuts", _USAGE, ["Size", "AF", "Height", "Type"], nut_rows)
    # render() ends with a trailing newline; append the second chart's table.
    block += "\nTHREAD-FORMING\n"
    block += table(["Size", "PilotSoft", "PilotHard", "BossOD"], tf_rows)
    block += "\n"
    return block
