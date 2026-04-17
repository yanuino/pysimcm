# Python Project Template

![CI](https://github.com/yanuino/python-project-template/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)

Opinionated Python project template using **uv**, **Ruff**, **pre-commit**, and **GitHub Actions**.

---

## Purpose

This repository is a **GitHub template** intended to bootstrap modern Python projects with:

- Fast dependency management (`uv`)
- Deterministic code quality (`ruff`, `pre-commit`)
- Clear CI responsibilities
- Optional documentation and binary release workflows

This template favors **clarity, explicitness, and maintainability** over complex automation.

---

## Using the template

1. Click **Use this template** on GitHub
2. Create your new repository
3. Clone it locally
4. Run the setup script

---

## Development setup

### Prerequisites

- Git
- Python **3.11+**
- `uv` — https://github.com/astral-sh/uv

### Linux / macOS / WSL

```bash
./scripts/dev-setup.sh
```

### Windows (PowerShell)

```powershell
.\scripts\dev-setup.ps1
```

If script execution is restricted:

```powershell
PowerShell -ExecutionPolicy Bypass -File scripts\dev-setup.ps1
```

---

## Common commands

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

---

## Code quality philosophy

- **pre-commit** enforces fast, deterministic checks (lint, format)
- **pytest** runs in CI, not on every commit
- CI is the **authority**, not the developer machine
- Heavy or OS-specific builds are CI-only

---

## Documentation

Documentation uses **MkDocs**.

- Validated locally via pre-commit (`mkdocs build --strict`)
- Fully built in CI
- Optional publication during release
See [README.mkdocs.md](README.mkdocs.md) for details.

---

## Releases

Releases are driven by Git tags (`vX.Y.Z`).

During a release:

- Documentation is built
- Documentation publication is optional
- Linux and/or Windows binaries may be built using PyInstaller

All release logic is handled by GitHub Actions.
See [README.release-workflow.md](README.release-workflow.md) for details.

---

## Tooling upgrades

Tool versions are intentionally pinned.

Upgrades must:

- Update versions explicitly
- Apply Ruff formatting and fixes
- Update pre-commit hooks
- Commit all generated changes

---

## License

MIT
