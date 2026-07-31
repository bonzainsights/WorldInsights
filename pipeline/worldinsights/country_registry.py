"""Deterministic ISO-3166 country and territory registry.

The registry is generated from the exactly pinned pycountry package. Internal IDs
remain dense for compact coverage bitsets, while the original MVP IDs for
Germany, Nepal, and the United States remain stable.
"""

from __future__ import annotations

from dataclasses import dataclass

import pycountry


LEGACY_GEOGRAPHY_IDS: dict[str, int] = {
    "DEU": 1,
    "NPL": 2,
    "USA": 3,
}


@dataclass(frozen=True, slots=True)
class Iso3166Entry:
    geography_id: int
    alpha_2: str
    alpha_3: str
    m49_code: str
    name: str
    official_name: str | None


def build_iso3166_registry() -> tuple[Iso3166Entry, ...]:
    """Return the pinned ISO registry with deterministic dense internal IDs."""

    countries = sorted(pycountry.countries, key=lambda country: country.alpha_3)
    assigned_ids = dict(LEGACY_GEOGRAPHY_IDS)
    next_id = len(LEGACY_GEOGRAPHY_IDS) + 1
    for country in countries:
        alpha_3 = str(country.alpha_3)
        if alpha_3 not in assigned_ids:
            assigned_ids[alpha_3] = next_id
            next_id += 1

    entries = tuple(
        sorted(
            (
                Iso3166Entry(
                    geography_id=assigned_ids[str(country.alpha_3)],
                    alpha_2=str(country.alpha_2),
                    alpha_3=str(country.alpha_3),
                    m49_code=str(country.numeric),
                    name=str(country.name),
                    official_name=(
                        str(country.official_name)
                        if hasattr(country, "official_name")
                        else None
                    ),
                )
                for country in countries
            ),
            key=lambda entry: entry.geography_id,
        )
    )
    _validate_registry(entries)
    return entries


def registry_by_alpha3() -> dict[str, Iso3166Entry]:
    return {entry.alpha_3: entry for entry in build_iso3166_registry()}


def _validate_registry(entries: tuple[Iso3166Entry, ...]) -> None:
    if len(entries) != 249:
        raise RuntimeError(f"expected 249 ISO-3166 entries, found {len(entries)}")

    geography_ids = [entry.geography_id for entry in entries]
    if geography_ids != list(range(1, len(entries) + 1)):
        raise RuntimeError("ISO registry geography IDs must be dense and one-based")

    alpha_2_codes = [entry.alpha_2 for entry in entries]
    alpha_3_codes = [entry.alpha_3 for entry in entries]
    m49_codes = [entry.m49_code for entry in entries]
    if len(set(alpha_2_codes)) != len(entries):
        raise RuntimeError("ISO registry contains duplicate alpha-2 codes")
    if len(set(alpha_3_codes)) != len(entries):
        raise RuntimeError("ISO registry contains duplicate alpha-3 codes")
    if len(set(m49_codes)) != len(entries):
        raise RuntimeError("ISO registry contains duplicate M49 codes")

    for entry in entries:
        if len(entry.alpha_2) != 2 or not entry.alpha_2.isalpha() or not entry.alpha_2.isupper():
            raise RuntimeError(f"invalid alpha-2 code: {entry.alpha_2}")
        if len(entry.alpha_3) != 3 or not entry.alpha_3.isalpha() or not entry.alpha_3.isupper():
            raise RuntimeError(f"invalid alpha-3 code: {entry.alpha_3}")
        if len(entry.m49_code) != 3 or not entry.m49_code.isdigit():
            raise RuntimeError(f"invalid M49 code: {entry.m49_code}")
        if not entry.name.strip():
            raise RuntimeError(f"missing ISO name for {entry.alpha_3}")

    for alpha_3, geography_id in LEGACY_GEOGRAPHY_IDS.items():
        entry = next((item for item in entries if item.alpha_3 == alpha_3), None)
        if entry is None or entry.geography_id != geography_id:
            raise RuntimeError(f"legacy geography ID changed for {alpha_3}")
