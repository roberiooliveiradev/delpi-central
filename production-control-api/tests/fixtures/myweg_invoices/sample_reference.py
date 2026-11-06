"""Amostra de referência sanitizada — 05/11/2026.

Totais (22 itens · 10 NFs · 21 materiais · 3281 UN) são da amostra homologada,
nunca constantes de produção.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from production_control_app.domain.myweg_invoice_observations_contract import (
    decimal_to_canonical_str,
)

SAMPLE_DOCUMENT_DATE = "2026-11-05"
SAMPLE_RECORD_COUNT = 22
SAMPLE_DISTINCT_INVOICES = 10
SAMPLE_DISTINCT_MATERIALS = 21
SAMPLE_TOTAL_UN = Decimal("3281")
# SHA-256 do XLSX real homologado (evidência; fixture sanitizada tem hash próprio).
REAL_XLSX_SHA256 = (
    "600ffd4ce5bc26059eac2dd3ff19ad7a4852b7b300b0900a9ad1a372eb964d7e"
)

EMPTY_DOCUMENT_DATE = "2026-11-01"


def build_sample_2026_11_05_records() -> list[dict[str, Any]]:
    """22 linhas: 10 NFs, 21 materiais, soma 3281 UN (inclui 1 linha em MI)."""
    # 21 linhas UN + 1 linha MI (2 MI = 2000 UN) → restam 1281 UN nas outras 21.
    base_un = Decimal("61")  # 61 * 21 = 1281
    rows: list[dict[str, Any]] = []
    invoice_numbers = [f"000{1000 + i}" for i in range(10)]
    materials = [f"MAT-WEG-{i:04d}" for i in range(21)]

    # Linha 1: MI → 2 MI = 2000 UN
    rows.append(
        {
            "source_line_no": 2,
            "invoice_number": invoice_numbers[0],
            "invoice_series": "001",
            "material_weg": materials[0],
            "material_description": "Material amostra 0000",
            "quantity_original": "2",
            "source_unit": "MI",
            "quantity_un": "2000",
            "unit_comparability": "comparable",
            "departure_date": SAMPLE_DOCUMENT_DATE,
        }
    )

    # 21 linhas UN (materiais 0..20, mas material[0] já usado — reusa material[0]
    # na NF diferente para ficar com 21 materiais distintos no total:
    # materials[0] aparece 2x (MI + UN) → 21 distintos com indices 0..20.
    for index in range(21):
        invoice = invoice_numbers[index % 10]
        material = materials[index]
        rows.append(
            {
                "source_line_no": index + 3,
                "invoice_number": invoice,
                "invoice_series": "001" if index % 2 == 0 else "1",
                "material_weg": material,
                "material_description": f"Material amostra {index:04d}",
                "quantity_original": decimal_to_canonical_str(base_un),
                "source_unit": "UN",
                "quantity_un": decimal_to_canonical_str(base_un),
                "unit_comparability": "comparable",
                "departure_date": SAMPLE_DOCUMENT_DATE,
            }
        )

    assert len(rows) == SAMPLE_RECORD_COUNT
    total = sum(Decimal(str(r["quantity_un"])) for r in rows)
    assert total == SAMPLE_TOTAL_UN
    assert len({r["invoice_number"] for r in rows}) == SAMPLE_DISTINCT_INVOICES
    assert len({r["material_weg"] for r in rows}) == SAMPLE_DISTINCT_MATERIALS
    return rows


def build_validated_manifest(
    *,
    collection_id: str,
    document_date: str = SAMPLE_DOCUMENT_DATE,
    xlsx_name: str,
    sha256: str,
    record_count: int = SAMPLE_RECORD_COUNT,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "collection_id": collection_id,
        "origem": "MyWEG",
        "tipo_relatorio": "notas_fiscais_emitidas",
        "unidade_delpi": "02",
        "empresa_myweg": "1009",
        "centro": "1106",
        "fornecedor": "50471",
        "data_documento": document_date,
        "executado_em": "2026-11-06T06:15:00-03:00",
        "publicado_em_preparacao_utc": "2026-11-06T09:16:00+00:00",
        "arquivo_original": xlsx_name,
        "sha256": sha256,
        "tamanho_bytes": 4096,
        "quantidade_linhas": record_count,
        "quantidade_notas_fiscais_distintas": SAMPLE_DISTINCT_INVOICES,
        "quantidade_materiais_distintos": SAMPLE_DISTINCT_MATERIALS,
        "status_validacao": "VALIDADO",
        "publicacao_atomica": True,
        "contexto_obtido_dos_filtros": True,
    }


def build_empty_manifest(*, collection_id: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "collection_id": collection_id,
        "origem": "MyWEG",
        "tipo_relatorio": "notas_fiscais_emitidas",
        "unidade_delpi": "02",
        "empresa_myweg": "1009",
        "centro": "1106",
        "fornecedor": "50471",
        "data_documento": EMPTY_DOCUMENT_DATE,
        "publicado_em_preparacao_utc": "2026-11-02T09:16:00+00:00",
        "arquivo_original": None,
        "sha256": None,
        "tamanho_bytes": 0,
        "quantidade_linhas": 0,
        "quantidade_notas_fiscais_distintas": 0,
        "quantidade_materiais_distintos": 0,
        "status_validacao": "SEM_REGISTROS_SINALIZADOS_PELO_SAP",
        "tipo_snapshot": "SEM_REGISTROS",
        "sem_xlsx": True,
        "fonte_da_ausencia": "SAP WebGUI: mensagem de consulta sem registros",
        "publicacao_atomica": True,
        "contexto_obtido_dos_filtros": True,
    }
