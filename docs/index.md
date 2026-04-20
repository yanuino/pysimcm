# pysimcm Documentation

`pysimcm` aims to rewrite `simcm` in Python with `pyscard`.

## Current status

The first implemented milestone is phonebook management.

Implemented capabilities:

- contact domain model
- backend contract for storage/access
- in-memory backend for development and tests
- pyscard SIM backend selecting MF/TELECOM/ADN and reading/writing ADN records
- GSM7/UCS2 name encoding and decoding
- EF_EXT1 chain logic for long-name overflow when available
- CLI backend switch (`sim` default, `memory` fallback)
- CLI commands for list/get/add/update/delete
- CLI command deleteall to clear all populated ADN records
- CSV export/import for ADN records with header `name,number,ton,npi`
- sequential CSV import guarded by an empty-phonebook precondition
- `readers` command to list available PC/SC readers by index
- `verify-pin` command for PIN1 verification via VERIFY CHV APDU
- `--pin` option for non-interactive PIN1 verification retry on SW 9808/9804/6982

## Next implementation target

Harden SIM write behavior for more card-specific edge cases, including EXT1 full-slots
degradation and card-type detection (GSM SIM vs UICC).
