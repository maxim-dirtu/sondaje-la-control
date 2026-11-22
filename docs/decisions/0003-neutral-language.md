# ADR-0003: Neutral, non-accusatory language

- **Status:** Proposed (working default)
- **Date:** 2026-11-22
- **Related:** I-002, T-054

## Context
Statistics can show that a pollster deviates systematically and beyond chance.
They cannot prove intent. Accusatory wording would be scientifically unsound
and a legal risk, and it would damage the platform's credibility.

## Decision
- Describe findings as "systematic deviation", "statistical lean", "house
  effect", always with a magnitude and an uncertainty interval.
- Never use "manipulation", "rigged", "fake", or "intentionally favors" in UI,
  docs, or identifiers.
- Every public claim links to its methodology section and to its underlying data.
- Pollsters get a right of reply (T-053) before ratings are published.

## Consequences
Messages are less sensational but defensible. The legal review (T-054) checks
compliance before launch.

## Alternatives considered
- "Call it as we see it" wording: rejected because of the legal and credibility risk.
