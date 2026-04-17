"""CSV helpers for phonebook import/export."""

from __future__ import annotations

import csv
from pathlib import Path

from .phonebook import Contact

_EXPORT_HEADER = ["name", "number", "ton", "npi"]


def read_contacts_csv(file_path: str) -> list[Contact]:
    """Read contacts from a CSV file with a header.

    Required columns: ``name``, ``number``.
    Optional columns: ``ton``, ``npi``.
    Missing or blank TON/NPI default to 1/1.
    """
    path = Path(file_path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV must have header: name,number[,ton,npi]")

        header = [field.strip() for field in reader.fieldnames]
        if "name" not in header or "number" not in header:
            raise ValueError("CSV must include header fields: name, number")

        contacts: list[Contact] = []
        for row_index, row in enumerate(reader, start=1):
            name = (row.get("name") or "").strip()
            number = (row.get("number") or "").strip()
            if not name and not number:
                continue
            if not name:
                raise ValueError(f"CSV row {row_index}: name must not be empty")
            if not number:
                raise ValueError(f"CSV row {row_index}: number must not be empty")

            ton_raw = (row.get("ton") or "").strip()
            npi_raw = (row.get("npi") or "").strip()
            ton = 1 if not ton_raw else int(ton_raw)
            npi = 1 if not npi_raw else int(npi_raw)

            contacts.append(
                Contact(
                    index=row_index,
                    name=name,
                    number=number,
                    ton=ton,
                    npi=npi,
                )
            )
        return contacts


def write_contacts_csv(contacts: list[Contact], file_path: str) -> None:
    """Write contacts to a CSV file with the canonical header."""
    path = Path(file_path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_EXPORT_HEADER)
        writer.writeheader()
        for contact in contacts:
            writer.writerow({
                "name": contact.name,
                "number": contact.number,
                "ton": contact.ton,
                "npi": contact.npi,
            })
