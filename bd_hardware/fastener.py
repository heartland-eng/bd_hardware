"""Screw clearance holes, counterbores, and countersinks.

Stub: signatures are fixed; geometry is not yet implemented. ``quick_ref()``
is functional and renders the ``fastener_clearance`` chart.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._quick_ref import render
from ._sizes import SizeChart

if TYPE_CHECKING:
    from build123d import Solid

__all__ = ["clearance_hole", "quick_ref"]


def clearance_hole(
    size: str,
    *,
    clearance_class: str = "normal",
    head: str = "none",  # "none" | "counterbore" | "countersink"
    head_clearance: float = 0.0,
    depth: float | None = None,
) -> "Solid":
    """Return a screw clearance hole cutter (opening at Z=0, +Z depth).

    Not yet implemented.
    """
    raise NotImplementedError("fastener.clearance_hole geometry is not yet implemented.")


_USAGE = [
    "from bd_hardware import fastener",
    'clearance_hole("M3-0.5", clearance_class="normal", head="counterbore")  # SHCS counterbore',
]

_HEADERS = ["Size", "Close", "Normal", "Loose", "CBoreØ", "CSinkØ"]
_COLS = ("close", "normal", "loose", "cbore", "csink")


def quick_ref() -> str:
    chart = SizeChart("fastener_clearance")
    rows = [
        [nom] + [f"{chart.get(nom)[c]:g}" for c in _COLS]
        for nom in chart.sizes()
    ]
    return render("fastener", _USAGE, _HEADERS, rows)
