"""Deterministic canonical geography registries."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pycountry

from worldinsights.contracts import Geography, GeographyType
from worldinsights.providers.world_bank import GeographyMapping


@dataclass(frozen=True, slots=True)
class CountryRegistryEntry:
    provider_code: str
    geography_id: int
    canonical_code: str
    name: str

    def __post_init__(self) -> None:
        if len(self.provider_code) != 3 or not self.provider_code.isascii():
            raise ValueError("provider_code must be an ISO alpha-3 code")
        if self.provider_code != self.provider_code.upper():
            raise ValueError("provider_code must be uppercase")
        if self.canonical_code != self.provider_code:
            raise ValueError("canonical_code must match provider_code")
        if not 1 <= self.geography_id <= 999:
            raise ValueError("country geography_id must be a numeric M49 code")
        if not self.name.strip():
            raise ValueError("country name is required")

    def geography(self) -> Geography:
        return Geography(
            geography_id=self.geography_id,
            canonical_code=self.canonical_code,
            name=self.name,
            geography_type=GeographyType.COUNTRY,
        )

    def world_bank_mapping(self) -> GeographyMapping:
        return GeographyMapping(
            provider_code=self.provider_code,
            geography_id=self.geography_id,
            canonical_code=self.canonical_code,
            geography_type=GeographyType.COUNTRY.value,
        )


@lru_cache(maxsize=1)
def iso_m49_country_registry() -> tuple[CountryRegistryEntry, ...]:
    """Return the pinned ISO alpha-3/M49 registry in deterministic code order."""

    entries: list[CountryRegistryEntry] = []
    for country in pycountry.countries:
        alpha_3 = str(country.alpha_3).upper()
        numeric = str(country.numeric)
        if len(numeric) != 3 or not numeric.isascii() or not numeric.isdigit():
            raise ValueError(f"invalid ISO numeric code for {alpha_3}: {numeric!r}")
        entries.append(
            CountryRegistryEntry(
                provider_code=alpha_3,
                geography_id=int(numeric),
                canonical_code=alpha_3,
                name=str(country.name),
            )
        )

    entries.sort(key=lambda entry: entry.provider_code)
    _validate_registry(entries)
    return tuple(entries)


def world_bank_country_mappings() -> dict[str, GeographyMapping]:
    return {
        entry.provider_code: entry.world_bank_mapping()
        for entry in iso_m49_country_registry()
    }


def canonical_country_geographies() -> tuple[Geography, ...]:
    return tuple(entry.geography() for entry in iso_m49_country_registry())


def _validate_registry(entries: list[CountryRegistryEntry]) -> None:
    if not entries:
        raise ValueError("country registry cannot be empty")
    provider_codes = [entry.provider_code for entry in entries]
    geography_ids = [entry.geography_id for entry in entries]
    if len(set(provider_codes)) != len(provider_codes):
        raise ValueError("country registry contains duplicate alpha-3 codes")
    if len(set(geography_ids)) != len(geography_ids):
        raise ValueError("country registry contains duplicate M49 codes")
