"""Phonebook domain layer.

This module provides a backend-agnostic phonebook manager that can later be
connected to a real SIM implementation based on pyscard.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Protocol


@dataclass(slots=True)
class Contact:
    """Represents one phonebook entry."""

    index: int
    name: str
    number: str
    ton: int = 0
    npi: int = 1


class PhonebookBackend(Protocol):
    """Interface implemented by concrete phonebook backends."""

    def list_contacts(self) -> list[Contact]:
        """Return all stored contacts in index order."""

    def get_contact(self, index: int) -> Contact | None:
        """Return a single contact by slot index, if present."""

    def upsert_contact(self, contact: Contact) -> Contact:
        """Create or update a contact by index and return persisted value."""

    def delete_contact(self, index: int) -> bool:
        """Delete a contact by index and return whether one existed."""


class InMemoryPhonebookBackend:
    """Simple backend for local development and testing."""

    def __init__(self, capacity: int = 250) -> None:
        """Initialize the in-memory backend."""
        if capacity <= 0:
            msg = "capacity must be strictly positive"
            raise ValueError(msg)
        self.capacity = capacity
        self._contacts: dict[int, Contact] = {}

    def list_contacts(self) -> list[Contact]:
        """Return all contacts ordered by index."""
        return [self._contacts[i] for i in sorted(self._contacts)]

    def get_contact(self, index: int) -> Contact | None:
        """Return one contact by index if present."""
        return self._contacts.get(index)

    def upsert_contact(self, contact: Contact) -> Contact:
        """Insert or replace one contact after validation."""
        self._validate_index(contact.index)
        self._validate_contact_fields(
            contact.name,
            contact.number,
            contact.ton,
            contact.npi,
        )
        self._contacts[contact.index] = contact
        return contact

    def delete_contact(self, index: int) -> bool:
        """Delete one contact by index."""
        self._validate_index(index)
        return self._contacts.pop(index, None) is not None

    def _validate_index(self, index: int) -> None:
        if index < 1 or index > self.capacity:
            msg = f"index must be in [1, {self.capacity}], got {index}"
            raise ValueError(msg)

    @staticmethod
    def _validate_contact_fields(name: str, number: str, ton: int, npi: int) -> None:
        if not name.strip():
            raise ValueError("name must not be empty")
        if not number.strip():
            raise ValueError("number must not be empty")
        if ton < 0 or ton > 7:
            raise ValueError(f"ton must be in [0, 7], got {ton}")
        if npi < 0 or npi > 15:
            raise ValueError(f"npi must be in [0, 15], got {npi}")


class PhonebookManager:
    """High-level phonebook API used by CLI and future integrations."""

    def __init__(self, backend: PhonebookBackend) -> None:
        """Initialize manager with a concrete phonebook backend."""
        self.backend = backend

    def list(self) -> list[Contact]:
        """List all contacts."""
        return self.backend.list_contacts()

    def get(self, index: int) -> Contact:
        """Get one contact or raise if missing."""
        contact = self.backend.get_contact(index)
        if contact is None:
            raise LookupError(f"no contact at index {index}")
        return contact

    def add(
        self,
        index: int,
        name: str,
        number: str,
        ton: int | None = None,
        npi: int | None = None,
    ) -> Contact:
        """Create a new contact and fail if slot already exists."""
        if self.backend.get_contact(index) is not None:
            raise ValueError(f"contact already exists at index {index}")
        resolved_ton, resolved_npi = self._resolve_ton_npi(number, ton, npi)
        return self.backend.upsert_contact(
            Contact(
                index=index,
                name=name,
                number=number,
                ton=resolved_ton,
                npi=resolved_npi,
            )
        )

    def update(
        self,
        index: int,
        name: str,
        number: str,
        ton: int | None = None,
        npi: int | None = None,
    ) -> Contact:
        """Update an existing contact and fail if slot is empty."""
        if self.backend.get_contact(index) is None:
            raise LookupError(f"no contact at index {index}")
        resolved_ton, resolved_npi = self._resolve_ton_npi(number, ton, npi)
        return self.backend.upsert_contact(
            Contact(
                index=index,
                name=name,
                number=number,
                ton=resolved_ton,
                npi=resolved_npi,
            )
        )

    def delete(self, index: int) -> bool:
        """Delete a contact and return whether a deletion happened."""
        return self.backend.delete_contact(index)

    def delete_all(self) -> int:
        """Delete all existing contacts and return how many were removed."""
        deleted = 0
        for contact in self.backend.list_contacts():
            if self.backend.delete_contact(contact.index):
                deleted += 1
        return deleted

    def import_contacts_sequential(self, contacts: list[Contact]) -> int:
        """Write contacts to slots 1..N only when the phonebook is empty."""
        existing = self.backend.list_contacts()
        if existing:
            raise ValueError("CSV import requires an empty phonebook")

        for slot_index, contact in enumerate(contacts, start=1):
            self.backend.upsert_contact(replace(contact, index=slot_index))
        return len(contacts)

    @staticmethod
    def _resolve_ton_npi(
        number: str,
        ton: int | None,
        npi: int | None,
    ) -> tuple[int, int]:
        if ton is None:
            ton = 1 if number.startswith("+") else 0
        if npi is None:
            npi = 1
        return ton, npi
