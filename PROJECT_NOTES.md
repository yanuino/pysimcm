# Project Notes

## Mission

pysimcm is a Python rewrite of simcm using pyscard, focused first on SIM phonebook management.

## Current State

- Package root: src/pysimcm
- CLI entrypoint: pysimcm -> pysimcm.__main__:main
- Domain model and manager: src/pysimcm/phonebook.py
- Real SIM read backend: src/pysimcm/sim_backend.py
- Tests:
  - tests/test_smoke.py for domain CRUD behavior with in-memory backend
  - tests/test_sim_backend.py for APDU flow and ADN decoding

## Backend Model

- PhonebookManager depends on PhonebookBackend protocol.
- InMemoryPhonebookBackend supports full CRUD for local development/tests.
- SimPhonebookBackend supports read and write operations on SIM now:
  - Connect reader
  - Select MF (3F00)
  - Select DF TELECOM (7F10)
  - Select EF ADN (6F3A)
  - Read ADN records with READ RECORD
  - Write/delete ADN records with UPDATE RECORD
  - Verify PIN1 with VERIFY CHV (INS 0x20, CHV1 in P2=0x01)
  - Decode and encode TON/NPI alongside phone numbers
  - Encode/decode names with GSM7 and UCS2 fallback
  - Use EF_EXT1 chain for long names when EXT1 is available
  - Encode/decode BCD numbers with extended symbols (`*`, `#`, `p`, `w`, `e`)

## CLI Behavior

- Default backend is sim.
- Memory fallback is available with --backend memory.
- Reader selection is available with --reader-index.
- PIN1 verification is available with `verify-pin` (SIM backend only).
- `--pin` enables non-interactive auto-verify/retry when operations hit SW 9808, 9804, or 6982.
- `export-csv` writes header `name,number,ton,npi`.
- `import-csv` is a sequential ADN writer and requires an empty phonebook before writing.
- `deleteall` removes all populated ADN records and reports the number of deleted contacts.

## Development Rules (source of truth)

- Python >= 3.11
- Ruff lint/format required
- Pytest required
- Contributing rules are documented in CONTRIBUTING.md

## Quality Gate

Run before pushing:

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

## Next Priorities

1. Expand tests for more card-specific write edge cases (EXT1 full slots, UICC CLA).
2. Consider USIM/ADF-based phonebook selection beyond DF_TELECOM fallback.
