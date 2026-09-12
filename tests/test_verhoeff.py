"""
Unit Tests for the Verhoeff Checksum Algorithm.
"""

import pytest
from app.core.verhoeff import (
    validate_verhoeff,
    compute_checksum,
    generate_demo_aadhaar,
    format_aadhaar,
)


def test_verhoeff_generation_and_validation():
    # Test generation of multiple demo Aadhaar numbers
    for _ in range(20):
        vid = generate_demo_aadhaar(prefix="0000")
        assert len(vid) == 12
        assert vid.startswith("0000")
        assert validate_verhoeff(vid) is True


def test_verhoeff_single_digit_corruption():
    vid = generate_demo_aadhaar()
    assert validate_verhoeff(vid) is True

    # Corrupt a digit
    digits = list(vid)
    orig_digit = digits[5]
    new_digit = str((int(orig_digit) + 1) % 10)
    digits[5] = new_digit
    corrupted_vid = "".join(digits)

    # Verhoeff must detect any single-digit replacement error
    assert validate_verhoeff(corrupted_vid) is False


def test_verhoeff_transposition_error():
    # Verhoeff detects all adjacent transposition errors
    vid = generate_demo_aadhaar()
    digits = list(vid)
    # Find two adjacent different digits
    idx = -1
    for i in range(len(digits) - 1):
        if digits[i] != digits[i + 1]:
            idx = i
            break

    if idx != -1:
        digits[idx], digits[idx + 1] = digits[idx + 1], digits[idx]
        transposed = "".join(digits)
        assert validate_verhoeff(transposed) is False


def test_format_aadhaar():
    raw = "000012345678"
    assert format_aadhaar(raw, mask=False) == "0000-1234-5678"
    assert format_aadhaar(raw, mask=True) == "XXXX-XXXX-5678"
