"""Strict World Bank country-catalog parsing and ISO registry intersection."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
from urllib.parse import urlencode

from worldinsights.geographies import CountryRegistryEntry, iso_m49_country_registry
from worldinsights.providers.world_bank import WORLD_BANK_BASE_URL, WorldBankError


# World Bank provider entities that are neither aggregates nor ISO-3166 entries.
# They require an explicit product decision before they can enter canonical releases.
EXPLICIT_NON_ISO_EXCLUSIONS = frozenset({"CHI", "XKX"})


@dataclass(frozen=True, slots=True)
class WorldBankCountryCatalogEntry:
    provider_code: str
    iso2_code: str
    name: str
    region_id: str
    region_name: str

    @property
    def is_aggregate(self) -> bool:
        return self.region_name == "Aggregates"


def build_country_catalog_url(*, per_page: int = 400) -> str:
    if per_page <= 0:
        raise ValueError("per_page must be positive")
    query = urlencode({"format": "json", "per_page": per_page})
    return f"{WORLD_BANK_BASE_URL}/country?{query}"


def parse_country_catalog(payload: Any) -> tuple[WorldBankCountryCatalogEntry, ...]:
    if not isinstance(payload, list) or len(payload) != 2:
        raise WorldBankError("expected [metadata, countries] World Bank response")
    metadata, rows = payload
    if not isinstance(metadata, dict) or not isinstance(rows, list):
        raise WorldBankError("invalid World Bank country-catalog response types")
    if int(metadata.get("page", 0)) != 1 or int(metadata.get("pages", 0)) != 1:
        raise WorldBankError("country catalog must be returned as one complete page")

    entries: list[WorldBankCountryCatalogEntry] = []
    seen_codes: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise WorldBankError(f"country catalog row {index} must be an object")
        region = row.get("region")
        if not isinstance(region, dict):
            raise WorldBankError(f"country catalog row {index} is missing region metadata")

        provider_code = str(row.get("id", "")).strip().upper()
        iso2_code = str(row.get("iso2Code", "")).strip().upper()
        name = str(row.get("name", "")).strip()
        region_id = str(region.get("id", "")).strip().upper()
        region_name = str(region.get("value", "")).strip()
        if len(provider_code) != 3 or not provider_code.isascii() or not provider_code.isalnum():
            raise WorldBankError(f"invalid World Bank country code: {provider_code!r}")
        if not name:
            raise WorldBankError(f"missing World Bank country name for {provider_code}")
        if provider_code in seen_codes:
            raise WorldBankError(f"duplicate World Bank country code: {provider_code}")
        seen_codes.add(provider_code)
        entries.append(
            WorldBankCountryCatalogEntry(
                provider_code=provider_code,
                iso2_code=iso2_code,
                name=name,
                region_id=region_id,
                region_name=region_name,
            )
        )

    if int(metadata.get("total", len(entries))) != len(entries):
        raise WorldBankError("country catalog metadata total does not match returned rows")
    return tuple(sorted(entries, key=lambda entry: entry.provider_code))


def supported_iso_registry_entries(
    catalog: Iterable[WorldBankCountryCatalogEntry],
    *,
    registry: Iterable[CountryRegistryEntry] | None = None,
) -> tuple[CountryRegistryEntry, ...]:
    registry_entries = tuple(registry or iso_m49_country_registry())
    registry_by_code = {entry.provider_code: entry for entry in registry_entries}
    supported_codes: set[str] = set()
    unknown_non_iso: set[str] = set()

    for provider_entry in catalog:
        if provider_entry.is_aggregate:
            continue
        if provider_entry.provider_code in EXPLICIT_NON_ISO_EXCLUSIONS:
            continue
        if provider_entry.provider_code not in registry_by_code:
            unknown_non_iso.add(provider_entry.provider_code)
            continue
        supported_codes.add(provider_entry.provider_code)

    if unknown_non_iso:
        raise WorldBankError(
            "unreviewed non-ISO World Bank country codes: "
            + ", ".join(sorted(unknown_non_iso))
        )
    if not supported_codes:
        raise WorldBankError("World Bank country catalog has no supported ISO entries")

    return tuple(
        registry_by_code[code]
        for code in sorted(supported_codes)
    )
