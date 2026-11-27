# Agent & Contributor Guide

This file is the operating manual for every contributor, human or AI agent.
Several agents work on this project **concurrently**, so these rules exist
mainly to keep work traceable and conflict-free.

## 1. Read before you start

1. [README.md](README.md) for the project overview
2. [docs/PLAN.md](docs/PLAN.md) for the current phase and where your task fits
3. Your task file in [tasks/](tasks/). Its scope and acceptance criteria are your contract
4. [docs/METHODOLOGY.md](docs/METHODOLOGY.md) if you touch any calculation
5. Any ADR in [docs/decisions/](docs/decisions/) referenced by your task
6. **If you are the coordinator** (you assign tasks, review, and open PRs):
   [docs/COORDINATOR.md](docs/COORDINATOR.md)

## 2. Language

- **English** for everything technical: code, identifiers, comments, docs,
  commit messages, task files, ADRs, prompts, and logs.
- **Romanian** only for public-facing UI copy. Keep it in locale/content
  files, never hard-coded in logic.
- **Chat with the project owner:** reply in the language the owner used in
  their latest message (Romanian → Romanian, English → English).

## 3. Traceability model

```
Idea (I-xxx) ──► Decision (ADR-xxxx) ──► Task (T-xxx) ──► Branch ──► Commits ──► Merge
   docs/IDEAS.md    docs/decisions/        tasks/          task/T-xxx-slug   "T-xxx: ..."
```

- **Every commit** message starts with the task ID: `T-010: add parl-2024-cd results`.
  Coordinator housekeeping (merges, new IDs, plan updates) uses `T-000`.
- **Every metric implementation** cites the methodology section it implements,
  in its docstring (e.g. `Implements METHODOLOGY M-2.3`). If code and spec
  disagree, the spec wins. Fix the code, or change the spec through a task.
- **Every data row** carries provenance (`source_url`, `retrieved_at`). See §6.
- **Every non-obvious choice** goes in the task's *Log* section, with the date.
  Choices that affect other tasks get an ADR.

## 4. Multi-agent workflow

### Picking up a task
1. Choose a task with `status: todo` whose `depends_on` tasks are all `done`,
   or take the task the coordinator assigned to you.
2. **Lock it by creating its branch.** Branches are shared across worktrees,
   so an existing branch means the task is taken:
   ```powershell
   git branch --list "task/T-012*"     # must print nothing
   git worktree add ..\sondaje-wt\T-012 -b task/T-012-short-slug main
   ```
3. Your first commit on the branch sets `status: in-progress`, `owner`, and
   `branch` in the task file.

### While working
- Stay inside the task's **Scope**. If you discover extra work, **do not**
  create new task IDs, because concurrent agents would collide. Add it to
  the task's *Follow-ups* section instead. The coordinator assigns IDs.
- **Shared files**: [docs/PLAN.md](docs/PLAN.md), [docs/METHODOLOGY.md](docs/METHODOLOGY.md),
  `docs/DATA_MODEL.md`, [docs/IDEAS.md](docs/IDEAS.md), and this file. Edit them only if
  your task's Scope lists them. Otherwise propose changes under *Follow-ups*.
- New ADRs written on a branch are named `docs/decisions/draft-<slug>.md`.
  The coordinator gives them a number when merging.
- Commit small and often. Rebase on `main` before handing off.

### Finishing
1. Check every acceptance criterion, then run the tests and the linter.
2. Fill in *Outcome*: what was done, the key commits, and known limitations.
3. Set `status: review`. **Do not push and do not merge.** Your final report
   should give the coordinator what the PR description needs: problem, goal,
   solution, what changed and how, verification, and open questions.

### Review and merge ([ADR-0011](docs/decisions/0011-pull-request-workflow.md))
- **Nothing is pushed directly to `main`.** Every change, including the
  coordinator's housekeeping on `chore/T-000-slug` branches, reaches `main`
  through a GitHub pull request.
- The coordinator reviews the branch and runs the checks, then sets
  `status: done` as the last commit. It then pushes the branch and opens a PR
  titled `T-xxx: <task title>` using
  [the PR template](.github/pull_request_template.md).
- **The owner approves** (in chat, or with an "approved" comment on the PR).
  **Then the coordinator merges** (merge method: "Create a merge commit").
  Nothing is merged without explicit owner approval. Change requests go back
  to the same branch.
- Dependent tasks start only after their prerequisites' PRs are merged.

### Status values
`todo` → `in-progress` → `review` → `done`; also `blocked` (explain why in
the *Log*) and `dropped`.

## 5. Neutral language (mandatory)

Statistics can show *systematic deviation*. They **cannot** prove intent.
- Use: "systematic deviation", "statistical lean", "house effect",
  "overestimates X by ~3 pp".
- Never use: "manipulation", "rigged", "fake", or "intentionally favors". This
  applies in UI copy, docs, and identifiers.
- See [ADR-0003](docs/decisions/0003-neutral-language.md).

## 6. Data rules

- **Never invent or estimate data.** If a value can't be verified, leave it
  empty and note it in the task *Log*.
- Every row carries the provenance block from
  [DATA_MODEL.md §5.1](docs/DATA_MODEL.md): `source_url`, `source_type`
  (`official` | `pollster` | `media` | `aggregator` | `wikipedia` | `other`),
  `retrieved_at` (ISO date), `verified`, and `notes`.
- Wikipedia and aggregators (e.g. sondajeromania.ro) are **indexes, not
  sources**. Verify against the original publication whenever possible.
- Polls are recorded as **full toplines**: every option exactly as published.
  The original report is archived ([ADR-0007](docs/decisions/0007-mvp-scope.md)).
- Official results come from AEP/BEC. Keep domestic, diaspora, and total
  results separate.
- Canonical data is versioned CSV in git ([ADR-0004](docs/decisions/0004-data-storage-csv-in-git.md)).
  The schema, the ID conventions, and the integrity rules are in
  [DATA_MODEL.md](docs/DATA_MODEL.md).

## 7. Definition of done

- [ ] All acceptance criteria are met
- [ ] Tests are added or updated and pass; the linter passes
- [ ] Docs are updated if behaviour, schema, or methodology changed
- [ ] The task file's *Log* and *Outcome* are filled in
- [ ] Every commit references the task ID

## 8. Commands

Prerequisite: [uv](https://docs.astral.sh/uv/). No system Python is needed;
uv installs the interpreter pinned in `.python-version` (3.12). Run every
command from the repository root (or your worktree root).

| Purpose | Command |
|---|---|
| Set up / update the environment (creates `.venv/` from `uv.lock`) | `uv sync` |
| Run the tests | `uv run pytest` |
| Lint | `uv run ruff check .` |
| Lint and auto-fix | `uv run ruff check --fix .` |
| Check formatting | `uv run ruff format --check .` |
| Apply formatting | `uv run ruff format .` |
| CLI help | `uv run sondaje --help` |
| Validate all data in `data/` | `uv run sondaje validate` (add `--against main` to also check that registries are append-only; `--strict` makes warnings fail) |
| Add a runtime / dev dependency | `uv add <pkg>` / `uv add --dev <pkg>` (commit `uv.lock`) |

Before handing off, all four checks must pass:

```powershell
uv sync; uv run pytest; uv run ruff check .; uv run ruff format --check .
```

New CLI subcommands are registered in `src/sondaje/cli.py` (see its
docstring). `.venv/`, `build/`, and `data/raw/` are git-ignored.
