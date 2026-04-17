# Contributing to pysimcm

This project follows a strict, simple workflow to keep development predictable.

## Development baseline

- Use Python 3.11 or newer.
- Keep source code in `src/pysimcm`.
- Keep tests in `tests`.

## Setup

1. Install dependencies:

```bash
uv sync --dev
```

2. Run quality checks before pushing:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

## Code style and linting

- Ruff is the source of truth for linting and formatting.
- Max line length: 88.
- Target Python version: 3.11.
- Enabled lint families: E, F, I, B, D.
- Docstrings should follow Google style.

Current intentionally ignored docstring rules:

- D100
- D104
- D203
- D213

## Imports and package organization

- Use explicit imports.
- Keep import ordering Ruff-compatible.
- The public CLI entrypoint is `pysimcm` mapped to `pysimcm.__main__:main`.

## Testing expectations

- Add or update tests for every behavior change.
- Prefer focused unit tests for domain logic.
- Keep tests deterministic and hardware-independent by default.
- Hardware/SIM-reader tests should be optional and clearly marked when added.

## Dependencies

- Runtime dependencies should remain minimal.
- Add new runtime packages only when necessary for end-user functionality.
- Prefer adding development-only tools to the `dev` dependency group.

## Documentation

- Keep README and docs aligned with implemented behavior.
- Ensure docs build cleanly in strict mode when documentation changes are made:

```bash
uv run mkdocs build --strict
```

## Pull request checklist

- Code is formatted and lint-clean.
- Tests pass locally.
- Documentation is updated for user-visible changes.
- Scope is focused and commit history is clear.
