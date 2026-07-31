"""Deterministic static release asset builders."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from worldinsights.compatibility import CoverageIndex
from worldinsights.contracts import DataRelease, Geography, IndicatorVariant, Observation

_SAFE_ASSET_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


@dataclass(frozen=True, slots=True)
class ReleaseArtifacts:
    """Files produced by the backwards-compatible single-indicator release."""

    release_directory: Path
    manifest_path: Path
    observations_path: Path
    coverage_path: Path
    latest_path: Path


@dataclass(frozen=True, slots=True)
class IndicatorReleaseInput:
    """One indicator and its observations inside a catalog release."""

    indicator: IndicatorVariant
    observations: tuple[Observation, ...]


@dataclass(frozen=True, slots=True)
class CatalogReleaseArtifacts:
    """Files produced by a version-two multi-indicator catalog release."""

    release_directory: Path
    catalog_path: Path
    latest_path: Path
    indicator_directories: tuple[Path, ...]


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for checksums and immutable assets."""

    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def write_json(path: Path, value: Any) -> str:
    content = canonical_json_bytes(value)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return sha256_bytes(content)


def observation_to_dict(observation: Observation) -> dict[str, Any]:
    return {
        "release_id": observation.release_id,
        "indicator_variant_id": observation.indicator_variant_id,
        "geography_id": observation.geography_id,
        "period_start": observation.period.start.isoformat(),
        "period_end": observation.period.end.isoformat(),
        "period_label": observation.period.label,
        "frequency": observation.period.frequency.value,
        "unit_id": observation.unit_id,
        "status": observation.status.value,
        "value": observation.value,
        "provider_quality_flags": list(observation.provider_quality_flags),
        "system_quality_flags": list(observation.system_quality_flags),
    }


def build_coverage_index(
    indicator: IndicatorVariant,
    observations: Iterable[Observation],
) -> CoverageIndex:
    geography_ids: set[int] = set()
    periods: set[str] = set()
    for observation in observations:
        if observation.indicator_variant_id != indicator.indicator_variant_id:
            raise ValueError("observation indicator does not match release indicator")
        geography_ids.add(observation.geography_id)
        periods.add(observation.period.label)

    return CoverageIndex.from_geography_ids(
        indicator_variant_id=indicator.indicator_variant_id,
        geography_ids=geography_ids,
        periods=periods,
        geography_types=set(indicator.geography_types),
        frequency=indicator.frequency,
        concept_id=indicator.concept_id,
        unit_id=indicator.unit_id,
    )


def release_to_dict(release: DataRelease) -> dict[str, Any]:
    retrieved_at: datetime = release.retrieved_at
    return {
        "release_id": release.release_id,
        "provider_id": release.provider_id,
        "dataset_id": release.dataset_id,
        "retrieved_at": retrieved_at.isoformat(),
        "source_checksum": release.source_checksum,
        "pipeline_version": release.pipeline_version,
    }


def geography_to_dict(geography: Geography) -> dict[str, Any]:
    return {
        "geography_id": geography.geography_id,
        "canonical_code": geography.canonical_code,
        "name": geography.name,
        "geography_type": geography.geography_type.value,
        "parent_id": geography.parent_id,
        "valid_from": geography.valid_from.isoformat() if geography.valid_from else None,
        "valid_to": geography.valid_to.isoformat() if geography.valid_to else None,
    }


def indicator_to_dict(indicator: IndicatorVariant) -> dict[str, Any]:
    return {
        "indicator_variant_id": indicator.indicator_variant_id,
        "provider_id": indicator.provider_id,
        "dataset_id": indicator.dataset_id,
        "provider_indicator_code": indicator.provider_indicator_code,
        "name": indicator.name,
        "concept_id": indicator.concept_id,
        "unit_id": indicator.unit_id,
        "frequency": indicator.frequency.value,
        "geography_types": sorted(item.value for item in indicator.geography_types),
    }


def coverage_to_dict(index: CoverageIndex) -> dict[str, Any]:
    return {
        "indicator_variant_id": index.indicator_variant_id,
        "geography_bits_hex": hex(index.geography_bits),
        "geography_ids": list(index.geography_ids()),
        "periods": sorted(index.periods),
        "geography_types": sorted(item.value for item in index.geography_types),
        "frequency": index.frequency.value,
        "concept_id": index.concept_id,
        "unit_id": index.unit_id,
    }


def build_static_release(
    *,
    output_root: Path,
    release: DataRelease,
    indicator: IndicatorVariant,
    observations: Iterable[Observation],
) -> ReleaseArtifacts:
    """Build one immutable V1 single-indicator release.

    This remains supported so already-published static clients and fixtures do not
    change silently while the multi-indicator catalog is introduced.
    """

    observation_list = _validated_observations(release, indicator, observations)
    release_directory = _prepare_release_directory(output_root, release.release_id)

    observations_path = release_directory / "observations.json"
    observations_checksum = write_json(
        observations_path,
        [observation_to_dict(row) for row in observation_list],
    )

    coverage = build_coverage_index(indicator, observation_list)
    coverage_path = release_directory / "coverage.json"
    coverage_checksum = write_json(coverage_path, coverage_to_dict(coverage))

    manifest = {
        "schema_version": 1,
        "release": release_to_dict(release),
        "indicator": indicator_to_dict(indicator),
        "row_count": len(observation_list),
        "files": {
            "observations.json": {"sha256": observations_checksum},
            "coverage.json": {"sha256": coverage_checksum},
        },
    }
    manifest_path = release_directory / "manifest.json"
    manifest_checksum = write_json(manifest_path, manifest)

    latest_path = output_root / "latest.json"
    write_json(
        latest_path,
        {
            "schema_version": 1,
            "release_id": release.release_id,
            "manifest": f"releases/{release.release_id}/manifest.json",
            "manifest_sha256": manifest_checksum,
        },
    )

    return ReleaseArtifacts(
        release_directory=release_directory,
        manifest_path=manifest_path,
        observations_path=observations_path,
        coverage_path=coverage_path,
        latest_path=latest_path,
    )


def build_catalog_release(
    *,
    output_root: Path,
    release: DataRelease,
    indicators: Iterable[IndicatorReleaseInput],
    geographies: Iterable[Geography],
) -> CatalogReleaseArtifacts:
    """Build an immutable V2 release containing independently queryable indicators.

    Indicator files are isolated so a browser can fetch only the selected
    feature. The catalog lists all paths and checksums in deterministic order.
    """

    indicator_inputs = sorted(
        indicators,
        key=lambda item: item.indicator.indicator_variant_id,
    )
    if not indicator_inputs:
        raise ValueError("a catalog release must contain at least one indicator")

    geography_list = sorted(geographies, key=lambda item: item.geography_id)
    if not geography_list:
        raise ValueError("a catalog release must contain at least one geography")
    geography_ids = [item.geography_id for item in geography_list]
    geography_codes = [item.canonical_code for item in geography_list]
    if len(set(geography_ids)) != len(geography_ids):
        raise ValueError("geography IDs must be unique inside a catalog release")
    if len(set(geography_codes)) != len(geography_codes):
        raise ValueError("geography codes must be unique inside a catalog release")
    known_geography_ids = set(geography_ids)
    for geography in geography_list:
        if geography.parent_id is not None and geography.parent_id not in known_geography_ids:
            raise ValueError("geography parent must exist inside the catalog release")

    indicator_ids = [item.indicator.indicator_variant_id for item in indicator_inputs]
    if len(set(indicator_ids)) != len(indicator_ids):
        raise ValueError("indicator IDs must be unique inside a catalog release")

    for item in indicator_inputs:
        _validate_indicator_asset_id(item.indicator.indicator_variant_id)
        if item.indicator.provider_id != release.provider_id:
            raise ValueError("indicator provider must match the release provider")
        if item.indicator.dataset_id != release.dataset_id:
            raise ValueError("indicator dataset must match the release dataset")

    release_directory = _prepare_release_directory(output_root, release.release_id)
    catalog_entries: list[dict[str, Any]] = []
    file_checksums: dict[str, dict[str, str]] = {}
    indicator_directories: list[Path] = []

    for item in indicator_inputs:
        indicator = item.indicator
        rows = _validated_observations(release, indicator, item.observations)
        if any(row.geography_id not in known_geography_ids for row in rows):
            raise ValueError("observation geography is not declared in the catalog")
        relative_directory = Path("indicators") / indicator.indicator_variant_id
        indicator_directory = release_directory / relative_directory
        indicator_directories.append(indicator_directory)

        observations_relative = relative_directory / "observations.json"
        observations_path = release_directory / observations_relative
        observations_checksum = write_json(
            observations_path,
            [observation_to_dict(row) for row in rows],
        )

        coverage = build_coverage_index(indicator, rows)
        coverage_relative = relative_directory / "coverage.json"
        coverage_path = release_directory / coverage_relative
        coverage_checksum = write_json(coverage_path, coverage_to_dict(coverage))

        observations_key = observations_relative.as_posix()
        coverage_key = coverage_relative.as_posix()
        file_checksums[observations_key] = {"sha256": observations_checksum}
        file_checksums[coverage_key] = {"sha256": coverage_checksum}
        catalog_entries.append(
            {
                **indicator_to_dict(indicator),
                "row_count": len(rows),
                "observations": observations_key,
                "coverage": coverage_key,
            }
        )

    catalog = {
        "schema_version": 2,
        "release": release_to_dict(release),
        "geographies": [geography_to_dict(item) for item in geography_list],
        "indicators": catalog_entries,
        "files": file_checksums,
    }
    catalog_path = release_directory / "catalog.json"
    catalog_checksum = write_json(catalog_path, catalog)

    latest_path = output_root / "latest.json"
    write_json(
        latest_path,
        {
            "schema_version": 2,
            "release_id": release.release_id,
            "catalog": f"releases/{release.release_id}/catalog.json",
            "catalog_sha256": catalog_checksum,
        },
    )

    return CatalogReleaseArtifacts(
        release_directory=release_directory,
        catalog_path=catalog_path,
        latest_path=latest_path,
        indicator_directories=tuple(indicator_directories),
    )


def _validated_observations(
    release: DataRelease,
    indicator: IndicatorVariant,
    observations: Iterable[Observation],
) -> list[Observation]:
    rows = sorted(
        observations,
        key=lambda row: (row.indicator_variant_id, row.geography_id, row.period.start),
    )
    if not rows:
        raise ValueError("an indicator release must contain at least one observation")
    if any(row.release_id != release.release_id for row in rows):
        raise ValueError("observation release IDs must match the release")
    if any(row.indicator_variant_id != indicator.indicator_variant_id for row in rows):
        raise ValueError("observation indicator does not match release indicator")
    if any(row.unit_id != indicator.unit_id for row in rows):
        raise ValueError("observation unit does not match release indicator")
    return rows


def _prepare_release_directory(output_root: Path, release_id: str) -> Path:
    _validate_indicator_asset_id(release_id)
    release_directory = output_root / "releases" / release_id
    if release_directory.exists() and any(release_directory.iterdir()):
        raise FileExistsError(f"immutable release already exists: {release_id}")
    release_directory.mkdir(parents=True, exist_ok=True)
    return release_directory


def _validate_indicator_asset_id(value: str) -> None:
    if not _SAFE_ASSET_ID.fullmatch(value):
        raise ValueError(f"unsafe static asset identifier: {value!r}")
