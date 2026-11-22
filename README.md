# Sondaje la control

A platform that evaluates Romanian political pollsters against actual election
results. It shows how accurate each polling firm has been, which parties it
systematically over- or under-estimates, and how much its polls can be trusted.
The results are presented in a way the general public can understand.

> Working name. Public-facing UI will be in Romanian; all technical material
> (code, docs, comments, commits, prompts) is in English. See
> [ADR-0002](docs/decisions/0002-language-policy.md).

## What it answers

- **Accuracy:** How close were this pollster's final polls to the result?
- **Bias:** Which parties does it systematically over- or under-estimate,
  relative to the rest of the market?
- **Behaviour:** Does it herd? Does it converge suddenly to the consensus just
  before election day?
- **Trust:** A single, explainable trust score (0–100, grade A–F) with a
  certainty level.

## Repository map

| Path | Purpose |
|---|---|
| [AGENTS.md](AGENTS.md) | **Start here.** Working rules for humans and AI agents |
| [docs/PLAN.md](docs/PLAN.md) | Roadmap: phases, milestones, task index |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Specification of every metric (stable section IDs `M-x.y`) |
| [docs/IDEAS.md](docs/IDEAS.md) | Idea log (`I-xxx`), promoted to tasks or ADRs |
| [docs/decisions/](docs/decisions/) | Architecture/Product Decision Records (`ADR-xxxx`) |
| [tasks/](tasks/) | One file per unit of work (`T-xxx`). The status of each task is kept here |

## Status

Phase 0 (Foundations). See [docs/PLAN.md](docs/PLAN.md).
