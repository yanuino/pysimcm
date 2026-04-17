# Copilot Instructions for pysimcm

## Goal

Help implement pysimcm as a Python rewrite of simcm with pyscard, with priority on safe and maintainable SIM phonebook features.

## Project-Specific Constraints

- Keep architecture backend-agnostic via PhonebookBackend and PhonebookManager.
- Preserve CLI command semantics while evolving backends.
- SIM backend is currently read-focused; do not silently pretend write support exists.
- Prefer explicit errors over hidden fallbacks when hardware/SIM actions fail.

## File Ownership and Layout

- Core domain logic: src/pysimcm/phonebook.py
- SIM APDU backend: src/pysimcm/sim_backend.py
- CLI: src/pysimcm/__main__.py
- Tests: tests/
- Contributor process: CONTRIBUTING.md
- Ongoing technical summary: PROJECT_NOTES.md

## Coding Standards

- Follow pyproject.toml and CONTRIBUTING.md.
- Use Python 3.11-compatible typing and syntax.
- Keep line length <= 88 and satisfy Ruff checks.
- Use Google-style docstrings where required.
- Avoid unnecessary dependencies.

## Testing Expectations

For any behavior change:

1. Add or update tests in tests/.
2. Run:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

3. Do not claim completion if these checks fail.

## SIM/APDU Change Guidance

When editing SIM backend behavior:

- Keep APDU sequence explicit and readable.
- Validate and propagate status words clearly.
- Prefer deterministic parsing functions with unit tests.
- Add fake/scripted APDU tests for parser/protocol changes.

## Documentation Expectations

- Update README.md and docs/index.md for user-visible behavior changes.
- Reflect milestone status accurately (implemented vs not implemented).

## Preferred Working Style

- Make focused changes with minimal unrelated edits.
- Keep error messages actionable.
- Preserve backward-compatible interfaces unless explicitly requested.
