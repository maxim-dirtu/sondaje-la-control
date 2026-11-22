# ADR-0006: Multi-agent workflow

- **Status:** Proposed (working default). The merge step is superseded by
  [ADR-0011](0011-pull-request-workflow.md): the owner merges through PRs.
- **Date:** 2026-11-22
- **Related:** none

## Context
Several AI agents work at the same time. We need to avoid duplicate work,
merge conflicts, and lost context, without a heavyweight tracker.

## Decision
- **One file per task** in `tasks/`, with YAML front matter. The task file is
  the single source of truth for that task's status. `docs/PLAN.md` holds
  structure only, never status.
- **Branch = lock:** `task/T-xxx-slug`. Each agent works in its own git
  worktree. If a branch for the task already exists, the task is taken.
- **The coordinator** (the owner, or the owner's main agent session) is the
  only one who assigns new IDs (T-, I-, ADR-), merges to `main`, and edits
  shared files outside a task's scope.
- Commit messages start with the task ID.
- The full rules are in [AGENTS.md](../../AGENTS.md).

## Consequences
- The setup works offline with plain git and no external tracker.
- It can migrate later to GitHub Issues/Projects if a remote is added. Task
  IDs would map to issues.

## Alternatives considered
- GitHub Issues now: no remote exists yet, and agents work locally.
- A single TODO/board file: constant merge conflicts.
