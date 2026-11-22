# ADR-0010: Grades and pollster-card framing

- **Status:** Accepted
- **Date:** 2026-11-22
- **Related:** T-031, T-043, T-051, M-5.2

## Context
The T-031 UX review raised three product questions:
- With at most 3 elections per pollster in the MVP, the M-5.2 shrinkage caps
  scores at about 75. Grade A is impossible, and most grades fall to C or D.
- Below how many elections should a pollster get no grade?
- What should the pollster card lead with?

## Decision
1. **Grades are shown in the MVP, labelled "provisional"** ("provizorie"),
   together with the certainty level. The UI states plainly that more elections
   are needed for a final grade.
2. **A grade requires at least 3 elections** with a final poll. Below that the
   card shows "no grade yet" ("fără notă deocamdată") together with the
   findings and their uncertainty.
3. **The pollster card leads with a balanced summary**: overall accuracy
   relative to other pollsters, and whether any clear deviation exists. The
   per-party deviations, including the strongest one, come next. A single
   party is never named in the first line by default.

## Consequences
- M-5.2 is updated: no grade when N < 3; MVP grades are provisional.
- T-030 and T-052 apply the balanced lead and the "no grade yet" state. The
  T-031 mock-ups still show the earlier, strongest-deviation lead, and are
  treated as superseded on this point.
- T-051 writes the Romanian copy for "provisional" and "no grade yet".

## Alternatives considered
- No grades in the MVP (findings only): rejected by the owner.
- A grade from 1 or 2 elections: too little evidence.
- Strongest deviation first: more striking, but it puts one party's name in
  the headline and reads as accusatory (ADR-0003).
