"""CLI entrypoint for pysimcm."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .phonebook import InMemoryPhonebookBackend, PhonebookManager
from .sim_backend import SimPhonebookBackend


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    parser = argparse.ArgumentParser(
        prog="pysimcm",
        description="SIM phonebook manager (initial milestone implementation).",
    )
    parser.add_argument(
        "--backend",
        choices=["sim", "memory"],
        default="sim",
        help="Backend to use: sim (default) or memory.",
    )
    parser.add_argument(
        "--reader-index",
        type=int,
        default=0,
        help="Smart card reader index used when --backend sim (default: 0).",
    )
    parser.add_argument(
        "--capacity",
        type=int,
        default=250,
        help="Maximum phonebook capacity when --backend memory (default: 250).",
    )
    parser.add_argument(
        "--pin",
        dest="provided_pin",
        default=None,
        help=(
            "PIN1 code used for non-interactive verification when the SIM "
            "requires authentication."
        ),
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("readers", help="List available PC/SC readers")
    verify_pin_parser = subparsers.add_parser(
        "verify-pin",
        help="Verify PIN1 on the SIM card",
    )
    verify_pin_parser.add_argument("pin", help="PIN1 code (4-8 digits)")

    subparsers.add_parser("list", help="List all contacts")

    get_parser = subparsers.add_parser("get", help="Get one contact by index")
    get_parser.add_argument("index", type=int)

    add_parser = subparsers.add_parser("add", help="Add a new contact")
    add_parser.add_argument("index", type=int)
    add_parser.add_argument("name")
    add_parser.add_argument("number")

    update_parser = subparsers.add_parser("update", help="Update an existing contact")
    update_parser.add_argument("index", type=int)
    update_parser.add_argument("name")
    update_parser.add_argument("number")

    delete_parser = subparsers.add_parser("delete", help="Delete a contact")
    delete_parser.add_argument("index", type=int)

    return parser


def format_contact(index: int, name: str, number: str) -> str:
    """Render one contact in a stable, grep-friendly format."""
    return f"{index}: {name} <{number}>"


def _is_pin_not_verified_error(exc: Exception) -> bool:
    message = str(exc).upper()
    return any(sw in message for sw in ("SW=9808", "SW=9804", "SW=6982"))


def run(argv: Sequence[str] | None = None) -> int:
    """Execute CLI command and return process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Readers command does not need a backend.
    if args.command == "readers":
        try:
            from smartcard.System import (
                readers as list_readers,  # type: ignore[import-untyped]
            )
        except ImportError:
            print("Error: pyscard is not installed")
            return 2
        available = list_readers()
        if not available:
            print("No readers found")
            return 1
        for i, reader in enumerate(available):
            print(f"{i}: {reader}")
        return 0

    if args.command == "verify-pin":
        if args.backend != "sim":
            print("Error: verify-pin is only available with --backend sim")
            return 2
        backend = SimPhonebookBackend(reader_index=args.reader_index)
        try:
            backend.verify_pin1(args.pin)
        except (RuntimeError, ValueError) as exc:
            print(f"Error: {exc}")
            return 2
        print("PIN1 verified")
        return 0

    sim_backend: SimPhonebookBackend | None = None
    if args.backend == "memory":
        backend = InMemoryPhonebookBackend(capacity=args.capacity)
    else:
        sim_backend = SimPhonebookBackend(reader_index=args.reader_index)
        backend = sim_backend

    manager = PhonebookManager(backend)

    def execute_command() -> int:
        if args.command == "list":
            contacts = manager.list()
            if not contacts:
                print("No contacts")
                return 0
            for contact in contacts:
                print(format_contact(contact.index, contact.name, contact.number))
            return 0

        if args.command == "get":
            contact = manager.get(args.index)
            print(format_contact(contact.index, contact.name, contact.number))
            return 0

        if args.command == "add":
            contact = manager.add(args.index, args.name, args.number)
            print(
                f"Added {format_contact(contact.index, contact.name, contact.number)}"
            )
            return 0

        if args.command == "update":
            contact = manager.update(args.index, args.name, args.number)
            print(
                f"Updated {format_contact(contact.index, contact.name, contact.number)}"
            )
            return 0

        if args.command == "delete":
            deleted = manager.delete(args.index)
            if deleted:
                print(f"Deleted contact at index {args.index}")
                return 0
            print(f"No contact at index {args.index}")
            return 1

        parser.error("Unknown command")
        return 2

    try:
        return execute_command()
    except RuntimeError as exc:
        if args.backend == "sim" and _is_pin_not_verified_error(exc):
            if args.provided_pin is None:
                print("Error: SIM PIN1 not verified; pass --pin <PIN1> and retry")
                return 2
            try:
                assert sim_backend is not None
                sim_backend.verify_pin1(args.provided_pin)
            except (RuntimeError, ValueError) as pin_exc:
                print(f"Error: {pin_exc}")
                return 2
            try:
                return execute_command()
            except (
                LookupError,
                NotImplementedError,
                RuntimeError,
                ValueError,
            ) as retry_exc:
                print(f"Error: {retry_exc}")
                return 2
        print(f"Error: {exc}")
        return 2
    except (LookupError, NotImplementedError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2

    return 0


def main() -> None:
    """Console script entrypoint."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
