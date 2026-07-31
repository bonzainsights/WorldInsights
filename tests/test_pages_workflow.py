from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pages.yml"


def test_pages_workflow_validates_deploys_and_smoke_tests_global_build() -> None:
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
    assert "path: apps/web/dist" in content

    validation = content.index("run: make check")
    build = content.index("run: npm --prefix apps/web run build")
    upload = content.index("uses: actions/upload-pages-artifact@v3")
    deploy = content.index("uses: actions/deploy-pages@v4")
    smoke = content.index("name: Verify deployed explorer")
    assert validation < build < upload < deploy < smoke

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
