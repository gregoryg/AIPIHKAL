---
name: emacs-lisp-dev
description: Write, review, and test Emacs Lisp code following idiomatic conventions and hard-won local best practices. Use when writing, editing, debugging, or reviewing .el files, Emacs packages, or gptel tools. Enforces a mandatory verify-before-deliver rule - all written code must be batch byte-compiled and smoke-tested before presenting to the user. Covers load-path management, buffer-local variable safety, HTML/XML parsing, file I/O patterns, and batch testing workflows.
license: Complete terms in LICENSE.txt
---

# Emacs Lisp Development

## Prime Directive: Verify Before You Deliver

**Every piece of Emacs Lisp code you write or edit MUST be tested before presenting it to the user.**

After writing or modifying a `.el` file:

1. **Syntax check** (byte-compile as linter — do NOT leave `.elc` artifacts behind):
   ```bash
   emacs --batch -L <deps> -L . --eval '(byte-compile-file "FILE.el")'
   rm -f FILE.elc   # clean up — stale .elc is a trap without (setq load-prefer-newer t)
   ```
   This catches unbalanced parens, unbound variables, and missing `require`s.
2. **Load check**: `emacs --batch -L <deps> -L . --eval '(require (quote FEATURE))'`
3. **Smoke test** (when practical): `emacs --batch -L <deps> --eval '(progn (require ...) (message "result: %s" (my-function "arg")))'`

If any step fails, **fix the code and re-test before responding**. You have shell access—use it.

### Load-Path Reality

Bare `emacs --batch` does NOT load the user's `.emacs.d` config or package paths. You must explicitly pass `-L` flags for every dependency directory. Ask the user for needed load-path extensions early in the session if they are not obvious from context.

Common pattern:
```bash
emacs --batch \
  -L ~/projects/emacs/ai/gptel/ \
  -L ~/emacs-gregoryg/ \
  -f batch-byte-compile target.el
```

**Tip**: Use `emacs --batch --eval '(message "%s" load-path)'` to inspect defaults, then add missing paths.

## Critical Safety Patterns

### Buffer-Local Variable Capture

Buffer-local variables are **lost** when entering `with-current-buffer` or `with-temp-buffer`. Capture them BEFORE switching:

```emacs-lisp
;; WRONG - my-local-var is nil in temp buffer
(with-temp-buffer
  (insert (format "%s" my-local-var)))

;; RIGHT - capture first
(let ((val my-local-var))
  (with-temp-buffer
    (insert (format "%s" val))))
```

### HTML/XML Parsing

**Never use regex for HTML/XML.** It is too fragile for namespaces (`<html:title>`), attributes, and nesting. Use:
- `libxml-parse-html-region` + `dom.el` for HTML
- `libxml-parse-xml-region` for XML

```emacs-lisp
(let* ((dom (with-temp-buffer
              (insert html-string)
              (libxml-parse-html-region (point-min) (point-max))))
       (title (dom-text (dom-by-tag dom 'title))))
  title)
```

### File I/O & Open Buffers

When writing auxiliary/sidecar files, **always check `find-buffer-visiting` first**. If the user has the file open with unsaved changes, modifying the buffer (and saving) is safer than blindly overwriting the file on disk:

```emacs-lisp
(let ((buf (find-buffer-visiting filepath)))
  (if buf
      (with-current-buffer buf
        (erase-buffer)
        (insert new-content)
        (save-buffer))
    (with-temp-file filepath
      (insert new-content))))
```

## Style & Conventions

- **Prefix all public symbols** with the package name: `mypackage-do-thing`, `mypackage--internal-helper` (double-dash for private).
- **Docstrings**: First line is a complete sentence. Mention argument names in CAPS.
- **`defcustom`** for user-facing options; `defvar` for internal state.
- **Prefer `when`/`unless`** over single-branch `if`.
- **Prefer `pcase`** for destructuring and multi-branch matching.
- **Autoloads**: Add `;;;###autoload` cookies to entry-point commands and major modes.

## Testing Approach

- Prefer batch-mode probes over interactive runs.
- Capture `message` output via `*Messages*` buffer reads when needed.
- Keep tests minimal and terminal-friendly; TTY behavior matters (e.g., `cursor-sensor` echoes).
- For gptel tools specifically: byte-compile the file, then `require` it in batch to confirm clean loading.
- Use `ert` for structured test suites when the project warrants it.

## Discovery & Exploration

- Avoid broad filesystem pokes inside Emacs batch; rely on shell tools (`rg`, `grep`, `find`, `sed`) for discovery and then use targeted Elisp for processing.
- Set `load-prefer-newer t` or delete stale `.elc` files to ensure fresh code is loaded during development.
