import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

from scripts.build_live_world_bank_release import build_live_release
from worldinsights.providers.world_bank import WorldBankError


ROOT = Path(__file__).resolve().parents[1]
POPULATION_FIXTURE = ROOT / "tests/fixtures/world_bank/population_2019_2023_page.json"
GDP_FIXTURE = ROOT / "tests/fixtures/world_bank/gdp_per_capita_2019_2023_page.json"
FIXED_RETRIEVAL = datetime(2026, 7, 31, 7, 30, tzinfo=timezone.utc)


def fixture_payloads() -> dict[str, Any]:
    return {
        "SP.POP.TOTL": json.loads(POPULATION_FIXTURE.read_text(encoding="utf-8")),
        "NY.GDP.PCAP.CD": json.loads(GDP_FIXTURE.read_text(encoding="utf-8")),
    }


def fixture_fetcher(payloads: dict[str, Any], requested_urls: list[str]):
    def fetch(url: str) -> Any:
        requested_urls.append(url)
        for indicator_code, payload in payloads.items():
            if f"/indicator/{indicator_code}?" in url:
                return copy.deepcopy(payload)
        raise AssertionError(f"unexpected World Bank URL: {url}")

    return fetch


def file_snapshot(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_live_builder_creates_bounded_multi_indicator_release(tmp_path: Path) -> None:
    requested_urls: list[str] = []
    latest_path = build_live_release(
        tmp_path,
        start_year=2019,
        end_year=2023,
        retrieved_at=FIXED_RETRIEVAL,
        fetch_payload=fixture_fetcher(fixture_payloads(), requested_urls),
    )

    assert len(requested_urls) == 2
    assert all("/country/DEU;NPL;USA/indicator/" in url for url in requested_urls)
    assert all("date=2019%3A2023" in url for url in requested_urls)
    assert all("source=2" in url for url in requested_urls)

    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["schema_version"] == 2
    assert latest["release_id"] == "world-bank-indicators-2019-2023-20260731T073000Z"

    release_root = tmp_path / "releases" / latest["release_id"]
    catalog = json.loads((release_root / "catalog.json").read_text(encoding="utf-8"))
    assert catalog["release"]["retrieved_at"] == "2026-07-31T07:30:00+00:00"
    assert catalog["release"]["pipeline_version"] == "0.6.0"
    assert len(catalog["release"]["source_checksum"]) == 64
    assert [item["geography_id"] for item in catalog["geographies"]] == [276, 524, 840]
    assert [item["indicator_variant_id"] for item in catalog["indicators"]] == [
        "wb.ny.gdp.pcap.cd",
        "wb.sp.pop.totl",
    ]

    for indicator_id in ("wb.ny.gdp.pcap.cd", "wb.sp.pop.totl"):
        indicator_root = release_root / "indicators" / indicator_id
        observations = json.loads(
            (indicator_root / "observations.json").read_text(encoding="utf-8")
        )
        coverage = json.loads((indicator_root / "coverage.json").read_text(encoding="utf-8"))
        assert len(observations) == 15
        assert coverage["geography_ids"] == [276, 524, 840]
        assert coverage["periods"] == ["2019", "2020", "2021", "2022", "2023"]


def test_live_builder_is_deterministic_for_fixed_payloads_and_timestamp(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"

    for output in (first, second):
        build_live_release(
            output,
            start_year=2019,
            end_year=2023,
            retrieved_at=FIXED_RETRIEVAL,
            fetch_payload=fixture_fetcher(fixture_payloads(), []),
        )

    assert file_snapshot(first) == file_snapshot(second)


def test_live_builder_rejects_incomplete_provider_grid(tmp_path: Path) -> None:
    payloads = fixture_payloads()
    payloads["SP.POP.TOTL"][1].pop()

    with pytest.raises(WorldBankError, match="grid mismatch"):
        build_live_release(
            tmp_path,
            start_year=2019,
            end_year=2023,
            retrieved_at=FIXED_RETRIEVAL,
            fetch_payload=fixture_fetcher(payloads, []),
        )


def test_live_builder_rejects_wrong_indicator_identity(tmp_path: Path) -> None:
    payloads = fixture_payloads()
    payloads["SP.POP.TOTL"][1][0]["indicator"]["id"] = "WRONG.CODE"

    with pytest.raises(WorldBankError, match="unexpected indicator code"):
        build_live_release(
            tmp_path,
            start_year=2019,
            end_year=2023,
            retrieved_at=FIXED_RETRIEVAL,
            fetch_payload=fixture_fetcher(payloads, []),
        )


def test_live_builder_requires_timezone_aware_retrieval_time(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        build_live_release(
            tmp_path,
            start_year=2019,
            end_year=2023,
            retrieved_at=datetime(2026, 7, 31, 7, 30),
            fetch_payload=fixture_fetcher(fixture_payloads(), []),
        )
