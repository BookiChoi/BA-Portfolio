"""Tests for scripts/new_project.py (uses tmp_path only; never writes inside Projects/)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "new_project.py"

EXPECTED_FILES = {
    "README.md",
    "config.yaml",
    "data_manifest.json",
    "data/.gitkeep",
    "pipeline/.gitkeep",
    "tests/.gitkeep",
    "notebooks/.gitkeep",
    "outputs/.gitkeep",
    "workflow/00_brief.md",
    "workflow/02_questions.md",
    "workflow/07_insights.md",
    "workflow/09_recommendations.md",
}


def run(slug: str, company: str, target: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), slug, "--company", company, "--target-dir", str(target)],
        capture_output=True,
        text=True,
    )


def files_in(root: Path) -> set[str]:
    return {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}


def test_creates_folders_and_files(tmp_path):
    result = run("acme-churn", "Acme Corp", tmp_path)
    assert result.returncode == 0, result.stderr
    project = tmp_path / "acme-churn"
    assert files_in(project) == EXPECTED_FILES
    assert "00_brief.md" in result.stdout  # next-step hint is printed


def test_placeholders_are_substituted(tmp_path):
    assert run("acme-churn", 'Acme "Quoted": Corp', tmp_path).returncode == 0
    project = tmp_path / "acme-churn"
    for rel in files_in(project):
        text = (project / rel).read_text(encoding="utf-8")
        assert "{{" not in text, f"unreplaced placeholder in {rel}"

    config = (project / "config.yaml").read_text(encoding="utf-8")
    assert 'slug: "acme-churn"' in config
    assert 'company: "Acme \\"Quoted\\": Corp"' in config
    assert re.search(r'created: "\d{4}-\d{2}-\d{2}"', config)
    assert "language: en" in config
    assert '"project": "acme-churn"' in (project / "data_manifest.json").read_text(encoding="utf-8")
    assert "Acme" in (project / "README.md").read_text(encoding="utf-8")
    for name in ("00_brief", "02_questions", "07_insights", "09_recommendations"):
        first = (project / "workflow" / f"{name}.md").read_text(encoding="utf-8").splitlines()[0]
        assert first == "Author: human"


def test_duplicate_slug_is_rejected_without_overwriting(tmp_path):
    assert run("acme-churn", "Acme", tmp_path).returncode == 0
    marker = tmp_path / "acme-churn" / "workflow" / "00_brief.md"
    marker.write_text("Author: human\nmy own notes\n", encoding="utf-8")

    result = run("acme-churn", "Other", tmp_path)
    assert result.returncode != 0
    assert "already exists" in result.stderr
    assert marker.read_text(encoding="utf-8") == "Author: human\nmy own notes\n"


@pytest.mark.parametrize("slug", ["Acme", "acme_churn", "-acme", "acme-", "acme--churn", "acme churn", ""])
def test_invalid_slug_is_rejected(tmp_path, slug):
    result = run(slug, "Acme", tmp_path)
    assert result.returncode != 0
    assert not any(tmp_path.iterdir())
