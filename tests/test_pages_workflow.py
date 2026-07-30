from pathlib import Path


WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/pages.yml"


def test_pages_workflow_validates_before_uploading_static_build() -> None:
    content = WORKFLOW.read_text(encoding="utf-8")

    assert "pull_request:" not in content
    assert "workflow_dispatch:" in content
    assert "branches:\n      - main" in content
    assert "pages: write" in content
    assert "id-token: write" in content
    assert "actions/configure-pages@v5" in content
    assert "actions/upload-pages-artifact@v3" in content
    assert "actions/deploy-pages@v4" in content
    assert "path: apps/web/dist" in content

    validation = content.index("run: make check")
    build = content.index("run: npm --prefix apps/web run build")
    upload = content.index("uses: actions/upload-pages-artifact@v3")
    assert validation < build < upload
