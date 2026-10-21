"""Press-fit bearing pockets.

Geometry follows the shared size model in
``_sizes``: every bearing dimension comes from the ``bearings`` JSON chart, and
every size string is validated through ``_sizes.parse()``.

Conventions:
  * ``bearing_pocket`` is a cutter (``Solid``), opening at ``Z=0`` and cutting
    ``+Z``;
  * ``bearing`` is a positive ``Part`` for visualisation / BOM.

The pocket is a blind bore whose diameter is the press-fit diameter (nominal OD
plus the fit-class interference) and whose depth seats the bearing width, leaving
a flat shoulder the bearing face rests on. With ``bore_through=True`` the cutter
also pierces the shaft bore at the requested clearance class. The three press-fit
``fit`` classes (``light``/``medium``/``heavy``) and the three shaft
``bore_class`` clearance classes (``close``/``normal``/``loose``) are the FFF
"clearance relief" options: light/heavy tune how tightly the bearing grips, and
close/normal/loose tune how freely a shaft clears the through-bore.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from build123d import Align, Cylinder, Location, Part, Sphere, Vector

from ._quick_ref import render
from ._sizes import BEARING_INTERFERENCE, SizeChart, parse

if TYPE_CHECKING:
    from build123d import Part, Solid

__all__ = ["bearing_pocket", "bearing", "quick_ref"]

# Shaft-bore clearance (diameter allowance, mm) by clearance class, applied to
# the through-bore so a shaft clears a printed hole. A global fit tolerance like
# ``_sizes.BEARING_INTERFERENCE`` (starter values; verify against the shaft fit
# your application needs).
_SHAFT_CLEARANCE: dict[str, float] = {
    "close": 0.05,
    "normal": 0.15,
    "loose": 0.30,
}

_CHART_NAME = "bearings"


def _resolve(size: str) -> tuple[str, dict[str, float]]:
    """Validate/normalize a bearing code and return (nominal, dims)."""
    chart = SizeChart(_CHART_NAME)
    nominal = parse(size).nominal  # parse() normalizes and rejects junk
    return nominal, chart.get(nominal)  # get() raises ValueError with valid sizes


def bearing_pocket(
    size: str,
    *,
    fit: str = "medium",
    depth: float | None = None,
    bore_through: bool = False,
    bore_class: str = "normal",
) -> "Solid":
    """Return a press-fit bearing pocket cutter (Z=0, +Z depth).

    ``fit`` selects the press-fit interference applied to the pocket OD
    (``light``/``medium``/``heavy`` -> 0.00 / -0.02 / -0.04 mm on the radius,
    see ``_sizes.BEARING_INTERFERENCE``). ``depth`` defaults to the bearing
    width (the seat depth). With ``bore_through=True`` the cutter also pierces
    the shaft bore at ``bore_class`` (``close``/``normal``/``loose``).
    """
    nominal, dims = _resolve(size)
    od, bore, width = dims["od"], dims["bore"], dims["width"]

    if fit not in BEARING_INTERFERENCE:
        raise ValueError(
            f"Invalid fit {fit!r}; expected one of {', '.join(BEARING_INTERFERENCE)}"
        )
    if bore_class not in _SHAFT_CLEARANCE:
        raise ValueError(
            f"Invalid bore_class {bore_class!r}; expected one of "
            f"{', '.join(_SHAFT_CLEARANCE)}"
        )

    interference = BEARING_INTERFERENCE[fit]
    pocket_d = od + 2.0 * interference  # press-fit diameter (interference is negative)
    seat_depth = width if depth is None else depth
    if seat_depth <= 0.0:
        raise ValueError(f"depth must be > 0, got {seat_depth:g}")

    pocket = Cylinder(
        pocket_d / 2.0,
        seat_depth,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    if not bore_through:
        return pocket.solid()

    # "through" bore: extend one full OD past the seat so it pierces the plate.
    bore_d = bore + _SHAFT_CLEARANCE[bore_class]
    bore = Cylinder(
        bore_d / 2.0,
        seat_depth + od,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )
    return pocket.fuse(bore).solid()


def bearing(size: str, *, simple: bool = True) -> "Part":
    """Return a positive bearing body for visualisation.

    ``simple=True`` returns a single annulus (outer race only, no inner race or
    balls). ``simple=False`` adds an inner race ring and a full complement of
    balls, derived from the nominal ``bore``/``od``/``width`` (no size data is
    hard-coded; race thickness and ball diameter are fractions of the radial
    gap).
    """
    nominal, dims = _resolve(size)
    od, bore, width = dims["od"], dims["bore"], dims["width"]

    outer = Cylinder(od / 2.0, width, align=(Align.CENTER, Align.CENTER, Align.MIN))
    inner = Cylinder(bore / 2.0, width, align=(Align.CENTER, Align.CENTER, Align.MIN))
    outer_race = outer.cut(inner)  # hollow outer ring (a Solid)

    if simple:
        return Part([outer_race])

    # Detailed bearing: outer race, inner race, and a full complement of balls.
    # Race thickness and ball diameter are fractions of the radial gap (no
    # hard-coded size data).
    radial_gap = (od - bore) / 2.0
    race_t = radial_gap / 3.0  # outer + inner race each take a third of the gap
    ball_d = radial_gap / 3.0  # ball diameter
    ball_r = ball_d / 2.0
    pitch_r = (bore + od) / 4.0  # midpoint of the radial gap
    n_balls = max(4, round(2.0 * math.pi * pitch_r / (ball_d * 1.3)))

    inner_race = Cylinder(
        bore / 2.0 + race_t,
        width,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).cut(Cylinder(bore / 2.0, width, align=(Align.CENTER, Align.CENTER, Align.MIN)))
    outer_race = Cylinder(
        od / 2.0,
        width,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    ).cut(
        Cylinder(
            od / 2.0 - race_t,
            width,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
    )

    children = [outer_race, inner_race]  # both already Solids
    for i in range(n_balls):
        ang = 2.0 * math.pi * i / n_balls
        pos = (pitch_r * math.cos(ang), pitch_r * math.sin(ang), width / 2.0)
        ball = Sphere(ball_r).solid().moved(Location(Vector(*pos)))
        children.append(ball)

    return Part(children)


_USAGE = [
    "from bd_hardware import bearings",
    'bearing_pocket("608", fit="medium")   # press-fit pocket, ISO 15 bearing',
]

_HEADERS = ["Size", "Bore", "OD", "Width", "Light", "Medium", "Heavy"]


def quick_ref() -> str:
    chart = SizeChart(_CHART_NAME)
    rows = []
    for nom in chart.sizes():
        d = chart.get(nom)
        od = d["od"]
        rows.append(
            [
                nom,
                f"{d['bore']:g}",
                f"{od:g}",
                f"{d['width']:g}",
                f"{od + 2 * BEARING_INTERFERENCE['light']:g}",
                f"{od + 2 * BEARING_INTERFERENCE['medium']:g}",
                f"{od + 2 * BEARING_INTERFERENCE['heavy']:g}",
            ]
        )
    return render("bearings", _USAGE, _HEADERS, rows)
