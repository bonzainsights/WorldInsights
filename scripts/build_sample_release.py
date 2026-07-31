#!/usr/bin/env python3
"""Build a deterministic, offline multi-indicator WorldInsights sample release."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

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
)
from worldinsights.release import (
    IndicatorReleaseInput,
    build_catalog_release,
    build_static_release,
)


ROOT = Path(__file__).resolve().parents[1]
LEGACY_POPULATION_FIXTURE = ROOT / "tests/fixtures/world_bank/population_page.json"
DEFAULT_POPULATION_FIXTURE = ROOT / "tests/fixtures/world_bank/population_2019_2023_page.json"
DEFAULT_GDP_FIXTURE = ROOT / "tests/fixtures/world_bank/gdp_per_capita_2019_2023_page.json"
DEFAULT_MAPPINGS = ROOT / "data/mappings/world_bank_geographies.json"

SAMPLE_GEOGRAPHIES = (
    Geography(276, "DEU", "Germany", GeographyType.COUNTRY),
    Geography(524, "NPL", "Nepal", GeographyType.COUNTRY),
    Geography(840, "USA", "United States", GeographyType.COUNTRY),
)
LEGACY_V1_GEOGRAPHY_IDS = {276: 1, 524: 2, 840: 3}


def build_sample(
    output_root: Path,
    population_fixture: Path = DEFAULT_POPULATION_FIXTURE,
    gdp_fixture: Path = DEFAULT_GDP_FIXTURE,
) -> Path:
    population_bytes = population_fixture.read_bytes()
    gdp_bytes = gdp_fixture.read_bytes()
    adapter = WorldBankAdapter.from_mapping_file(DEFAULT_MAPPINGS)
    release_id = "world-bank-indicators-2019-2023-sample"

    population_records = [
        record
        for record in adapter.parse_records(json.loads(population_bytes))
        if record.country_code in {"DEU", "NPL", "USA"}
    ]
    gdp_records = adapter.parse_records(json.loads(gdp_bytes))

    population_observations = adapter.normalize_records(
        population_records,
        release_id=release_id,
        indicator_variant_id="wb.sp.pop.totl",
        unit_id="people",
    )
    gdp_observations = adapter.normalize_records(
        gdp_records,
        release_id=release_id,
        indicator_variant_id=GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID,
        unit_id=GDP_PER_CAPITA_CURRENT_USD_UNIT_ID,
    )

    combined_source = hashlib.sha256()
    for name, content in sorted(
        (
            (population_fixture.name, population_bytes),
            (gdp_fixture.name, gdp_bytes),
        )
    ):
        combined_source.update(name.encode("utf-8"))
        combined_source.update(b"\0")
        combined_source.update(content)
        combined_source.update(b"\0")

    release = DataRelease(
        release_id=release_id,
        provider_id=adapter.provider_id,
        dataset_id=adapter.dataset_id,
        retrieved_at=datetime(2026, 7, 30, tzinfo=timezone.utc),
        source_checksum=combined_source.hexdigest(),
        pipeline_version="0.6.0",
    )
    population = IndicatorVariant(
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
    gdp_per_capita = IndicatorVariant(
        indicator_variant_id=GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID,
        provider_id=adapter.provider_id,
        dataset_id=adapter.dataset_id,
        provider_indicator_code=GDP_PER_CAPITA_CURRENT_USD_CODE,
        name="GDP per capita (current US$)",
        concept_id="economy.gdp_per_capita",
        unit_id=GDP_PER_CAPITA_CURRENT_USD_UNIT_ID,
        frequency=Frequency.ANNUAL,
        geography_types=frozenset({GeographyType.COUNTRY}),
    )
    artifacts = build_catalog_release(
        output_root=output_root,
        release=release,
        indicators=(
            IndicatorReleaseInput(population, tuple(population_observations)),
            IndicatorReleaseInput(gdp_per_capita, tuple(gdp_observations)),
        ),
        geographies=SAMPLE_GEOGRAPHIES,
    )
    return artifacts.latest_path


def build_legacy_v1_contract_fixture(
    output_root: Path,
    population_fixture: Path = LEGACY_POPULATION_FIXTURE,
) -> Path:
    """Rebuild the frozen V1 fixture used for cross-language compatibility tests."""

    source_bytes = population_fixture.read_bytes()
    adapter = WorldBankAdapter.from_mapping_file(DEFAULT_MAPPINGS)
    records = [
        record
        for record in adapter.parse_records(json.loads(source_bytes))
        if record.country_code != "WLD"
    ]
    release_id = "world-bank-population-2023-sample"
    normalized = adapter.normalize_records(
        records,
        release_id=release_id,
        indicator_variant_id="wb.sp.pop.totl",
        unit_id="people",
    )
    observations = [
        replace(row, geography_id=LEGACY_V1_GEOGRAPHY_IDS[row.geography_id])
        for row in normalized
    ]
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
    return build_static_release(
        output_root=output_root,
        release=release,
        indicator=indicator,
        observations=observations,
    ).latest_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Directory for static release assets")
    parser.add_argument("--population-fixture", type=Path, default=DEFAULT_POPULATION_FIXTURE)
    parser.add_argument("--gdp-fixture", type=Path, default=DEFAULT_GDP_FIXTURE)
    args = parser.parse_args()
    latest = build_sample(args.output, args.population_fixture, args.gdp_fixture)
    print(latest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
