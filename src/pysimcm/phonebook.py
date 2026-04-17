"""Phonebook domain layer.

This module provides a backend-agnostic phonebook manager that can later be
connected to a real SIM implementation based on pyscard.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(slots=True)
class Contact:
    """Represents one phonebook entry."""

    index: int
    name: str
    number: str


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
    """Simple backend for local development and testing.

    This backend intentionally mirrors the shape we need for a future SIM-backed
    implementation while remaining deterministic in tests.
    """

    def __init__(self, capacity: int = 250) -> None:
        """Initialize the in-memory backend.

        Args:
            capacity: Maximum number of valid phonebook slots.

        Raises:
            ValueError: If ``capacity`` is not strictly positive.
        """
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
        self._validate_contact_fields(contact.name, contact.number)
        self._contacts[contact.index] = contact
        return contact

    def delete_contact(self, index: int) -> bool:
        """Delete one contact by index.

        Returns:
            ``True`` if a contact existed and was removed, ``False`` otherwise.
        """
        self._validate_index(index)
        return self._contacts.pop(index, None) is not None

    def _validate_index(self, index: int) -> None:
        if index < 1 or index > self.capacity:
            msg = f"index must be in [1, {self.capacity}], got {index}"
            raise ValueError(msg)

    @staticmethod
    def _validate_contact_fields(name: str, number: str) -> None:
        if not name.strip():
            raise ValueError("name must not be empty")
        if not number.strip():
            raise ValueError("number must not be empty")


class PhonebookManager:
    """High-level phonebook API used by CLI and future integrations."""

    def __init__(self, backend: PhonebookBackend) -> None:
        """Initialize manager with a concrete phonebook backend.

        Args:
            backend: Backend implementation used for storage and retrieval.
        """
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

    def add(self, index: int, name: str, number: str) -> Contact:
        """Create a new contact and fail if slot already exists."""
        if self.backend.get_contact(index) is not None:
            raise ValueError(f"contact already exists at index {index}")
        return self.backend.upsert_contact(
            Contact(index=index, name=name, number=number)
        )

    def update(self, index: int, name: str, number: str) -> Contact:
        """Update an existing contact and fail if slot is empty."""
        if self.backend.get_contact(index) is None:
            raise LookupError(f"no contact at index {index}")
        return self.backend.upsert_contact(
            Contact(index=index, name=name, number=number)
        )

    def delete(self, index: int) -> bool:
        """Delete a contact and return whether a deletion happened."""
        return self.backend.delete_contact(index)
