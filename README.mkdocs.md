# MkDocs Documentation

This project uses **MkDocs** with the **Material for MkDocs** theme to build and publish documentation.

The documentation setup is designed to be:
- strict (errors fail the build)
- reproducible locally and in CI
- provider-agnostic for publishing

---

## Tooling

Documentation relies on the following tools (installed as development dependencies):

- `mkdocs`
- `mkdocs-material`
- `mkdocs-macros-plugin`
- `mkdocstrings[python]`
- `mkdocs-git-revision-date-localized-plugin`

All documentation tools are installed with:

```bash
uv sync --dev
```

---

## Project structure

```text
docs/
├── index.md
├── api/
│   └── index.md
└── ...
mkdocs.yml
```

- `docs/` contains all documentation sources
- `mkdocs.yml` defines site configuration
- generated files are placed in `site/` (ignored by Git)

---

## Building documentation locally

To validate the documentation build:

```bash
uv run mkdocs build --strict
```

This command:
- builds the site
- fails on warnings or errors
- generates output in `site/`

---

## Live preview (optional)

To preview documentation locally:

```bash
uv run mkdocs serve
```

The site will be available at:

```
http://127.0.0.1:8000/
```

---

## CI and releases

Documentation is validated in CI using the same strict build.

During a release:
- documentation is always built
- publication is optional and configured separately

See the release documentation for details on publishing workflows.
