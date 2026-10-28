"""Screw clearance holes, counterbores, and countersinks.

Geometry follows the shared size model in ``_sizes``: every dimension comes from
the ``fastener_clearance`` JSON chart, and every size string is validated through
``_sizes.parse()``.

Conventions:
  * ``clearance_hole`` is a cutter (``Solid``), opening at ``Z=0`` and cutting
    ``+Z``.

The shank hole is a through-bore at the selected ``clearance_class`` (``close``/
``normal``/``loose``). ``head="counterbore"`` adds a coaxial socket-head recess
of diameter ``cbore + head_clearance`` (ISO 4762 SHCS); ``head="countersink"``
adds a 90-degree conical recess of top diameter ``csink + head_clearance``
(ISO 10642 flat head). ``depth`` defaults to ``4 x`` the clearance diameter (a
generic through-depth; there is no part thickness in the size chart), so set it
to the actual plate thickness. ``head_clearance`` is a diametral allowance (mm)
added to the head feature so the head seats without binding.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from build123d import Align, Cone, Cylinder

from ._quick_ref import render
from ._sizes import SizeChart, parse

if TYPE_CHECKING:
    from build123d import Solid

__all__ = ["clearance_hole", "quick_ref"]

_CHART_NAME = "fastener_clearance"

_CLEARANCE_CLASSES = ("close", "normal", "loose")
_HEADS = ("none", "counterbore", "countersink")

# Default through-depth of the shank hole as a multiple of the clearance
# diameter. A clearance hole has no "part thickness" in its chart, so it
# defaults to a through-bore deep enough to pierce a plate up to ~4 diameters
# thick; callers should override ``depth`` with their real plate thickness.
_THROUGH_DEPTH_FACTOR = 4.0

# Socket-head recess depth as a fraction of the counterbore (head) diameter.
# ISO 4762 SHCS head height is ~0.5x the head diameter; documented approximation
# (the real chart carries no head-height column).
_CBORE_DEPTH_FACTOR = 0.5


def _resolve(size: str) -> tuple[str, dict[str, float]]:
    """Validate/normalize a fastener size and return (nominal, dims)."""
    chart = SizeChart(_CHART_NAME)
    nominal = parse(size).nominal  # parse() normalizes and rejects junk
    return nominal, chart.get(nominal)  # get() raises ValueError with valid sizes


def clearance_hole(
    size: str,
    *,
    clearance_class: str = "normal",
    head: str = "none",  # "none" | "counterbore" | "countersink"
    head_clearance: float = 0.0,
    depth: float | None = None,
) -> "Solid":
    """Return a screw clearance hole cutter (opening at Z=0, +Z depth).

    The shank hole is a through-bore of diameter ``dims[clearance_class]``
    (``close``/``normal``/``loose``). ``head="counterbore"`` adds a coaxial
    socket-head recess (diameter ``cbore + head_clearance``, depth ``0.5 x
    cbore``); ``head="countersink"`` adds a 90-degree conical recess (top
    diameter ``csink + head_clearance``) that tapers to an apex inside the shank
    hole. ``depth`` defaults to ``4 x`` the clearance diameter.
    """
    nominal, dims = _resolve(size)

    if clearance_class not in _CLEARANCE_CLASSES:
        raise ValueError(
            f"Invalid clearance_class {clearance_class!r}; expected one of "
            f"{', '.join(_CLEARANCE_CLASSES)}"
        )
    if head not in _HEADS:
        raise ValueError(
            f"Invalid head {head!r}; expected one of {', '.join(_HEADS)}"
        )
    if head_clearance < 0.0:
        raise ValueError(f"head_clearance must be >= 0, got {head_clearance:g}")

    hole_d = dims[clearance_class]
    through = _THROUGH_DEPTH_FACTOR * hole_d if depth is None else depth
    if through <= 0.0:
        raise ValueError(f"depth must be > 0, got {through:g}")

    shank = Cylinder(
        hole_d / 2.0,
        through,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    if head == "counterbore":
        cbore_d = dims["cbore"] + head_clearance
        cbore_depth = dims["cbore"] * _CBORE_DEPTH_FACTOR
        recess = Cylinder(
            cbore_d / 2.0,
            cbore_depth,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        return shank.fuse(recess)

    if head == "countersink":
        csink_d = dims["csink"] + head_clearance
        # 90-degree included angle => a full cone whose height is half its top
        # diameter. The cone tapers to an apex inside the shank hole, so the
        # union with the shank stays a single clean solid (no coincident faces).
        recess = Cone(
            csink_d / 2.0,
            0.0,
            csink_d / 2.0,
            align=(Align.CENTER, Align.CENTER, Align.MIN),
        )
        return shank.fuse(recess)

    return shank.solid()


_USAGE = [
    "from bd_hardware import fastener",
    'clearance_hole("M3-0.5")                                    # through hole, normal clearance',
    'clearance_hole("M3-0.5", head="counterbore")               # SHCS counterbore recess',
    'clearance_hole("M3-0.5", head="countersink")               # 90deg flat-head recess',
]

_HEADERS = ["Size", "Close", "Normal", "Loose", "CBoreØ", "CSinkØ"]
_COLS = ("close", "normal", "loose", "cbore", "csink")


def quick_ref() -> str:
    chart = SizeChart(_CHART_NAME)
    rows = [
        [nom] + [f"{chart.get(nom)[c]:g}" for c in _COLS]
        for nom in chart.sizes()
    ]
    return render("fastener", _USAGE, _HEADERS, rows)
