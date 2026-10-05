"""Chave fiscal de 44 dígitos. NF-e usa modelo 55; CT-e usa modelo 57.

O dígito verificador é o mesmo algoritmo da NF-e. Extrair aqui evita uma segunda
implementação no adapter do CT-e sem mudar o resultado da NF-e.
"""

from __future__ import annotations

_WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9)


def access_key_digits(value: str) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def access_key_check_digit_ok(digits: str) -> bool:
    if len(digits) != 44 or not digits.isdigit():
        return False
    total = sum(int(digit) * _WEIGHTS[index % 8] for index, digit in enumerate(reversed(digits[:43])))
    remainder = total % 11
    expected = 0 if remainder < 2 else 11 - remainder
    return digits[43] == str(expected)


def access_key_model(digits: str) -> str:
    return digits[20:22] if len(digits) >= 22 else ""


def access_key_cnpj(digits: str) -> str:
    return digits[6:20] if len(digits) >= 20 else ""


def access_key_series(digits: str) -> str:
    return digits[22:25] if len(digits) >= 25 else ""


def access_key_number(digits: str) -> str:
    return digits[25:34] if len(digits) >= 34 else ""
