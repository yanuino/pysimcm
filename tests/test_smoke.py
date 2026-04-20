import pytest

from pysimcm.__main__ import run
from pysimcm.csv_phonebook import read_contacts_csv, write_contacts_csv
from pysimcm.phonebook import Contact, InMemoryPhonebookBackend, PhonebookManager


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
    assert updated.ton == 1
    assert updated.npi == 1
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


def test_import_contacts_requires_empty_phonebook() -> None:
    """Sequential import must fail when the target phonebook is not empty."""
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=3))
    manager.add(1, "Alice", "+12025550123")

    with pytest.raises(ValueError, match="empty phonebook"):
        manager.import_contacts_sequential([
            Contact(index=1, name="Bob", number="0612345678", ton=1, npi=1)
        ])


def test_csv_round_trip_with_header_and_ton_npi(
    tmp_path,
) -> None:
    """CSV export/import should preserve header and explicit TON/NPI values."""
    file_path = tmp_path / "phonebook.csv"
    contacts = [
        Contact(index=1, name="Alice", number="+12025550123", ton=1, npi=1),
        Contact(index=2, name="Bob", number="0612345678", ton=0, npi=1),
    ]

    write_contacts_csv(contacts, str(file_path))
    loaded = read_contacts_csv(str(file_path))

    assert [c.name for c in loaded] == ["Alice", "Bob"]
    assert [c.ton for c in loaded] == [1, 0]
    assert [c.npi for c in loaded] == [1, 1]


def test_csv_import_defaults_ton_npi_when_columns_missing(
    tmp_path,
) -> None:
    """CSV import should default ton/npi to 1/1 when the columns are omitted."""
    file_path = tmp_path / "import.csv"
    file_path.write_text("name,number\nAlice,+12025550123\n", encoding="utf-8")

    loaded = read_contacts_csv(str(file_path))

    assert len(loaded) == 1
    assert loaded[0].ton == 1
    assert loaded[0].npi == 1


def test_csv_import_requires_header(tmp_path) -> None:
    """CSV import must reject files without the required header."""
    file_path = tmp_path / "invalid.csv"
    file_path.write_text("Alice,+12025550123\n", encoding="utf-8")

    with pytest.raises(ValueError, match="CSV must"):
        read_contacts_csv(str(file_path))


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


def test_export_csv_command_writes_header_and_rows(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    """export-csv should write the canonical header and current contacts."""
    file_path = tmp_path / "export.csv"

    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=3))
    manager.add(1, "Alice", "+12025550123")
    manager.add(2, "Bob", "0612345678")

    from unittest.mock import patch

    with patch("pysimcm.__main__.PhonebookManager", return_value=manager):
        rc = run(["--backend", "memory", "export-csv", str(file_path)])

    out = capsys.readouterr().out
    content = file_path.read_text(encoding="utf-8")
    assert rc == 0
    assert "Exported 2 contacts" in out
    assert content.startswith("name,number,ton,npi")


def test_import_csv_command_requires_empty_phonebook(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    """import-csv should fail when the target phonebook already has ADN records."""
    file_path = tmp_path / "import.csv"
    file_path.write_text(
        "name,number,ton,npi\nAlice,+12025550123,1,1\n",
        encoding="utf-8",
    )
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=3))
    manager.add(1, "Existing", "+33123456789")

    from unittest.mock import patch

    with patch("pysimcm.__main__.PhonebookManager", return_value=manager):
        rc = run(["--backend", "memory", "import-csv", str(file_path)])

    out = capsys.readouterr().out
    assert rc == 2
    assert "empty phonebook" in out


def test_import_csv_command_writes_sequential_slots(
    capsys: pytest.CaptureFixture[str],
    tmp_path,
) -> None:
    """import-csv should write rows sequentially into slots 1..N."""
    file_path = tmp_path / "import.csv"
    file_path.write_text(
        "name,number\nAlice,+12025550123\nBob,0612345678\n",
        encoding="utf-8",
    )
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=3))

    from unittest.mock import patch

    with patch("pysimcm.__main__.PhonebookManager", return_value=manager):
        rc = run(["--backend", "memory", "import-csv", str(file_path)])

    out = capsys.readouterr().out
    contacts = manager.list()
    assert rc == 0
    assert "Imported 2 contacts" in out
    assert [contact.index for contact in contacts] == [1, 2]
    assert [contact.ton for contact in contacts] == [1, 1]


def test_deleteall_command_deletes_all_contacts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deleteall should remove all contacts and report the deletion count."""
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=4))
    manager.add(1, "Alice", "+12025550123")
    manager.add(2, "Bob", "0612345678")

    from unittest.mock import patch

    with patch("pysimcm.__main__.PhonebookManager", return_value=manager):
        rc = run(["--backend", "memory", "deleteall"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "Deleted 2 contacts" in out
    assert manager.list() == []


def test_deleteall_command_on_empty_phonebook(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Deleteall should succeed and report zero deletions when already empty."""
    manager = PhonebookManager(InMemoryPhonebookBackend(capacity=4))

    from unittest.mock import patch

    with patch("pysimcm.__main__.PhonebookManager", return_value=manager):
        rc = run(["--backend", "memory", "deleteall"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "Deleted 0 contacts" in out


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
