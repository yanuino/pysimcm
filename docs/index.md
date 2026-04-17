# Project Documentation

Welcome to the project documentation.

This documentation is built using **MkDocs** and is intended to provide:

- an overview of the project
- usage and configuration guidance
- API reference documentation (when applicable)

---

## Getting started

This project uses an opinionated Python setup with:

- `uv` for dependency management
- `Ruff` for linting and formatting
- `pytest` for testing

Refer to the repository **README** for development setup instructions.

---

## Documentation structure

Documentation sources are located in the `docs/` directory.

Typical sections include:

- project overview
- user guides
- API reference
- development notes

Additional pages can be added by creating Markdown files under `docs/` and
registering them in `mkdocs.yml`.

---

## API reference

If enabled, API documentation is generated automatically from source code
docstrings using **mkdocstrings**.

---

## Versioning and releases

Documentation is built in **strict mode**, meaning warnings are treated as errors.

During releases:

- documentation is always built
- publication is optional and handled via CI

Refer to the release documentation for details.
