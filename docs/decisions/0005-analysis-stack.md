# ADR-0005: Analysis stack

- **Status:** Proposed (working default)
- **Date:** 2026-11-22
- **Related:** T-002

## Context
We need tooling that agents can run reproducibly on Windows, with mature
statistics libraries.

## Decision
- **Python ≥ 3.12**, managed by **uv**. uv also installs the Python
  interpreter, so no system Python is required.
- Libraries: pandas, DuckDB, SciPy/statsmodels (M-4.1–M-4.3), PyMC + ArviZ (M-4.4).
- Quality: ruff (lint + format) and pytest. Pyright/mypy are optional, added
  later if needed.
- Layout: `src/sondaje/` package, `tests/`, `notebooks/` for exploration only.
  Any logic that is reused belongs in `src/`.
- The prototype dashboard (T-030) is chosen in that task: Streamlit or a
  static site.
- The public web stack is decided separately (T-050).

## Consequences
One command (`uv sync`) sets up the environment. All metric logic is
unit-testable in `src/`.

## Alternatives considered
- R: strong statistics, but weaker for building the web and data pipeline.
- Poetry/pip: slower, and they do not manage the Python version.
