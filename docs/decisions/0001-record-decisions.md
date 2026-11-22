# ADR-0001: Record decisions as ADRs

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** none

## Context
Several agents work on the project in parallel. Decisions made in chat or
inside one agent's context are lost to the others, which causes inconsistent
implementations and repeated debates.

## Decision
Any decision that affects more than one task, or that is hard to reverse, is
recorded as a short ADR in `docs/decisions/NNNN-slug.md`, using
[the template](_TEMPLATE.md). ADRs are immutable once accepted. A change is
made by writing a new ADR that supersedes the old one. Drafts written on task
branches are named `draft-<slug>.md` and get a number at merge time.

## Consequences
- Decisions can be traced to their ideas and tasks.
- Writing each ADR takes a little extra effort, which is acceptable.

## Alternatives considered
- Decisions recorded only in commit messages: too hard to find later.
- A single DECISIONS.md file: concurrent edits cause merge conflicts.
