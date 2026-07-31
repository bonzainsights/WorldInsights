from worldinsights.geographies import (
    canonical_country_geographies,
    iso_m49_country_registry,
    world_bank_country_mappings,
)


def test_pinned_iso_registry_is_complete_deterministic_and_unique() -> None:
    registry = iso_m49_country_registry()

    assert len(registry) == 249
    assert [entry.provider_code for entry in registry] == sorted(
        entry.provider_code for entry in registry
    )
    assert len({entry.provider_code for entry in registry}) == len(registry)
    assert len({entry.geography_id for entry in registry}) == len(registry)
    assert all(1 <= entry.geography_id <= 999 for entry in registry)


def test_known_country_codes_use_canonical_m49_ids() -> None:
    registry = {entry.provider_code: entry for entry in iso_m49_country_registry()}

    assert registry["AFG"].geography_id == 4
    assert registry["DEU"].geography_id == 276
    assert registry["NPL"].geography_id == 524
    assert registry["USA"].geography_id == 840
    assert registry["ZWE"].geography_id == 716
    assert registry["DEU"].name == "Germany"
    assert registry["USA"].name == "United States"


def test_registry_builds_matching_canonical_and_provider_views() -> None:
    geographies = {item.canonical_code: item for item in canonical_country_geographies()}
    mappings = world_bank_country_mappings()

    assert set(geographies) == set(mappings)
    assert geographies["DEU"].geography_id == mappings["DEU"].geography_id == 276
    assert geographies["NPL"].geography_id == mappings["NPL"].geography_id == 524
    assert geographies["USA"].geography_id == mappings["USA"].geography_id == 840
    assert all(item.geography_type.value == "country" for item in geographies.values())
    assert all(item.geography_type == "country" for item in mappings.values())


def test_registry_does_not_include_world_bank_aggregates() -> None:
    codes = {entry.provider_code for entry in iso_m49_country_registry()}

    assert "WLD" not in codes
    assert "AFE" not in codes
    assert "HIC" not in codes
