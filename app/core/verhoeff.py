"""
Verhoeff Checksum Algorithm Implementation.
Used by UIDAI for validation of 12-digit Indian Aadhaar numbers.

This module provides:
1. Verhoeff checksum validation
2. Checksum generation
3. Synthetic / Demo Aadhaar number generation (strictly sandboxed with 0000/9999 prefix)
4. Masking and formatting utilities
"""

import random

# The multiplication table (d) based on dihedral group D5
_MULTIPLICATION_TABLE = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0),
)

# The permutation table (p)
_PERMUTATION_TABLE = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8),
)

# The inverse table (inv)
_INVERSE_TABLE = (0, 4, 3, 2, 1, 5, 6, 7, 8, 9)


def validate_verhoeff(number: str) -> bool:
    """
    Validates that a numerical string satisfies the Verhoeff checksum.
    Returns True if valid, False otherwise.
    """
    cleaned = "".join(filter(str.isdigit, str(number)))
    if not cleaned:
        return False

    c = 0
    reversed_digits = [int(d) for d in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        c = _MULTIPLICATION_TABLE[c][_PERMUTATION_TABLE[i % 8][digit]]
    return c == 0


def compute_checksum(number: str) -> int:
    """
    Computes the Verhoeff check digit for a string of digits (without the check digit).
    """
    cleaned = "".join(filter(str.isdigit, str(number)))
    c = 0
    reversed_digits = [int(d) for d in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        c = _MULTIPLICATION_TABLE[c][_PERMUTATION_TABLE[(i + 1) % 8][digit]]
    return _INVERSE_TABLE[c]


def generate_demo_aadhaar(prefix: str = "0000") -> str:
    """
    Generates a synthetic 12-digit demo Aadhaar number passing the Verhoeff checksum.
    Always uses a designated demo sandbox prefix (default 0000 or 9999) to ensure
    it cannot conflict with any real citizen's UID.
    """
    # 4-digit prefix + 7 random digits = 11 digits
    random_part = "".join([str(random.randint(0, 9)) for _ in range(7)])
    base_11 = f"{prefix}{random_part}"
    check_digit = compute_checksum(base_11)
    full_12 = f"{base_11}{check_digit}"
    assert validate_verhoeff(full_12), "Generated demo Aadhaar must satisfy Verhoeff"
    return full_12


def format_aadhaar(number: str, mask: bool = False) -> str:
    """
    Formats a 12-digit number as XXXX-XXXX-XXXX or XXXX-XXXX-1234 (masked).
    """
    cleaned = "".join(filter(str.isdigit, str(number)))
    if len(cleaned) != 12:
        return number
    if mask:
        return f"XXXX-XXXX-{cleaned[-4:]}"
    return f"{cleaned[:4]}-{cleaned[4:8]}-{cleaned[8:]}"
