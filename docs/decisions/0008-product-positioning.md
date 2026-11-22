# ADR-0008: Product positioning: an explanation-first investigation, not an aggregator

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** I-017, I-018, T-031, T-051, T-052

## Context
Poll aggregators already exist in Romania (e.g. sondajeromania.ro: averages,
trends, seat projections, coalition simulations). Building another one would
add little. The owner's goal is different: an **investigative case study**
that shows which pollsters deviate systematically and which do not, and that
can **explain this to the general public**.

## Decision
- The product is an **investigation**: pollster accountability, not a poll
  feed. Features such as averages, projections, and simulations exist only
  where they support the investigation, for example the market average used
  as a reference.
- **The UI explanation is the top priority.** Every finding must be
  understandable by a non-expert within seconds: a plain-language headline,
  one simple visual, then the details on demand (methodology, data, uncertainty).
- The design should feel calm and credible, clearly not a generic template.
  sondajeromania.ro is a good reference for clarity and visual tone.
  We take **general ideas only** (layout, readability, chart style) and never
  copy its code, assets, or text.
- The UX concept is developed **early and in parallel** with the data work
  (T-031). It does not wait for the public-site phase.

## Consequences
- Every metric task should also answer the question "how will this be shown
  and explained?"
- Scope decisions favour depth on a few pollsters over breadth (consistent with
  ADR-0007).

## Alternatives considered
- A full-featured aggregator: it duplicates existing sites and dilutes the
  investigative message.
