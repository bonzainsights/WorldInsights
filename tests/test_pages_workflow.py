from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pages.yml"


def test_pages_workflow_validates_deploys_and_browser_tests_global_build() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request:" not in content
    assert "workflow_dispatch:" in content
    assert "branches:\n      - main" in content
    assert 'cron: "17 5 * * 1"' in content
    assert "pages: write" in content
    assert "id-token: write" in content
    assert "actions/configure-pages@v5" in content
    assert "actions/upload-pages-artifact@v3" in content
    assert "actions/deploy-pages@v4" in content
    assert "actions/upload-artifact@v4" in content
    assert "path: apps/web/dist" in content

    validation = content.index("run: make check")
    build = content.index("run: npm --prefix apps/web run build")
    upload = content.index("uses: actions/upload-pages-artifact@v3")
    deploy = content.index("uses: actions/deploy-pages@v4")
    smoke = content.index("name: Verify deployed explorer")
    metadata = content.index("name: Smoke test public Pages metadata")
    install_browser = content.index("name: Install pinned Playwright and Chromium")
    browser = content.index("name: Verify global user flows in Chromium")
    report = content.index("name: Upload browser report on failure")
    assert validation < build < upload < deploy < smoke
    assert smoke < metadata < install_browser < browser < report

    assert "WORLDINSIGHTS_RELEASE_MODE: live" in content
    assert "WORLDINSIGHTS_RELEASE_SCOPE: global" in content
    assert 'WORLDINSIGHTS_START_YEAR: "2019"' in content
    assert 'WORLDINSIGHTS_END_YEAR: "2024"' in content
    assert "page_url: ${{ steps.deployment.outputs.page_url }}" in content
    assert "SITE_URL: ${{ needs.deploy.outputs.page_url }}" in content
    assert 'fetch("build.json")' in content
    assert 'fetch("data/latest.json")' in content
    assert 'fetch("data/" + latest["catalog"])' in content
    assert 'fetch("apps/web/src/main.js")' in content
    assert 'fetch("styles.css")' in content
    assert "build.get(\"release_mode\") != \"live\"" in content
    assert "build.get(\"release_scope\") != \"global\"" in content
    assert "latest.get(\"schema_version\") != 2" in content
    assert 'release_id.startswith("world-bank-global-indicators-")' in content
    assert 'len(catalog.get("geographies", [])) < 200' in content
    assert 'item.get("row_count", 0) < 1_000' in content

    assert "node-version: \"22\"" in content
    assert "npm install --no-save @playwright/test@1.60.0" in content
    assert "npx playwright install --with-deps chromium" in content
    assert "npx playwright test --config=playwright.config.mjs --project=chromium" in content
    assert "name: deployed-browser-report" in content
    assert "path: apps/web/playwright-report" in content
    assert "if: failure()" in content
