from __future__ import annotations

from copy import deepcopy
from typing import Any

from app.domain.propostas_comerciais.services.proposta_comercial_formatter import (
    PropostaComercialFormatter,
)

_ALLOWED_NESTED_FIELDS: dict[str, frozenset[str]] = {
    "contato": frozenset({"nome", "departamento", "email", "telefone"}),
    "condicoes": frozenset({"descricao", "icms", "ipi", "frete", "embalagem"}),
    "vendedor": frozenset({"nome", "cargo", "email", "telefone"}),
}


class PropostaComercialPdfExportOverridesService:
    @staticmethod
    def apply(detail: dict[str, Any], overrides: dict[str, Any] | None) -> dict[str, Any]:
        if not overrides:
            return detail

        result = deepcopy(detail)

        if "observacoes" in overrides and overrides["observacoes"] is not None:
            result["observacoes"] = PropostaComercialFormatter.normalize_observacoes(
                overrides["observacoes"]
            )

        for section, allowed_fields in _ALLOWED_NESTED_FIELDS.items():
            section_overrides = overrides.get(section)
            if not isinstance(section_overrides, dict):
                continue

            current = result.get(section)
            if not isinstance(current, dict):
                current = {}
                result[section] = current

            for field, value in section_overrides.items():
                if field not in allowed_fields or value is None:
                    continue
                current[field] = str(value).strip() if isinstance(value, str) else value

        return result
