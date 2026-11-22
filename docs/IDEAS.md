# Idea Log

Ideas are captured here before they become decisions or tasks. IDs are stable.
Only the coordinator adds new IDs. Agents propose ideas in their task's
*Follow-ups* section.

**Status:** `captured` → `planned` (linked to T-/ADR-) → `done` | `rejected` (with reason)

| ID | Idea | Status | Links |
|---|---|---|---|
| I-001 | Rate pollsters on accuracy vs. actual results | planned | M-2, T-021, T-022 |
| I-002 | Detect systematic lean toward/against specific parties, separated from industry-wide misses | planned | M-2.5, M-4, T-022, T-040 |
| I-003 | Single trust score (0–100, A–F) with a certainty level | planned | M-5, T-043 |
| I-004 | Campaign-long house effect, not just final polls | planned | M-3.2, T-023 |
| I-005 | "Convergence" flag: lean during campaign, alignment just before the vote | planned | M-3.3, T-042 |
| I-006 | Herding detection (polls too stable for their sample size) | planned | M-3.4, T-041 |
| I-007 | "Adjusted poll": correct a new poll using the house's historical bias | planned | M-6, T-060 |
| I-008 | Transparency score (sample size, mode, wording, sponsor published?) | planned | M-5.3, T-005 |
| I-009 | Flag party-commissioned polls | planned | M-5.1d, T-005 |
| I-010 | Right of reply for pollsters before publishing ratings | planned | T-053 |
| I-011 | Compare polls to the domestic result (exclude diaspora) by default | planned | M-1.4 |
| I-012 | Visuals: diverging bar per party, house × party heatmap, target plot per election, timeline vs. market | planned | T-030, T-052 |
| I-013 | Reference market built from the toplines of *all* houses (index-level verification), so that house effects for the MVP houses don't depend on only 2–4 peers | captured | M-2.5, M-3.1, ADR-0007 |
| I-014 | Extract crosstabs (age, region, education…) from the archived reports | captured | ADR-0007 |
| I-015 | Automated discovery and extraction of polls (RSS, LLM-assisted, human-verified) to scale beyond the MVP | captured | T-065 |
| I-016 | Track a lean toward a *party* across election types by linking presidential candidates to the parties that supported them | planned | T-004 |
| I-017 | Scrape sondajeromania.ro (polls, linked documents, pollster pages) as a discovery source when scaling beyond the MVP. Check its terms/robots first, give attribution, and still verify every value against the original | captured | T-065, ADR-0007 |
| I-018 | Take design inspiration from sondajeromania.ro (visual design, design system, UX, light mode). Design only: none of its product logic or mechanisms | planned | ADR-0008, ADR-0009, T-031 |
