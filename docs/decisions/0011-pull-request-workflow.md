# ADR-0011: All changes reach `main` through owner-approved pull requests

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** ADR-0006 (refines its merge step)

## Context
Until now the coordinator merged reviewed task branches into `main` locally
and pushed them. The owner wants to approve every change and to see, for each
merge, what it is responsible for: problem, goal, solution, what changed and
how. That is the usual PR/MR workflow.

## Decision
- **Nothing is pushed directly to `main`**, including the coordinator's own
  housekeeping. Every change goes through a GitHub pull request.
- **Branches:** `task/T-xxx-slug` for tasks, and `chore/T-000-slug` for
  coordinator housekeeping (plan updates, follow-ups, new task files).
- **Flow:**
  1. The agent finishes the task on its branch (`status: review`).
  2. The coordinator reviews it and runs the checks. As the last commit on the
     branch, the coordinator sets `status: done`, so `main` only ever sees
     finished tasks.
  3. The coordinator pushes the branch and opens a PR using
     [the template](../../.github/pull_request_template.md): problem, goal,
     solution, what changed and how, verification, traceability, and notes.
  4. **The owner reviews and merges.** Change requests go back to the branch.
- **Merge method:** "Create a merge commit", so that the task-ID commits stay
  visible in the history.
- PR titles follow the commit convention: `T-xxx: <task title>`.

## Consequences
- The owner is the gate for `main`. Dependent tasks start only after their
  prerequisites' PRs are merged.
- Coordinator follow-ups (e.g. applying a task's proposals to other task
  files) are batched into `chore/T-000-*` PRs instead of going straight to
  `main`.
- Recommended GitHub settings: protect `main` by requiring a pull request
  before merging. Required approvals are not used, because GitHub does not let
  an author approve their own PR and every push comes from the owner's
  account. Also enable "Automatically delete head branches".

## Alternatives considered
- Coordinator merges locally (the previous practice): the owner had no review
  gate and no per-change description.
- Squash merges: they hide the per-task commit history that ADR-0006 relies on.
