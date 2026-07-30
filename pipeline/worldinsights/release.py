"""Deterministic static release asset builder."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from worldinsights.compatibility import CoverageIndex
from worldinsights.contracts import DataRelease, GeographyType, IndicatorVariant, Observation


@dataclass(frozen=True, slots=True)
class ReleaseArtifacts:
    release_directory: Path
    manifest_path: Path
    observations_path: Path
    coverage_path: Path
    latest_path: Path


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize JSON deterministically for checksums and immutable assets."""

    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


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
    """Build one immutable static release and atomically update latest metadata."""

    observation_list = sorted(
        observations,
        key=lambda row: (row.indicator_variant_id, row.geography_id, row.period.start),
    )
    if not observation_list:
        raise ValueError("a release must contain at least one observation")
    if any(row.release_id != release.release_id for row in observation_list):
        raise ValueError("observation release IDs must match the release")

    release_directory = output_root / "releases" / release.release_id
    if release_directory.exists() and any(release_directory.iterdir()):
        raise FileExistsError(f"immutable release already exists: {release.release_id}")
    release_directory.mkdir(parents=True, exist_ok=True)

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
