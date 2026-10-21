"""Shared size-data model for bd_hardware.

Written ONCE by the scaffold task (API_CONTRACT.md §8). Module implementers
import from here and MUST NOT edit this file.

This module owns:
  * the frozen :class:`Size` dataclass (nominal, units, clearance_class, source)
  * the JSON-backed :class:`SizeChart` loader (all dimensions in millimetres)
  * the single :func:`parse` entry point that normalizes size strings
  * unit constants ``MM`` / ``IN`` and the manufacturing-compensation default
  * the press-fit interference map used by the bearings module

Data files live in ``bd_hardware/data/`` and are validated against a fixed
schema (see :meth:`SizeChart._validate` and ``tests/test_schema.py``).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------------- #
# Units
# --------------------------------------------------------------------------- #
MM = 1.0
IN = 25.4

# --------------------------------------------------------------------------- #
# Type aliases
# --------------------------------------------------------------------------- #
Units = str  # "metric" | "imperial"  (kept as str for 3.10+ friendliness)
ClearanceClass = str  # "close" | "normal" | "loose"
Material = str  # "soft" | "hard"

# --------------------------------------------------------------------------- #
# Tolerances / fits
# --------------------------------------------------------------------------- #
# Global default manufacturing compensation (mm), applied by modules at
# generation time. Data files stay nominal; fudge factors are never baked in.
MANUFACTURING_COMPENSATION = 0.0

# Press-fit interference applied to the pocket radius (mm) by fit class.
# Negative => the pocket OD is undersized relative to the nominal bearing OD.
BEARING_INTERFERENCE: dict[str, float] = {
    "light": 0.00,
    "medium": -0.02,
    "heavy": -0.04,
}

# --------------------------------------------------------------------------- #
# Size dataclass
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Size:
    """A canonical hardware size.

    The four fields map 1:1 to the required size attributes from the task:
    nominal size, units, clearance class, and source chart.
    """

    nominal: str
    units: str
    clearance_class: str = "normal"
    source: str = ""


# --------------------------------------------------------------------------- #
# Metric coarse pitch table (ISO 68-1) -- fills the bare "M3" form.
# --------------------------------------------------------------------------- #
_METRIC_COARSE_PITCH: dict[float, float] = {
    2.0: 0.4,
    2.5: 0.45,
    3.0: 0.5,
    4.0: 0.7,
    5.0: 0.8,
    6.0: 1.0,
    8.0: 1.25,
}

_METRIC_RE = re.compile(
    r"^[mM](?P<dia>\d+(?:\.\d+)?)(?:\s*[-xX×*]\s*(?P<pitch>\d+(?:\.\d+)?))?$"
)
_FRACTION_RE = re.compile(r"^(?P<num>\d+)/(?P<den>\d+)\s*-\s*(?P<tpi>\d+)$")
_IMPERIAL_RE = re.compile(r"^(?:#)?(?P<num>\d+)\s*-\s*(?P<tpi>\d+)$")
_BEARING_RE = re.compile(r"^\d{3,4}$")

_VALID_CLEARANCE = ("close", "normal", "loose")

# Numbered imperial screw sizes -> actual major diameter (inches), for correct
# ascending-by-diameter ordering of mixed numbered + fractional imperial sets.
_IMPERIAL_NUMBER_MAJOR: dict[str, float] = {
    "0": 0.060,
    "1": 0.073,
    "2": 0.086,
    "3": 0.099,
    "4": 0.112,
    "5": 0.125,
    "6": 0.138,
    "8": 0.164,
    "10": 0.190,
    "12": 0.216,
}


# --------------------------------------------------------------------------- #
# Size-string constructors
# --------------------------------------------------------------------------- #
def metric(diameter_mm: float, pitch_mm: float | None = None) -> str:
    """Build a canonical metric nominal, e.g. ``metric(3.0) -> "M3-0.5"``.

    When ``pitch_mm`` is omitted, the ISO coarse pitch is looked up; an unknown
    diameter raises ``ValueError``.
    """
    if pitch_mm is None:
        pitch_mm = _METRIC_COARSE_PITCH.get(diameter_mm)
        if pitch_mm is None:
            raise ValueError(
                f"No coarse pitch known for M{diameter_mm:g}; "
                f"provide pitch explicitly, e.g. metric({diameter_mm:g}, 0.5)"
            )
    return f"M{diameter_mm:g}-{pitch_mm:g}"


def imperial(major: str, tpi: int) -> str:
    """Build a canonical imperial nominal, e.g. ``imperial("#6", 32) -> "#6-32"``.

    Numbered majors (``"6"``) gain a ``#`` prefix; fractional majors (``"1/4"``)
    do not.
    """
    major = major.strip()
    if "/" in major:
        return f"{major}-{tpi}"
    if not major.startswith("#"):
        major = "#" + major
    return f"{major}-{tpi}"


def bearing_608(size: str) -> str:
    """Normalize a bearing code, e.g. ``"608" -> "608"`` (whitespace stripped)."""
    s = size.strip()
    if not s.isdigit():
        raise ValueError(f"Invalid bearing code {size!r}; expected digits like '608'")
    return s


# --------------------------------------------------------------------------- #
# parse()
# --------------------------------------------------------------------------- #
def parse(spec: str, *, clearance_class: str = "normal") -> Size:
    """Normalize a size string to a :class:`Size`.

    Accepted forms (see API_CONTRACT.md §4.2):

      * ``"M3"``     -> metric, coarse pitch assumed -> nominal ``"M3-0.5"``
      * ``"M4-0.7"`` -> metric, explicit pitch
      * ``"#6-32"``  -> imperial numbered machine screw
      * ``"1/4-20"`` -> imperial fractional screw
      * ``"608"``    -> bearing size code

    Invalid sizes raise ``ValueError``.
    """
    if clearance_class not in _VALID_CLEARANCE:
        raise ValueError(
            f"Invalid clearance_class {clearance_class!r}; "
            f"expected one of {', '.join(_VALID_CLEARANCE)}"
        )

    s = spec.strip()

    m = _METRIC_RE.match(s)
    if m:
        diameter = float(m.group("dia"))
        pitch = float(m.group("pitch")) if m.group("pitch") else None
        return Size(metric(diameter, pitch), "metric", clearance_class)

    m = _FRACTION_RE.match(s)
    if m:
        nominal = imperial(f"{m.group('num')}/{m.group('den')}", int(m.group("tpi")))
        return Size(nominal, "imperial", clearance_class)

    m = _IMPERIAL_RE.match(s)
    if m:
        nominal = imperial(m.group("num"), int(m.group("tpi")))
        return Size(nominal, "imperial", clearance_class)

    if _BEARING_RE.match(s):
        return Size(bearing_608(s), "metric", clearance_class)

    raise ValueError(
        f"Unrecognized size {spec!r}; expected a metric size like 'M3'/'M4-0.7', "
        "an imperial size like '#6-32' or '1/4-20', or a bearing code like '608'"
    )


# --------------------------------------------------------------------------- #
# Sorting helper
# --------------------------------------------------------------------------- #
def _sort_key(nominal: str) -> tuple:
    """Order nominals ascending: metric first, then imperial, numeric bearings."""
    m = _METRIC_RE.match(nominal)
    if m:
        return (0, float(m.group("dia")), float(m.group("pitch") or 0))
    f = _FRACTION_RE.match(nominal)
    if f:
        return (1, int(f.group("num")) / int(f.group("den")), int(f.group("tpi")))
    i = _IMPERIAL_RE.match(nominal)
    if i:
        major = _IMPERIAL_NUMBER_MAJOR.get(i.group("num"), float(i.group("num")))
        return (1, major, int(i.group("tpi")))
    if nominal.isdigit():
        return (0, float(nominal), 0.0)
    return (2, 0.0, 0.0)


# --------------------------------------------------------------------------- #
# SizeChart
# --------------------------------------------------------------------------- #
_DATA_DIR = Path(__file__).with_name("data")


class SizeChart:
    """A validated, JSON-backed table of nominal dimensions (all mm).

    A chart file must match the fixed schema (API_CONTRACT.md §4.3):

    .. code-block:: json

        {
          "chart": "inserts",
          "units": "metric",
          "source": "cnc-kitchen",
          "columns": ["od", "length", "pilot"],
          "sizes": {"M3-0.5": {"od": 4.6, "length": 5.7, "pilot": 4.0}}
        }
    """

    def __init__(self, name: str):
        self.name = name
        path = _DATA_DIR / f"{name}.json"
        if not path.is_file():
            raise ValueError(f"No size chart named {name!r} (looked for {path})")
        self._data = json.loads(path.read_text(encoding="utf-8"))
        self._validate(self._data)

    # -- schema ------------------------------------------------------------
    @staticmethod
    def _validate(data: dict[str, Any]) -> None:
        for key in ("chart", "units", "source", "columns", "sizes"):
            if key not in data:
                raise ValueError(f"Size chart is missing required key {key!r}")
        if data["units"] not in ("metric", "imperial"):
            raise ValueError(
                f"Size chart units must be 'metric' or 'imperial', got {data['units']!r}"
            )
        if not isinstance(data["sizes"], dict):
            raise ValueError("Size chart 'sizes' must be an object keyed by nominal size")
        columns = list(data["columns"])
        for nominal, dims in data["sizes"].items():
            if not isinstance(dims, dict):
                raise ValueError(f"Size {nominal!r} dims must be an object")
            for col in columns:
                if col not in dims:
                    raise ValueError(f"Size {nominal!r} is missing column {col!r}")
                value = dims[col]
                # Dimension columns are numeric; categorical columns (e.g. nut
                # "type") are strings. Anything else is a malformed chart.
                if not isinstance(value, (int, float, str)):
                    raise ValueError(
                        f"Size {nominal!r} column {col!r} must be numeric or a "
                        f"string, got {value!r}"
                    )

    # -- accessors ---------------------------------------------------------
    def sizes(self) -> list[str]:
        """Nominal size ids, sorted ascending (metric before imperial)."""
        return sorted(self._data["sizes"], key=_sort_key)

    def get(self, nominal: str) -> dict[str, Any]:
        """Return the dimension dict for ``nominal``, or raise ``ValueError``."""
        try:
            return dict(self._data["sizes"][nominal])
        except KeyError:
            valid = ", ".join(self.sizes())
            raise ValueError(
                f"Size {nominal!r} not in chart {self.name!r}; valid sizes: {valid}"
            ) from None

    @property
    def source(self) -> str:
        return self._data["source"]

    @property
    def units(self) -> str:
        return self._data["units"]

    @property
    def columns(self) -> list[str]:
        return list(self._data["columns"])

    def quick_ref(self) -> str:
        """Render this chart's raw columns as a SIZES table (no USAGE block)."""
        from ._quick_ref import table  # local import avoids a cycle

        headers = ["Size"] + self.columns
        rows = [
            [nom] + [str(dims[c]) for c in self.columns]
            for nom, dims in self._data["sizes"].items()
        ]
        rows.sort(key=lambda r: _sort_key(r[0]))
        return table(headers, rows)
