from pathlib import Path


BUILD_SCRIPT = Path(__file__).resolve().parents[1] / "apps/web/scripts/build.mjs"


def test_static_build_defaults_to_offline_sample_and_supports_explicit_live_mode() -> None:
    content = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert 'process.env.WORLDINSIGHTS_RELEASE_MODE ?? "sample"' in content
    assert 'new Set(["sample", "live"])' in content
    assert "scripts/build_sample_release.py" in content
    assert "scripts/build_live_world_bank_release.py" in content
    assert 'WORLDINSIGHTS_START_YEAR", "2019"' in content
    assert 'WORLDINSIGHTS_END_YEAR", "2024"' in content
    assert 'release_mode: releaseMode' in content
    assert 'data_source: releaseMode === "live"' in content
    assert "startYear > endYear" in content
    assert "must be a four-digit year" in content
