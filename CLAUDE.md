# CLAUDE.md

## Overview
- Business Analyst portfolio monorepo (Learning/, Practice/, Projects/).
- Learning/ and Practice/ are the owner's study material: never modify unless asked.
- The two existing projects in Projects/ follow a school-style structure; treat them as reference only.
- Folders under Projects/ whose names start with `_` (for example `_template`) are not projects.

## Environment
- Python 3.12, root `.venv`. Deps: `requirements.txt` (direct), `requirements-dev.txt` (dev).
- Test (run inside a project folder): `pytest -q`. Run: `MPLBACKEND=Agg python main.py`.

## Code and deliverable principles
Defaults; deviate if you have a better approach, and note the reason briefly in the project README.
- Goals: (a) readable for recruiters, (b) reproducible, (c) outputs a website can present as
  question -> chart -> interpretation -> business impact.
- Save the aggregated data behind each chart as small CSV/JSON next to the PNG, so the web can
  render interactive charts and animations. Never export raw data to the web.
- Organize analysis by business question. For each: question, method, chart, one-line takeaway, limitations.
- Record the why of every cleaning/analysis decision (comment or doc).
- `pipeline/` split into load/clean/analyze/visualize is a reference default.
  Visualization functions return a Figure; library code never calls `plt.show()`.
- Extract shared code only when two or more projects need it. No premature abstraction.
- Docstrings and READMEs of new projects are written in English.

## Data rules
- Never commit data files (csv, xlsx, sqlite, ...).
- New projects record source URL, download date and row count in `data_manifest.json` at the project root.

## Git rules
- Every commit starts with `[AI-<TYPE>]`, TYPE in PROJECT, FEAT, CHORE, FIX.
- Project work: `[AI-PROJECT] <slug> <stage>: <summary>`.
- Keep the Co-Authored-By trailer. One logical change per commit.
- Never `git add -A` or `git add .`; add explicit paths (untracked study notebooks must not get mixed in).
- Never push without the owner's permission. Never amend or rebase commits that were already pushed.

## Safety
- Do not read or print the contents of `.env`, `.zshrc`, `.envrc`.
- Open `.ipynb` only when necessary, read only parts, and skip cells with large outputs.
