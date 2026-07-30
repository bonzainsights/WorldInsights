import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from worldinsights.contracts import (
    DataRelease,
    Frequency,
    GeographyType,
    IndicatorVariant,
    Observation,
    ObservationStatus,
    Period,
)
from worldinsights.release import build_static_release, canonical_json_bytes, sha256_bytes


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
