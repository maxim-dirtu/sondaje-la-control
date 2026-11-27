# Sondaje la control

[![CI](https://github.com/maxim-dirtu/sondaje-la-control/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/maxim-dirtu/sondaje-la-control/actions/workflows/ci.yml)

An investigative case study of Romanian political pollsters, measured against
actual election results. It shows how accurate each polling firm has been,
which parties it systematically over- or under-estimates, and how much its
polls can be trusted. Above all, it **explains this simply to the general
public**. It is not a poll aggregator; see
[ADR-0008](docs/decisions/0008-product-positioning.md).

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
| [docs/COORDINATOR.md](docs/COORDINATOR.md) | Playbook for whoever coordinates: the task loop, owner preferences, tooling notes |
| [docs/METHODOLOGY.md](docs/METHODOLOGY.md) | Specification of every metric (stable section IDs `M-x.y`) |
| [docs/IDEAS.md](docs/IDEAS.md) | Idea log (`I-xxx`), promoted to tasks or ADRs |
| [docs/decisions/](docs/decisions/) | Architecture/Product Decision Records (`ADR-xxxx`) |
| [tasks/](tasks/) | One file per unit of work (`T-xxx`). The status of each task is kept here |

## Development

The analysis code is a Python 3.12 package (`src/sondaje/`) managed by
[uv](https://docs.astral.sh/uv/), which also installs the interpreter
([ADR-0005](docs/decisions/0005-analysis-stack.md)).

```powershell
uv sync                       # create .venv/ from uv.lock
uv run pytest                 # tests
uv run ruff check .           # lint
uv run ruff format --check .  # formatting
uv run sondaje --help         # command-line tool
```

See [AGENTS.md §8](AGENTS.md#8-commands) for the full command list.

## Status

Phase 0 (Foundations). See [docs/PLAN.md](docs/PLAN.md).
