import json
from pathlib import Path

from scripts.build_sample_release import build_sample


def test_sample_release_builds_real_multi_indicator_catalog(tmp_path: Path) -> None:
    latest_path = build_sample(tmp_path)
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    release_root = tmp_path / "releases" / latest["release_id"]
    catalog = json.loads((release_root / "catalog.json").read_text(encoding="utf-8"))

    assert latest["schema_version"] == 2
    assert latest["release_id"] == "world-bank-indicators-2023-sample"
    assert [entry["indicator_variant_id"] for entry in catalog["indicators"]] == [
        "wb.ny.gdp.pcap.cd",
        "wb.sp.pop.totl",
    ]
    assert [geography["name"] for geography in catalog["geographies"]] == [
        "Germany",
        "Nepal",
        "United States",
    ]

    population_root = release_root / "indicators" / "wb.sp.pop.totl"
    gdp_root = release_root / "indicators" / "wb.ny.gdp.pcap.cd"
    population = json.loads((population_root / "observations.json").read_text(encoding="utf-8"))
    gdp = json.loads((gdp_root / "observations.json").read_text(encoding="utf-8"))
    population_coverage = json.loads((population_root / "coverage.json").read_text(encoding="utf-8"))
    gdp_coverage = json.loads((gdp_root / "coverage.json").read_text(encoding="utf-8"))

    assert [row["value"] for row in population] == [83280000.0, 30896590.0, 334914895.0]
    assert [row["value"] for row in gdp] == [54776.8, 1382.4, 82586.8]
    assert population_coverage["geography_ids"] == [1, 2, 3]
    assert gdp_coverage["geography_ids"] == [1, 2, 3]
    assert population_coverage["periods"] == gdp_coverage["periods"] == ["2023"]
    assert all(row["status"] == "observed" for row in population + gdp)
