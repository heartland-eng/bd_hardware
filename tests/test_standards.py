"""Tests for the clearance-hole standards lookup.

These are pure data tests — no OCP geometry — so they run fast and never
touch the CAD kernel.
"""

import pytest

from bd_hardware import clearance_diameter


@pytest.mark.parametrize(
    "nominal,close,normal,loose",
    [
        (1.6, 1.8, 2.0, 2.4),
        (2.0, 2.2, 2.4, 2.7),
        (2.5, 2.7, 2.9, 3.2),
        (3.0, 3.2, 3.4, 3.7),
        (4.0, 4.3, 4.5, 4.8),
        (5.0, 5.3, 5.5, 5.9),
        (6.0, 6.4, 6.6, 7.0),
        (8.0, 8.4, 9.0, 10.0),
        (10.0, 10.5, 11.0, 12.0),
        (30.0, 31.0, 33.0, 35.0),
    ],
)
def test_clearance_diameter_values(nominal, close, normal, loose):
    assert clearance_diameter(nominal, "close") == close
    assert clearance_diameter(nominal, "normal") == normal
    assert clearance_diameter(nominal, "loose") == loose


def test_default_fit_is_normal():
    assert clearance_diameter(3.0) == clearance_diameter(3.0, "normal")


def test_unknown_size_raises_loudly():
    # A size we do not table (e.g. M7) must fail, not silently interpolate.
    with pytest.raises(KeyError):
        clearance_diameter(7.0)


def test_unknown_fit_raises():
    with pytest.raises(ValueError):
        clearance_diameter(3.0, "snug")
