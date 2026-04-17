
#!/usr/bin/env bash
set -e

echo "▶ Installing dependencies (including dev)…"
uv sync --dev

echo "▶ Installing pre-commit hooks…"
uv run pre-commit install
uv run pre-commit install --hook-type commit-msg || true

echo "✅ Development environment ready"
