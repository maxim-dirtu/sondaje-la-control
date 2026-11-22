# Tasks

One Markdown file per task: `T-XXX-short-slug.md`, based on
[_TEMPLATE.md](_TEMPLATE.md). The front matter `status` field is the single
source of truth for the task's status.

- Workflow and locking rules: [AGENTS.md §4](../AGENTS.md)
- Order and dependencies: [docs/PLAN.md](../docs/PLAN.md)

ID ranges follow phases: `T-00x` Phase 0, `T-01x` Phase 1, `T-02x` Phase 2, and
so on. Only the coordinator creates new task IDs.

To list open tasks quickly:
```powershell
Select-String -Path tasks\T-*.md -Pattern '^status: (todo|in-progress|review|blocked)'
```
