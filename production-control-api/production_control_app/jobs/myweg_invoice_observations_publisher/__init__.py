"""Publicador one-shot MyWEG NF Emitidas → Production Control (Etapa 1)."""

from __future__ import annotations

EXPECTED_HEADERS = (
    "Nº nota fiscal",
    "Séries",
    "Material",
    "Texto breve de material",
    "Quantidade",
    "Unidade de medida",
    "Data de Saída",
)

DEFAULT_INVOICE_ROOT = (
    "/home/michael/.local/share/MyWEG-Automacao/notas-fiscais/"
    "filial-02/empresa-1009/centro-1106/fornecedor-50471"
)

__all__ = ["EXPECTED_HEADERS", "DEFAULT_INVOICE_ROOT"]
