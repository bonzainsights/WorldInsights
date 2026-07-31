import json
from pathlib import Path

import pytest

from worldinsights.providers.world_bank import WorldBankAdapter

ROOT = Path(__file__).resolve().parents[1]
MAPPINGS = ROOT / "data/mappings/world_bank_geographies.json"


@pytest.mark.parametrize(
    ("fixture_name", "indicator_code"),
    [
        ("population_2019_2023_page.json", "SP.POP.TOTL"),
        ("gdp_per_capita_2019_2023_page.json", "NY.GDP.PCAP.CD"),
    ],
)
def test_pinned_history_has_complete_country_year_grid(
    fixture_name: str,
    indicator_code: str,
) -> None:
    fixture = ROOT / "tests/fixtures/world_bank" / fixture_name
    adapter = WorldBankAdapter.from_mapping_file(MAPPINGS)
    records = adapter.parse_records(json.loads(fixture.read_text(encoding="utf-8")))

    assert len(records) == 15
    assert {record.indicator_code for record in records} == {indicator_code}
    assert {record.country_code for record in records} == {"DEU", "NPL", "USA"}
    assert {record.year for record in records} == {2019, 2020, 2021, 2022, 2023}
    assert len({(record.country_code, record.year) for record in records}) == 15
    assert all(record.value is not None for record in records)
