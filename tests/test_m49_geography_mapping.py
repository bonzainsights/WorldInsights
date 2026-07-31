import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAPPINGS = ROOT / "data/mappings/world_bank_geographies_m49.json"


def test_m49_registry_uses_stable_numeric_country_ids() -> None:
    rows = json.loads(MAPPINGS.read_text(encoding="utf-8"))
    countries = [row for row in rows if row["geography_type"] == "country"]

    assert {row["provider_code"] for row in countries} == {"DEU", "NPL", "USA"}
    assert {row["canonical_code"] for row in countries} == {"DEU", "NPL", "USA"}
    assert {row["geography_id"] for row in countries} == {276, 524, 840}
    assert all(1 <= row["geography_id"] <= 999 for row in countries)
    assert len({row["geography_id"] for row in rows}) == len(rows)
    assert len({row["provider_code"] for row in rows}) == len(rows)


def test_legacy_registry_remains_frozen_for_v1_contract_rebuilds() -> None:
    legacy = json.loads(
        (ROOT / "data/mappings/world_bank_geographies.json").read_text(encoding="utf-8")
    )

    assert [row["geography_id"] for row in legacy[:3]] == [1, 2, 3]
