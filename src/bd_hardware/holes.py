"""Clearance holes for metric fasteners.

The functions here are "function-first": each returns a build123d solid
that the caller positions and booleans however they like. They do not
mutate or assume a specific part — you bring the geometry, we hand you the
cut tool.

Units are millimetres throughout. Z is the hole axis; the counterbore (when
present) opens toward +Z (the fastener-head side, i.e. the wall surface).
"""

from __future__ import annotations

import build123d as bd

from ._standards import clearance_diameter

# How far a through-cut is extended past the stock faces, in mm. Extending
# avoids degenerate coplanar faces where a rod would otherwise end exactly on
# the part surface, which OCP can triangulate into non-manifold slivers.
_EXTEND = 1.0


def through_hole(nominal: float, depth: float, fit: str = "normal") -> bd.Part:
    """A straight through-hole as a cut tool (rod), centred on the origin.

    The rod runs along Z from ``-(depth/2 + _EXTEND)`` to ``+(depth/2 + _EXTEND)``
    so that, placed at the mid-plane of a ``depth``-thick wall, it cuts cleanly
    out of both faces.

    Args:
        nominal: nominal screw diameter, mm (e.g. 3.0 for M3).
        depth: thickness of the wall being drilled, mm.
        fit: ``"close"``, ``"normal"``, or ``"loose"``.
    """
    d = clearance_diameter(nominal, fit)
    return bd.Cylinder(d / 2.0, depth + 2 * _EXTEND)


def counterbore_hole(
    nominal: float,
    depth: float,
    fit: str = "normal",
    head_diameter: float = 0.0,
    head_depth: float = 0.0,
) -> bd.Shape:
    """A counterbored clearance hole as a stepped cut tool.

    Combines a through shank hole with a wider counterbore on the +Z (head)
    side, recessing the fastner head flush with the wall surface. The two
    cylinders overlap by ``_EXTEND`` so the boolean fuses cleanly rather than
    leaving coplanar faces (the OCP non-manifold trap).

    Args:
        nominal: nominal screw diameter, mm.
        depth: full wall thickness, mm.
        fit: ``"close"``, ``"normal"``, or ``"loose"``.
        head_diameter: counterbore diameter, mm (must exceed the through hole).
        head_depth: counterbore depth from the head side, mm.

    Raises:
        ValueError: if the counterbore is not larger than the through hole,
            or if ``head_depth`` is not in ``(0, depth)``.
    """
    d = clearance_diameter(nominal, fit)
    if head_diameter <= d:
        raise ValueError(
            f"head_diameter {head_diameter} must exceed the {fit} clearance "
            f"hole diameter {d}"
        )
    if not 0 < head_depth < depth:
        raise ValueError(
            f"head_depth {head_depth} must be between 0 and depth {depth}"
        )

    shank = bd.Cylinder(d / 2.0, depth + 2 * _EXTEND)

    # Counterbore on the head (top, +Z) side. It is flush with the wall's top
    # face, extends up by _EXTEND (harmless: cuts empty space) and overlaps the
    # shank by _EXTEND so the union fuses.
    cb_len = head_depth + _EXTEND
    z_top = depth / 2.0 + _EXTEND
    z_bottom = z_top - cb_len
    cb = bd.Cylinder(head_diameter / 2.0, cb_len).move(
        bd.Location((0, 0, (z_top + z_bottom) / 2.0))
    )

    return shank + cb
