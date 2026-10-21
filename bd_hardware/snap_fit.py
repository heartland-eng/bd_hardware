"""Cantilever and annular snap-fit features (owner t_fbd4e557).

Snap-fits are parametric and have NO size chart (API_CONTRACT.md §7.4). The
:class:`CantileverSpec` dataclass carries every geometric knob; the three
recommended starting points are listed in :func:`quick_ref`.

Geometry conventions (API_CONTRACT.md §5.2):
  * positive parts (``cantilever_hook``, ``annular_snap``) are modeled with
    their reference face at ``Z=0`` and the feature extending ``+Z``;
  * the cutter (``cantilever_catch``) opens at ``Z=0`` and cuts ``+Z``.

The cantilever hook is a beam (length x width x thickness) whose free end
carries a retention lip that rises ``retention`` above the beam top on a ramp
at ``angle`` degrees; the retention face is the vertical face at the free end.
The mating catch is a slot (beam clearance) with an undercut ledge of depth
``retention`` that the lip snaps behind.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from build123d import Align, Axis, BuildPart, BuildSketch, Plane, Polygon, extrude, revolve

from ._quick_ref import render

if TYPE_CHECKING:
    from build123d import Solid

__all__ = [
    "CantileverSpec",
    "cantilever_hook",
    "cantilever_catch",
    "annular_snap",
    "quick_ref",
]

# Clearance allowance (mm, on the diameter / both sides) between a snap hook and
# its mating catch, so a printed hook deflects and seats without binding. This is
# a global fit tolerance (like ``_sizes.BEARING_INTERFERENCE`` / ``_sizes.
# MANUFACTURING_COMPENSATION``), not a size-chart dimension.
_SNAP_CLEARANCE = 0.2


@dataclass(frozen=True)
class CantileverSpec:
    """Geometry for a cantilever snap hook (all dimensions in mm).

    ``angle`` is the retention-ramp angle in degrees and ``root_fillet`` the
    fillet radius applied where the beam meets the reference face.
    """

    length: float  # beam length
    width: float  # beam width
    thickness: float  # beam thickness at root
    retention: float  # engagement / undercut depth
    angle: float = 45.0  # retention ramp angle (deg)
    root_fillet: float = 0.5  # fillet radius at root


# Three recommended starting points (API_CONTRACT.md §9). Retention ≈ deflection;
# keep the undercut shallow for FFF to avoid a brittle hook.
_RECOMMENDED: dict[str, CantileverSpec] = {
    "small": CantileverSpec(length=10.0, width=3.0, thickness=1.0, retention=0.4),
    "medium": CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6),
    "large": CantileverSpec(length=25.0, width=8.0, thickness=2.5, retention=1.0),
}


def _validate_spec(spec: CantileverSpec) -> None:
    """Raise ValueError on a physically meaningless cantilever spec."""
    for name, value in (
        ("length", spec.length),
        ("width", spec.width),
        ("thickness", spec.thickness),
    ):
        if value <= 0.0:
            raise ValueError(f"CantileverSpec.{name} must be > 0, got {value:g}")
    if spec.retention <= 0.0:
        raise ValueError(
            f"CantileverSpec.retention must be > 0, got {spec.retention:g}"
        )
    if not 0.0 < spec.angle < 90.0:
        raise ValueError(
            f"CantileverSpec.angle must be in (0, 90) degrees, got {spec.angle:g}"
        )
    if spec.root_fillet < 0.0:
        raise ValueError(
            f"CantileverSpec.root_fillet must be >= 0, got {spec.root_fillet:g}"
        )


def _ramp(spec: CantileverSpec) -> float:
    """Horizontal run of the retention ramp (mm)."""
    return spec.retention / math.tan(math.radians(spec.angle))


def _hook_profile(spec: CantileverSpec) -> list[tuple[float, float]]:
    """Closed (X, Z) profile of the hook, beam root at X=0, reference face Z=0."""
    ramp = _ramp(spec)
    if ramp >= spec.length:
        raise ValueError(
            f"CantileverSpec retention ramp ({ramp:.3g} mm) reaches or exceeds the "
            f"beam length ({spec.length:g} mm); reduce retention, increase angle, "
            "or lengthen the beam"
        )
    return [
        (0.0, 0.0),  # root, reference face
        (0.0, spec.thickness),  # root top
        (spec.length - ramp, spec.thickness),  # ramp start on beam top
        (spec.length, spec.thickness + spec.retention),  # retention-lip peak
        (spec.length, 0.0),  # free-end bottom
    ]


def _extrude_profile(pts: list[tuple[float, float]], width: float) -> "Solid":
    """Extrude a closed (X, Z) polygon ``width`` in Y (centered) to a Solid."""
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            Polygon(*pts)
        extrude(amount=width / 2.0, both=True)
    return bp.part.solid()


def cantilever_hook(spec: CantileverSpec) -> "Solid":
    """Return a positive cantilever hook feature (a Solid).

    The beam spans ``length`` along ``+X`` from its root at ``X=0``, is centered
    on ``Y`` across ``width``, and rises ``thickness`` along ``+Z`` from the
    reference face at ``Z=0``. A retention lip of ``retention`` rises above the
    beam top at the free end on a ramp of ``angle`` degrees.
    """
    _validate_spec(spec)
    solid = _extrude_profile(_hook_profile(spec), spec.width)
    if spec.root_fillet > 0.0:
        # Root fillet: the edge along Y where the beam root meets the reference
        # face (X=0, Z=0), reducing the stress concentration at the wall.
        root_edges = [
            e
            for e in solid.edges()
            if abs(e.center().X) < 1e-6 and abs(e.center().Z) < 1e-6
        ]
        if root_edges:
            solid = solid.fillet(spec.root_fillet, root_edges)
    return solid


def cantilever_catch(spec: CantileverSpec) -> "Solid":
    """Return the mating undercut cutter (a Solid) for a cantilever hook.

    The cutter is a stepped slot (opening at ``Z=0``, cutting ``+Z``): a full
    slot of height ``thickness + retention + clearance`` for the beam and lip,
    plus an undercut ledge of depth ``retention + clearance`` beyond the slot's
    far end that the retention face catches behind. The slot width is
    ``width + 2*clearance``.
    """
    _validate_spec(spec)
    clearance = _SNAP_CLEARANCE
    slot_height = spec.thickness + spec.retention + clearance
    slot_length = spec.length
    undercut_height = spec.retention + clearance
    undercut_depth = spec.retention + clearance
    profile = [
        (0.0, 0.0),
        (0.0, slot_height),
        (slot_length, slot_height),
        (slot_length, undercut_height),
        (slot_length + undercut_depth, undercut_height),
        (slot_length + undercut_depth, 0.0),
    ]
    return _extrude_profile(profile, spec.width + 2.0 * clearance)


def _annular_profile(
    radius: float, thickness: float, retention: float, angle: float
) -> list[tuple[float, float]]:
    """Closed (r, z) profile of the annular snap, revolved about the Z axis."""
    height = thickness
    ramp = retention / math.tan(math.radians(angle))
    if ramp >= height:
        raise ValueError(
            f"annular_snap retention ramp ({ramp:.3g} mm) reaches or exceeds the "
            f"ring height ({height:g} mm); reduce retention, increase angle, or "
            "increase thickness"
        )
    return [
        (radius, 0.0),  # inner face, bottom
        (radius + thickness, 0.0),  # outer face, bottom
        (radius + thickness, height),  # outer face, top
        (radius - retention, height),  # inward retention-lip peak
        (radius, height - ramp),  # lip ramp meets inner face
    ]


def annular_snap(
    radius: float,
    *,
    thickness: float,
    retention: float,
    angle: float = 45.0,
) -> "Solid":
    """Return a revolved annular snap feature (a Solid).

    A ring of inner radius ``radius`` and radial wall ``thickness`` (axial
    height also ``thickness``), carrying an inward retention lip of ``retention``
    at its top edge on a ramp of ``angle`` degrees. Revolved 360° about ``+Z``.
    """
    if radius <= 0.0:
        raise ValueError(f"radius must be > 0, got {radius:g}")
    if thickness <= 0.0:
        raise ValueError(f"thickness must be > 0, got {thickness:g}")
    if retention <= 0.0:
        raise ValueError(f"retention must be > 0, got {retention:g}")
    if not 0.0 < angle < 90.0:
        raise ValueError(f"angle must be in (0, 90) degrees, got {angle:g}")
    if retention >= radius:
        raise ValueError(
            f"retention ({retention:g} mm) must be less than radius ({radius:g} mm)"
        )
    profile = _annular_profile(radius, thickness, retention, angle)
    with BuildPart() as bp:
        with BuildSketch(Plane.XZ):
            Polygon(*profile)
        revolve(axis=Axis.Z)
    return bp.part.solid()


_USAGE = [
    "from bd_hardware import snap_fit",
    "hook = snap_fit.cantilever_hook(snap_fit.CantileverSpec(length=15.0, width=5.0, thickness=1.5, retention=0.6))",
    "catch = snap_fit.cantilever_catch(hook_spec)   # subtract from the mating part",
]

_HEADERS = ["Config", "Length", "Width", "Thickness", "Retention"]


def quick_ref() -> str:
    rows = [
        [name, f"{s.length:g}", f"{s.width:g}", f"{s.thickness:g}", f"{s.retention:g}"]
        for name, s in _RECOMMENDED.items()
    ]
    return render("snap_fit", _USAGE, _HEADERS, rows)
