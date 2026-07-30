import json
from pathlib import Path

from scripts.build_sample_release import build_sample
from worldinsights.recipe import recipe_from_dict, recipe_to_dict

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "contracts"


def test_python_accepts_canonical_recipe_fixture() -> None:
    payload = json.loads((FIXTURE_ROOT / "exploration_recipe_v1.json").read_text())
    assert recipe_to_dict(recipe_from_dict(payload)) == payload


def test_static_release_fixture_matches_python_builder(tmp_path: Path) -> None:
    latest_path = build_sample(tmp_path)
    latest = json.loads(latest_path.read_text())
    release_root = tmp_path / "releases" / latest["release_id"]
    actual = {
        "latest": latest,
        "manifest": json.loads((release_root / "manifest.json").read_text()),
        "coverage": json.loads((release_root / "coverage.json").read_text()),
        "observations": json.loads((release_root / "observations.json").read_text()),
    }
    expected = json.loads((FIXTURE_ROOT / "static_release_v1.json").read_text())
    assert actual == expected
