import json
from pathlib import Path

import pytest

from worldinsights.contracts import ObservationStatus
from worldinsights.providers.world_bank import WorldBankAdapter, WorldBankError


ROOT = Path(__file__).resolve().parents[1]
MAPPINGS = ROOT / "data/mappings/world_bank_geographies.json"
FIXTURE = ROOT / "tests/fixtures/world_bank/population_page.json"


def adapter() -> WorldBankAdapter:
    return WorldBankAdapter.from_mapping_file(MAPPINGS)


def payload() -> object:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def test_build_url_is_bounded_and_encoded() -> None:
    url = adapter().build_indicator_url("SP.POP.TOTL", start_year=2020, end_year=2024)

    assert url.startswith("https://api.worldbank.org/v2/")
    assert "date=2020%3A2024" in url
    assert "per_page=20000" in url


def test_fixture_parses_records() -> None:
    records = adapter().parse_records(payload())

    assert len(records) == 4
    assert records[0].country_code == "DEU"
    assert records[1].observation_status == "E"
    assert records[-1].value is None


def test_records_normalize_without_conflating_missing_and_zero() -> None:
    instance = adapter()
    observations = instance.normalize_records(
        instance.parse_records(payload()),
        release_id="wb-2023-test",
        indicator_variant_id="wb.sp.pop.totl",
        unit_id="people",
    )

    assert observations[0].value == 83280000
    assert observations[1].provider_quality_flags == ("E",)
    assert observations[-1].status is ObservationStatus.MISSING
    assert observations[-1].value is None


def test_unknown_geography_fails_closed() -> None:
    raw = payload()
    assert isinstance(raw, list)
    raw[1][0]["countryiso3code"] = "ZZZ"
    instance = adapter()

    with pytest.raises(WorldBankError, match="unknown World Bank geography"):
        instance.normalize_records(
            instance.parse_records(raw),
            release_id="wb-2023-test",
            indicator_variant_id="wb.sp.pop.totl",
            unit_id="people",
        )


def test_paginated_response_is_rejected() -> None:
    raw = payload()
    assert isinstance(raw, list)
    raw[0]["pages"] = 2

    with pytest.raises(WorldBankError, match="paginated"):
        adapter().parse_records(raw)
