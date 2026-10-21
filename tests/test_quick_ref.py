"""Acceptance: every module's quick_ref() returns the fixed format."""

import bd_hardware as bdh

_MODULES = (bdh.fastener, bdh.inserts, bdh.nuts, bdh.snap_fit, bdh.bearings)
_NAMES = ("fastener", "inserts", "nuts", "snap_fit", "bearings")


def test_module_quick_ref_shape():
    for mod in _MODULES:
        text = mod.quick_ref()
        assert isinstance(text, str)
        assert text.startswith("== ")
        assert "USAGE" in text
        assert "SIZES" in text
        assert text.endswith("\n")


def test_module_quick_ref_header_matches_module_name():
    for name, mod in zip(_NAMES, _MODULES):
        assert mod.quick_ref().startswith(f"== {name} ==")


def test_package_quick_ref_all_and_one():
    all_text = bdh.quick_ref()
    for name in _NAMES:
        assert f"== {name} ==" in all_text

    one = bdh.quick_ref("bearings")
    assert one.startswith("== bearings ==")


def test_quick_ref_unknown_module_raises():
    import pytest

    with pytest.raises(ValueError):
        bdh.quick_ref("does_not_exist")
