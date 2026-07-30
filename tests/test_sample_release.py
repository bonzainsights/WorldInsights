import json
from pathlib import Path

from scripts.build_sample_release import build_sample


def test_sample_release_builds_real_multi_indicator_history(tmp_path: Path) -> None:
    latest_path = build_sample(tmp_path)
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    release_root = tmp_path / "releases" / latest["release_id"]
    catalog = json.loads((release_root / "catalog.json").read_text(encoding="utf-8"))

    assert latest["schema_version"] == 2
    assert latest["release_id"] == "world-bank-indicators-2019-2023-sample"
    assert [entry["indicator_variant_id"] for entry in catalog["indicators"]] == [
        "wb.ny.gdp.pcap.cd",
        "wb.sp.pop.totl",
    ]
    assert [entry["row_count"] for entry in catalog["indicators"]] == [15, 15]
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

    population_values = {
        (row["geography_id"], row["period_label"]): row["value"] for row in population
    }
    gdp_values = {(row["geography_id"], row["period_label"]): row["value"] for row in gdp}

    assert len(population) == len(gdp) == 15
    assert population_values[(1, "2019")] == 83_092_962.0
    assert population_values[(3, "2023")] == 336_806_231.0
    assert gdp_values[(2, "2019")] == 1_203.1
    assert gdp_values[(3, "2023")] == 82_586.8
    assert population_coverage["geography_ids"] == [1, 2, 3]
    assert gdp_coverage["geography_ids"] == [1, 2, 3]
    assert population_coverage["periods"] == gdp_coverage["periods"] == [
        "2019",
        "2020",
        "2021",
        "2022",
        "2023",
    ]
    assert all(row["status"] == "observed" for row in population + gdp)
