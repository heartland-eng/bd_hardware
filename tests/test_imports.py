"""Acceptance: the package and every module import cleanly."""

import importlib


def test_package_imports():
    import bd_hardware as bdh

    assert bdh.__version__ == "0.1.0"


def test_each_module_imports():
    for name in ("fastener", "inserts", "nuts", "snap_fit", "bearings"):
        mod = importlib.import_module(f"bd_hardware.{name}")
        assert callable(getattr(mod, "quick_ref"))


def test_package_reexports_modules():
    import bd_hardware as bdh

    for name in ("fastener", "inserts", "nuts", "snap_fit", "bearings"):
        assert hasattr(bdh, name)
