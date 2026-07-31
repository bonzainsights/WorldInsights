from worldinsights.country_registry import (
    LEGACY_GEOGRAPHY_IDS,
    build_iso3166_registry,
    registry_by_alpha3,
)


def test_iso_registry_is_complete_dense_and_deterministic() -> None:
    first = build_iso3166_registry()
    second = build_iso3166_registry()

    assert first == second
    assert len(first) == 249
    assert [entry.geography_id for entry in first] == list(range(1, 250))
    assert len({entry.alpha_2 for entry in first}) == 249
    assert len({entry.alpha_3 for entry in first}) == 249
    assert len({entry.m49_code for entry in first}) == 249


def test_iso_registry_preserves_original_mvp_geography_ids() -> None:
    entries = registry_by_alpha3()

    assert entries["DEU"].geography_id == LEGACY_GEOGRAPHY_IDS["DEU"] == 1
    assert entries["NPL"].geography_id == LEGACY_GEOGRAPHY_IDS["NPL"] == 2
    assert entries["USA"].geography_id == LEGACY_GEOGRAPHY_IDS["USA"] == 3


def test_iso_registry_contains_canonical_map_join_codes() -> None:
    entries = registry_by_alpha3()

    assert entries["DEU"].m49_code == "276"
    assert entries["NPL"].m49_code == "524"
    assert entries["USA"].m49_code == "840"
    assert entries["AFG"].m49_code == "004"
    assert entries["ZWE"].m49_code == "716"
    assert all(len(entry.m49_code) == 3 and entry.m49_code.isdigit() for entry in entries.values())


def test_iso_registry_keeps_official_names_without_using_them_as_identity() -> None:
    entries = registry_by_alpha3()

    assert entries["DEU"].name == "Germany"
    assert entries["USA"].name == "United States"
    assert entries["BOL"].official_name is not None
    assert entries["BOL"].alpha_3 == "BOL"
