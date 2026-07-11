# LLM Council - Agents Guide

## Session startup

At the start of each session:

1. Confirm the working directory, then run `date`. It probably ain't 2024, Dorothy.
2. Read `Agents.md` and the Org-mode project files `README.org`,
   `PLANNING.org`, and `TASKS.org` when they exist.
3. Inspect relevant Git history and worktree state before changing files.
4. Report keen observations that affect the work.

Do not create missing project files until the repository and task are understood.
Some useful local files may be ignored by Git; read them with targeted commands
when they are relevant.

The repository history is documentation for past, present, and future work. Use it
to understand why code exists, avoid restoring removed ideas, match established
conventions, and preserve the human's Git discipline.

## Skills and capabilities

Check `skills/` in the repository and `~/.skills/` when available. Read skill
metadata first, then load the complete `SKILL.md` only when the skill is relevant.
Skills may bundle scripts and references that replace fragile ad hoc workflows.

## Context and tooling discipline

- Prefer `rg`, exact paths, and shallow patterns over broad recursive searches.
- Never run unbounded searches such as `**/*` or `rg -uu ""`.
- List top-level directories first, then widen discovery one step at a time.
- Reading many known files is fine; uncontrolled discovery is not.
- Include enough command verbosity and sanity checks to make failures visible.
- Inspect tool output before deciding the next action.
- Do not ask the human to run a command when available tools can answer safely.

Think like SQL: avoid `SELECT *` without a useful `WHERE` clause.

## Working approach

- Treat planning and architecture as first-class work.
- Build context before editing, but do not stop at a proposal when implementation
  is requested and feasible.
- Edit files freely, keep documentation current, and verify behavior with focused
  tests.
- Preserve unrelated user changes in a dirty worktree.
- Prefer deterministic scripts and compact structured output where repeated model
  reasoning would be slow or error-prone.

## Commit message guidance

Use Conventional Commit form:

```text
type(scope): concise imperative summary

Explain what the commit changes and why the change belongs together. Prefer one
or two short prose paragraphs. Mention important tradeoffs or compatibility
effects when they are not obvious from the diff.
```

Formatting rules:

- Keep the subject under 72 characters.
- Separate the subject and body with a blank line.
- Wrap body text at approximately 80 characters.
- Prefer factual repository-state language over session narrative.
- Describe what the commit introduces, not the chronology of discovering it.
- Use bullets only when several distinct details are clearer as a list.
- Keep the tone practical and history-friendly; avoid jokes or editorial flourish
  unless the human requests them.

Choose the type that best describes the change: `feat`, `fix`, `refactor`, `test`,
`docs`, `style`, or `build`. Use `dev(planning)` for planning-only changes when
that convention fits the repository.

### Commit breakdowns

When asked to propose multiple commits:

- Give each commit one coherent purpose and a surgical file grouping.
- Group files by behavior, not alphabetically.
- Separate tests when the human requests a distinct test commit; otherwise keep
  tests with the behavior they verify when that makes the history clearer.
- Prefer independent commits that can be reviewed and reverted safely.
- Mark a file with `*` when its hunks belong to multiple proposed commits.
- For shared files, briefly identify which hunks belong to each commit.

Suggested presentation:

```text
## Commit N: Purpose

type(scope): concise imperative summary

Prose explaining what changes and why.

Files: path/one, path/two*
```

## Coding style and naming

- Use Python 3.12, four-space indentation, PEP 8, and type hints.
- Use `lowercase_with_underscores` for Python modules and `test_*.py` for tests.
- Keep functions cohesive and add short Google-style docstrings where useful.
- Use `black` locally when available; it is not currently enforced by CI.

## Emacs programming

- Ask for required load-path extensions early, such as external package checkout
  paths needed by batch tests.
- Use `emacs -Q --batch -L <deps> -L . --eval '(require ...)'` for smoke tests.
- Set `load-prefer-newer` or remove stale `.elc` files when necessary.
- Prefer batch probes over interactive testing and capture relevant messages.
- Keep tests terminal-friendly; TTY behavior can matter.
- Use `libxml-parse-html-region` and `dom.el` for HTML/XML, not regular
  expressions.
- Capture buffer-local values before entering `with-current-buffer` or
  `with-temp-buffer`.
- Before writing a sidecar file, check `find-buffer-visiting`; preserve unsaved
  buffer changes instead of overwriting them on disk.

## Pull requests

Write a clear description, link relevant issues, and include reproducible
verification steps. Call out environment variables, migrations, compatibility
effects, or operational follow-up. Include request/response examples for API
changes when they materially help review.

# THE IRON RULE OF GIT: READ-ONLY

**You write code. The Human writes history.**

1. **NO WRITE ACCESS TO GIT**: You must **NEVER** run `git commit`, `git push`, `git merge`, or `git rebase`.
2. **READ ACCESS ONLY**: You are encouraged to run `git status`, `git diff`, and `git log` to understand the state of the repo.
3. **THE REASON**: The Human uses **Magit** to perform surgical, hunk-level staging and committing. Automated `git commit` commands destroy this workflow and clump distinct logical changes into messy blobs.
4. **YOUR JOB**:
   - Edit files freely and aggressively to complete tasks.
   - Run tests to verify.
   - Stop.
   - Inform the user you are done.
   - (Optional) Propose a commit message in the chat if asked.

**Mnemonic**: "I am the Editor. You are the Librarian."

## Team agreement

The human gives the agent broad freedom to edit code and documentation without
presenting patches in chat first. The human reviews the worktree, tests as needed,
and owns all staging and commits through Magit.
