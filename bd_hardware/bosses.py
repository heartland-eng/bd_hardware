"""Self-tapping screw bosses.

Geometry follows the shared size model in ``_sizes``: every dimension comes
from the ``thread_forming`` JSON chart, and every size string is validated
through ``_sizes.parse()``.

Conventions:
  * ``screw_boss`` is a positive body (``Solid``) — a raised cylindrical post
    whose base sits on ``Z=0`` and rises ``+Z``, carrying a coaxial pilot hole
    drilled from the top.

``screw_boss`` is the additive counterpart to ``nuts.thread_forming_boss``:
that returns the cavity a thread-forming screw leaves in a plate; this returns
the boss itself. The post OD is the chart ``boss_od`` (a minimum wall; pass
``boss_od=`` to thicken), the pilot hole is ``pilot_soft`` or ``pilot_hard`` by
``material`` (``soft`` = smaller pilot for more thread engagement in PLA/ABS;
``hard`` = larger pilot for brittle PC/glass-filled), and ``height`` defaults to
``boss_od`` (a sensible boss height). The pilot extends one pilot diameter below
the boss base so the screw tip has room and the hole guides the screw to full
engagement; ``countersink=True`` adds a 45-degree conical lead-in at the mouth
so the screw starts cleanly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from build123d import (
    Align,
    Axis,
    BuildPart,
    BuildSketch,
    Cylinder,
    Location,
    Plane,
    Polygon,
    revolve,
)

from ._quick_ref import render
from ._sizes import SizeChart, parse

if TYPE_CHECKING:
    from build123d import Solid

__all__ = ["screw_boss", "quick_ref"]

_CHART_NAME = "thread_forming"

_MATERIALS = ("soft", "hard")

# 45-degree conical lead-in at the pilot mouth (mm, radial = axial). A small
# chamfer so a self-tapping screw self-centers without mushrooming the boss rim.
_COUNTERSINK_LEAD = 0.5


def _resolve(size: str) -> tuple[str, dict[str, float]]:
    """Validate/normalize a screw size and return (nominal, dims)."""
    chart = SizeChart(_CHART_NAME)
    nominal = parse(size).nominal  # parse() normalizes and rejects junk
    return nominal, chart.get(nominal)  # get() raises ValueError with valid sizes


def _pilot_bore(
    pilot_r: float, pilot_depth: float, height: float, lead: float
) -> "Solid":
    """Return the coaxial pilot bore (a cutter), top-aligned to the boss top.

    The bore spans ``[height - pilot_depth, height]``: a straight pilot of
    radius ``pilot_r``, with (when ``lead > 0``) a 45-degree conical mouth that
    widens from ``pilot_r`` to ``pilot_r + lead`` over the top ``lead`` mm.
    Built as a single revolved solid so the countersink and pilot fuse watertight
    (no coincident faces to trip the boolean).
    """
    z0 = height - pilot_depth
    if lead <= 0.0:
        return Cylinder(
            pilot_r, pilot_depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
        ).moved(Location((0.0, 0.0, z0)))

    z1 = height - lead
    profile = [
        (0.0, z0),  # axis, bore bottom
        (pilot_r, z0),  # pilot wall, bottom
        (pilot_r, z1),  # pilot wall, countersink start
        (pilot_r + lead, height),  # mouth, top surface
        (0.0, height),  # axis, top surface
    ]
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            Polygon(*profile)
        revolve(axis=Axis.Z)
    return bp.part.solid()


def screw_boss(
    size: str,
    *,
    material: str = "soft",
    boss_od: float | None = None,
    height: float | None = None,
    pilot_depth: float | None = None,
    countersink: bool = False,
) -> "Solid":
    """Return a self-tapping screw boss (positive post, base at Z=0, +Z).

    ``material`` selects the pilot diameter (``soft``/``hard``). ``boss_od``
    overrides the chart minimum wall OD. ``height`` defaults to ``boss_od``.
    ``pilot_depth`` is measured from the top of the boss and defaults to
    ``height + pilot_d`` so the pilot extends one pilot diameter below the base
    (a place for the screw tip). ``countersink=True`` adds a 45-degree conical
    lead-in at the mouth.
    """
    nominal, dims = _resolve(size)

    if material not in _MATERIALS:
        raise ValueError(
            f"Invalid material {material!r}; expected one of {', '.join(_MATERIALS)}"
        )

    pilot_d = dims["pilot_soft"] if material == "soft" else dims["pilot_hard"]
    od = dims["boss_od"] if boss_od is None else boss_od
    if od <= 0.0:
        raise ValueError(f"boss_od must be > 0, got {od:g}")
    if od <= pilot_d:
        raise ValueError(
            f"boss_od ({od:g}) must exceed the pilot diameter ({pilot_d:g})"
        )

    boss_height = od if height is None else height
    if boss_height <= 0.0:
        raise ValueError(f"height must be > 0, got {boss_height:g}")

    pilot_r = pilot_d / 2.0
    pdepth = boss_height + pilot_d if pilot_depth is None else pilot_depth
    if pdepth <= 0.0:
        raise ValueError(f"pilot_depth must be > 0, got {pdepth:g}")

    lead = _COUNTERSINK_LEAD if countersink else 0.0
    if lead > 0.0:
        if pdepth < lead:
            raise ValueError(
                f"pilot_depth ({pdepth:g}) must be >= the countersink lead "
                f"({lead:g} mm)"
            )
        if pilot_r + lead >= od / 2.0:
            raise ValueError(
                f"countersink mouth (r={pilot_r + lead:g}) must fit within the "
                f"boss OD ({od:g})"
            )

    post = Cylinder(
        od / 2.0, boss_height, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    bore = _pilot_bore(pilot_r, pdepth, boss_height, lead)
    return post.cut(bore).solid()


_USAGE = [
    "from bd_hardware import bosses",
    'bosses.screw_boss("M3-0.5")                        # self-tapping boss, soft material',
    'bosses.screw_boss("M3-0.5", material="hard")      # larger pilot, brittle plastic',
    'bosses.screw_boss("M3-0.5", countersink=True)     # 45deg lead-in at the mouth',
]

_HEADERS = ["Size", "BossOD", "PilotSoft", "PilotHard"]


def quick_ref() -> str:
    chart = SizeChart(_CHART_NAME)
    rows = [
        [
            nom,
            f"{chart.get(nom)['boss_od']:g}",
            f"{chart.get(nom)['pilot_soft']:g}",
            f"{chart.get(nom)['pilot_hard']:g}",
        ]
        for nom in chart.sizes()
    ]
    return render("bosses", _USAGE, _HEADERS, rows)
