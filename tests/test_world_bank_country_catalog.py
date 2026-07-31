import pytest

from worldinsights.geographies import iso_m49_country_registry
from worldinsights.providers.world_bank import WorldBankError
from worldinsights.providers.world_bank_countries import (
    build_country_catalog_url,
    parse_country_catalog,
    supported_iso_registry_entries,
)


def make_payload(*rows: dict[str, object]) -> list[object]:
    return [
        {"page": 1, "pages": 1, "per_page": "400", "total": len(rows)},
        list(rows),
    ]


def make_row(code: str, name: str, region: str = "Europe & Central Asia") -> dict[str, object]:
    aggregate = region == "Aggregates"
    return {
        "id": code,
        "iso2Code": code[:2],
        "name": name,
        "region": {
            "id": "NA" if aggregate else "ECS",
            "iso2code": "NA" if aggregate else "Z7",
            "value": region,
        },
    }


def test_country_catalog_url_is_bounded_and_official() -> None:
    assert build_country_catalog_url() == (
        "https://api.worldbank.org/v2/country?format=json&per_page=400"
    )
    with pytest.raises(ValueError, match="positive"):
        build_country_catalog_url(per_page=0)


def test_catalog_parsing_is_strict_sorted_and_complete() -> None:
    parsed = parse_country_catalog(
        make_payload(make_row("USA", "United States"), make_row("DEU", "Germany"))
    )
    assert [entry.provider_code for entry in parsed] == ["DEU", "USA"]
    assert parsed[0].name == "Germany"
    assert not parsed[0].is_aggregate

    broken = make_payload(make_row("DEU", "Germany"))
    metadata = broken[0]
    assert isinstance(metadata, dict)
    metadata["total"] = 2
    with pytest.raises(WorldBankError, match="metadata total"):
        parse_country_catalog(broken)


def test_catalog_rejects_pagination_duplicates_and_malformed_rows() -> None:
    paginated = make_payload(make_row("DEU", "Germany"))
    metadata = paginated[0]
    assert isinstance(metadata, dict)
    metadata["pages"] = 2
    with pytest.raises(WorldBankError, match="one complete page"):
        parse_country_catalog(paginated)

    with pytest.raises(WorldBankError, match="duplicate"):
        parse_country_catalog(
            make_payload(make_row("DEU", "Germany"), make_row("DEU", "Germany"))
        )

    with pytest.raises(WorldBankError, match="region metadata"):
        parse_country_catalog(make_payload({"id": "DEU", "name": "Germany"}))


def test_supported_registry_intersection_excludes_aggregates_and_reviewed_non_iso() -> None:
    parsed = parse_country_catalog(
        make_payload(
            make_row("DEU", "Germany"),
            make_row("NPL", "Nepal", "South Asia"),
            make_row("USA", "United States", "North America"),
            make_row("WLD", "World", "Aggregates"),
            make_row("CHI", "Channel Islands"),
            make_row("XKX", "Kosovo"),
        )
    )
    registry = [
        entry
        for entry in iso_m49_country_registry()
        if entry.provider_code in {"DEU", "NPL", "USA"}
    ]
    supported = supported_iso_registry_entries(parsed, registry=registry)
    assert [entry.provider_code for entry in supported] == ["DEU", "NPL", "USA"]
    assert [entry.geography_id for entry in supported] == [276, 524, 840]


def test_unreviewed_non_iso_provider_code_fails_closed() -> None:
    parsed = parse_country_catalog(make_payload(make_row("ZZZ", "Unknown Entity")))
    with pytest.raises(WorldBankError, match="unreviewed non-ISO"):
        supported_iso_registry_entries(parsed, registry=iso_m49_country_registry())
