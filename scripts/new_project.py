"""Create a new analysis project from templates/project/.

Usage:
    python scripts/new_project.py <slug> --company "<name>" [--target-dir <path>]

--target-dir is the PARENT folder; the project is created at <target-dir>/<slug>/.
Default: Projects/ at the repo root. Existing folders are never overwritten.
Standard library only.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = REPO_ROOT / "templates" / "project"
DEFAULT_TARGET_DIR = REPO_ROOT / "Projects"

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
TEXT_SUFFIXES = {".md", ".yaml", ".yml", ".json"}


def validate_slug(slug: str) -> None:
    """Allow lowercase letters, digits and single hyphens only."""
    if not SLUG_RE.fullmatch(slug):
        raise ValueError(
            f"invalid slug {slug!r}: use lowercase letters, digits and single "
            "hyphens (no leading/trailing/double hyphens)"
        )


def validate_company(company: str) -> str:
    company = company.strip()
    if not company:
        raise ValueError("--company must not be empty")
    if any(ord(ch) < 32 for ch in company):
        raise ValueError("--company must not contain control characters or newlines")
    return company


def _escape_for(path: Path, value: str) -> str:
    """Escape a value for use inside double quotes in YAML/JSON files."""
    if path.suffix in {".yaml", ".yml", ".json"}:
        return value.replace("\\", "\\\\").replace('"', '\\"')
    return value


def render_template(slug: str, company: str, created: str) -> dict[Path, bytes]:
    """Render every template file in memory. Returns {relative path: content}."""
    if not TEMPLATE_DIR.is_dir():
        raise FileNotFoundError(f"template folder not found: {TEMPLATE_DIR}")
    values = {"slug": slug, "company": company, "created": created}
    rendered: dict[Path, bytes] = {}
    for src in sorted(TEMPLATE_DIR.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(TEMPLATE_DIR)
        if src.suffix in TEXT_SUFFIXES:
            text = src.read_text(encoding="utf-8")
            for key, value in values.items():
                text = text.replace("{{" + key + "}}", _escape_for(src, value))
            rendered[rel] = text.encode("utf-8")
        else:
            rendered[rel] = src.read_bytes()  # e.g. .gitkeep: copied as-is
    return rendered


def create_project(slug: str, company: str, target_dir: Path) -> list[Path]:
    """Validate, render in memory, then write. Returns the created files."""
    validate_slug(slug)
    company = validate_company(company)
    project_dir = target_dir / slug
    if project_dir.exists():
        raise FileExistsError(f"{project_dir} already exists; nothing was written")

    files = render_template(slug, company, date.today().isoformat())

    created: list[Path] = []
    for rel, content in files.items():
        dest = project_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        created.append(dest)
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a new analysis project from the template.")
    parser.add_argument("slug", help="lowercase letters, digits and hyphens, e.g. acme-churn")
    parser.add_argument("--company", required=True, help="company name")
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=DEFAULT_TARGET_DIR,
        help=f"parent folder for the project (default: {DEFAULT_TARGET_DIR})",
    )
    args = parser.parse_args(argv)

    try:
        created = create_project(args.slug, args.company, args.target_dir)
    except (ValueError, FileExistsError, FileNotFoundError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    project_dir = args.target_dir / args.slug
    print(f"Created {project_dir} ({len(created)} files):")
    for path in created:
        print(f"  {path.relative_to(project_dir)}")
    print("\nNext step: write workflow/00_brief.md yourself (company choice, what you found, questions, constraints).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
