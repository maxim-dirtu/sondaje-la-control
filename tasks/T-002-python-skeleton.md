---
id: T-002
title: Python project skeleton
status: done
phase: 0
depends_on: []
owner: agent-t002
branch: task/T-002-python-skeleton
methodology: []
created: 2026-11-22
updated: 2026-11-22
---

## Goal
A reproducible Python project: any agent can set it up, then lint and test it
with three commands on Windows.

## Context
[ADR-0005](../docs/decisions/0005-analysis-stack.md). Python is not on the
system PATH. uv manages the interpreter.

## Scope
**In:**
- `pyproject.toml` (uv), `.python-version` (3.12), and `uv.lock`
- The package `src/sondaje/` with a CLI entry point `sondaje` (subcommands
  added by later tasks)
- ruff config (lint + format) and pytest config; `tests/` with a smoke test
- `.gitignore` additions (`.venv/`, `build/`, caches)
- **Shared files allowed:** `AGENTS.md` §8 Commands; `README.md` (Development
  section)

**Out:**
- Heavy dependencies (PyMC etc.), which are added by the tasks that need them.

## Acceptance criteria
- [x] After a fresh clone, `uv sync`, `uv run pytest`, `uv run ruff check .` and
      `uv run ruff format --check .` all succeed.
- [x] `uv run sondaje --help` works.
- [x] AGENTS.md §8 lists the exact commands.

## Follow-ups
- uv prints "Failed to hardlink files" on machines where the uv cache and the
  repo are on different drives (here: cache on C:, repo on E:). It is harmless;
  setting `UV_LINK_MODE=copy` in the user environment silences it. It is
  deliberately not set in `pyproject.toml` because it is machine-specific.
- Optional CI (e.g. a GitHub Actions job running the four checks) once the
  repository has a remote. Not in this task's scope.

## Log
- 2026-11-22: Tooling: uv 0.12.21, CPython 3.12.14 (installed by
  `uv python install 3.12`), build backend `uv_build` (uv's default, pinned
  `>=0.12.21,<0.13.0`). Dev dependencies only: pytest 9.2.0, ruff 0.17.6. No
  runtime dependencies yet; later tasks add pandas/DuckDB/SciPy/PyMC as needed.
- 2026-11-22: CLI uses **argparse**, not typer. Reasons: zero dependencies
  (stdlib), stable, and enough for subcommands such as `validate`,
  `ingest-results <election_id>`, `archive`, `report`. Extension point:
  `sondaje.cli.COMMANDS` is a list of registrar functions
  `register(subparsers)`; each registrar adds its subparser and sets
  `handler=<fn(args) -> int>` via `set_defaults`. `main()` returns the exit
  code, so the console script and `python -m sondaje` exit with it. The
  `commands:` section only appears in `--help` once a subcommand exists.
  Without a subcommand the CLI prints help and exits 0. `--version` reads the
  installed package metadata.
- 2026-11-22: ruff rules: E, W, F, I (isort), UP (pyupgrade), B (bugbear),
  SIM, C4, PTH (pathlib), RUF; line length 100; target py312.
  Verified on stdin that I001, UP006/UP035 and B006 fire.
- 2026-11-22: ruff 0.17 also formats Python code blocks inside Markdown files.
  Added `extend-exclude = ["*.md"]` so `ruff format .` never rewrites the
  shared docs (PLAN, METHODOLOGY, ...).
- 2026-11-22: `ruff format` uses `line-ending = "auto"` instead of `"lf"`:
  `.gitattributes` (`* text=auto eol=lf`) already normalizes committed files
  to LF, and `"lf"` made `format --check` fail on files that Windows tools
  write with CRLF before they are committed.
- 2026-11-22: pytest config in `[tool.pytest.ini_options]`: `testpaths =
  ["tests"]`, `-ra --strict-markers --strict-config`, `xfail_strict`. The smoke
  tests cover the import and version, `--help`, `--version`, no-command, an
  unknown command (exit 2), dispatch to a registered subcommand, and `--help`
  run in a subprocess via both `python -m sondaje` and the `sondaje` console
  script.
- 2026-11-22: `.gitignore`: added `data/raw/` (raw downloads, see T-010/T-011),
  `.coverage`, `htmlcov/`, `dist/`, `*.egg-info/`. `.venv/`, `build/` and the
  tool caches were already listed.
- 2026-11-22: Verified in a fresh `git clone` of this branch:
  `uv sync` → 8 packages installed, exit 0; `uv run pytest` → 8 passed;
  `uv run ruff check .` → "All checks passed!"; `uv run ruff format --check .`
  → "4 files already formatted"; `uv run sondaje --help` → usage text, exit 0;
  `uv lock --check` → exit 0. `git status --ignored` showed `.venv/` and the
  caches as ignored, and none of them are tracked.

## Outcome
A reproducible uv-managed Python 3.12 project:
- `pyproject.toml` (package `sondaje`, src layout, console script
  `sondaje = sondaje.cli:main`, ruff + pytest config), `.python-version`,
  `uv.lock`.
- `src/sondaje/` with `__init__.py` (`__version__`), `__main__.py`, and
  `cli.py` (argparse, pluggable subcommand registry; only `--help`/`--version`
  for now).
- `tests/test_smoke.py` (8 tests).
- `.gitignore` additions; AGENTS.md §8 Commands; README "Development" section.

Key commits: `b8cba78` (start), `c02229c` (.gitignore), `38a6fb8` (uv
project and config), `76e34d1` (package, CLI, tests), `eb120ce` (docs).

Known limitations: no runtime dependencies or subcommands yet (added by
T-003, T-010, T-011, T-025). No type checker configured (optional per
ADR-0005).
