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
### Properties Property Syntax
===================

Properties are key-value pairs.  When they are associated with a single
entry or with a tree they need to be inserted into a special drawer (see
*note Drawers::) with the name ‘PROPERTIES’, which has to be located
right below a headline, and its planning line (see *note Deadlines and
Scheduling::) when applicable.  Each property is specified on a single
line, with the key--surrounded by colons--first, and the value after it.
Keys are case-insensitive.  Here is an example:

     * CD collection
     ** Classic
     *** Goldberg Variations
         :PROPERTIES:
         :Title:     Goldberg Variations
         :Composer:  J.S. Bach
         :Artist:    Glenn Gould
         :Publisher: Deutsche Grammophon
         :NDisks:    1
         :END:

   Depending on the value of ‘org-use-property-inheritance’, a property
set this way is associated either with a single entry, or with the
subtree defined by the entry, see *note Property Inheritance::.

   You may define the allowed values for a particular property ‘Xyz’ by
setting a property ‘Xyz_ALL’.  This special property is _inherited_, so
if you set it in a level 1 entry, it applies to the entire tree.  When
allowed values are defined, setting the corresponding property becomes
easier and is less prone to typing errors.  For the example with the CD
collection, we can pre-define publishers and the number of disks in a
box like this:

     * CD collection
       :PROPERTIES:
       :NDisks_ALL:  1 2 3 4
       :Publisher_ALL: "Deutsche Grammophon" Philips EMI
       :END:

   Properties can be inserted at the buffer level.  That means they
apply before the first headline and can be inherited by all entries in a
file.  Property blocks defined before the first headline must be at the
top of the buffer with only comments above them.

   Properties can also be defined using lines like:

     #+PROPERTY: NDisks_ALL 1 2 3 4

   If you want to add to the value of an existing property, append a ‘+’
to the property name.  The following results in the property ‘var’
having the value ‘foo=1 bar=2’.

     #+PROPERTY: var  foo=1
     #+PROPERTY: var+ bar=2

   It is also possible to add to the values of inherited properties.
The following results in the ‘Genres’ property having the value ‘Classic
Baroque’ under the ‘Goldberg Variations’ subtree.

     * CD collection
     ** Classic
         :PROPERTIES:
         :Genres: Classic
         :END:
     *** Goldberg Variations
         :PROPERTIES:
         :Title:     Goldberg Variations
         :Composer:  J.S. Bach
         :Artist:    Glenn Gould
         :Publisher: Deutsche Grammophon
         :NDisks:    1
         :Genres+:   Baroque
         :END:

   Note that a property can only have one entry per drawer.

   Property values set with the global variable ‘org-global-properties’
can be inherited by all entries in all Org files.

   The following commands help to work with properties:

‘M-<TAB>’ (‘pcomplete’)
     After an initial colon in a line, complete property keys.  All keys
     used in the current file are offered as possible completions.

‘C-c C-x p’ (‘org-set-property’)
     Set a property.  This prompts for a property name and a value.  If
     necessary, the property drawer is created as well.

‘C-u M-x org-insert-drawer’
     Insert a property drawer into the current entry.  The drawer is
     inserted early in the entry, but after the lines with planning
     information like deadlines.  If before first headline the drawer is
     inserted at the top of the drawer after any potential comments.

‘C-c C-c’ (‘org-property-action’)
     With point in a property drawer, this executes property commands.

‘C-c C-c s’ (‘org-set-property’)
     Set a property in the current entry.  Both the property and the
     value can be inserted using completion.

‘S-<RIGHT>’ (‘org-property-next-allowed-value’)
‘S-<LEFT>’ (‘org-property-previous-allowed-value’)
     Switch property at point to the next/previous allowed value.

‘C-c C-c d’ (‘org-delete-property’)
     Remove a property from the current entry.

‘C-c C-c D’ (‘org-delete-property-globally’)
     Globally remove a property, from all entries in the current file.

‘C-c C-c c’ (‘org-compute-property-at-point’)
     Compute the property at point, using the operator and scope from
     the nearest column format definition.


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
