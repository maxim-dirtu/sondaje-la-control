# ADR-0009: Design direction: light-first, design inspiration only

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** ADR-0008, I-018, T-031, T-052 (refines ADR-0008)

## Context
The owner likes the visual design and UX of sondajeromania.ro: it is clear and
calm, and it doesn't look like a generic AI-generated site. Its *purpose*,
however, is different. It is a poll aggregator and visualizer, whereas this
project is an investigative case study (ADR-0008).

## Decision
- From sondajeromania.ro we take **inspiration only for the visual design, the
  design system, and the UX**: layout, typography, spacing, component style,
  readability, navigation, and theming.
- We **do not adopt its product logic or mechanisms**: poll averages as a
  feature, seat projections, coalition simulations, its accuracy approach
  (last-poll MAE, "favored candidate"), or aggregator-style poll feeds. Every
  feature must serve the investigation as specified in
  [METHODOLOGY.md](../METHODOLOGY.md).
- **Light mode is the primary theme.** The UI is designed and reviewed in light
  mode first. Dark mode is optional and secondary. It is made possible through
  design tokens (CSS custom properties), but it is not a launch requirement.
- The visual language is a small design system: tokens (colour, type scale,
  spacing, radius, elevation) plus a component inventory shared by the
  prototype and the public site.

## Consequences
- T-031 (UX concept), T-030 (prototype), and T-052 (public site) build on the
  same tokens and components.
- No code, assets, or text are copied from any reference site.
- Using sondajeromania.ro as a *data discovery* source (I-017) is a separate
  matter and is unaffected.

## Alternatives considered
- Dark-first: rejected by the owner, who finds it looks generic and "AI-ish".
- Reusing aggregator features to make the site richer: this would dilute the
  investigative message (ADR-0008).
