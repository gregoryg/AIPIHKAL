---
name: org-mode-syntax
description: Write correct, idiomatic Org mode (vanilla) including denote-style optional frontmatter, agenda-aware tasks (TODO/STARTED/PAUSED/DONE, SCHEDULED/DEADLINE, repeaters, tags), and interactive executable Org Babel blocks (emacs-lisp, python, bash, sql) that produce in-buffer results. Use when asked to draft or transform .org files, planning/task documents, executable notes, or when Org syntax/agenda/Babel interactivity is needed instead of Markdown.
license: Complete terms in LICENSE.txt
---

# Org Mode Syntax (vanilla) + Interactivity (Babel) + Agenda hygiene

Operate as an Org author, not a Markdown author. Prefer Org-native constructs.

## Default behaviors

- When drafting a new standalone note, optionally start with denote-style frontmatter:
  - `#+title: …`
  - `#+date: 2026-02-08` (YYYY-MM-DD)
  - `#+filetags: :tag1:tag2:`
  Only include this if the user is creating a new note/document (ask if unsure).

- When the user asks for plans, tasks, project tracking, or anything time-based:
  - Use Org headlines with TODO keywords and agenda timestamps (`SCHEDULED`, `DEADLINE`).
  - Default TODO workflow (portable subset): `TODO`, `STARTED`, `PAUSED`, `DONE`.
  - Add tags where useful for filtering (e.g. `:work:`, `:home:`, `:deep:`).

- When computation, transformation, querying, or “let’s check” would help:
  - Prefer executable Org Babel blocks that can be run in situ (vanilla: `C-c C-c` in the block).
  - Emit blocks with explicit `:results …` and (often) `:exports both` so the document captures output as shared context.

- When a task subtree/phase is clearly complete and both user + LLM agree:
  - Propose archiving the subtree via `org-archive-subtree` to reduce clutter.
  - Do not assume the archive filename/location.

## Minimal syntax patterns (authoring)

### Headings

```org
* Heading
** Subheading
*** Sub-subheading
```

### Emphasis

```org
*bold* /italic/ _underline_ +strike+ =verbatim=
```

### Links

```org
[[https://www.example.com][This is the link description]]
[[file:references/org-mode-syntax-cheat-sheet-for-llms.org][File link to our Org Mode Cheatsheet]]
```

### Lists + checkboxes

```org
- item
- [ ] todo checkbox
- [X] done checkbox
  - nested item
```

## Agenda-aware tasks (the “why” + the “how”)

Org agenda primarily “sees” tasks via:
- TODO keywords on headlines
- timestamps (especially `SCHEDULED`/`DEADLINE`)
- tags/properties (for filtering)

### Task headline template

```org
** TODO Write proposal draft                :work:writing:
   SCHEDULED: <2026-02-10 Tue>
```

### STARTED / PAUSED states

Use these when the *state* is meaningful to the user, not just the checkbox status.

```org
** STARTED Implement parser                :dev:
SCHEDULED: <2026-02-08 Sun>
```

```org
** PAUSED Wait for API access              :blocked:
```

### DEADLINE vs SCHEDULED

- Use `SCHEDULED` for “work on this on/after this date”.
- Use `DEADLINE` for “must be done by this date”.

```org
** TODO Submit expense report              :admin:
DEADLINE: <2026-02-12 Thu>
```

### Repeaters

```org
** TODO Pay rent                           :home:
DEADLINE: <2026-03-01 Sun +1m>
```

## Interactivity: Org Babel blocks that execute in situ

### Principles for runnable blocks

- Keep blocks small and single-purpose.
- Add header args so results are usable and captured in-buffer.
- Prefer `:results verbatim` when you want readable text/log output.
- Prefer `:results value` when you want a returned value (lists/tables).
- Consider `:exports both` so the note shows code + results.

When helpful, add a short instruction line:
- “Run this block with `C-c C-c`.”

### “Consider adding” per-file defaults (ask the user)

If the user wants many executable blocks in one file, suggest:

```org
#+property: header-args:bash :results verbatim :exports both
#+property: header-args:python :results verbatim :exports both
```

Also consider tangling when the user wants scripts checked into a repo or reused:

```org
#+property: header-args:bash  :shebang #!/usr/bin/env/bash :tangle ./scripts/example.sh
#+property: header-args:python :tangle ./scripts/example.py
```

These header-args properties affect all blocks of that language in the file.

### emacs-lisp example

```org
#+begin_src emacs-lisp :results verbatim :exports both
(format-time-string "%Y-%m-%d")
#+end_src
```

### python example (verbatim results)

```org
#+begin_src python :results verbatim :exports both
import platform
print(platform.platform())
#+end_src
```

### bash example (verbatim results)

```org
#+begin_src bash :results verbatim :exports both
pwd
ls -la
#+end_src
```

### SQL (preferred: org-babel sql blocks)

Assume the user has configured their SQL Babel engine(s). Prefer file-level header args for connection details.

Example (as Org content):

```org
#+property: header-args:sql :engine postgres :dbhost protomolecule.magichome :database bartenders_friend :user lucille :dbport 31432
```

Then write SQL blocks like:

```org
#+begin_src sql :results table :exports both
select now() as current_time;
#+end_src
```

Notes:
- Use `:results table` when you want tabular output.
- If multiple engines are in play, keep connection details in header args or per-block args; ask the user which DB target they intend.

## Tables + spreadsheet formulas

```org
| A | B |
|---+---|
| 1 | 2 |
#+TBLFM: $2=$1*2
```

Recalculate with `C-c C-c` on the `#+TBLFM` line.

## Archiving to reduce clutter (explicit agreement)

When a subtree/phase is DONE and no longer needed in the active tracking context:
- Ask: “Shall we archive this subtree?”
- If yes: instruct the user to run `org-archive-subtree` with point on the subtree headline.

Rationale: keeps active PLANNING/TASK files (and shared LLM context) clean and reduces confusion over stale items.

## Bundled reference

- If you need a compact markup refresher, read `references/org-mode-syntax-cheat-sheet-for-llms.org`.
