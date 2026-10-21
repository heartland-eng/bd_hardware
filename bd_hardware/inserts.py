"""Heat-set insert pockets.

Stub; geometry not yet implemented. ``quick_ref()`` renders the ``inserts``
chart.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._quick_ref import render
from ._sizes import SizeChart

if TYPE_CHECKING:
    from build123d import Solid

__all__ = ["insert_hole", "heat_set_insert", "quick_ref"]


def insert_hole(
    size: str,
    *,
    clearance_class: str = "normal",
    depth: float | None = None,
    compensation: float = 0.0,
    lead_in: bool = True,
) -> "Solid":
    """Return a heat-set insert pilot pocket cutter (Z=0, +Z depth).

    Not yet implemented.
    """
    raise NotImplementedError("inserts.insert_hole geometry is not yet implemented.")


def heat_set_insert(size: str, *, simple: bool = True) -> "Solid":
    """Return a positive heat-set insert body (for viz / BOM).

    Not yet implemented.
    """
    raise NotImplementedError("inserts.heat_set_insert geometry is not yet implemented.")


_USAGE = [
    "from bd_hardware import inserts",
    'insert_hole("M3-0.5", clearance_class="normal")   # heat-set pilot pocket',
]

_HEADERS = ["Size", "OD", "Length", "Pilot", "Source"]
_COLS = ("od", "length", "pilot")


def quick_ref() -> str:
    chart = SizeChart("inserts")
    rows = [
        [nom, f"{chart.get(nom)['od']:g}", f"{chart.get(nom)['length']:g}",
         f"{chart.get(nom)['pilot']:g}", chart.source]
        for nom in chart.sizes()
    ]
    return render("inserts", _USAGE, _HEADERS, rows)
