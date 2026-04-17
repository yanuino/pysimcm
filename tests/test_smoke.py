import pytest

from pysimcm.__main__ import run
from pysimcm.phonebook import InMemoryPhonebookBackend, PhonebookManager


def test_import_pysimcm() -> None:
    """The pysimcm package can be imported."""
    import pysimcm  # noqa: F401


def test_phonebook_crud_flow() -> None:
    """Contacts can be added, read, updated, listed, and deleted."""
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=5))

    added = manager.add(1, "Alice", "+12025550123")
    assert added.name == "Alice"

    loaded = manager.get(1)
    assert loaded.number == "+12025550123"

    updated = manager.update(1, "Alice A", "+12025550999")
    assert updated.name == "Alice A"
    assert manager.list() == [updated]

    assert manager.delete(1) is True
    assert manager.list() == []


def test_phonebook_errors() -> None:
    """Domain-level errors are explicit for invalid operations."""
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=2))

    with pytest.raises(LookupError):
        manager.get(1)

    manager.add(1, "Bob", "+33123456789")
    with pytest.raises(ValueError):
        manager.add(1, "Bob Duplicate", "+33123456789")

    with pytest.raises(LookupError):
        manager.update(2, "Missing", "+33123456789")

    with pytest.raises(ValueError):
        manager.add(3, "Out of range", "+33123456789")


def test_readers_command_lists_readers(capsys: pytest.CaptureFixture[str]) -> None:
    """Readers command prints indexed reader names and returns 0."""
    import sys
    from unittest.mock import MagicMock, patch

    fake_readers = [
        MagicMock(__str__=lambda s: "ACS ACR38U-CCID 0"),
        MagicMock(__str__=lambda s: "Gemalto PC Twin Reader 1"),
    ]
    fake_system = MagicMock(readers=lambda: fake_readers)

    with patch.dict(sys.modules, {"smartcard.System": fake_system}):
        rc = run(["readers"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "0:" in out
    assert "1:" in out


def test_readers_command_no_readers(capsys: pytest.CaptureFixture[str]) -> None:
    """Readers command prints a message and returns 1 when no readers are present."""
    import sys
    from unittest.mock import MagicMock, patch

    fake_system = MagicMock(readers=lambda: [])

    with patch.dict(sys.modules, {"smartcard.System": fake_system}):
        rc = run(["readers"])

    out = capsys.readouterr().out
    assert rc == 1
    assert "No readers" in out


def test_verify_pin_command_invokes_backend(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """verify-pin should call backend PIN1 verification and report success."""
    from unittest.mock import patch

    with patch("pysimcm.__main__.SimPhonebookBackend") as backend_cls:
        backend = backend_cls.return_value
        backend.verify_pin1.return_value = None

        rc = run(["verify-pin", "1234"])

    out = capsys.readouterr().out
    assert rc == 0
    backend.verify_pin1.assert_called_once_with("1234")
    assert "PIN1 verified" in out


def test_verify_pin_command_rejects_memory_backend(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """verify-pin is SIM-only and should fail with --backend memory."""
    rc = run(["--backend", "memory", "verify-pin", "1234"])

    out = capsys.readouterr().out
    assert rc == 2
    assert "only available with --backend sim" in out


def test_list_retries_after_pin_verification_when_sw9808(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """On SW9808, list should verify PIN from --pin and retry once."""
    from unittest.mock import patch

    with patch("pysimcm.__main__.SimPhonebookBackend") as backend_cls:
        backend = backend_cls.return_value
        backend.verify_pin1.return_value = None

        with patch("pysimcm.__main__.PhonebookManager") as manager_cls:
            manager = manager_cls.return_value
            manager.list.side_effect = [
                RuntimeError("failed reading ADN record 1 (SW=9808)"),
                [],
            ]

            rc = run(["--pin", "1234", "list"])

    out = capsys.readouterr().out
    assert rc == 0
    backend.verify_pin1.assert_called_once_with("1234")
    assert manager.list.call_count == 2
    assert "No contacts" in out


def test_list_sw9808_without_pin_shows_actionable_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """When PIN is required and --pin is missing, error should explain next step."""
    from unittest.mock import patch

    with patch("pysimcm.__main__.PhonebookManager") as manager_cls:
        manager = manager_cls.return_value
        manager.list.side_effect = RuntimeError("failed selecting MF (SW=9808)")

        rc = run(["list"])

    out = capsys.readouterr().out
    assert rc == 2
    assert "pass --pin <PIN1>" in out


@pytest.mark.parametrize("sw", ["9804", "6982"])
def test_list_retries_after_pin_verification_for_other_pin_required_sw(
    capsys: pytest.CaptureFixture[str],
    sw: str,
) -> None:
    """SW9804/SW6982 should trigger PIN verify+retry the same as SW9808."""
    from unittest.mock import patch

    with patch("pysimcm.__main__.SimPhonebookBackend") as backend_cls:
        backend = backend_cls.return_value
        backend.verify_pin1.return_value = None

        with patch("pysimcm.__main__.PhonebookManager") as manager_cls:
            manager = manager_cls.return_value
            manager.list.side_effect = [
                RuntimeError(f"failed reading ADN record 1 (SW={sw})"),
                [],
            ]

            rc = run(["--pin", "1234", "list"])

    out = capsys.readouterr().out
    assert rc == 0
    backend.verify_pin1.assert_called_once_with("1234")
    assert manager.list.call_count == 2
    assert "No contacts" in out
