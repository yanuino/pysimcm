"""SIM-backed phonebook backend using pyscard APDU commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .phonebook import Contact, PhonebookBackend


class APDUConnection(Protocol):
    """Protocol for card connections that can transmit APDU commands."""

    def connect(self) -> None:
        """Connect to the smart card."""

    def transmit(self, command: list[int]) -> tuple[list[int], int, int]:
        """Transmit one APDU command and return response data and status words."""


@dataclass(slots=True)
class SimAdnLayout:
    """Describes ADN EF record sizing."""

    record_length: int
    record_count: int


@dataclass(slots=True)
class SimExt1Layout:
    """Describes EXT1 EF record sizing."""

    record_length: int
    record_count: int


class SimPhonebookBackend(PhonebookBackend):
    """Phonebook backend that reads and writes ADN records on a SIM card."""

    MF = (0x3F, 0x00)
    DF_TELECOM = (0x7F, 0x10)
    EF_ADN = (0x6F, 0x3A)
    EF_EXT1 = (0x6F, 0x4A)

    _BCD_CHAR_TO_NIBBLE = {
        "0": 0x0,
        "1": 0x1,
        "2": 0x2,
        "3": 0x3,
        "4": 0x4,
        "5": 0x5,
        "6": 0x6,
        "7": 0x7,
        "8": 0x8,
        "9": 0x9,
        "*": 0xA,
        "#": 0xB,
        "p": 0xC,
        "w": 0xD,
        "e": 0xE,
    }
    _BCD_NIBBLE_TO_CHAR = {value: key for key, value in _BCD_CHAR_TO_NIBBLE.items()}

    _GSM7_DEFAULT = {
        "@": 0x00,
        "£": 0x01,
        "$": 0x02,
        "¥": 0x03,
        "è": 0x04,
        "é": 0x05,
        "ù": 0x06,
        "ì": 0x07,
        "ò": 0x08,
        "Ç": 0x09,
        "\n": 0x0A,
        "Ø": 0x0B,
        "ø": 0x0C,
        "\r": 0x0D,
        "Å": 0x0E,
        "å": 0x0F,
        "Δ": 0x10,
        "_": 0x11,
        "Φ": 0x12,
        "Γ": 0x13,
        "Λ": 0x14,
        "Ω": 0x15,
        "Π": 0x16,
        "Ψ": 0x17,
        "Σ": 0x18,
        "Θ": 0x19,
        "Ξ": 0x1A,
        "Æ": 0x1C,
        "æ": 0x1D,
        "ß": 0x1E,
        "É": 0x1F,
        " ": 0x20,
        "!": 0x21,
        '"': 0x22,
        "#": 0x23,
        "¤": 0x24,
        "%": 0x25,
        "&": 0x26,
        "'": 0x27,
        "(": 0x28,
        ")": 0x29,
        "*": 0x2A,
        "+": 0x2B,
        ",": 0x2C,
        "-": 0x2D,
        ".": 0x2E,
        "/": 0x2F,
        "0": 0x30,
        "1": 0x31,
        "2": 0x32,
        "3": 0x33,
        "4": 0x34,
        "5": 0x35,
        "6": 0x36,
        "7": 0x37,
        "8": 0x38,
        "9": 0x39,
        ":": 0x3A,
        ";": 0x3B,
        "<": 0x3C,
        "=": 0x3D,
        ">": 0x3E,
        "?": 0x3F,
        "¡": 0x40,
        "A": 0x41,
        "B": 0x42,
        "C": 0x43,
        "D": 0x44,
        "E": 0x45,
        "F": 0x46,
        "G": 0x47,
        "H": 0x48,
        "I": 0x49,
        "J": 0x4A,
        "K": 0x4B,
        "L": 0x4C,
        "M": 0x4D,
        "N": 0x4E,
        "O": 0x4F,
        "P": 0x50,
        "Q": 0x51,
        "R": 0x52,
        "S": 0x53,
        "T": 0x54,
        "U": 0x55,
        "V": 0x56,
        "W": 0x57,
        "X": 0x58,
        "Y": 0x59,
        "Z": 0x5A,
        "Ä": 0x5B,
        "Ö": 0x5C,
        "Ñ": 0x5D,
        "Ü": 0x5E,
        "§": 0x5F,
        "¿": 0x60,
        "a": 0x61,
        "b": 0x62,
        "c": 0x63,
        "d": 0x64,
        "e": 0x65,
        "f": 0x66,
        "g": 0x67,
        "h": 0x68,
        "i": 0x69,
        "j": 0x6A,
        "k": 0x6B,
        "l": 0x6C,
        "m": 0x6D,
        "n": 0x6E,
        "o": 0x6F,
        "p": 0x70,
        "q": 0x71,
        "r": 0x72,
        "s": 0x73,
        "t": 0x74,
        "u": 0x75,
        "v": 0x76,
        "w": 0x77,
        "x": 0x78,
        "y": 0x79,
        "z": 0x7A,
        "ä": 0x7B,
        "ö": 0x7C,
        "ñ": 0x7D,
        "ü": 0x7E,
        "à": 0x7F,
    }
    _GSM7_EXTENSION = {
        "^": 0x14,
        "{": 0x28,
        "}": 0x29,
        "\\": 0x2F,
        "[": 0x3C,
        "~": 0x3D,
        "]": 0x3E,
        "|": 0x40,
        "€": 0x65,
    }
    _GSM7_DEFAULT_REV = {value: key for key, value in _GSM7_DEFAULT.items()}
    _GSM7_EXTENSION_REV = {value: key for key, value in _GSM7_EXTENSION.items()}

    def __init__(
        self,
        reader_index: int = 0,
        connection: APDUConnection | None = None,
    ) -> None:
        """Initialize a SIM backend.

        Args:
            reader_index: Index of the card reader to open when no explicit
                connection is provided.
            connection: Optional pre-connected APDU connection used mainly for
                tests.
        """
        self.reader_index = reader_index
        self._connection = connection
        self._layout: SimAdnLayout | None = None
        self._ext1_layout: SimExt1Layout | None = None
        self._ext1_checked = False
        self._selected_file: tuple[int, int] | None = None

    def list_contacts(self) -> list[Contact]:
        """Read and decode all non-empty ADN contacts from the SIM card."""
        self._ensure_adn_selected()
        assert self._layout is not None

        contacts: list[Contact] = []
        for index in range(1, self._layout.record_count + 1):
            record = self._read_record(index)
            contact = self._decode_adn_record(index=index, record=record)
            if contact is not None:
                contacts.append(contact)
        return contacts

    def get_contact(self, index: int) -> Contact | None:
        """Return one contact by slot index, if present on the SIM card."""
        self._ensure_adn_selected()
        assert self._layout is not None
        self._validate_index(index)

        record = self._read_record(index)
        return self._decode_adn_record(index=index, record=record)

    def upsert_contact(self, contact: Contact) -> Contact:
        """Create or update one contact by slot index on the SIM card."""
        self._ensure_adn_selected()
        assert self._layout is not None
        self._validate_index(contact.index)

        previous = self._read_record(contact.index)
        previous_ptr = self._extract_ext1_pointer_from_adn(previous)
        if previous_ptr is not None:
            self._clear_ext1_chain(previous_ptr)

        record = self._encode_adn_record(contact)
        self._update_record(contact.index, record)
        return contact

    def delete_contact(self, index: int) -> bool:
        """Delete one contact by slot index.

        Returns:
            ``True`` when a contact existed before deletion, ``False`` when the
            slot was already empty.
        """
        self._ensure_adn_selected()
        assert self._layout is not None
        self._validate_index(index)

        previous_record = self._read_record(index)
        existed = (
            self._decode_adn_record(index=index, record=previous_record) is not None
        )

        previous_ptr = self._extract_ext1_pointer_from_adn(previous_record)
        if previous_ptr is not None:
            self._clear_ext1_chain(previous_ptr)

        self._update_record(index, [0xFF] * self._layout.record_length)
        return existed

    def verify_pin1(self, pin: str) -> None:
        """Verify PIN1 (CHV1) against the SIM card.

        Uses VERIFY CHV with GSM SIM CLA 0xA0:
        CLA=0xA0, INS=0x20, P1=0x00, P2=0x01, Lc=0x08, Data=<PIN padded with FF>.
        """
        self._connect_if_needed()
        assert self._connection is not None

        pin_data = self._encode_pin_data(pin)
        cmd = [0xA0, 0x20, 0x00, 0x01, 0x08, *pin_data]
        _, sw1, sw2 = self._connection.transmit(cmd)

        if (sw1, sw2) == (0x90, 0x00):
            return

        sw = (sw1 << 8) | sw2
        if sw1 == 0x63 and (sw2 & 0xF0) == 0xC0:
            retries = sw2 & 0x0F
            raise RuntimeError(f"wrong PIN1, retries remaining: {retries}")
        if sw == 0x6983:
            raise RuntimeError("PIN1 is blocked")
        if sw == 0x6984:
            raise RuntimeError("PIN1 verification is disabled on this card")

        raise RuntimeError(f"failed verifying PIN1 (SW={sw1:02X}{sw2:02X})")

    def _ensure_adn_selected(self) -> None:
        if self._layout is not None:
            return

        self._connect_if_needed()
        self._select_file(self.MF)
        self._select_file(self.DF_TELECOM)
        adn_response = self._select_file(self.EF_ADN)
        self._layout = self._parse_adn_layout(adn_response)

    def _connect_if_needed(self) -> None:
        if self._connection is None:
            self._connection = self._connect_default()

    def _connect_default(self) -> APDUConnection:
        try:
            from smartcard.System import readers
        except ImportError as exc:
            raise RuntimeError("pyscard is required for SIM backend") from exc

        available_readers = readers()
        if not available_readers:
            raise RuntimeError("no smart card readers available")
        if self.reader_index < 0 or self.reader_index >= len(available_readers):
            msg = (
                f"reader index {self.reader_index} out of range "
                f"(available: 0..{len(available_readers) - 1})"
            )
            raise RuntimeError(msg)

        connection = available_readers[self.reader_index].createConnection()
        connection.connect()
        return connection

    def _select_file(self, file_id: tuple[int, int]) -> list[int]:
        assert self._connection is not None
        select_cmd = [0xA0, 0xA4, 0x00, 0x00, 0x02, file_id[0], file_id[1]]
        data, sw1, sw2 = self._connection.transmit(select_cmd)

        if sw1 in (0x9F, 0x61):
            get_response_cmd = [0xA0, 0xC0, 0x00, 0x00, sw2]
            data, sw1, sw2 = self._connection.transmit(get_response_cmd)

        if (sw1, sw2) != (0x90, 0x00):
            fid = f"{file_id[0]:02X}{file_id[1]:02X}"
            msg = f"failed to select file {fid} (SW={sw1:02X}{sw2:02X})"
            raise RuntimeError(msg)

        self._selected_file = file_id
        return data

    def _ensure_file_selected(self, file_id: tuple[int, int]) -> None:
        if self._selected_file == file_id:
            return
        self._select_file(file_id)

    def _read_record(self, index: int) -> list[int]:
        assert self._connection is not None
        assert self._layout is not None
        self._ensure_file_selected(self.EF_ADN)
        cmd = [0xA0, 0xB2, index, 0x04, self._layout.record_length]
        data, sw1, sw2 = self._connection.transmit(cmd)
        if (sw1, sw2) != (0x90, 0x00):
            msg = f"failed reading ADN record {index} (SW={sw1:02X}{sw2:02X})"
            raise RuntimeError(msg)
        return data

    def _update_record(self, index: int, record: list[int]) -> None:
        assert self._connection is not None
        assert self._layout is not None
        self._ensure_file_selected(self.EF_ADN)
        if len(record) != self._layout.record_length:
            msg = (
                f"record length mismatch: expected {self._layout.record_length}, "
                f"got {len(record)}"
            )
            raise ValueError(msg)

        cmd = [0xA0, 0xDC, index, 0x04, self._layout.record_length, *record]
        _, sw1, sw2 = self._connection.transmit(cmd)
        if (sw1, sw2) != (0x90, 0x00):
            msg = f"failed updating ADN record {index} (SW={sw1:02X}{sw2:02X})"
            raise RuntimeError(msg)

    @staticmethod
    def _parse_adn_layout(select_response: list[int]) -> SimAdnLayout:
        if not select_response:
            raise RuntimeError("empty EF ADN select response")

        record_length = select_response[-1]
        if record_length <= 0:
            raise RuntimeError("invalid ADN record length")

        file_size_candidates: list[int] = []
        for offset in (0, 2):
            if len(select_response) > offset + 1:
                size = (select_response[offset] << 8) | select_response[offset + 1]
                if size > 0:
                    file_size_candidates.append(size)

        if not file_size_candidates:
            raise RuntimeError("unable to determine EF ADN file size")

        divisible = [size for size in file_size_candidates if size % record_length == 0]
        chosen_size = divisible[0] if divisible else max(file_size_candidates)
        record_count = chosen_size // record_length
        if record_count <= 0:
            raise RuntimeError("invalid EF ADN record count")

        return SimAdnLayout(record_length=record_length, record_count=record_count)

    @staticmethod
    def _parse_ext1_layout(select_response: list[int]) -> SimExt1Layout:
        adn = SimPhonebookBackend._parse_adn_layout(select_response)
        return SimExt1Layout(
            record_length=adn.record_length, record_count=adn.record_count
        )

    def _ensure_ext1_loaded(self) -> None:
        if self._ext1_checked:
            return
        self._ext1_checked = True

        try:
            response = self._select_file(self.EF_EXT1)
        except RuntimeError:
            self._ext1_layout = None
            return

        self._ext1_layout = self._parse_ext1_layout(response)

    def _read_ext1_record(self, index: int) -> list[int]:
        assert self._connection is not None
        assert self._ext1_layout is not None
        self._ensure_file_selected(self.EF_EXT1)
        cmd = [0xA0, 0xB2, index, 0x04, self._ext1_layout.record_length]
        data, sw1, sw2 = self._connection.transmit(cmd)
        if (sw1, sw2) != (0x90, 0x00):
            msg = f"failed reading EXT1 record {index} (SW={sw1:02X}{sw2:02X})"
            raise RuntimeError(msg)
        return data

    def _update_ext1_record(self, index: int, record: list[int]) -> None:
        assert self._connection is not None
        assert self._ext1_layout is not None
        self._ensure_file_selected(self.EF_EXT1)
        if len(record) != self._ext1_layout.record_length:
            msg = (
                "EXT1 record length mismatch: "
                f"expected {self._ext1_layout.record_length}, "
                f"got {len(record)}"
            )
            raise ValueError(msg)

        cmd = [0xA0, 0xDC, index, 0x04, self._ext1_layout.record_length, *record]
        _, sw1, sw2 = self._connection.transmit(cmd)
        if (sw1, sw2) != (0x90, 0x00):
            msg = f"failed updating EXT1 record {index} (SW={sw1:02X}{sw2:02X})"
            raise RuntimeError(msg)

    def _validate_index(self, index: int) -> None:
        assert self._layout is not None
        if index < 1 or index > self._layout.record_count:
            msg = f"index must be in [1, {self._layout.record_count}], got {index}"
            raise ValueError(msg)

    def _decode_adn_record(self, index: int, record: list[int]) -> Contact | None:
        if not record:
            return None
        if all(value in (0x00, 0xFF) for value in record):
            return None
        if len(record) < 14:
            raise RuntimeError("ADN record too short")

        alpha_len = len(record) - 14
        alpha_raw = record[:alpha_len]
        number_length = record[alpha_len]
        ton_npi = record[alpha_len + 1]
        bcd_number_field = record[alpha_len + 2 : alpha_len + 12]

        name_field = bytes(value for value in alpha_raw if value != 0xFF)
        ext1_payload = b""
        pointer = self._extract_ext1_pointer_from_adn(record)
        if pointer is not None:
            name_field = bytes(value for value in alpha_raw[:-1] if value != 0xFF)
            ext1_payload = self._read_ext1_chain(pointer)

        name = self._decode_alpha(name_field + ext1_payload)
        number = self._decode_bcd_number(
            bcd_number_field,
            number_length=number_length,
            ton_npi=ton_npi,
        )
        ton, npi = self._decode_ton_npi(ton_npi, number_length)

        if not name and not number:
            return None
        if not name:
            name = f"slot-{index}"
        return Contact(index=index, name=name, number=number, ton=ton, npi=npi)

    @staticmethod
    def _decode_ton_npi(ton_npi: int, number_length: int) -> tuple[int, int]:
        if number_length in (0, 0xFF):
            return 1, 1
        ton = (ton_npi >> 4) & 0x07
        npi = ton_npi & 0x0F
        return ton, npi

    def _extract_ext1_pointer_from_adn(self, record: list[int]) -> int | None:
        self._ensure_ext1_loaded()
        if self._ext1_layout is None:
            return None
        if len(record) < 14:
            return None

        alpha_len = len(record) - 14
        if alpha_len <= 0:
            return None

        pointer = record[alpha_len - 1]
        if pointer in (0x00, 0xFF):
            return None
        if pointer < 1 or pointer > self._ext1_layout.record_count:
            return None

        rec = self._read_ext1_record(pointer)
        if rec and rec[0] in (0x01, 0x02):
            return pointer
        return None

    @classmethod
    def _decode_alpha(cls, raw: bytes) -> str:
        trimmed = raw
        if not trimmed:
            return ""
        if trimmed[0] == 0x80 and len(trimmed) > 1:
            try:
                return trimmed[1:].decode("utf-16-be", errors="ignore").strip("\x00 ")
            except UnicodeDecodeError:
                return ""
        return cls._decode_gsm7_unpacked(trimmed).strip("\x00 ")

    @classmethod
    def _decode_gsm7_unpacked(cls, payload: bytes) -> str:
        chars: list[str] = []
        idx = 0
        while idx < len(payload):
            code = payload[idx]
            idx += 1
            if code == 0x1B:
                if idx >= len(payload):
                    break
                ext_code = payload[idx]
                idx += 1
                chars.append(cls._GSM7_EXTENSION_REV.get(ext_code, "?"))
                continue
            if code in cls._GSM7_DEFAULT_REV:
                chars.append(cls._GSM7_DEFAULT_REV[code])
            else:
                chars.append(chr(code))
        return "".join(chars)

    @classmethod
    def _decode_bcd_number(
        cls,
        bcd_digits: list[int],
        number_length: int,
        ton_npi: int,
    ) -> str:
        if number_length in (0, 0xFF):
            return ""

        octet_count = max(number_length - 1, 0)
        octet_count = min(octet_count, len(bcd_digits))

        digits: list[str] = []
        for byte in bcd_digits[:octet_count]:
            low = byte & 0x0F
            high = (byte >> 4) & 0x0F
            if low in cls._BCD_NIBBLE_TO_CHAR:
                digits.append(cls._BCD_NIBBLE_TO_CHAR[low])
            if high in cls._BCD_NIBBLE_TO_CHAR:
                digits.append(cls._BCD_NIBBLE_TO_CHAR[high])

        number = "".join(digits)
        if ton_npi == 0x91 and number:
            return f"+{number}"
        return number

    def _encode_adn_record(self, contact: Contact) -> list[int]:
        assert self._layout is not None
        alpha_len = self._layout.record_length - 14
        if alpha_len <= 0:
            raise RuntimeError("ADN record length does not allow alpha identifier")

        self._ensure_ext1_loaded()
        encoded_name = self._encode_name(contact.name)

        ext1_ptr = 0xFF
        if self._ext1_layout is None:
            if len(encoded_name) > alpha_len:
                raise ValueError(
                    f"name too long for ADN record (max {alpha_len} bytes)"
                )
            alpha = list(encoded_name) + [0xFF] * (alpha_len - len(encoded_name))
        else:
            if alpha_len <= 1:
                raise RuntimeError("ADN alpha field too short for EXT1 pointer mode")
            adn_payload_len = alpha_len - 1
            alpha_adn = encoded_name[:adn_payload_len]
            overflow = encoded_name[adn_payload_len:]
            if overflow:
                ext1_ptr = self._write_ext1_chain(overflow)
            alpha = list(alpha_adn) + [0xFF] * (adn_payload_len - len(alpha_adn))
            alpha.append(ext1_ptr)

        number_length, ton_npi, bcd_field = self._encode_number(
            contact.number,
            ton=contact.ton,
            npi=contact.npi,
        )
        return alpha + [number_length, ton_npi] + bcd_field + [0xFF, 0xFF]

    @classmethod
    def _encode_name(cls, name: str) -> bytes:
        text = name.strip()
        if not text:
            raise ValueError("name must not be empty")

        if cls._can_encode_gsm7(text):
            return cls._encode_gsm7_unpacked(text)

        ucs2 = text.encode("utf-16-be")
        if len(ucs2) > 254:
            raise ValueError("UCS2 encoded name too long")
        return bytes([0x80]) + ucs2

    @classmethod
    def _can_encode_gsm7(cls, text: str) -> bool:
        for char in text:
            if char in cls._GSM7_DEFAULT:
                continue
            if char in cls._GSM7_EXTENSION:
                continue
            return False
        return True

    @classmethod
    def _encode_gsm7_unpacked(cls, text: str) -> bytes:
        out: list[int] = []
        for char in text:
            if char in cls._GSM7_DEFAULT:
                out.append(cls._GSM7_DEFAULT[char])
                continue
            if char in cls._GSM7_EXTENSION:
                out.append(0x1B)
                out.append(cls._GSM7_EXTENSION[char])
                continue
            raise ValueError(f"character {char!r} is not GSM7 encodable")
        return bytes(out)

    @classmethod
    def _encode_number(
        cls,
        number: str,
        ton: int | None = None,
        npi: int | None = None,
    ) -> tuple[int, int, list[int]]:
        cleaned = number.strip()
        if not cleaned:
            raise ValueError("number must not be empty")

        digits = cleaned
        if digits.startswith("+"):
            digits = digits[1:]

        if ton is None:
            ton = 1 if cleaned.startswith("+") else 0
        if npi is None:
            npi = 1
        if ton < 0 or ton > 7:
            raise ValueError(f"ton must be in [0, 7], got {ton}")
        if npi < 0 or npi > 15:
            raise ValueError(f"npi must be in [0, 15], got {npi}")

        ton_npi = 0x80 | ((ton & 0x07) << 4) | (npi & 0x0F)

        if not digits:
            raise ValueError("number must contain at least one dialable character")

        for char in digits:
            if char not in cls._BCD_CHAR_TO_NIBBLE:
                raise ValueError(
                    "number supports digits and these symbols only: * # p w e"
                )

        if len(digits) > 20:
            raise ValueError("number too long for ADN record (max 20 symbols)")

        nibbles = [cls._BCD_CHAR_TO_NIBBLE[char] for char in digits]
        octets: list[int] = []
        cursor = 0
        while cursor < len(nibbles):
            low = nibbles[cursor]
            high = 0x0F
            if cursor + 1 < len(nibbles):
                high = nibbles[cursor + 1]
            octets.append((high << 4) | low)
            cursor += 2

        number_length = 1 + len(octets)
        bcd_field = octets + [0xFF] * (10 - len(octets))
        return number_length, ton_npi, bcd_field

    @staticmethod
    def _encode_pin_data(pin: str) -> list[int]:
        cleaned = pin.strip()
        if len(cleaned) < 4 or len(cleaned) > 8:
            raise ValueError("PIN must be 4-8 digits (0-9 only)")
        if not all("0" <= ch <= "9" for ch in cleaned):
            raise ValueError("PIN must be 4-8 digits (0-9 only)")

        return [ord(ch) for ch in cleaned] + [0xFF] * (8 - len(cleaned))

    def _read_ext1_chain(self, first_record: int) -> bytes:
        assert self._ext1_layout is not None
        payload_start = 2
        next_offset = self._ext1_layout.record_length - 1
        payload_capacity = next_offset - payload_start
        if payload_capacity <= 0:
            return b""

        current = first_record
        visited: set[int] = set()
        data = bytearray()

        while current not in (0x00, 0xFF):
            if current in visited:
                raise RuntimeError("EXT1 chain loop detected")
            if current < 1 or current > self._ext1_layout.record_count:
                raise RuntimeError("EXT1 pointer outside valid record range")

            visited.add(current)
            record = self._read_ext1_record(current)
            if not record or record[0] not in (0x01, 0x02):
                break

            length = min(record[1], payload_capacity)
            data.extend(record[payload_start : payload_start + length])
            current = record[next_offset]

        return bytes(data)

    def _clear_ext1_chain(self, first_record: int) -> None:
        assert self._ext1_layout is not None
        next_offset = self._ext1_layout.record_length - 1
        current = first_record
        visited: set[int] = set()

        while current not in (0x00, 0xFF):
            if current in visited:
                break
            if current < 1 or current > self._ext1_layout.record_count:
                break

            visited.add(current)
            record = self._read_ext1_record(current)
            nxt = record[next_offset] if len(record) > next_offset else 0xFF
            self._update_ext1_record(current, [0xFF] * self._ext1_layout.record_length)
            current = nxt

    def _write_ext1_chain(self, payload: bytes) -> int:
        assert self._ext1_layout is not None
        if not payload:
            return 0xFF

        payload_start = 2
        next_offset = self._ext1_layout.record_length - 1
        payload_capacity = next_offset - payload_start
        if payload_capacity <= 0:
            raise RuntimeError("EXT1 record length too small")

        all_records = [
            self._read_ext1_record(index)
            for index in range(1, self._ext1_layout.record_count + 1)
        ]
        needed = (len(payload) + payload_capacity - 1) // payload_capacity

        free_slots: list[int] = []
        for index, record in enumerate(all_records, start=1):
            if not record or record[0] in (0x00, 0xFF):
                free_slots.append(index)
                if len(free_slots) == needed:
                    break

        if len(free_slots) < needed:
            raise RuntimeError("not enough free EXT1 records for name overflow")

        cursor = 0
        for chain_index, slot in enumerate(free_slots):
            chunk = payload[cursor : cursor + payload_capacity]
            cursor += len(chunk)
            nxt = 0xFF
            if chain_index + 1 < len(free_slots):
                nxt = free_slots[chain_index + 1]

            record = [0xFF] * self._ext1_layout.record_length
            record[0] = 0x02
            record[1] = len(chunk)
            record[payload_start : payload_start + len(chunk)] = chunk
            record[next_offset] = nxt
            self._update_ext1_record(slot, record)

        return free_slots[0]
