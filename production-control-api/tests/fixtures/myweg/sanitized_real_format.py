"""Fixture sanitizada no formato da planilha real MyWEG (amostra homologada).

Os totais 532 / 745746 UN são da **amostra de referência**, não restrições
permanentes para coletas futuras.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from production_control_app.domain.myweg_needs_contract import decimal_to_canonical_str

# Metadados da amostra (somente fixture / evidência).
SAMPLE_RECORD_COUNT = 532
SAMPLE_TOTAL_UN = Decimal("745746")
SAMPLE_TOTAL_MI = Decimal("745.746")
SAMPLE_REFS_STARTING_9 = 528
SAMPLE_REFS_STARTING_8 = 2
SAMPLE_REFS_EMPTY = 2


def build_sanitized_real_format_records(
    *,
    count: int = SAMPLE_RECORD_COUNT,
    total_un: Decimal = SAMPLE_TOTAL_UN,
) -> list[dict[str, Any]]:
    """Gera 532 linhas no shape real: quantidade, data_remessa, linha_fonte, assinatura_registro.

    Distribuição de ``codigo_referencia_weg``:
    - 528 iniciados em ``9``
    - 2 iniciados em ``8``
    - 2 vazios (``""``) — necessidades legítimas sem referência
    """
    if count != SAMPLE_RECORD_COUNT:
        raise ValueError("Fixture sanitizada fixa em 532 registros representativos.")
    if total_un != SAMPLE_TOTAL_UN:
        raise ValueError("Fixture sanitizada fixa no total UN da amostra homologada.")

    base = total_un // count
    remainder = total_un - (base * count)
    rows: list[dict[str, Any]] = []

    for index in range(count):
        qty = base + (remainder if index == count - 1 else Decimal("0"))
        if index < SAMPLE_REFS_STARTING_9:
            codigo: str | None = f"9{index:07d}"
        elif index < SAMPLE_REFS_STARTING_9 + SAMPLE_REFS_STARTING_8:
            codigo = f"8{index:07d}"
        else:
            codigo = ""

        rows.append(
            {
                "material_weg_tratado": f"MAT-WEG-SANIT-{index:04d}",
                "codigo_referencia_weg": codigo,
                "origem_material_weg": "MYWEG-ORIGEM",
                "quantidade": decimal_to_canonical_str(qty),
                "unidade": "UN",
                "data_remessa": "15/11/2026",
                "documento": f"DOC-{index:04d}" if index % 11 == 0 else None,
                "linha_fonte": index + 2,  # típico: cabeçalho na linha 1
                "assinatura_registro": f"sig-{index:04d}-{qty}",
            }
        )
    return rows


def summarize_codigo_referencia(records: list[dict[str, Any]]) -> dict[str, int]:
    start_9 = start_8 = empty = other = 0
    for row in records:
        code = row.get("codigo_referencia_weg")
        text = "" if code is None else str(code).strip()
        if text == "":
            empty += 1
        elif text.startswith("9"):
            start_9 += 1
        elif text.startswith("8"):
            start_8 += 1
        else:
            other += 1
    return {
        "start_9": start_9,
        "start_8": start_8,
        "empty": empty,
        "other": other,
    }
