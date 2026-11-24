"""Metric clearance-hole size standards.

Data follows the ISO 273 "fine / medium / coarse" series for metric
clearance holes, collapsed into three practical fits:

* ``close``  -> ISO 273 fine (tight positional tolerance)
* ``normal`` -> ISO 273 medium (default)
* ``loose``  -> ISO 273 coarse (for alignment slop / field assembly)

Values are the *hole diameter* in millimetres for a given nominal screw
(M) size. They are the through-hole sizes recommended for bolt/screw
clearance (the fastener shank must pass freely with no thread engagement).

The table covers common metric sizes M1.6 through M30. Sizes outside the
table raise ``KeyError`` so callers get a loud, honest failure rather than
a silently interpolated (and possibly wrong) hole.
"""

from __future__ import annotations

from typing import Tuple

# nominal diameter -> (close, normal, loose) clearance diameters, mm
CLEARANCE_HOLES: dict[float, Tuple[float, float, float]] = {
    1.6: (1.8, 2.0, 2.4),
    2.0: (2.2, 2.4, 2.7),
    2.5: (2.7, 2.9, 3.2),
    3.0: (3.2, 3.4, 3.7),
    3.5: (3.7, 3.9, 4.3),
    4.0: (4.3, 4.5, 4.8),
    5.0: (5.3, 5.5, 5.9),
    6.0: (6.4, 6.6, 7.0),
    8.0: (8.4, 9.0, 10.0),
    10.0: (10.5, 11.0, 12.0),
    12.0: (13.0, 13.5, 14.5),
    14.0: (15.0, 15.5, 16.5),
    16.0: (17.0, 17.5, 18.5),
    20.0: (21.0, 22.0, 24.0),
    24.0: (25.0, 26.0, 28.0),
    30.0: (31.0, 33.0, 35.0),
}

FIT_INDEX = {"close": 0, "normal": 1, "loose": 2}


def clearance_diameter(nominal: float, fit: str = "normal") -> float:
    """Return the clearance-hole diameter (mm) for a nominal screw size.

    Args:
        nominal: nominal screw diameter in millimetres (e.g. 3.0 for M3).
        fit: one of ``"close"``, ``"normal"`` (default), ``"loose"``.

    Raises:
        KeyError: if ``nominal`` is not a tabled size.
        ValueError: if ``fit`` is not a recognised value.
    """
    if fit not in FIT_INDEX:
        raise ValueError(f"unknown fit {fit!r}; expected one of {sorted(FIT_INDEX)}")
    return CLEARANCE_HOLES[nominal][FIT_INDEX[fit]]
