#!/usr/bin/env python3
"""Build an immutable WorldInsights release for the World Bank-supported ISO registry."""

from __future__ import annotations

import argparse
import hashlib
from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worldinsights.contracts import DataRelease
from worldinsights.geographies import (
    CountryRegistryEntry,
    iso_m49_country_registry,
    world_bank_country_mappings,
)
from worldinsights.providers.world_bank import WorldBankAdapter
from worldinsights.providers.world_bank_countries import (
    build_country_catalog_url,
    parse_country_catalog,
    supported_iso_registry_entries,
)
from worldinsights.release import IndicatorReleaseInput, build_catalog_release

try:
    from scripts.build_live_world_bank_release import (
        INDICATORS,
        _canonical_json_bytes,
        _validate_record_grid,
    )
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from build_live_world_bank_release import (  # type: ignore[no-redef]
        INDICATORS,
        _canonical_json_bytes,
        _validate_record_grid,
    )


PayloadFetcher = Callable[[str], Any]


def build_global_live_release(
    output_root: Path,
    *,
    start_year: int,
    end_year: int,
    retrieved_at: datetime | None = None,
    fetch_payload: PayloadFetcher | None = None,
    registry: Iterable[CountryRegistryEntry] | None = None,
    timeout_seconds: float = 45.0,
) -> Path:
    """Fetch, validate, normalize, and publish the provider-supported ISO subset."""

    if start_year > end_year:
        raise ValueError("start_year cannot be after end_year")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    timestamp = retrieved_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    timestamp = timestamp.astimezone(timezone.utc).replace(microsecond=0)

    adapter = WorldBankAdapter(world_bank_country_mappings())

    def fetch(url: str) -> Any:
        return (
            fetch_payload(url)
            if fetch_payload is not None
            else adapter.fetch_payload(url, timeout_seconds=timeout_seconds)
        )

    country_catalog_url = build_country_catalog_url()
    country_catalog_payload = fetch(country_catalog_url)
    supported_entries = supported_iso_registry_entries(
        parse_country_catalog(country_catalog_payload),
        registry=tuple(registry or iso_m49_country_registry()),
    )
    country_codes = tuple(entry.provider_code for entry in supported_entries)
    geographies = tuple(entry.geography() for entry in supported_entries)

    release_id = (
        f"world-bank-global-indicators-{start_year}-{end_year}-"
        f"{timestamp:%Y%m%dT%H%M%SZ}"
    )
    source_parts: list[tuple[str, bytes]] = [
        (country_catalog_url, _canonical_json_bytes(country_catalog_payload))
    ]
    release_inputs: list[IndicatorReleaseInput] = []

    for spec in INDICATORS:
        url = adapter.build_indicator_url(
            spec.provider_code,
            start_year=start_year,
            end_year=end_year,
            country_codes=country_codes,
        )
        payload = fetch(url)
        source_parts.append((url, _canonical_json_bytes(payload)))
        records = adapter.parse_records(payload)
        _validate_record_grid(
            records,
            indicator_code=spec.provider_code,
            country_codes=country_codes,
            start_year=start_year,
            end_year=end_year,
        )
        observations = adapter.normalize_records(
            records,
            release_id=release_id,
            indicator_variant_id=spec.variant_id,
            unit_id=spec.unit_id,
        )
        release_inputs.append(
            IndicatorReleaseInput(spec.variant(adapter), tuple(observations))
        )

    source_checksum = hashlib.sha256()
    for url, source_bytes in sorted(source_parts):
        source_checksum.update(url.encode("utf-8"))
        source_checksum.update(b"\0")
        source_checksum.update(source_bytes)
        source_checksum.update(b"\0")

    release = DataRelease(
        release_id=release_id,
        provider_id=adapter.provider_id,
        dataset_id=adapter.dataset_id,
        retrieved_at=timestamp,
        source_checksum=source_checksum.hexdigest(),
        pipeline_version="0.8.0",
    )
    artifacts = build_catalog_release(
        output_root=output_root,
        release=release,
        indicators=tuple(release_inputs),
        geographies=geographies,
    )
    return artifacts.latest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2024)
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    args = parser.parse_args()

    latest = build_global_live_release(
        args.output,
        start_year=args.start_year,
        end_year=args.end_year,
        timeout_seconds=args.timeout_seconds,
    )
    print(latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
