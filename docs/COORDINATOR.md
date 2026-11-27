# Coordinator playbook

For whoever coordinates the work (the owner, or an AI session acting for the
owner). It exists so that a **new session can take over without the previous
conversation**. The rules for all contributors are in [AGENTS.md](../AGENTS.md);
this file covers what only the coordinator does.

## First steps in a new session

1. Read [AGENTS.md](../AGENTS.md), [PLAN.md](PLAN.md), and the ADRs in
   [decisions/](decisions/) (the newest ones first).
2. See the state of every task:
   ```powershell
   Select-String -Path tasks\T-*.md -Pattern '^status:' | ForEach-Object { "$($_.Filename.Substring(0,5)) $($_.Line)" }
   ```
3. See what is in flight: `git branch -a`, `git worktree list`, and
   `gh pr list` (see "Tools" below).
4. A task is ready when it is `todo` and its `depends_on` tasks are all `done`
   **and their PRs are merged**.

## Owner preferences (decided in chat; the ADRs hold the reasons)

- **Reply in the language of the owner's latest message** (Romanian or
  English). Technical artifacts are always in English (ADR-0002).
- **The owner approves everything that reaches `main`**, in the chat or with an
  "approved" comment on the PR. The coordinator merges after that
  (ADR-0011). Never merge or push to `main` without approval.
- The product is an **investigation**, not an aggregator (ADR-0008). Design
  inspiration comes from sondajeromania.ro **only** for visual design and UX,
  never its mechanisms; light mode first (ADR-0009).
- Neutral language, always (ADR-0003).
- The owner prefers decisions asked in a short form with a recommended
  default, and a plain explanation of the consequences.

## The loop for one task

1. **Brief an agent** (general-purpose, in the background). The brief says:
   read AGENTS.md, the task file, and the ADRs it names; lock the task by
   creating the worktree and branch; do the work; commit with the task ID and
   the `Co-authored-by` trailer; set `status: review`; **never push or merge**;
   and end with a PR-ready summary (problem, goal, solution, changes,
   verification, open questions, follow-ups).
2. **Review the branch yourself**: read the diff, run `uv sync`,
   `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and
   `uv run sondaje validate` in the task's worktree. When several branches are
   in flight, merge them into a throw-away branch and run the checks there, to
   catch interactions. Delete it afterwards.
3. **Send fixes back** to the same agent (`write_agent`), or fix small things
   yourself.
4. **Finish the branch**: set `status: done` as the last commit, push, and open
   the PR with `gh pr create`, filling in
   [the template](../.github/pull_request_template.md): problem, goal,
   solution, what changed and how, verification, traceability, notes, and
   checklist.
5. **Wait for the owner's approval.** Then, if `main` moved, run
   `gh pr update-branch <n>` and wait for the CI check `Required checks`
   to pass. Then `gh pr merge <n> --merge` ("Create a merge commit").
6. **Clean up**: `git pull --ff-only`, remove the worktree, delete the local
   and remote branch.

Coordinator-only changes (new tasks, plan updates, applying a task's
follow-ups) go on `chore/T-000-<slug>` branches and also through a PR.

## Tools and environment (Windows)

- **uv** manages Python. Set `UV_LINK_MODE=copy` to silence the hardlink
  warning (the uv cache and the repo are on different drives).
- **GitHub CLI**: `C:\Program Files\GitHub CLI\gh.exe`, which may not be on
  `PATH` in an older shell. It is logged in as the owner's account
  (`maxim-dirtu`). Its "hint: gh event listen" output goes to stderr, so
  PowerShell prints it as an error even when the command succeeded.
- **The repo's Git identity** is set in `.git/config` (the owner's noreply
  email). The remote URL includes the username, so the right credentials are
  used.
- **PowerShell 5 corrupts UTF-8.** `Get-Content`/`Set-Content` mangle Romanian
  diacritics and symbols (`§`, `→`) and can add a BOM. Edit files with the
  editor tools. If a script must write a file, use
  `[IO.File]::ReadAllText/WriteAllText` with
  `New-Object Text.UTF8Encoding $false`.
- **Use absolute paths in briefs and in commands run for a worktree.** Two
  agents once edited a file in the main worktree through a relative path
  (they reverted it at once). Tell agents to work only in their worktree.
- Very long chained commands (several `git worktree` and `git merge` steps
  at once) were blocked by a permission prompt. Run them as small steps.
- The temporary PR descriptions are written to a scratch folder and passed with
  `--body-file`. They are not kept in the repo; the PR itself is the record.

## Where things are

| Need | Look at |
|---|---|
| What is built, what is next | [PLAN.md](PLAN.md), then `tasks/` |
| Why something was decided | [decisions/](decisions/) |
| A formula or rule | [METHODOLOGY.md](METHODOLOGY.md) (open questions: OI-1…OI-5) |
| A column, ID, or validation rule | [DATA_MODEL.md](DATA_MODEL.md) |
| The pollster selection and its evidence | [reports/pollster-selection.md](reports/pollster-selection.md) |
| The UX concept | [ux/](ux/) and `ux/mockups/index.html` |
