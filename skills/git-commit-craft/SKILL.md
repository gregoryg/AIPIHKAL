---
name: git-commit-craft
description: Plan, draft, review, and refine durable Git commit series and messages. Use when asked for commit messages, commit granularity, hunk-staging guidance, or a history-quality review. Inspect the actual diff and repository history before writing; proposing messages never grants permission to stage, commit, amend, or push.
---

# Git Commit Craft

Write commits as durable explanations and reviewable, reversible units. A future
reader should be able to recover the change's purpose, constraints, and behavior
without reconstructing the original development session.

## Preserve the authorization boundary

Treat Git as read-only unless the user explicitly authorizes a mutation. A request
for messages or a staging plan is not authorization to run `git add`, `git commit`,
`git reset`, `git rebase`, or `git push`.

When the user authorizes commits:

- state exactly what will be staged;
- inspect the index before every commit;
- preserve unrelated and pre-existing changes;
- never amend or push unless separately authorized; and
- report the resulting commit IDs and remaining worktree state.

## Inspect evidence before proposing history

Read the repository's instructions first. Then inspect, as applicable:

```sh
git status --short --branch
git diff --stat
git diff --numstat
git diff
git diff --cached
git log -12 --format='%h%x09%s%n%b'
```

Use recent, well-explained commits to discover local conventions: subject syntax,
scope names, capitalization, body length, ChangeLog-style anchors, issue references,
and whether tests or documentation normally travel with implementation.

Distinguish the user's existing changes from work produced in the current task.
Never infer authorship merely because a file is modified.

## Design the commit series

Map the diff into semantic changes before grouping files. Typical roles include
implementation, tests, user documentation, contributor or planning documentation,
build support, data migrations, and mechanical cleanup.

Prefer one commit when the changes together establish one invariant and separating
them would make the history misleading or unusable. Prefer separate commits when
the parts have distinct purposes, audiences, review paths, or revert boundaries.

Use these tests for each proposed commit:

1. Its purpose fits in one specific sentence.
2. Its message is true at that point in the series.
3. Its diff is coherent without relying on unstated future work.
4. It can be reviewed and reverted as a meaningful unit.
5. It leaves the repository buildable and testable when reasonably possible.

Do not split merely to achieve a small diff. Do not combine merely because files
were edited together. Source and tests often belong together, but a repository or
user may deliberately keep implementation, tests, user docs, and planning records
separate. Respect that convention when each commit remains coherent. The org-fc
history demonstrates this approach particularly well.

Order prerequisites before consumers. Keep pure renames or formatting separate
when that materially improves blame and review. Avoid speculative refactors hidden
inside feature or fix commits.

## Plan hunk staging explicitly

When one file serves multiple commits, mark it as shared and describe each hunk by
behavior, symbol, heading, or line purpose. A usable staging plan identifies both
paths and semantic boundaries; a path-only list is insufficient.

For a human using Magit or `git add -p`:

- review every hunk rather than staging a broad directory;
- split a mixed hunk, then edit the patch if necessary;
- use intent-to-add for an untracked file that needs partial staging;
- inspect both staged and unstaged remainders after every selection; and
- abort and regroup if the staged diff cannot support its proposed message.

For an LLM authorized to stage or commit:

- never use `git add .` in a dirty worktree;
- prefer explicit paths for files wholly owned by one commit;
- use patch staging for shared files, preserving the worktree's final content;
- do not rewrite a user's file merely to make staging easier; and
- stop for direction if ownership or hunk boundaries remain ambiguous.

Before each commit, inspect the full staged diff and run appropriate checks such as:

```sh
git diff --cached --stat
git diff --cached --check
git diff --cached
git diff --stat
```

The last command helps confirm that the intended later commits remain unstaged.

## Write the message

Follow the repository's established format. Do not impose Conventional Commits on
a project whose history uses another style.

Treat the subject as three possible dimensions:

```text
change kind + semantic locator + imperative outcome
```

Conventional Commits supplies the change kind. Karthik's gptel style demonstrates
a strong semantic locator: the component that owns the change, often the principal
file stem. These ideas combine naturally when a repository permits it:

```text
type(component): imperative outcome
component: Imperative outcome
```

Choose a component scope that helps a future reader locate the behavior:

- prefer a stable subsystem or module when it clearly owns the invariant;
- use the principal file stem when that is the repository's component vocabulary;
- retain a broader capability name when several modules share ownership; and
- omit the scope rather than inventing a vague or misleading one.

A scope is a semantic locator, not a manifest of every touched file. A commit can
update implementation, tests, documentation, and compatibility code while still
belonging primarily to one component. Name that owner in the subject and identify
important secondary files or symbols in the body when useful. Do not concatenate
multiple file names merely to account for the whole diff.

Keep the subject specific, imperative, and normally under 72 characters. Prefer
the observable outcome over an implementation detail. Match local capitalization.

After a blank line, explain the facts a future maintainer cannot obtain cheaply
from the diff:

- the problem, invariant, or user-visible behavior;
- why this approach is appropriate;
- important boundaries, compatibility concerns, or failure modes; and
- known limitations or design debt when they affect future work.

Describe repository state, not session chronology. Avoid “this commit,” diary-like
accounts, praise, jokes, and vague subjects such as “updates” or “cleanup.” Mention
an issue, regression commit, file, or symbol only when it sharpens understanding.
Use ChangeLog-style file and symbol anchors when the repository values them; they
are especially effective in Emacs projects but are not universal.

Match the body to the change. A self-evident one-line fix may need no body or one
short explanation. A subtle state transition may need several paragraphs, an
ordered model, and an honest limitation.

Wrap body text at the repository's width; use 78 columns by default. Apply `fold`
to body text, not the subject:

```sh
fold -s -w 78 draft-body.txt
awk 'length($0) > 78 { print NR ":" length($0) ":" $0 }' message.txt
```

Re-read the wrapped result. `fold` enforces width but cannot preserve a sentence's
clarity or repair awkward Markdown and ChangeLog indentation.

## Present a proposal

Give the user an ordered commit series. For each commit, provide:

1. the complete subject and body in a code block;
2. the files to stage;
3. the semantic hunk boundaries for shared files; and
4. any dependency on an earlier commit.

Call out assumptions and uncertain boundaries. If several groupings are genuinely
good, recommend one and explain the tradeoff succinctly.

Read [references/examples.md](references/examples.md) when examples would help,
when choosing between repository styles, or when designing a multi-commit split.
It contains annotated real messages from gptel and org-fc.

## Final review

Before handing off messages or making authorized commits, verify:

- the series covers every intended hunk exactly once;
- subjects distinguish the commits at a glance;
- bodies explain why and behavior rather than restating the diff;
- line wrapping, spelling, identifiers, and commit references are correct;
- no message claims tests, docs, compatibility, or behavior absent from its diff;
- each staged diff matches its message; and
- unrelated work remains untouched.

## Format of the presentation
Present the text of both the commit header and its body as left-flush text.
The user will copy and paste the text, so keeping it flush against the left
margin means no extra steps deleting whitespace.
