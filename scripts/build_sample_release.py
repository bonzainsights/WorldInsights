#!/usr/bin/env python3
"""Build a deterministic, offline sample WorldInsights release."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from worldinsights.contracts import DataRelease, Frequency, GeographyType, IndicatorVariant
from worldinsights.providers.world_bank import WorldBankAdapter
from worldinsights.release import build_static_release


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = ROOT / "tests/fixtures/world_bank/population_page.json"
DEFAULT_MAPPINGS = ROOT / "data/mappings/world_bank_geographies.json"


def build_sample(output_root: Path, fixture: Path = DEFAULT_FIXTURE) -> Path:
    source_bytes = fixture.read_bytes()
    payload = json.loads(source_bytes)
    adapter = WorldBankAdapter.from_mapping_file(DEFAULT_MAPPINGS)
    records = [record for record in adapter.parse_records(payload) if record.country_code != "WLD"]

    release_id = "world-bank-population-2023-sample"
    observations = adapter.normalize_records(
        records,
        release_id=release_id,
        indicator_variant_id="wb.sp.pop.totl",
        unit_id="people",
    )
    release = DataRelease(
        release_id=release_id,
        provider_id=adapter.provider_id,
        dataset_id=adapter.dataset_id,
        retrieved_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        source_checksum=hashlib.sha256(source_bytes).hexdigest(),
        pipeline_version="0.1.0",
    )
    indicator = IndicatorVariant(
        indicator_variant_id="wb.sp.pop.totl",
        provider_id=adapter.provider_id,
        dataset_id=adapter.dataset_id,
        provider_indicator_code="SP.POP.TOTL",
        name="Population, total",
        concept_id="population.total",
        unit_id="people",
        frequency=Frequency.ANNUAL,
        geography_types=frozenset({GeographyType.COUNTRY}),
    )
    artifacts = build_static_release(
        output_root=output_root,
        release=release,
        indicator=indicator,
        observations=observations,
    )
    return artifacts.latest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Directory for static release assets")
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    args = parser.parse_args()
    latest = build_sample(args.output, args.fixture)
    print(latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
