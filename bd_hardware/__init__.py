"""bd_hardware -- a lightweight, function-first hardware feature library for build123d.

Import as ``import bd_hardware as bdh``.

Five feature modules (one import, one function call per feature):

    fastener    -- screw clearance / counterbore / countersink holes
    inserts     -- heat-set insert pockets
    nuts        -- nut traps + thread-forming bosses
    snap_fit    -- cantilever + annular snap fits
    bearings    -- press-fit bearing pockets

Plus a package-level :func:`quick_ref` dispatcher for discovery.

This file is written ONCE by the scaffold and must not be edited by module
implementers (API_CONTRACT.md §8).
"""

from __future__ import annotations

from . import bearings, fastener, inserts, nuts, snap_fit
from ._quick_ref import dispatch as _dispatch
from ._sizes import (
    BEARING_INTERFERENCE,
    IN,
    MM,
    MANUFACTURING_COMPENSATION,
    ClearanceClass,
    Material,
    Size,
    SizeChart,
    Units,
    bearing_608,
    imperial,
    metric,
    parse,
)

__version__ = "0.1.0"

_MODULES = {
    "fastener": fastener.quick_ref,
    "inserts": inserts.quick_ref,
    "nuts": nuts.quick_ref,
    "snap_fit": snap_fit.quick_ref,
    "bearings": bearings.quick_ref,
}


def quick_ref(module: str | None = None) -> str:
    """Return the cheatsheet for one module, or all modules concatenated.

    ``quick_ref()`` -> every module's block; ``quick_ref("fastener")`` -> just
    that module.
    """
    return _dispatch(_MODULES, module)


__all__ = [
    "bearings",
    "fastener",
    "inserts",
    "nuts",
    "snap_fit",
    "Size",
    "SizeChart",
    "parse",
    "metric",
    "imperial",
    "bearing_608",
    "MM",
    "IN",
    "MANUFACTURING_COMPENSATION",
    "BEARING_INTERFERENCE",
    "ClearanceClass",
    "Material",
    "Units",
    "quick_ref",
    "__version__",
]
