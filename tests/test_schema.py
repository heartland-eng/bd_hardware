"""Every data/*.json chart loads through the schema-validating SizeChart."""

from pathlib import Path

import bd_hardware as bdh
from bd_hardware._sizes import SizeChart


def test_all_charts_load():
    data_dir = Path(bdh.__file__).with_name("data")
    charts = sorted(p.stem for p in data_dir.glob("*.json"))
    assert charts, "no data charts found"
    for name in charts:
        chart = SizeChart(name)
        assert chart.sizes(), f"{name} has no sizes"
        # every size resolves and carries every declared column
        for nominal in chart.sizes():
            dims = chart.get(nominal)
            for col in chart.columns:
                assert col in dims, f"{name}/{nominal} missing {col}"


def test_parse_metric_coarse_pitch():
    from bd_hardware._sizes import parse

    assert parse("M3").nominal == "M3-0.5"
    assert parse("M4-0.7").nominal == "M4-0.7"
    assert parse("#6-32").nominal == "#6-32"
    assert parse("608").nominal == "608"


def test_parse_invalid_raises():
    import pytest

    from bd_hardware._sizes import parse

    with pytest.raises(ValueError):
        parse("banana")
    with pytest.raises(ValueError):
        parse("M3", clearance_class="banana")
