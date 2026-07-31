from pathlib import Path


def test_country_registry_source_dependency_is_exactly_pinned() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    assert "pycountry==24.6.1" in content
