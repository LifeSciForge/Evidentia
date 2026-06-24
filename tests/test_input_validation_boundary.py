"""
Tests for input validation boundary -- Task 2 of Stage 4 Security.

These tests verify the InputValidator contract that the UI now relies on.
Rules (from src/service/validators/input_validator.py):
  validate_drug_name:  non-empty, >=2 chars, not all digits,
                       only [A-Za-z0-9 space - . /] allowed
  validate_indication: non-empty, >=3 chars (no character restriction beyond strip)
"""
import pytest
from src.service.validators.input_validator import InputValidator


# ---------------------------------------------------------------------------
# validate_drug_name
# ---------------------------------------------------------------------------

def test_valid_drug_name_is_cleaned():
    assert InputValidator.validate_drug_name("  sotorasib  ") == "sotorasib"


def test_valid_drug_name_with_hyphen():
    assert InputValidator.validate_drug_name("BNT-111") == "BNT-111"


def test_valid_drug_name_with_slash():
    assert InputValidator.validate_drug_name("PD-1/L1 inhibitor") == "PD-1/L1 inhibitor"


def test_empty_drug_name_rejected():
    with pytest.raises(ValueError, match="required"):
        InputValidator.validate_drug_name("")


def test_whitespace_only_drug_name_rejected():
    # strip() → "" → len < 2
    with pytest.raises(ValueError):
        InputValidator.validate_drug_name("   ")


def test_single_char_drug_name_rejected():
    # min length is 2
    with pytest.raises(ValueError, match="at least 2"):
        InputValidator.validate_drug_name("x")


def test_all_digits_drug_name_rejected():
    with pytest.raises(ValueError, match="all digits"):
        InputValidator.validate_drug_name("12345")


def test_invalid_chars_in_drug_name_rejected():
    with pytest.raises(ValueError, match="invalid characters"):
        InputValidator.validate_drug_name("drug<script>")


def test_at_sign_in_drug_name_rejected():
    with pytest.raises(ValueError, match="invalid characters"):
        InputValidator.validate_drug_name("drug@name")


def test_two_char_drug_name_accepted():
    # Exactly 2 chars — should pass min-length check
    assert InputValidator.validate_drug_name("ab") == "ab"


# ---------------------------------------------------------------------------
# validate_indication
# ---------------------------------------------------------------------------

def test_valid_indication_is_cleaned():
    assert InputValidator.validate_indication("  KRAS G12C NSCLC ") == "KRAS G12C NSCLC"


def test_empty_indication_rejected():
    with pytest.raises(ValueError, match="required"):
        InputValidator.validate_indication("")


def test_too_short_indication_rejected():
    # min length is 3; "ab" has len 2
    with pytest.raises(ValueError, match="at least 3"):
        InputValidator.validate_indication("ab")


def test_exactly_3_char_indication_accepted():
    assert InputValidator.validate_indication("CRC") == "CRC"


def test_indication_allows_special_chars():
    # validate_indication has no character restriction beyond strip + length
    assert InputValidator.validate_indication("KRAS G12C (NSCLC)") == "KRAS G12C (NSCLC)"
