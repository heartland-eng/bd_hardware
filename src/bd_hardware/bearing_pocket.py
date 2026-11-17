"""Bearing pocket block — a parametric boss with a press/slip-fit bearing bore.

The part is a rectangular base with a raised cylindrical boss. The boss holds a
blind bore (pocket) sized for a radial ball bearing, plus a through-hole for
the shaft. Every dimension is a named parameter with a source comment so a new
bearing or a different fit is a one-line change, never geometry surgery.

All units are millimetres.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Align, Box, Cylinder, Part, Pos


@dataclass(frozen=True)
class BearingPocketSpec:
    """Dimensions for a bearing pocket block (all in mm)."""

    bearing_od: float = 22.0  # 608 bearing outer diameter (SKF 608-2RS1)
    bearing_id: float = 8.0  # 608 bearing bore diameter
    bearing_w: float = 7.0  # 608 bearing width
    pocket_clearance: float = 0.20  # diametral clearance for an FDM slip fit
    shaft_clearance: float = 0.40  # diametral clearance on the shaft hole
    boss_wall: float = 3.0  # minimum boss wall around the bearing
    base_margin: float = 8.0  # base extends past the boss on each side
    base_h: float = 4.0  # base plate thickness
    overlap: float = 0.5  # boolean overlap to avoid coplanar non-manifold faces


def bearing_pocket_block(spec: BearingPocketSpec | None = None) -> Part:
    """Build a parametric bearing pocket block and return it as a Part.

    Parameters
    ----------
    spec : BearingPocketSpec, optional
        Override any of the default 608-bearing dimensions.

    Returns
    -------
    build123d.Part
        A single watertight solid.
    """
    spec = spec or BearingPocketSpec()

    # --- Derived geometry ---------------------------------------------------
    pocket_od = spec.bearing_od + spec.pocket_clearance
    boss_od = pocket_od + 2 * spec.boss_wall
    base_len = boss_od + 2 * spec.base_margin
    base_w = base_len  # square footprint keeps the example simple
    total_h = spec.base_h + spec.bearing_w  # bearing sits flush with boss top
    shaft_hole_d = spec.bearing_id + spec.shaft_clearance

    # --- Base plate (top face at z = base_h) --------------------------------
    base = Box(
        base_len,
        base_w,
        spec.base_h,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # --- Boss (overlaps into the base so the boolean fuses) -----------------
    boss = Pos(0, 0, spec.base_h + (spec.bearing_w - spec.overlap) / 2) * Cylinder(
        boss_od / 2,
        spec.bearing_w + spec.overlap,
    )

    # --- Bearing pocket (blind bore, floor at the base top face) ------------
    pocket = Pos(
        0, 0, spec.base_h + (spec.bearing_w + spec.overlap) / 2
    ) * Cylinder(
        pocket_od / 2,
        spec.bearing_w + spec.overlap,
    )

    # --- Shaft through-hole -------------------------------------------------
    shaft_hole = Pos(0, 0, total_h / 2) * Cylinder(shaft_hole_d / 2, total_h + 4)

    return (base + boss) - pocket - shaft_hole
