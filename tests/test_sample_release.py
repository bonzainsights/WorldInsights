import json
from pathlib import Path

from scripts.build_sample_release import build_sample


LIFE_EXPECTANCY_ID = "wb.sp.dyn.le00.in"


def test_sample_release_builds_real_three_indicator_history(tmp_path: Path) -> None:
    latest_path = build_sample(tmp_path)
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    release_root = tmp_path / "releases" / latest["release_id"]
    catalog = json.loads((release_root / "catalog.json").read_text(encoding="utf-8"))

    assert latest["schema_version"] == 2
    assert latest["release_id"] == "world-bank-indicators-2019-2023-sample"
    assert catalog["release"]["pipeline_version"] == "0.9.0"
    assert len(catalog["release"]["source_checksum"]) == 64
    assert [entry["indicator_variant_id"] for entry in catalog["indicators"]] == [
        "wb.ny.gdp.pcap.cd",
        LIFE_EXPECTANCY_ID,
        "wb.sp.pop.totl",
    ]
    assert [entry["row_count"] for entry in catalog["indicators"]] == [15, 15, 15]
    assert [geography["geography_id"] for geography in catalog["geographies"]] == [
        276,
        524,
        840,
    ]
    assert [geography["name"] for geography in catalog["geographies"]] == [
        "Germany",
        "Nepal",
        "United States",
    ]

    life_expectancy_catalog = next(
        entry
        for entry in catalog["indicators"]
        if entry["indicator_variant_id"] == LIFE_EXPECTANCY_ID
    )
    assert life_expectancy_catalog["provider_indicator_code"] == "SP.DYN.LE00.IN"
    assert life_expectancy_catalog["name"] == "Life expectancy at birth, total (years)"
    assert life_expectancy_catalog["concept_id"] == "health.life_expectancy_at_birth.total"
    assert life_expectancy_catalog["unit_id"] == "years"

    population_root = release_root / "indicators" / "wb.sp.pop.totl"
    gdp_root = release_root / "indicators" / "wb.ny.gdp.pcap.cd"
    life_expectancy_root = release_root / "indicators" / LIFE_EXPECTANCY_ID
    population = json.loads((population_root / "observations.json").read_text(encoding="utf-8"))
    gdp = json.loads((gdp_root / "observations.json").read_text(encoding="utf-8"))
    life_expectancy = json.loads(
        (life_expectancy_root / "observations.json").read_text(encoding="utf-8")
    )
    population_coverage = json.loads((population_root / "coverage.json").read_text(encoding="utf-8"))
    gdp_coverage = json.loads((gdp_root / "coverage.json").read_text(encoding="utf-8"))
    life_expectancy_coverage = json.loads(
        (life_expectancy_root / "coverage.json").read_text(encoding="utf-8")
    )

    population_values = {
        (row["geography_id"], row["period_label"]): row["value"] for row in population
    }
    gdp_values = {(row["geography_id"], row["period_label"]): row["value"] for row in gdp}
    life_expectancy_values = {
        (row["geography_id"], row["period_label"]): row["value"]
        for row in life_expectancy
    }

    assert len(population) == len(gdp) == len(life_expectancy) == 15
    assert population_values[(276, "2019")] == 83_092_962.0
    assert population_values[(840, "2023")] == 336_806_231.0
    assert gdp_values[(524, "2019")] == 1_203.1
    assert gdp_values[(840, "2023")] == 82_586.8
    assert life_expectancy_values[(276, "2019")] == 81.2926829268293
    assert life_expectancy_values[(524, "2021")] == 68.385
    assert life_expectancy_values[(840, "2023")] == 78.3853658536585

    expected_geography_ids = [276, 524, 840]
    assert population_coverage["geography_ids"] == expected_geography_ids
    assert gdp_coverage["geography_ids"] == expected_geography_ids
    assert life_expectancy_coverage["geography_ids"] == expected_geography_ids
    expected_periods = ["2019", "2020", "2021", "2022", "2023"]
    assert population_coverage["periods"] == expected_periods
    assert gdp_coverage["periods"] == expected_periods
    assert life_expectancy_coverage["periods"] == expected_periods
    assert all(
        row["status"] == "observed"
        for row in population + gdp + life_expectancy
    )
