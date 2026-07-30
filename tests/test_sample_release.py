import json
from pathlib import Path

from scripts.build_sample_release import build_sample


def test_sample_release_builds_end_to_end(tmp_path: Path) -> None:
    latest_path = build_sample(tmp_path)
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    release_root = tmp_path / "releases" / latest["release_id"]
    observations = json.loads((release_root / "observations.json").read_text(encoding="utf-8"))
    coverage = json.loads((release_root / "coverage.json").read_text(encoding="utf-8"))

    assert latest["release_id"] == "world-bank-population-2023-sample"
    assert [row["geography_id"] for row in observations] == [1, 2, 3]
    assert coverage["geography_ids"] == [1, 2, 3]
    assert coverage["periods"] == ["2023"]
    assert all(row["status"] == "observed" for row in observations)
