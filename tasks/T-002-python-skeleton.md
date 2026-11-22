---
id: T-002
title: Python project skeleton
status: todo
phase: 0
depends_on: []
owner: null
branch: null
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
- [ ] After a fresh clone, `uv sync`, `uv run pytest`, `uv run ruff check .` and
      `uv run ruff format --check .` all succeed.
- [ ] `uv run sondaje --help` works.
- [ ] AGENTS.md §8 lists the exact commands.

## Follow-ups

## Log

## Outcome
