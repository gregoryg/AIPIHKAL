# LLM Council - Agents Guide

Note to self: always run `date` at the start of a session.  It probably ain't 2024, Dorothy - output date and working directory so that it's in context

Start out by any new session by reading Agents.md, LLM-system-prompt.org, and the org mode Holy Trinity: README.org, PLANNING.org and TASKS.org

If they do not exist, consider creating them once we know what we're dealing with.

Output keen observations about what you gleaned from reading so that the wisdom stays in context

Keep in mind that some suggested files may be in `.gitignore` - in which case you can use cat or sed to read them.

**Benefits:**
- Understand *why* code exists (archaeology)
- Avoid re-implementing recently removed features
- Match established commit message conventions
- Honor the human's careful git discipline

The human has crafted this history as documentation for their Dream Team (Past/Present/Future Self). Read it. Learn from it. Don't be a tourist.

## Skills & Capabilities
Check for the existence of `skills/` in the current directory or `~/.skills/`. These directories contain Markdown definitions (`SKILL.md`) and scripts for advanced capabilities (e.g., "Rubber Duck Council", "Home Assistant CLI").
- If found, read `SKILL.md` to understand available tools and protocols.
- These skills often wrap complex CLI tools or orchestration logic.

## Context discipline (read this before using tools)
- Avoid recursive, broad-glob searches like `**/*`. This is the shell equivalent of `SELECT *` with no WHERE clause and can flood the context window, crash LLM sessions, or cause API 400s.
- Prefer targeted patterns and shallow globs:
  - Good: `src/test/recipes-page-categories.test.tsx`, `src/features/recipes/RecipesPage.tsx`
  - Good: `src/*/TopNav.tsx`, `src/*/landing/*.tsx`
  - Risky: `src/**/*.tsx` (only if you will immediately filter client-side—generally avoid)
  - Reading multiple specific files at once is fine. The problem is unbounded discovery, not targeted reading.
- Strategy:
  1) List top-level dirs with `ls` or the list_directory tool.
  2) Search with the most specific pattern possible.
  3) Read exact files; only widen the pattern if necessary, stepwise.
- When constructing shell commands or tool calls, include verbosity and sanity checks to surface output and avoid ambiguity.

## Commit Message Generation (when user asks for commit breakdown)
When the user requests commit message suggestions, provide **granular, purpose-driven commits** following Conventional Commit format with surgical file groupings:

**Prompt pattern:** "I need commit message suggestions for [feature/area]"

**Response format:**
```
## Commit N: [Purpose]
```
type(scope): concise description

A readable paragraph (or two) explaining the purpose, intent, and high-level "why" of this change. This serves as the TL;DR for the context.

- Optional bullet point for specific implementation detail
- Optional bullet point for architectural decision or side effects

Files: file1.ts, file2.tsx*, file3.ts
       (* = appears in multiple commits, hunk staging recommended)
```

**Categories by priority:**
1. `feat(scope)` - New functionality, components, APIs
2. `fix(scope)` - Bug fixes, corrections
3. `refactor(scope)` - Code reorganization without feature change
4. `test(scope)` - Test additions, test improvements
5. `dev(planning)` - TASK.org, PLANNING.org updates
6. `docs(scope)` - README.org, documentation
7. `style(scope)` - Formatting, CSS, visual changes
8. `build(deps)` - Package updates, build config

**Granularity principles:**
- Each commit tells one coherent story
- Group files by logical purpose, not alphabetically
- Separate API/logic/UI/tests into different commits
- Enable surgical rollbacks and `git blame` clarity
- **Style:** Paragraph(s) for intent/context first, then optional bullets for details
- **Mark files with asterisk (*) when they appear in multiple commits**
- Asterisk alerts human to activate magit hunk-staging for surgical commits

**Example file groupings:**
- API client methods together: `src/lib/api/*.ts`
- UI components by feature: `src/features/admin/*.tsx`
- Tests with their subjects: `src/test/similarity.test.ts`
- Config/routing changes: `src/App.tsx, vite.config.ts`

**Magit hunk-staging markers:**
When a file appears in multiple commits, mark it with `*` in each occurrence:
```
## Commit 1: Foundation
Files: src/lib/session.tsx*, src/lib/types.ts

## Commit 2: Actions
Files: src/lib/session.tsx*, src/lib/api/auth.ts
```
This signals the human that `session.tsx` needs hunk-level staging because it contains changes for multiple semantic commits.

**Hunk-staging guide (for shared files):**
When files are marked with `*`, add a **Note:** section at the end explaining the logical boundaries within each shared file. This helps the human know which hunks belong to which commit:
```
**Note:** `session.tsx*` appears in commits 1-2. Logical boundaries:
- Commit 1: The `SessionProvider` component and `useSession` hook
- Commit 2: The `logout()` and `refreshToken()` functions
```
This eliminates guesswork during hunk-staging and speeds up the surgical commit process.

This approach supports magit hunk-staging workflow and produces meaningful git history for debugging and code archaeology.

## Tooling hygiene (must-follow)
- Never run a broad recursive search like `**/*` or `rg -uu ""`.
- Think like SQL: avoid `SELECT *` without a WHERE.
- Prefer exact filenames or shallow globs and iterate.
- Reading many specific files is OK; flooding discovery is not.
- When in doubt, ask the human to run a targeted command and paste results.

## Coding Style & Naming Conventions
- Python 3.12, 4-space indentation, PEP 8, type hints.
- Module/file names: lowercase_with_underscores; tests as `test_*.py`.
- Keep functions cohesive and documented; include short Google-style docstrings.
- Formatting: use `black` locally if available (not enforced in CI).

## Emacs programming (local best practices)
- Ask for load-path extensions early (e.g., `~/.emacs.d/straight/repos/esxml/` for nov.el deps).
- Run `emacs -Q --batch -L <deps> -L . --eval '(require ...)'` for linty smoke tests; set `load-prefer-newer t` or delete stale `.elc` to load fresh code.
- Prefer batch probes over interactive runs; capture messages with `message-log-max` and `*Messages*` reads.
- Keep tests minimal and terminal-friendly; TTY behavior matters (e.g., cursor-sensor echoes).
- Avoid broad filesystem pokes inside Emacs; rely on shell tools (`rg`, `sed`) for discovery.
- **HTML/XML Parsing:** Avoid regex for HTML tags. Use `libxml-parse-html-region` and `dom.el`. Regex is too fragile for namespaces (`<html:title>`) and attributes.
- **Context Safety:** Capture buffer-local variables  *before* entering `with-current-buffer` or `with-temp-buffer`. They are lost in the new context.
- **File I/O & Buffers:** When writing auxiliary/sidecar files, always check `find-buffer-visiting`. If the user has the file open with unsaved changes, modifying the buffer (and saving it) is safer than blindly overwriting the file.

## Commit & Pull Request Guidelines
- Commits: imperative mood, concise summary (<72 chars), body for rationale. Example: `Add pattern matching and tests`.
- PRs: clear description, linked issues, reproducible steps; include curl screenshots/snippets for API changes; call out env vars or migrations.


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

# How we work as a team 'round these parts

Human gives free reign to the LLM to make any and all code edits, keep docs up to date etc.  No need to present proposed code changes in the chat context, or diffs or patches.  Just do it ... as they say.  We are kept safe by human's diligent git hygeine.  After implementing a feature or two, human will test and confirm.  **Human does all git commits.**

ONE VERY IMPORTANT NOTE:
Please treat planning and architecture as high priority, so that human is not tempted to switch back to a certain rather arrogant LLM that thinks it's so very superior in coding tasks!
