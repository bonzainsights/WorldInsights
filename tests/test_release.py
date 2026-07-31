import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from worldinsights.contracts import (
    DataRelease,
    Frequency,
    Geography,
    GeographyType,
    IndicatorVariant,
    Observation,
    ObservationStatus,
    Period,
)
from worldinsights.release import build_static_release, canonical_json_bytes, sha256_bytes




def geographies() -> list[Geography]:
    return [
        Geography(1, "DEU", "Germany", GeographyType.COUNTRY),
        Geography(2, "NPL", "Nepal", GeographyType.COUNTRY),
        Geography(3, "USA", "United States", GeographyType.COUNTRY),
    ]

def indicator() -> IndicatorVariant:
    return IndicatorVariant(
        indicator_variant_id="wb.sp.pop.totl",
        provider_id="world-bank",
        dataset_id="indicators",
        provider_indicator_code="SP.POP.TOTL",
        name="Population, total",
        concept_id="population.total",
        unit_id="people",
        frequency=Frequency.ANNUAL,
        geography_types=frozenset({GeographyType.COUNTRY}),
    )


def release() -> DataRelease:
    return DataRelease(
        release_id="wb-2023-test",
        provider_id="world-bank",
        dataset_id="indicators",
        retrieved_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        source_checksum="source-checksum",
        pipeline_version="0.1.0",
    )


def observations() -> list[Observation]:
    return [
        Observation(
            release_id="wb-2023-test",
            indicator_variant_id="wb.sp.pop.totl",
            geography_id=2,
            period=Period.annual(2023),
            unit_id="people",
            status=ObservationStatus.OBSERVED,
            value=30_896_590,
        ),
        Observation(
            release_id="wb-2023-test",
            indicator_variant_id="wb.sp.pop.totl",
            geography_id=1,
            period=Period.annual(2023),
            unit_id="people",
            status=ObservationStatus.OBSERVED,
            value=83_280_000,
        ),
    ]


def test_canonical_json_is_order_independent() -> None:
    left = canonical_json_bytes({"b": 2, "a": 1})
    right = canonical_json_bytes({"a": 1, "b": 2})

    assert left == right
    assert sha256_bytes(left) == sha256_bytes(right)


def test_static_release_is_sorted_and_checksummed(tmp_path: Path) -> None:
    artifacts = build_static_release(
        output_root=tmp_path,
        release=release(),
        indicator=indicator(),
        observations=observations(),
    )

    rows = json.loads(artifacts.observations_path.read_text(encoding="utf-8"))
    manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    coverage = json.loads(artifacts.coverage_path.read_text(encoding="utf-8"))
    latest = json.loads(artifacts.latest_path.read_text(encoding="utf-8"))

    assert [row["geography_id"] for row in rows] == [1, 2]
    assert coverage["geography_ids"] == [1, 2]
    assert coverage["periods"] == ["2023"]
    assert manifest["row_count"] == 2
    assert manifest["files"]["observations.json"]["sha256"] == sha256_bytes(
        artifacts.observations_path.read_bytes()
    )
    assert latest["release_id"] == "wb-2023-test"
    assert latest["manifest"] == "releases/wb-2023-test/manifest.json"


def test_existing_immutable_release_is_not_overwritten(tmp_path: Path) -> None:
    arguments = {
        "output_root": tmp_path,
        "release": release(),
        "indicator": indicator(),
        "observations": observations(),
    }
    build_static_release(**arguments)

    with pytest.raises(FileExistsError, match="immutable release"):
        build_static_release(**arguments)


def test_release_rejects_mismatched_observation_release(tmp_path: Path) -> None:
    bad = observations()[0]
    mismatched = Observation(
        release_id="other-release",
        indicator_variant_id=bad.indicator_variant_id,
        geography_id=bad.geography_id,
        period=bad.period,
        unit_id=bad.unit_id,
        status=bad.status,
        value=bad.value,
    )

    with pytest.raises(ValueError, match="release IDs"):
        build_static_release(
            output_root=tmp_path,
            release=release(),
            indicator=indicator(),
            observations=[mismatched],
        )


def second_indicator() -> IndicatorVariant:
    return IndicatorVariant(
        indicator_variant_id="test.gdp.per.capita",
        provider_id="world-bank",
        dataset_id="indicators",
        provider_indicator_code="TEST.GDP.PC",
        name="Synthetic GDP per capita fixture",
        concept_id="economy.gdp.per_capita",
        unit_id="test_currency_per_person",
        frequency=Frequency.ANNUAL,
        geography_types=frozenset({GeographyType.COUNTRY}),
    )


def second_observations() -> list[Observation]:
    return [
        Observation(
            release_id="wb-2023-test",
            indicator_variant_id="test.gdp.per.capita",
            geography_id=3,
            period=Period.annual(2022),
            unit_id="test_currency_per_person",
            status=ObservationStatus.OBSERVED,
            value=30.0,
        ),
        Observation(
            release_id="wb-2023-test",
            indicator_variant_id="test.gdp.per.capita",
            geography_id=2,
            period=Period.annual(2022),
            unit_id="test_currency_per_person",
            status=ObservationStatus.OBSERVED,
            value=20.0,
        ),
    ]


def test_catalog_release_is_deterministic_and_partitioned_by_indicator(tmp_path: Path) -> None:
    from worldinsights.release import IndicatorReleaseInput, build_catalog_release

    artifacts = build_catalog_release(
        output_root=tmp_path,
        release=release(),
        indicators=[
            IndicatorReleaseInput(second_indicator(), tuple(second_observations())),
            IndicatorReleaseInput(indicator(), tuple(observations())),
        ],
        geographies=geographies(),
    )

    catalog = json.loads(artifacts.catalog_path.read_text(encoding="utf-8"))
    latest = json.loads(artifacts.latest_path.read_text(encoding="utf-8"))

    assert catalog["schema_version"] == 2
    assert [(item["geography_id"], item["canonical_code"]) for item in catalog["geographies"]] == [
        (1, "DEU"),
        (2, "NPL"),
        (3, "USA"),
    ]
    assert [entry["indicator_variant_id"] for entry in catalog["indicators"]] == [
        "test.gdp.per.capita",
        "wb.sp.pop.totl",
    ]
    assert catalog["indicators"][0]["coverage"] == (
        "indicators/test.gdp.per.capita/coverage.json"
    )
    assert catalog["indicators"][1]["observations"] == (
        "indicators/wb.sp.pop.totl/observations.json"
    )
    assert latest == {
        "schema_version": 2,
        "release_id": "wb-2023-test",
        "catalog": "releases/wb-2023-test/catalog.json",
        "catalog_sha256": sha256_bytes(artifacts.catalog_path.read_bytes()),
    }

    population_coverage = json.loads(
        (artifacts.release_directory / "indicators/wb.sp.pop.totl/coverage.json").read_text()
    )
    synthetic_coverage = json.loads(
        (
            artifacts.release_directory
            / "indicators/test.gdp.per.capita/coverage.json"
        ).read_text()
    )
    assert population_coverage["geography_ids"] == [1, 2]
    assert population_coverage["periods"] == ["2023"]
    assert synthetic_coverage["geography_ids"] == [2, 3]
    assert synthetic_coverage["periods"] == ["2022"]

    for path, metadata in catalog["files"].items():
        assert metadata["sha256"] == sha256_bytes(
            (artifacts.release_directory / path).read_bytes()
        )


def test_catalog_release_rejects_duplicate_indicator_ids(tmp_path: Path) -> None:
    from worldinsights.release import IndicatorReleaseInput, build_catalog_release

    item = IndicatorReleaseInput(indicator(), tuple(observations()))
    with pytest.raises(ValueError, match="indicator IDs must be unique"):
        build_catalog_release(
            output_root=tmp_path,
            release=release(),
            indicators=[item, item],
            geographies=geographies(),
        )


def test_catalog_release_rejects_mismatched_indicator_observations(tmp_path: Path) -> None:
    from worldinsights.release import IndicatorReleaseInput, build_catalog_release

    with pytest.raises(ValueError, match="observation indicator"):
        build_catalog_release(
            output_root=tmp_path,
            release=release(),
            indicators=[
                IndicatorReleaseInput(indicator(), tuple(second_observations())),
            ],
            geographies=geographies(),
        )


def test_catalog_release_rejects_unsafe_asset_identifiers(tmp_path: Path) -> None:
    from worldinsights.release import IndicatorReleaseInput, build_catalog_release

    unsafe = IndicatorVariant(
        indicator_variant_id="../escape",
        provider_id="world-bank",
        dataset_id="indicators",
        provider_indicator_code="ESCAPE",
        name="Unsafe fixture",
        concept_id="test.unsafe",
        unit_id="people",
        frequency=Frequency.ANNUAL,
        geography_types=frozenset({GeographyType.COUNTRY}),
    )
    row = Observation(
        release_id="wb-2023-test",
        indicator_variant_id="../escape",
        geography_id=1,
        period=Period.annual(2023),
        unit_id="people",
        status=ObservationStatus.OBSERVED,
        value=1.0,
    )
    with pytest.raises(ValueError, match="unsafe static asset identifier"):
        build_catalog_release(
            output_root=tmp_path,
            release=release(),
            indicators=[IndicatorReleaseInput(unsafe, (row,))],
            geographies=geographies(),
        )


def test_catalog_release_rejects_undeclared_observation_geography(tmp_path: Path) -> None:
    from worldinsights.release import IndicatorReleaseInput, build_catalog_release

    with pytest.raises(ValueError, match="not declared"):
        build_catalog_release(
            output_root=tmp_path,
            release=release(),
            indicators=[IndicatorReleaseInput(second_indicator(), tuple(second_observations()))],
            geographies=geographies()[:2],
        )


def test_catalog_release_rejects_missing_geography_parent(tmp_path: Path) -> None:
    from worldinsights.release import IndicatorReleaseInput, build_catalog_release

    invalid_geographies = [
        Geography(1, "DEU", "Germany", GeographyType.COUNTRY, parent_id=99),
        Geography(2, "NPL", "Nepal", GeographyType.COUNTRY),
    ]
    with pytest.raises(ValueError, match="parent must exist"):
        build_catalog_release(
            output_root=tmp_path,
            release=release(),
            indicators=[IndicatorReleaseInput(indicator(), tuple(observations()))],
            geographies=invalid_geographies,
        )
