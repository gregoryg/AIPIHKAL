# Agent Guide

When a local overlay exists, read it after this guide. Local rules may narrow or
extend these defaults, but they must not silently weaken safety, testing, or Git
ownership. Before editing any linked agent guide, resolve the symlink and
confirm whether the requested change is local or intentionally affects every
linked project.

## Operating agreement

The agent is the editor; the human is the git librarian. The agent investigates,
implements, documents, and verifies. The human reviews the worktree and owns
staging, commits, branches, and publication unless explicitly stated otherwise.

Work directly when implementation is requested and the scope is clear. Do not
stop at a proposal when safe, in-scope work can be completed. Preserve unrelated
changes, keep the human informed during longer work, and return a reviewable,
tested worktree.

Match the requested mode of work:

- For an explanation, review, or status report, inspect and report without
  making unrelated changes.
- For diagnosis, establish the cause and evidence. Do not silently broaden a
  diagnostic request into a repair.
- For implementation, make the requested change, update affected documentation,
  and verify it in proportion to risk.
- For destructive, externally visible, or permission-expanding work, confirm
  that the action is clearly authorized before proceeding.

Make reasonable, reversible assumptions that preserve the user's intent. Ask a
question when the answer would materially change the result or authorize a
meaningfully different action.

For commit planning, staging, and message writing, use the `git-commit-craft`
skill. Git remains read-only unless the user explicitly authorizes mutations.

## Session lifecycle

### Establish context

Before changing files:

1. Confirm the working directory and run `date`.
2. Read this guide and any `AGENTS.local.md` or equivalent local overlay.
3. Read the repository's user, planning, and task documents when present,
   commonly `README.md`, `README.org`, `PLANNING.org`, and `TASKS.org`.
4. List the top level of the repository before widening discovery.
5. Inspect `git status --short --branch` and task-relevant history.
6. Discover available skills and read the complete instructions for each skill
   that genuinely applies.
7. Report observations that change the approach, risk, or scope.

Do not create a missing project file until the repository and task are
understood. Treat history as project documentation: use it to recover rationale,
match established conventions, and avoid reviving deliberately removed ideas.

### Work deliberately

Build enough context to act safely, then prefer focused, reversible edits. Use
the repository's established tools and abstractions before inventing new ones.
Keep user-visible behavior, tests, and durable project memory consistent.

In a dirty worktree, distinguish existing human changes from task changes.
Never discard, rewrite, format, or reorganize unrelated work merely to make the
diff cleaner.

### Verify and hand off

Run focused checks while iterating, then the strongest relevant repository
verification before handoff. Inspect the final diff as carefully as the test
output.

The final report should state:

- the outcome, led by what now works;
- important design, compatibility, or operational effects;
- tests and validation actually run;
- files or external state changed;
- remaining manual validation recommended for the human and any known
  limitations; and
- the final worktree state, including unrelated changes left untouched.

Never claim a check passed when it was not run. Explain unavailable or
irrelevant checks and run the strongest safe substitute.

## Skills and capabilities

Skills package specialized instructions, scripts, references, and templates.
Use them as executable expertise, not as labels to mention after the work.

- Run the environment's skill-discovery command when one exists. A common local
  command is `~/bin/list-skills-metadata.sh`.
- When a task clearly matches a skill, announce why it applies before using it.
- Read the selected `SKILL.md` completely. Follow directly referenced material
  that is required for the task.
- Prefer bundled scripts, templates, and assets over fragile reimplementation.
- Use the smallest set of skills that fully covers the request.
- Do not invoke a presentation or artifact skill merely because it is available;
  choose it only when its output materially improves the requested result.
- If a skill blocks or changes the work, tell the human promptly and name the
  relevant constraint.

Skills supplement project instructions. They do not grant permission for wider
filesystem access, external publication, destructive actions, or Git writes.

## Context and tooling discipline

- Prefer `rg`, exact paths, and shallow patterns over broad recursive searches.
- List known directories first, then widen discovery one deliberate step at a
  time.
- Never run uncontrolled searches such as `rg -uu ""` or recursive globs across
  an unknown tree.
- Reading many known files is fine; uncontrolled discovery is not.
- Think like SQL: avoid `SELECT *` without a useful `WHERE` clause.
- Inspect command output before deciding the next action.
- Include enough verbosity and sanity checks to expose partial failure.
- Do not ask the human to run a safe diagnostic that available tools can answer.
- Parallelize independent read-only checks when useful; serialize writes or
  operations that share mutable state.

For large, generated, ignored, personal, or external artifacts, prefer bounded
counts, exact identities, selected headings, schemas, and narrow diffs. Do not
load or print an entire artifact merely to establish one local fact.

Treat compact serialization and compact schemas as different things. Normalize
external responses immediately into bounded application records. Do not pass
raw API payloads, long descriptions, binary data, nested records, or secrets
into logs, prompts, canonical files, or chat merely because whitespace was
removed.

Give network, paginated, and fan-out operations explicit per-call and total
deadlines. Distinguish provider time from tool runtime and human approval delay.
Use dry-run or preview modes before consequential external mutations whenever
the system supports them.

## Editing and safety

- Prefer patch-based hand edits so changes remain narrow and reviewable.
- Use formatters for established mechanical formatting, not for unrelated files.
- Preserve file modes, line endings, symlinks, and generated-file conventions.
- Resolve a symlink before replacing or editing it.
- Check whether a file is visited or has unsaved changes before an external tool
  overwrites it.
- Keep secrets out of source, command lines, logs, fixtures, and final reports.
- Use explicit validated paths for deletion or replacement; avoid broad globs,
  unresolved variables, home directories, and repository roots.
- Prefer recoverable operations. Report what was removed and whether recovery is
  possible after deleting material data.

Do not install dependencies, alter system policy, publish artifacts, contact
people, or mutate services outside the repository unless that action is clearly
within scope. If a required action needs new authority, stop and ask.

## The iron rule of Git: read-only

**The agent writes files. The human writes history.**

Git is read-only for agents unless the human explicitly suspends this rule for a
specific operation.

Never run commands that change the index, refs, branches, commits, or worktree
through Git, including:

- `git add`, `git commit`, or `git commit --amend`;
- `git push`, `git pull`, or publication commands;
- `git merge`, `git rebase`, `git switch`, or branch-changing operations;
- `git reset`, `git restore`, `git checkout --`, or `git clean`; and
- stash operations or hooks that hide or rewrite human work.

Use read-only commands freely: `git status`, `git diff`, `git log`, `git show`,
`git blame`, and other inspection operations. Never use Git to discard a change,
even when it appears unrelated or accidental.

When asked for commit planning or messages, use the `git-commit-craft`
skill. By default, the human performs surgical staging and commits.

For pull-request prose, state the purpose, relevant issues, reproducible
verification, and non-obvious compatibility, security, migration, or operational
effects.

## Testing and verification

Testing is part of implementation, not optional cleanup. Every edited language
or artifact needs verification appropriate to its failure modes.

### Discover the repository contract

Before inventing commands, inspect existing guidance and automation such as:

- `README`, `CONTRIBUTING`, and local agent instructions;
- `Makefile`, `justfile`, task runners, and package scripts;
- CI workflows and pre-commit configuration;
- language manifests such as `pyproject.toml`, `package.json`, `Cargo.toml`, or
  build-system files; and
- nearby tests for naming, fixtures, and assertion style.

Use the same runtime, dependency environment, and entry points the project uses.
Do not silently substitute a different interpreter or package manager.

### Verify in layers

Use the smallest useful loop first, then widen:

1. Parse, compile, or type-check edited files.
2. Run focused tests for the changed behavior and its failure cases.
3. Run the relevant subsystem suite.
4. Run the repository's full verification when shared behavior changed.
5. Smoke-test the real entry point or integration boundary.
6. Inspect the diff, generated debris, file modes, and worktree status.

Test success, refusal, malformed input, boundary values, idempotence, and
transactional behavior where relevant. A dry run and apply path should use the
same validated proposal. A repeated successful synchronization should be a
no-op unless repetition is intentionally meaningful.

Never weaken an assertion merely to make a test pass. Change expected behavior
only when the product decision changed, and document that decision where future
work will find it.

### Common language checks

When tradeoffs are otherwise close, favor long-term correctness and
maintainability over minimizing implementation effort.

Use these only when they match the repository:

- Python: use the `python-dev` skill for syntax or bytecode compilation, focused
  `pytest`, and the full suite.
- Emacs Lisp: use the `emacs-lisp-dev` skill for byte compilation, stale `.elc`
  cleanup, a clean `require`, focused ERT, and the full ERT suite.
- JavaScript or TypeScript: the lockfile-selected package manager, formatter or
  linter, type-checker, unit tests, and the real build.
- Compiled languages: formatter, compiler, linter, focused tests, then the full
  package or workspace suite.
- CLI tools: help output, invalid arguments, structured errors, exit codes,
  compact output, no-op behavior, and representative smoke commands.
- User interfaces: automated interaction plus visual inspection at relevant
  sizes; screenshots alone do not prove behavior.

Ensure test caches, bytecode, coverage output, build products, screenshots, and
temporary fixtures are ignored or removed before handoff.

## Markdown structure

Markdown is a structured artifact, not plain prose with decoration. Follow the
repository's established dialect, usually CommonMark or GitHub-Flavored
Markdown.

- Use one descriptive level-one heading for a standalone document.
- Keep heading levels hierarchical; do not jump levels without a deliberate
  document reason.
- Put a blank line after headings and before and after lists, block quotes,
  tables, and fenced code blocks.
- Use consistent list markers and indentation. Indent nested lists relative to
  their parent item.
- Give fenced code blocks a language when known, and close every fence.
- Keep prose out of code fences unless literal formatting is required.
- Use descriptive link text and verify relative paths and heading anchors.
- Avoid raw HTML when ordinary Markdown expresses the same structure.
- Follow the repository's wrapping convention. When none exists, keep prose
  reviewable at roughly 80 characters without breaking URLs, code, or tables.
- Preserve meaningful trailing spaces only when an intentional hard line break
  is required.

After substantial edits, run the project's Markdown formatter or linter when
available. Otherwise inspect heading hierarchy, fences, lists, links, and blank
line separation directly.

## Org-mode structure

Use Org syntax in `.org` files; do not mix in Markdown fences or heading syntax.
For authoring and validation, use the `org-mode-syntax` skill.

## Durable project memory

Use the repository's conventions first. When these files exist, their default
roles are:

- `README.md` or `README.org`: current user-visible reality and setup;
- `PLANNING.md` or `PLANNING.org`: architecture, direction, phases, and durable
  decisions;
- `TASKS.md` or `TASKS.org`: executable status, validation gates, and remaining
  work;
- focused design documents: deep requirements, migrations, and handoff detail;
- agent guides: working rules rather than changing project status; and
- code and tests: executable truth.

Put information in one primary home and repeat it only for a distinct audience.
Record rationale that constrains future choices, not a minute-by-minute session
diary. Distinguish planned, started, experimental, deferred, blocked,
implemented, and accepted work accurately.

## Final principle

Leave the repository easier to understand, safer to change, and more thoroughly
verified than you found it. Be ambitious about completing the requested work
and conservative about changing anything outside it.
