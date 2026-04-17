Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "▶ Installing dependencies (including dev)…"
uv sync --dev

Write-Host "▶ Installing pre-commit hooks…"
uv run pre-commit install

# Optional: commit-msg hook (non bloquant)
try {
    uv run pre-commit install --hook-type commit-msg
} catch {
    Write-Host "ℹ commit-msg hook not installed (optional)"
}

Write-Host "✅ Development environment ready"