"""Global release integration boundary.

The provider-support catalog is implemented first. Global release assembly will
be added only after this discovery layer is independently validated.
"""

from __future__ import annotations

from worldinsights.providers.world_bank_countries import (
    build_country_catalog_url,
    parse_country_catalog,
    supported_iso_registry_entries,
)

__all__ = [
    "build_country_catalog_url",
    "parse_country_catalog",
    "supported_iso_registry_entries",
]
