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

## 2. Language

- **English** for everything technical: code, identifiers, comments, docs,
  commit messages, task files, ADRs, prompts, and logs.
- **Romanian** only for public-facing UI copy. Keep it in locale/content
  files, never hard-coded in logic. Conversations with the project owner may
  be in Romanian.

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
  the task's *Follow-ups* section instead. The coordinator assigns IDs on `main`.
- **Shared files**: [docs/PLAN.md](docs/PLAN.md), [docs/METHODOLOGY.md](docs/METHODOLOGY.md),
  `docs/DATA_MODEL.md`, [docs/IDEAS.md](docs/IDEAS.md), and this file. Edit them only if
  your task's Scope lists them. Otherwise propose changes under *Follow-ups*.
- New ADRs written on a branch are named `docs/decisions/draft-<slug>.md`.
  The coordinator gives them a number when merging.
- Commit small and often. Rebase on `main` before handing off.

### Finishing
1. Check every acceptance criterion, then run the tests and the linter.
2. Fill in *Outcome*: what was done, the key commits, and known limitations.
3. Set `status: review`. The coordinator merges into `main` and sets `status: done`.

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
- Every row records `source_url` and `retrieved_at` (ISO date). Polls also
  record where the source came from (e.g. pollster site, media article, or
  Wikipedia).
- Wikipedia and aggregators (e.g. sondajeromania.ro) are **indexes, not
  sources**. Verify against the original publication whenever possible.
- Polls are recorded as **full toplines**: every option exactly as published.
  The original report is archived ([ADR-0007](docs/decisions/0007-mvp-scope.md)).
- Official results come from AEP/BEC. Keep domestic, diaspora, and total
  results separate.
- Canonical data is versioned CSV in git ([ADR-0004](docs/decisions/0004-data-storage-csv-in-git.md)).

## 7. Definition of done

- [ ] All acceptance criteria are met
- [ ] Tests are added or updated and pass; the linter passes
- [ ] Docs are updated if behaviour, schema, or methodology changed
- [ ] The task file's *Log* and *Outcome* are filled in
- [ ] Every commit references the task ID

## 8. Commands

_To be filled in by T-002 (Python project skeleton)._
