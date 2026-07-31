"""World Bank API parsing and canonical normalization."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from worldinsights.contracts import Observation, ObservationStatus, Period


WORLD_BANK_BASE_URL = "https://api.worldbank.org/v2"

GDP_PER_CAPITA_CURRENT_USD_CODE = "NY.GDP.PCAP.CD"
GDP_PER_CAPITA_CURRENT_USD_VARIANT_ID = "wb.ny.gdp.pcap.cd"
GDP_PER_CAPITA_CURRENT_USD_UNIT_ID = "current_usd_per_person"


class WorldBankError(RuntimeError):
    """Raised when the World Bank response cannot be safely normalized."""


@dataclass(frozen=True, slots=True)
class WorldBankRecord:
    indicator_code: str
    indicator_name: str
    country_code: str
    country_name: str
    year: int
    value: float | None
    unit: str
    observation_status: str
    decimal: int


@dataclass(frozen=True, slots=True)
class GeographyMapping:
    provider_code: str
    geography_id: int
    canonical_code: str
    geography_type: str


class WorldBankAdapter:
    provider_id = "world-bank"
    dataset_id = "indicators"

    def __init__(self, geography_mappings: dict[str, GeographyMapping]) -> None:
        self._geography_mappings = geography_mappings

    @classmethod
    def from_mapping_file(cls, path: Path) -> WorldBankAdapter:
        payload = json.loads(path.read_text(encoding="utf-8"))
        mappings: dict[str, GeographyMapping] = {}
        for row in payload:
            mapping = GeographyMapping(
                provider_code=str(row["provider_code"]),
                geography_id=int(row["geography_id"]),
                canonical_code=str(row["canonical_code"]),
                geography_type=str(row["geography_type"]),
            )
            if mapping.provider_code in mappings:
                raise WorldBankError(f"duplicate geography mapping: {mapping.provider_code}")
            if mapping.geography_id <= 0:
                raise WorldBankError("geography IDs must be positive")
            mappings[mapping.provider_code] = mapping
        return cls(mappings)

    def build_indicator_url(
        self,
        indicator_code: str,
        *,
        start_year: int,
        end_year: int,
        country_codes: Sequence[str] | None = None,
        per_page: int = 20_000,
    ) -> str:
        indicator = indicator_code.strip()
        if not indicator:
            raise ValueError("indicator_code is required")
        if start_year > end_year:
            raise ValueError("start_year cannot be after end_year")
        if per_page <= 0:
            raise ValueError("per_page must be positive")

        country_segment = "all"
        if country_codes is not None:
            normalized_codes: list[str] = []
            seen_codes: set[str] = set()
            for raw_code in country_codes:
                code = raw_code.strip().upper()
                if len(code) != 3 or not code.isascii() or not code.isalpha():
                    raise ValueError("country codes must be three ASCII letters")
                if code in seen_codes:
                    raise ValueError(f"duplicate country code: {code}")
                seen_codes.add(code)
                normalized_codes.append(code)
            if not normalized_codes:
                raise ValueError("country_codes cannot be empty")
            normalized_codes.sort()
            country_segment = ";".join(normalized_codes)
            if len(country_segment) > 1_500:
                raise ValueError("country code path exceeds the World Bank API limit")

        query = urlencode(
            {
                "format": "json",
                "date": f"{start_year}:{end_year}",
                "per_page": per_page,
                "source": 2,
            }
        )
        return (
            f"{WORLD_BANK_BASE_URL}/country/{country_segment}/indicator/{indicator}?{query}"
        )

    def fetch_payload(self, url: str, *, timeout_seconds: float = 30.0) -> Any:
        if not url.startswith(WORLD_BANK_BASE_URL):
            raise ValueError("only the configured World Bank API host is allowed")
        request = Request(url, headers={"User-Agent": "WorldInsights/0.1"})
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310
            if response.status != 200:
                raise WorldBankError(f"World Bank returned HTTP {response.status}")
            return json.load(response)

    def parse_records(self, payload: Any) -> list[WorldBankRecord]:
        if not isinstance(payload, list) or len(payload) != 2:
            raise WorldBankError("expected [metadata, records] World Bank response")
        metadata, rows = payload
        if not isinstance(metadata, dict) or not isinstance(rows, list):
            raise WorldBankError("invalid World Bank response types")
        if int(metadata.get("page", 0)) != 1:
            raise WorldBankError("adapter expects the first page")
        if int(metadata.get("pages", 0)) != 1:
            raise WorldBankError("response is paginated; increase per_page or implement paging")

        records: list[WorldBankRecord] = []
        for row in rows:
            if not isinstance(row, dict):
                raise WorldBankError("record must be an object")
            indicator = row.get("indicator")
            country = row.get("country")
            if not isinstance(indicator, dict) or not isinstance(country, dict):
                raise WorldBankError("record is missing indicator or country metadata")
            try:
                year = int(row["date"])
                decimal = int(row.get("decimal", 0))
            except (KeyError, TypeError, ValueError) as exc:
                raise WorldBankError("invalid year or decimal field") from exc

            raw_value = row.get("value")
            value = None if raw_value is None else float(raw_value)
            records.append(
                WorldBankRecord(
                    indicator_code=str(indicator.get("id", "")),
                    indicator_name=str(indicator.get("value", "")),
                    country_code=str(row.get("countryiso3code", "")),
                    country_name=str(country.get("value", "")),
                    year=year,
                    value=value,
                    unit=str(row.get("unit", "")),
                    observation_status=str(row.get("obs_status", "")),
                    decimal=decimal,
                )
            )
        return records

    def normalize_records(
        self,
        records: list[WorldBankRecord],
        *,
        release_id: str,
        indicator_variant_id: str,
        unit_id: str,
    ) -> list[Observation]:
        observations: list[Observation] = []
        seen_keys: set[tuple[int, int]] = set()
        for record in records:
            mapping = self._geography_mappings.get(record.country_code)
            if mapping is None:
                raise WorldBankError(
                    f"unknown World Bank geography code: {record.country_code or '<empty>'}"
                )
            key = (mapping.geography_id, record.year)
            if key in seen_keys:
                raise WorldBankError(f"duplicate observation for geography/year: {key}")
            seen_keys.add(key)

            status = (
                ObservationStatus.MISSING
                if record.value is None
                else ObservationStatus.OBSERVED
            )
            observations.append(
                Observation(
                    release_id=release_id,
                    indicator_variant_id=indicator_variant_id,
                    geography_id=mapping.geography_id,
                    period=Period.annual(record.year),
                    unit_id=unit_id,
                    status=status,
                    value=record.value,
                    provider_quality_flags=(record.observation_status,)
                    if record.observation_status
                    else (),
                )
            )
        return observations
