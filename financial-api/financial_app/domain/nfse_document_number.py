"""Número operacional da NFS-e recebida do Questor.

A regra vale só para a proveniência Questor. O domínio de lançamento continua
recebendo um documento já com 9 posições e não trunca entradas maiores.
"""

from __future__ import annotations

import re

OPERATIONAL_NFSE_DIGITS = 9


class NfseDocumentNumberError(ValueError):
    """NumberNfse sem dígitos utilizáveis."""


def operational_nfse_number(provider_document_number: str | None) -> str:
    """Últimos 9 dígitos, com zeros à esquerda quando o original é mais curto.

    1830 → 000001830
    2600000002224 → 000002224
    2600000074919 → 000074919
    """

    digits = re.sub(r"\D", "", str(provider_document_number or ""))
    if not digits:
        raise NfseDocumentNumberError("A NFS-e não trouxe um número utilizável.")
    tail = digits[-OPERATIONAL_NFSE_DIGITS:]
    return tail.zfill(OPERATIONAL_NFSE_DIGITS)
