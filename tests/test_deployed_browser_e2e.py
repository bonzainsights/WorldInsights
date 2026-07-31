from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "apps/web/e2e/global-pages.spec.mjs"
CONFIG = ROOT / "apps/web/playwright.config.mjs"
INDEX = ROOT / "apps/web/index.html"


def test_deployed_browser_spec_covers_global_interactions_and_full_export() -> None:
    content = SPEC.read_text(encoding="utf-8")

    assert 'page.locator("#country-search")' in content
    assert 'page.locator("[data-country-option]:not([hidden])")' in content
    assert 'name: "Clear visible"' in content
    assert 'name: "Select all visible"' in content
    assert 'input[name="indicators"][value="wb.sp.dyn.le00.in"]' in content
    assert "toHaveCount(3)" in content
    assert 'operation.selectOption("correlation")' in content
    assert 'page.locator(".correlation-card")' in content
    assert "Pearson correlation coefficient" in content
    assert 'toHaveText(/^r = -?(?:0\\.\\d{3}|1\\.000)$/)' in content
    assert "correlation does not imply causation" in content
    assert 'name: "Use latest period"' in content
    assert 'input[name="scope-period"][value="2023"]' in content
    assert 'searchParams.has("r")' in content
    assert 'toHaveClass(/dense-scatter/)' in content
    assert 'page.locator("table.data-table").first()' in content
    assert "resultRowCount" in content
    assert 'Showing 100 of ${resultRowCount} rows' in content
    assert 'name: "Download CSV"' in content
    assert "resultRowCount + 1" in content
    assert 'operation.selectOption("trend")' in content
    assert 'name: "Keep first 5 selected"' in content
    assert 'page.locator(".chart-legend li")' in content
    assert "toHaveCount(5)" in content
    assert 'page.on("pageerror"' in content
    assert "expect(pageErrors).toEqual([])" in content


def test_playwright_configuration_is_bounded_and_failure_diagnostic() -> None:
    content = CONFIG.read_text(encoding="utf-8")

    assert 'process.env.SITE_URL' in content
    assert 'workers: 1' in content
    assert 'retries: 1' in content
    assert 'name: "chromium"' in content
    assert 'devices["Desktop Chrome"]' in content
    assert 'trace: "retain-on-failure"' in content
    assert 'screenshot: "only-on-failure"' in content
    assert 'open: "never"' in content


def test_recipe_transition_guard_precedes_the_explorer() -> None:
    content = INDEX.read_text(encoding="utf-8")
    guard = content.index("apps/web/src/recipe-transition-guard.js")
    main = content.index("apps/web/src/main.js")

    assert guard < main


def test_playwright_files_are_valid_javascript_modules() -> None:
    for path in (CONFIG, SPEC):
        result = subprocess.run(
            ["node", "--check", str(path)],
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stderr
