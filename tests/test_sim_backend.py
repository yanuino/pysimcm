from __future__ import annotations

import pytest

from pysimcm.phonebook import Contact
from pysimcm.sim_backend import SimPhonebookBackend


class FakeConnection:
    """Deterministic APDU connection used to test backend logic."""

    def __init__(
        self, script: list[tuple[list[int], tuple[list[int], int, int]]]
    ) -> None:
        """Initialize scripted APDU command/response pairs."""
        self._script = script
        self._cursor = 0

    def connect(self) -> None:
        """No-op connect for protocol compatibility."""

    def transmit(self, command: list[int]) -> tuple[list[int], int, int]:
        """Return scripted responses and assert APDU sequence."""
        if self._cursor >= len(self._script):
            raise AssertionError(f"unexpected APDU command: {command}")

        expected_command, response = self._script[self._cursor]
        self._cursor += 1
        assert command == expected_command
        return response

    def assert_consumed(self) -> None:
        """Ensure all scripted APDUs were consumed."""
        assert self._cursor == len(self._script)


def _build_adn_record(name: str, number: str, record_length: int = 32) -> list[int]:
    alpha_len = record_length - 14
    alpha_bytes = list(name.encode("ascii"))[:alpha_len]
    alpha_field = alpha_bytes + [0xFF] * (alpha_len - len(alpha_bytes))

    ton_npi = 0x81
    digits = number
    if digits.startswith("+"):
        ton_npi = 0x91
        digits = digits[1:]

    bcd_octets: list[int] = []
    i = 0
    while i < len(digits):
        low = int(digits[i])
        high = 0x0F
        if i + 1 < len(digits):
            high = int(digits[i + 1])
        bcd_octets.append((high << 4) | low)
        i += 2

    number_length = 1 + len(bcd_octets)
    number_field = bcd_octets + [0xFF] * (10 - len(bcd_octets))

    return alpha_field + [number_length, ton_npi] + number_field + [0xFF, 0xFF]


def _fci(file_size: int, record_length: int) -> list[int]:
    return [
        (file_size >> 8) & 0xFF,
        file_size & 0xFF,
        (file_size >> 8) & 0xFF,
        file_size & 0xFF,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        record_length,
    ]


def test_list_contacts_reads_adn_records() -> None:
    """SIM backend selects MF/TELECOM/ADN and decodes non-empty records."""
    select_response = _fci(file_size=64, record_length=32)

    first_record = _build_adn_record("ALICE", "+12345", record_length=32)
    second_record = [0xFF] * 32

    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x20], (first_record, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x4A], ([], 0x6A, 0x82)),
        ([0xA0, 0xB2, 0x02, 0x04, 0x20], (second_record, 0x90, 0x00)),
    ]

    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)

    contacts = backend.list_contacts()

    assert len(contacts) == 1
    assert contacts[0].index == 1
    assert contacts[0].name == "ALICE"
    assert contacts[0].number == "+12345"
    connection.assert_consumed()


def test_get_contact_reads_single_record_after_select() -> None:
    """Single-contact reads should decode one ADN slot."""
    select_response = _fci(file_size=64, record_length=32)
    record = _build_adn_record("BOB", "0612345678", record_length=32)

    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x20], (record, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x4A], ([], 0x6A, 0x82)),
    ]

    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)

    contact = backend.get_contact(1)

    assert contact is not None
    assert contact.name == "BOB"
    assert contact.number == "0612345678"
    connection.assert_consumed()


def test_get_contact_out_of_range_raises_value_error() -> None:
    """Out-of-range indices are rejected against derived record count."""
    select_response = _fci(file_size=64, record_length=32)
    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
    ]

    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)

    with pytest.raises(ValueError):
        backend.get_contact(3)

    connection.assert_consumed()


def test_upsert_contact_updates_one_record() -> None:
    """Upsert should encode the contact and issue one UPDATE RECORD APDU."""
    select_response = _fci(file_size=64, record_length=32)
    expected_record = _build_adn_record("ALICE", "+12345", record_length=32)
    erased_record = [0xFF] * 32

    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x20], (erased_record, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x4A], ([], 0x6A, 0x82)),
        ([0xA0, 0xDC, 0x01, 0x04, 0x20, *expected_record], ([], 0x90, 0x00)),
    ]

    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)

    stored = backend.upsert_contact(
        Contact(index=1, name="ALICE", number="+12345", ton=1, npi=1)
    )

    assert stored.index == 1
    assert stored.name == "ALICE"
    assert stored.number == "+12345"
    connection.assert_consumed()


def test_delete_contact_writes_erased_record_and_reports_existence() -> None:
    """Delete should blank a slot with 0xFF-filled record and return existed flag."""
    select_response = _fci(file_size=64, record_length=32)
    existing_record = _build_adn_record("BOB", "0612345678", record_length=32)
    erased_record = [0xFF] * 32

    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x20], (existing_record, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x4A], ([], 0x6A, 0x82)),
        ([0xA0, 0xDC, 0x01, 0x04, 0x20, *erased_record], ([], 0x90, 0x00)),
    ]

    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)

    deleted = backend.delete_contact(1)

    assert deleted is True
    connection.assert_consumed()


def test_encode_decode_bcd_supports_extended_symbols() -> None:
    """BCD codec supports *, # and pause/wild/expansion symbols."""
    number_length, ton_npi, bcd = SimPhonebookBackend._encode_number("12*#pwe")

    assert ton_npi == 0x81
    decoded = SimPhonebookBackend._decode_bcd_number(
        bcd_digits=bcd,
        number_length=number_length,
        ton_npi=ton_npi,
    )
    assert decoded == "12*#pwe"


def test_decode_contact_preserves_ton_npi() -> None:
    """Decoded SIM contacts should expose TON/NPI from the ADN record."""
    select_response = _fci(file_size=64, record_length=32)
    record = _build_adn_record("ALICE", "+12345", record_length=32)

    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (select_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x20], (record, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x4A], ([], 0x6A, 0x82)),
    ]

    backend = SimPhonebookBackend(connection=FakeConnection(script))
    contact = backend.get_contact(1)

    assert contact is not None
    assert contact.ton == 1
    assert contact.npi == 1


def test_encode_number_accepts_explicit_ton_npi() -> None:
    """Explicit TON/NPI should override inference when encoding a number."""
    number_length, ton_npi, bcd = SimPhonebookBackend._encode_number(
        "0612345678",
        ton=1,
        npi=1,
    )

    assert number_length == 6
    assert ton_npi == 0x91
    assert (
        SimPhonebookBackend._decode_bcd_number(bcd, number_length, ton_npi)
        == "+0612345678"
    )


def test_long_name_uses_ext1_chain_when_available() -> None:
    """Long names should overflow into EXT1 and set ADN pointer byte."""
    adn_response = _fci(file_size=64, record_length=32)
    ext1_response = _fci(file_size=26, record_length=13)
    erased_adn = [0xFF] * 32
    empty_ext1 = [0xFF] * 13

    # record length 32 -> alpha length 18; EXT1 mode uses 17 bytes in ADN + pointer.
    long_name = "ABCDEFGHIJKLMNOPQRSTUVWXY"
    expected_adn = _build_adn_record("ABCDEFGHIJKLMNOPQ", "+12345", 32)
    expected_adn[17] = 0x01

    expected_ext1 = [0xFF] * 13
    expected_ext1[0] = 0x02
    expected_ext1[1] = 8
    expected_ext1[2:10] = list("RSTUVWXY".encode("ascii"))
    expected_ext1[12] = 0xFF

    script = [
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x3F, 0x00], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (adn_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x7F, 0x10], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (adn_response, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (adn_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x20], (erased_adn, 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x4A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (ext1_response, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x01, 0x04, 0x0D], (empty_ext1, 0x90, 0x00)),
        ([0xA0, 0xB2, 0x02, 0x04, 0x0D], (empty_ext1, 0x90, 0x00)),
        ([0xA0, 0xDC, 0x01, 0x04, 0x0D, *expected_ext1], ([], 0x90, 0x00)),
        ([0xA0, 0xA4, 0x00, 0x00, 0x02, 0x6F, 0x3A], ([], 0x9F, 0x0F)),
        ([0xA0, 0xC0, 0x00, 0x00, 0x0F], (adn_response, 0x90, 0x00)),
        ([0xA0, 0xDC, 0x01, 0x04, 0x20, *expected_adn], ([], 0x90, 0x00)),
    ]

    backend = SimPhonebookBackend(connection=FakeConnection(script))
    written = backend.upsert_contact(
        Contact(index=1, name=long_name, number="+12345", ton=1, npi=1)
    )

    assert written.name == long_name
    assert written.number == "+12345"


def test_verify_pin1_sends_verify_chv_apdu() -> None:
    """PIN1 verification should send VERIFY CHV with FF-padded PIN bytes."""
    expected = [
        0xA0,
        0x20,
        0x00,
        0x01,
        0x08,
        0x31,
        0x32,
        0x33,
        0x34,
        0xFF,
        0xFF,
        0xFF,
        0xFF,
    ]
    script = [(expected, ([], 0x90, 0x00))]

    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)
    backend.verify_pin1("1234")

    connection.assert_consumed()


def test_verify_pin1_rejects_invalid_format_before_apdu() -> None:
    """Invalid PIN format should fail locally before touching card I/O."""
    connection = FakeConnection([])
    backend = SimPhonebookBackend(connection=connection)

    with pytest.raises(ValueError):
        backend.verify_pin1("12a")

    connection.assert_consumed()


def test_verify_pin1_wrong_pin_reports_retries() -> None:
    """SW 63Cx should raise a clear wrong-PIN error with retry count."""
    script = [
        (
            [
                0xA0,
                0x20,
                0x00,
                0x01,
                0x08,
                0x31,
                0x32,
                0x33,
                0x34,
                0xFF,
                0xFF,
                0xFF,
                0xFF,
            ],
            ([], 0x63, 0xC2),
        )
    ]
    connection = FakeConnection(script)
    backend = SimPhonebookBackend(connection=connection)

    with pytest.raises(RuntimeError, match="retries remaining: 2"):
        backend.verify_pin1("1234")

    connection.assert_consumed()
