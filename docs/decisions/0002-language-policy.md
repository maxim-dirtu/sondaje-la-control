# ADR-0002: Language policy

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** none

## Context
The audience is Romanian. Code, tooling, AI agents, and the statistical
literature work best in English.

## Decision
- **English:** code, identifiers, comments, docs, commit messages, task files,
  ADRs, prompts, and logs.
- **Romanian:** public-facing UI copy and public explanations. This copy lives in
  locale/content files and is never hard-coded in logic.
- Party, candidate, and pollster names keep their original Romanian spelling,
  diacritics included (UTF-8 everywhere).

## Consequences
The Romanian copy needs its own guidelines (T-051). Glossary terms (e.g.
"house effect" → "abatere sistematică") are defined there.

## Alternatives considered
- Romanian everywhere: worse tooling and agent performance, and inconsistent
  technical vocabulary.
