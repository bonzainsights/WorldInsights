#!/usr/bin/env python3
"""Fetch a bounded World Bank slice and build an immutable WorldInsights release."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worldinsights.contracts import (
    DataRelease,
    Frequency,
    Geography,
    GeographyType,
    IndicatorVariant,
)
from worldinsights.providers.world_bank import (
    GDP_PER_CAPITA_CURRENT_USD_CODE,
    GDP_PER_CAPITA_CURRENT_USD_UNIT_ID,
    GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID,
    WorldBankAdapter,
    WorldBankError,
    WorldBankRecord,
)
from worldinsights.release import IndicatorReleaseInput, build_catalog_release


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAPPINGS = ROOT / "data/mappings/world_bank_geographies.json"
DEFAULT_COUNTRY_CODES = ("DEU", "NPL", "USA")
DEFAULT_GEOGRAPHIES = (
    Geography(276, "DEU", "Germany", GeographyType.COUNTRY),
    Geography(524, "NPL", "Nepal", GeographyType.COUNTRY),
    Geography(840, "USA", "United States", GeographyType.COUNTRY),
)

PayloadFetcher = Callable[[str], Any]


@dataclass(frozen=True, slots=True)
class IndicatorSpec:
    provider_code: str
    variant_id: str
    name: str
    concept_id: str
    unit_id: str

    def variant(self, adapter: WorldBankAdapter) -> IndicatorVariant:
        return IndicatorVariant(
            indicator_variant_id=self.variant_id,
            provider_id=adapter.provider_id,
            dataset_id=adapter.dataset_id,
            provider_indicator_code=self.provider_code,
            name=self.name,
            concept_id=self.concept_id,
            unit_id=self.unit_id,
            frequency=Frequency.ANNUAL,
            geography_types=frozenset({GeographyType.COUNTRY}),
        )


INDICATORS = (
    IndicatorSpec(
        provider_code="SP.POP.TOTL",
        variant_id="wb.sp.pop.totl",
        name="Population, total",
        concept_id="population.total",
        unit_id="people",
    ),
    IndicatorSpec(
        provider_code=GDP_PER_CAPITA_CURRENT_USD_CODE,
        variant_id=GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID,
        name="GDP per capita (current US$)",
        concept_id="economy.gdp_per_capita",
        unit_id=GDP_PER_CAPITA_CURRENT_USD_UNIT_ID,
    ),
)


def build_live_release(
    output_root: Path,
    *,
    start_year: int,
    end_year: int,
    country_codes: Sequence[str] = DEFAULT_COUNTRY_CODES,
    geographies: Sequence[Geography] = DEFAULT_GEOGRAPHIES,
    retrieved_at: datetime | None = None,
    fetch_payload: PayloadFetcher | None = None,
    timeout_seconds: float = 30.0,
) -> Path:
    """Fetch, validate, normalize, and publish a bounded live release."""

    if start_year > end_year:
        raise ValueError("start_year cannot be after end_year")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")

    normalized_codes = tuple(sorted(code.strip().upper() for code in country_codes))
    if len(set(normalized_codes)) != len(normalized_codes):
        raise ValueError("country_codes must be unique")
    declared_codes = tuple(sorted(geography.canonical_code for geography in geographies))
    if normalized_codes != declared_codes:
        raise ValueError("country_codes must exactly match declared geography codes")

    timestamp = retrieved_at or datetime.now(timezone.utc)
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ValueError("retrieved_at must be timezone-aware")
    timestamp = timestamp.astimezone(timezone.utc).replace(microsecond=0)

    adapter = WorldBankAdapter.from_mapping_file(DEFAULT_MAPPINGS)
    release_id = (
        f"world-bank-indicators-{start_year}-{end_year}-"
        f"{timestamp:%Y%m%dT%H%M%SZ}"
    )
    source_parts: list[tuple[str, bytes]] = []
    release_inputs: list[IndicatorReleaseInput] = []

    for spec in INDICATORS:
        url = adapter.build_indicator_url(
            spec.provider_code,
            start_year=start_year,
            end_year=end_year,
            country_codes=normalized_codes,
        )
        payload = (
            fetch_payload(url)
            if fetch_payload is not None
            else adapter.fetch_payload(url, timeout_seconds=timeout_seconds)
        )
        source_bytes = _canonical_json_bytes(payload)
        source_parts.append((url, source_bytes))

        records = adapter.parse_records(payload)
        _validate_record_grid(
            records,
            indicator_code=spec.provider_code,
            country_codes=normalized_codes,
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
        pipeline_version="0.6.0",
    )
    artifacts = build_catalog_release(
        output_root=output_root,
        release=release,
        indicators=tuple(release_inputs),
        geographies=tuple(geographies),
    )
    return artifacts.latest_path


def _validate_record_grid(
    records: Sequence[WorldBankRecord],
    *,
    indicator_code: str,
    country_codes: Sequence[str],
    start_year: int,
    end_year: int,
) -> None:
    if not records:
        raise WorldBankError(f"World Bank returned no rows for {indicator_code}")

    expected_keys = {
        (country_code, year)
        for country_code in country_codes
        for year in range(start_year, end_year + 1)
    }
    actual_keys: list[tuple[str, int]] = []
    for record in records:
        if record.indicator_code != indicator_code:
            raise WorldBankError(
                f"unexpected indicator code {record.indicator_code!r}; expected {indicator_code!r}"
            )
        if record.country_code not in country_codes:
            raise WorldBankError(
                f"unexpected country code in live response: {record.country_code or '<empty>'}"
            )
        if not start_year <= record.year <= end_year:
            raise WorldBankError(f"unexpected year in live response: {record.year}")
        actual_keys.append((record.country_code, record.year))

    if len(set(actual_keys)) != len(actual_keys):
        raise WorldBankError(f"duplicate country/year rows returned for {indicator_code}")

    actual_key_set = set(actual_keys)
    if actual_key_set != expected_keys:
        missing = sorted(expected_keys - actual_key_set)
        unexpected = sorted(actual_key_set - expected_keys)
        raise WorldBankError(
            f"live response grid mismatch for {indicator_code}; "
            f"missing={missing[:5]}, unexpected={unexpected[:5]}"
        )


def _canonical_json_bytes(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise WorldBankError("World Bank payload is not canonical JSON") from exc
    return text.encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--start-year", type=int, default=2019)
    parser.add_argument("--end-year", type=int, default=2023)
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    args = parser.parse_args()

    latest = build_live_release(
        args.output,
        start_year=args.start_year,
        end_year=args.end_year,
        timeout_seconds=args.timeout_seconds,
    )
    print(latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
