---
name: org-mode-syntax
description: Write, transform, and validate correct, idiomatic Org mode while preserving repository TODO workflows and existing document structure. Use for .org files, planning and task documents, Agenda-aware content, literal Org examples, or executable Babel blocks instead of Markdown.
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
  - Inspect project guidance, file-local `#+TODO` keywords, and existing headlines
    before choosing states. Preserve the repository's workflow and state order.
  - Only when no workflow exists, use the portable subset `TODO`, `STARTED`,
    `PAUSED`, and `DONE`, adapting it when the user supplies a preference.
  - Add tags where useful for filtering (e.g. `:work:`, `:home:`, `:deep:`),
    without changing established file-tag or inheritance semantics.

- When computation, transformation, querying, or “let’s check” would help:
  - Prefer executable Org Babel blocks that can be run in situ (vanilla: `C-c C-c` in the block).
  - Emit blocks with explicit `:results …` and (often) `:exports both` so the document captures output as shared context.

- When a task subtree/phase is clearly complete and both user + LLM agree:
  - Propose archiving the subtree via `org-archive-subtree` to reduce clutter.
  - Do not assume the archive filename/location.

## Preserve structure when editing

Treat existing Org structure as data. Unless the task explicitly changes it:

- preserve headline depth and subtree boundaries;
- keep planning lines immediately below their headline and the property drawer
  immediately after any planning line;
- preserve drawers, clocks, links, affiliated keywords such as `#+name`,
  `#+caption`, and `#+results`, and all unmanaged user text;
- preserve TODO keyword, tag, and property identity and inheritance; and
- avoid moving content across subtree boundaries when that changes inherited
  tags, properties, or Agenda behavior.

When generating or transforming a managed subtree, record enough before-and-after
structure to detect accidental loss. Useful invariants include heading, TODO,
tag, property, link, drawer, clock, and block identities or counts.

## Minimal syntax patterns (authoring)

### Properties

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

### Literal Org examples

Use `#+begin_example` and `#+end_example` for literal material that must not
execute. Use a source block only when language semantics or execution matter.

When an Org document embeds Org syntax, prefix potentially structural lines with
a comma so they cannot become real headings, keywords, or block delimiters in the
surrounding document. This is especially important for headings and nested blocks:

```org
#+begin_example
,* Literal heading
,#+begin_src emacs-lisp
(message "This is shown, not executed")
,#+end_src
#+end_example
```

Use the same escape for a literal line that would otherwise close its surrounding
block. Reparse and lint after editing nested examples; visual inspection alone is
not sufficient.

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

## Verify Org artifacts before delivery

For generated or substantially edited `.org` files, validate in layers:

1. Parse the file with vanilla Org:

   ```bash
   emacs -Q --batch --eval \
     '(progn (require '\''org)
             (with-temp-buffer
               (insert-file-contents "FILE.org")
               (org-mode)
               (org-element-parse-buffer)))'
   ```

2. Run `org-lint`. In batch mode, `org-lint` returns its reports, so make any
   report fail validation:

   ```bash
   emacs -Q --batch --eval '
   (progn
     (require (quote org))
     (require (quote org-lint))
     (with-temp-buffer
       (insert-file-contents "FILE.org")
       (org-mode)
       (let ((reports (org-lint)))
         (dolist (report reports)
           (let ((fields (cadr report)))
             (princ (format "line %s [%s] %s\n"
                            (aref fields 0)
                            (aref fields 1)
                            (aref fields 2)))))
         (when reports (kill-emacs 1)))))'
   ```

3. Assert task-specific semantics such as headline hierarchy, TODO keywords and
   sequences, tags, property identity uniqueness, links, block boundaries, and
   preservation of drawers, clocks, affiliated keywords, and unmanaged text.
4. If a tool updates the file, run it twice and require the second run to be a
   no-op unless repeated changes are intentional.
5. Test Agenda commands in the user's normal Emacs when custom TODO keywords,
   inheritance, `org-agenda-files`, or display settings affect the result.

Successful parsing proves structural readability, not lint cleanliness or correct
Agenda behavior. `org-lint` catches suspicious constructs, including malformed or
incomplete blocks, which an element parse may tolerate.
When exact Org behavior is uncertain, prefer the installed Info manual over
memory; on this system it may be available at
`/usr/local/share/info/org.info.gz`.

## Archiving to reduce clutter (explicit agreement)

When a subtree/phase is DONE and no longer needed in the active tracking context:
- Ask: “Shall we archive this subtree?”
- If yes: instruct the user to run `org-archive-subtree` with point on the subtree headline.

Rationale: keeps active PLANNING/TASK files (and shared LLM context) clean and reduces confusion over stale items.

## Bundled reference

- If you need a compact markup refresher, read `references/org-mode-syntax-cheat-sheet-for-llms.org`.
