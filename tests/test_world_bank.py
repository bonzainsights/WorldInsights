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
    assert "/country/all/indicator/SP.POP.TOTL" in url
    assert "date=2020%3A2024" in url
    assert "per_page=20000" in url


def test_build_url_scopes_and_sorts_explicit_country_codes() -> None:
    url = adapter().build_indicator_url(
        "SP.POP.TOTL",
        start_year=2019,
        end_year=2023,
        country_codes=["usa", "DEU", "npl"],
    )

    assert "/country/DEU;NPL;USA/indicator/SP.POP.TOTL" in url
    assert "date=2019%3A2023" in url


@pytest.mark.parametrize(
    "country_codes, message",
    [
        ([], "cannot be empty"),
        (["DE"], "three ASCII letters"),
        (["D3U"], "three ASCII letters"),
        (["DEU", "deu"], "duplicate country code"),
    ],
)
def test_build_url_rejects_invalid_country_scopes(
    country_codes: list[str],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        adapter().build_indicator_url(
            "SP.POP.TOTL",
            start_year=2019,
            end_year=2023,
            country_codes=country_codes,
        )


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


def test_normalizes_pinned_gdp_per_capita_fixture() -> None:
    from worldinsights.providers.world_bank import (
        GDP_PER_CAPITA_CURRENT_USD_UNIT_ID,
        GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID,
    )

    fixture = ROOT / "tests/fixtures/world_bank/gdp_per_capita_2023_page.json"
    instance = adapter()
    records = instance.parse_records(json.loads(fixture.read_text(encoding="utf-8")))
    observations = instance.normalize_records(
        records,
        release_id="world-bank-gdp-per-capita-2023-sample",
        indicator_variant_id=GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID,
        unit_id=GDP_PER_CAPITA_CURRENT_USD_UNIT_ID,
    )

    assert records[0].indicator_code == "NY.GDP.PCAP.CD"
    assert records[0].indicator_name == "GDP per capita (current US$)"
    assert [row.geography_id for row in observations] == [1, 2, 3]
    assert [row.value for row in observations] == [54776.8, 1382.4, 82586.8]
    assert all(row.period.label == "2023" for row in observations)
    assert all(row.unit_id == "current_usd_per_person" for row in observations)


def test_builds_gdp_per_capita_query_url() -> None:
    from worldinsights.providers.world_bank import GDP_PER_CAPITA_CURRENT_USD_CODE

    url = adapter().build_indicator_url(
        GDP_PER_CAPITA_CURRENT_USD_CODE,
        start_year=2023,
        end_year=2023,
    )

    assert "/indicator/NY.GDP.PCAP.CD" in url
    assert "date=2023%3A2023" in url
