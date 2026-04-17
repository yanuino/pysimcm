# pysimcm

`pysimcm` is a Python rewrite of [simcm](https://github.com/jze2/simcm) using `pyscard`.

## Project goal

Build a maintainable Python CLI and library for SIM card management.

## First milestone: SIM phonebook management

The current milestone provides a backend-agnostic phonebook domain API and a CLI
for contact management operations:

- list contacts
- get one contact by index
- add a contact
- update a contact
- delete a contact

The current CLI uses an in-memory backend to validate behavior and workflows.
This is intentionally structured so a real `pyscard` backend can be plugged in
without changing command semantics.

## Usage

Run as module (SIM backend by default):

```bash
uv run python -m pysimcm list
```

Or with the console script:

```bash
uv run pysimcm readers
uv run pysimcm verify-pin 1234
uv run pysimcm --pin 1234 list
uv run pysimcm export-csv phonebook.csv
uv run pysimcm --pin 1234 import-csv phonebook.csv
uv run pysimcm list
uv run pysimcm --reader-index 0 get 1
```

CSV format:

```csv
name,number,ton,npi
Alice,+12025550123,1,1
Bob,0612345678,0,1
```

- export always writes the header `name,number,ton,npi`
- import requires a header with at least `name,number`
- `ton` and `npi` are optional on import and default to `1` and `1`
- import is sequential: rows are written to ADN slots `1..N`
- import requires an empty phonebook and fails if any ADN record already exists

Use the in-memory backend for development without a reader:

```bash
uv run pysimcm --backend memory list
uv run pysimcm --backend memory add 1 Alice +12025550123
uv run pysimcm --backend memory update 1 "Alice A" +12025550999
uv run pysimcm --backend memory delete 1
```

Current SIM backend scope:

- implemented: list/get/add/update/delete (MF -> TELECOM -> ADN selection, ADN record reads and UPDATE RECORD writes)
- `export-csv` writes phonebook contents with header `name,number,ton,npi`
- `import-csv` writes CSV rows sequentially to ADN only when the phonebook is empty
- `readers` command lists available PC/SC readers by index without requiring a SIM card
- `verify-pin` command verifies PIN1 using VERIFY CHV (INS 0x20) with 8-byte FF padding
- `--pin` can be passed with SIM operations to auto-verify and retry when card returns SW 9808, 9804, or 6982
- name encoding: GSM7 when possible, UCS2 fallback for non-GSM7 names
- long-name handling: EXT1 chain read/write when EF_EXT1 is available
- number encoding: BCD with support for digits and `*`, `#`, `p`, `w`, `e`

## Development

### Prerequisites

- Python 3.11+
- `uv` (https://github.com/astral-sh/uv)

### Setup

Linux / macOS / WSL:

```bash
./scripts/dev-setup.sh
```

Windows PowerShell:

```powershell
.\scripts\dev-setup.ps1
```

### Common commands

```bash
uv run ruff check . --fix
uv run ruff format .
uv run pytest
```

### Contributing guidelines

See [CONTRIBUTING.md](CONTRIBUTING.md) for development and review expectations.

### Project notes and Copilot instructions

- Project notes: [PROJECT_NOTES.md](PROJECT_NOTES.md)
- Copilot repo instructions: [.github/copilot-instructions.md](.github/copilot-instructions.md)

## Documentation and releases

- MkDocs setup: [README.mkdocs.md](README.mkdocs.md)
- Release workflow: [README.release-workflow.md](README.release-workflow.md)
