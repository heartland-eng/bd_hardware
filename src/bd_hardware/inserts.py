"""Heat-set threaded insert bosses.

A heat-set insert is a brass cylinder with internal threads that is melted
into a 3D-printed boss. The boss must be bored with a counterbored pocket:
a slight lead-in ("pilot") at the mouth, a press-fit bore matching the insert
OD, and a through hole for the fastening screw.
"""

from __future__ import annotations

from dataclasses import dataclass

from build123d import Align, Cylinder, Part, Pos

__all__ = ["InsertSpec", "STANDARD_INSERTS", "insert_boss"]


@dataclass(frozen=True)
class InsertSpec:
    """Nominal dimensions of a heat-set threaded insert.

    All units are millimetres. These are *typical* brass-insert dimensions;
    always confirm against the datasheet for the specific insert you use.
    """

    od: float              # outside diameter of the insert body
    length: float          # overall insert length
    screw_clearance: float  # through-hole diameter for the fastening screw
    pilot: float           # lead-in diameter at the mouth of the pocket
    pilot_depth: float     # depth of the lead-in

    def __post_init__(self) -> None:
        if not (self.pilot >= self.od >= self.screw_clearance > 0):
            raise ValueError("expected pilot >= od >= screw_clearance > 0")


# Typical brass heat-set insert dimensions (mm), keyed by thread size.
STANDARD_INSERTS: dict[str, InsertSpec] = {
    "M2":   InsertSpec(od=3.2, length=3.2, screw_clearance=2.4, pilot=3.4, pilot_depth=0.8),
    "M2.5": InsertSpec(od=4.0, length=3.8, screw_clearance=2.9, pilot=4.2, pilot_depth=0.8),
    "M3":   InsertSpec(od=4.6, length=4.0, screw_clearance=3.2, pilot=4.8, pilot_depth=1.0),
    "M4":   InsertSpec(od=5.6, length=5.0, screw_clearance=4.3, pilot=5.8, pilot_depth=1.0),
    "M5":   InsertSpec(od=6.4, length=5.0, screw_clearance=5.3, pilot=6.6, pilot_depth=1.0),
}


def _hole(radius: float, height: float, z0: float) -> Cylinder:
    """A cylinder standing on the plane z = z0, extending upward by ``height``."""
    return Pos(0, 0, z0) * Cylinder(
        radius=radius,
        height=height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )


def insert_boss(
    spec: InsertSpec,
    *,
    boss_od: float | None = None,
    wall: float = 1.5,
    boss_height: float | None = None,
) -> Part:
    """Build a cylindrical boss with a counterbored heat-set insert pocket.

    The returned part sits on the XY plane with its axis along Z: bottom at
    ``z = 0`` and top at ``z = boss_height``. The pocket is bored from the top:
    a short ``pilot`` lead-in, the press-fit ``spec.od`` bore, and a through
    hole of ``spec.screw_clearance`` for the screw.

    Parameters
    ----------
    spec:
        The insert dimensions (see :class:`InsertSpec`).
    boss_od:
        Outside diameter of the boss. Defaults to ``spec.od + 2 * wall``.
    wall:
        Minimum wall thickness between the insert bore and the boss OD. Used
        only when ``boss_od`` is not given.
    boss_height:
        Boss height. Defaults to ``spec.length + wall`` (a little solid
        material below the insert so the screw shank is supported).

    Returns
    -------
    build123d.Part
        A watertight, positive-volume boss ready to fuse into a larger part.
    """
    if boss_od is None:
        boss_od = spec.od + 2 * wall
    if boss_height is None:
        boss_height = spec.length + wall

    if boss_od <= spec.pilot:
        raise ValueError(
            f"boss_od ({boss_od}) must exceed the pilot diameter ({spec.pilot})"
        )
    if boss_height < spec.length:
        raise ValueError(
            f"boss_height ({boss_height}) must be at least the insert length ({spec.length})"
        )

    boss = Cylinder(
        radius=boss_od / 2,
        height=boss_height,
        align=(Align.CENTER, Align.CENTER, Align.MIN),
    )

    # Through hole for the fastening screw.
    boss -= _hole(spec.screw_clearance / 2, boss_height, 0.0)
    # Press-fit bore for the insert body.
    boss -= _hole(spec.od / 2, spec.length, boss_height - spec.length)
    # Lead-in pilot at the mouth.
    boss -= _hole(spec.pilot / 2, spec.pilot_depth, boss_height - spec.pilot_depth)

    return boss
