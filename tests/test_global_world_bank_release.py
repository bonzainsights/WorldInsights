import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from scripts.build_global_world_bank_release import build_global_live_release
from worldinsights.geographies import CountryRegistryEntry, iso_m49_country_registry
from worldinsights.providers.world_bank import WorldBankError


FIXED_RETRIEVAL = datetime(2026, 7, 31, 9, 0, tzinfo=timezone.utc)
LIFE_EXPECTANCY_CODE = "SP.DYN.LE00.IN"
LIFE_EXPECTANCY_ID = "wb.sp.dyn.le00.in"
INDICATORS = {
    "SP.POP.TOTL": "Population, total",
    "NY.GDP.PCAP.CD": "GDP per capita (current US$)",
    LIFE_EXPECTANCY_CODE: "Life expectancy at birth, total (years)",
}


def registry_subset() -> tuple[CountryRegistryEntry, ...]:
    entries = {
        entry.provider_code: entry
        for entry in iso_m49_country_registry()
        if entry.provider_code in {"DEU", "NPL", "USA"}
    }
    return tuple(entries[code] for code in ("DEU", "NPL", "USA"))


def country_catalog_payload() -> list[object]:
    def row(code: str, name: str, region: str) -> dict[str, object]:
        return {
            "id": code,
            "iso2Code": code[:2],
            "name": name,
            "region": {"id": "ECS", "iso2code": "Z7", "value": region},
        }

    rows = [
        row("USA", "United States", "North America"),
        row("DEU", "Germany", "Europe & Central Asia"),
        row("NPL", "Nepal", "South Asia"),
        {
            "id": "WLD",
            "iso2Code": "1W",
            "name": "World",
            "region": {"id": "NA", "iso2code": "NA", "value": "Aggregates"},
        },
        row("XKX", "Kosovo", "Europe & Central Asia"),
    ]
    return [{"page": 1, "pages": 1, "per_page": "400", "total": len(rows)}, rows]


def indicator_payload(
    indicator_code: str,
    *,
    missing_key: tuple[str, int] | None = None,
) -> list[object]:
    rows: list[dict[str, object]] = []
    country_names = {"DEU": "Germany", "NPL": "Nepal", "USA": "United States"}
    for country_index, code in enumerate(("DEU", "NPL", "USA"), start=1):
        for year in (2022, 2023):
            if missing_key == (code, year):
                continue
            value = float(country_index * 1_000 + year)
            rows.append(
                {
                    "indicator": {"id": indicator_code, "value": INDICATORS[indicator_code]},
                    "country": {"id": code[:2], "value": country_names[code]},
                    "countryiso3code": code,
                    "date": str(year),
                    "value": value,
                    "unit": "",
                    "obs_status": "",
                    "decimal": 0,
                }
            )
    return [{"page": 1, "pages": 1, "per_page": "20000", "total": len(rows)}, rows]


def fixture_fetcher(
    *,
    missing_key: tuple[str, int] | None = None,
    requested_urls: list[str] | None = None,
):
    payloads = {
        code: indicator_payload(code, missing_key=missing_key)
        for code in INDICATORS
    }

    def fetch(url: str) -> Any:
        if requested_urls is not None:
            requested_urls.append(url)
        if url.endswith("/country?format=json&per_page=400"):
            return copy.deepcopy(country_catalog_payload())
        for code, payload in payloads.items():
            if f"/indicator/{code}?" in url:
                return copy.deepcopy(payload)
        raise AssertionError(f"unexpected World Bank URL: {url}")

    return fetch


def file_snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_global_builder_intersects_catalog_and_builds_m49_release(tmp_path: Path) -> None:
    requested_urls: list[str] = []
    latest_path = build_global_live_release(
        tmp_path,
        start_year=2022,
        end_year=2023,
        retrieved_at=FIXED_RETRIEVAL,
        fetch_payload=fixture_fetcher(requested_urls=requested_urls),
        registry=registry_subset(),
    )

    assert len(requested_urls) == 4
    assert requested_urls[0].endswith("/country?format=json&per_page=400")
    assert all(
        "/country/DEU;NPL;USA/indicator/" in url
        for url in requested_urls[1:]
    )
    assert all("date=2022%3A2023" in url for url in requested_urls[1:])
    assert any(f"/indicator/{LIFE_EXPECTANCY_CODE}?" in url for url in requested_urls[1:])

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["release_id"] == "world-bank-global-indicators-2022-2023-20260731T090000Z"
    release_root = tmp_path / "releases" / latest["release_id"]
    catalog = json.loads((release_root / "catalog.json").read_text(encoding="utf-8"))

    assert catalog["release"]["pipeline_version"] == "0.9.0"
    assert len(catalog["release"]["source_checksum"]) == 64
    assert {
        item["canonical_code"]: item["geography_id"]
        for item in catalog["geographies"]
    } == {"DEU": 276, "NPL": 524, "USA": 840}
    assert [item["indicator_variant_id"] for item in catalog["indicators"]] == [
        "wb.ny.gdp.pcap.cd",
        LIFE_EXPECTANCY_ID,
        "wb.sp.pop.totl",
    ]
    assert {item["row_count"] for item in catalog["indicators"]} == {6}
    life_expectancy = next(
        item for item in catalog["indicators"]
        if item["indicator_variant_id"] == LIFE_EXPECTANCY_ID
    )
    assert life_expectancy["provider_indicator_code"] == LIFE_EXPECTANCY_CODE
    assert life_expectancy["concept_id"] == "health.life_expectancy_at_birth.total"
    assert life_expectancy["unit_id"] == "years"


def test_global_builder_is_deterministic_for_fixed_inputs(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    arguments = {
        "start_year": 2022,
        "end_year": 2023,
        "retrieved_at": FIXED_RETRIEVAL,
        "fetch_payload": fixture_fetcher(),
        "registry": registry_subset(),
    }

    build_global_live_release(first, **arguments)
    build_global_live_release(second, **arguments)

    assert file_snapshot(first) == file_snapshot(second)


def test_global_builder_rejects_incomplete_indicator_grid(tmp_path: Path) -> None:
    with pytest.raises(WorldBankError, match="grid mismatch"):
        build_global_live_release(
            tmp_path,
            start_year=2022,
            end_year=2023,
            retrieved_at=FIXED_RETRIEVAL,
            fetch_payload=fixture_fetcher(missing_key=("NPL", 2023)),
            registry=registry_subset(),
        )


def test_global_builder_validates_time_arguments(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="start_year"):
        build_global_live_release(
            tmp_path,
            start_year=2024,
            end_year=2023,
            fetch_payload=fixture_fetcher(),
            registry=registry_subset(),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        build_global_live_release(
            tmp_path,
            start_year=2022,
            end_year=2023,
            retrieved_at=datetime(2026, 7, 31, 9, 0),
            fetch_payload=fixture_fetcher(),
            registry=registry_subset(),
        )
