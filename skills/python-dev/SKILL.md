---
name: python-dev
description: Write, review, and test Python code following PEP 8, type hints, and modern best practices (Python 3.12+). Use when writing, editing, debugging, or reviewing Python files. Enforces a mandatory verify-before-deliver rule - all written code must be tested for syntax and functionality using available shell tools before presenting to the user. Covers naming conventions, project layout, docstrings, formatting, and test authoring.
license: Complete terms in LICENSE.txt
---

# Python Development

## Prime Directive: Verify Before You Deliver

**Every piece of Python code you write or edit MUST be tested before presenting it to the user.**

After writing or modifying a `.py` file:

1. **Syntax check**: `python3 -c "import ast; ast.parse(open('FILE').read())"` or `python3 -m py_compile FILE`
2. **Smoke run**: Execute the file or its entry point: `python3 FILE`
3. **Run tests**: If tests exist, run them: `python3 -m pytest TEST_FILE -v`

If any step fails, **fix the code and re-test before responding**. Do not present broken code and ask the user to debug it. You have shell access—use it.

## Style & Conventions

- **Python version**: 3.12+ unless the project specifies otherwise.
- **Indentation**: 4 spaces (PEP 8).
- **Type hints**: Always. Use `str | None` union syntax (3.10+), not `Optional[str]`.
- **Naming**:
  - Modules/files: `lowercase_with_underscores`
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Tests: `test_*.py` files, `test_*` functions
- **Docstrings**: Google-style, short. One-liner for trivial functions.

```python
def fetch_user(user_id: int) -> dict:
    """Fetch a user record by ID.

    Args:
        user_id: The unique user identifier.

    Returns:
        A dict with user fields.

    Raises:
        ValueError: If user_id is negative.
    """
```

- **Formatting**: Use `black` if available (`black --check FILE`). Do not obsess if unavailable—PEP 8 compliance is sufficient.
- **Imports**: stdlib → third-party → local, separated by blank lines. Prefer explicit imports over star imports.

## Testing Patterns

- Prefer `pytest` over `unittest` unless the project already uses `unittest`.
- Keep test functions focused: one behavior per test.
- Use fixtures for shared setup; avoid deep inheritance in test classes.
- Name tests descriptively: `test_fetch_user_returns_none_for_missing_id`.

## Error Handling

- Catch specific exceptions, not bare `except:`.
- Use `raise ... from e` to preserve tracebacks.
- Validate inputs early; fail fast with clear messages.

## When Editing Existing Code

- Read the surrounding code first to match existing style.
- Run the project's existing test suite after changes.
- If no tests exist for the changed code, write at least one.
