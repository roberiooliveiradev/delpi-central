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
_ITEM_TEXT_FIELDS = frozenset({"descricao", "referencia_cliente", "ncm"})
_ROTULO_COLUNAS_KEYS = frozenset(
    {
        "item",
        "produto",
        "descricao",
        "referencia_cliente",
        "ncm",
        "quantidade",
        "valor_bruto",
        "valor_liquido",
        "total",
        "prazo",
        "lote_minimo",
    }
)
_ROTULO_RESUMO_KEYS = frozenset(
    {"numero_ov", "data", "versao", "total_r_mil", "empresa", "cliente"}
)


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

        if "exibir_coluna_valor_liquido" in overrides:
            value = overrides["exibir_coluna_valor_liquido"]
            result["exibir_coluna_valor_liquido"] = True if value is None else bool(value)

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

        PropostaComercialPdfExportOverridesService._apply_item_text_overrides(
            result,
            overrides.get("itens"),
        )
        PropostaComercialPdfExportOverridesService._apply_rotulos(
            result,
            overrides.get("rotulos"),
        )

        return result

    @staticmethod
    def _apply_item_text_overrides(
        result: dict[str, Any],
        item_overrides: Any,
    ) -> None:
        if not isinstance(item_overrides, list):
            return

        overrides_by_item: dict[str, dict[str, Any]] = {}
        for override in item_overrides:
            if not isinstance(override, dict):
                continue
            item_key = str(override.get("item") or "").strip()
            if not item_key:
                continue
            overrides_by_item[item_key] = override

        if not overrides_by_item:
            return

        current_items = result.get("itens")
        if not isinstance(current_items, list):
            return

        for item in current_items:
            if not isinstance(item, dict):
                continue
            item_key = str(item.get("item") or "").strip()
            override = overrides_by_item.get(item_key)
            if not override:
                continue

            for field in _ITEM_TEXT_FIELDS:
                if field not in override or override[field] is None:
                    continue
                value = override[field]
                item[field] = str(value).strip() if isinstance(value, str) else value

    @staticmethod
    def _apply_rotulos(result: dict[str, Any], rotulos: Any) -> None:
        if not isinstance(rotulos, dict):
            return

        current = result.setdefault("rotulos", {})
        if not isinstance(current, dict):
            current = {}
            result["rotulos"] = current

        colunas = rotulos.get("colunas_itens")
        if isinstance(colunas, dict):
            target_colunas = current.setdefault("colunas_itens", {})
            if not isinstance(target_colunas, dict):
                target_colunas = {}
                current["colunas_itens"] = target_colunas
            for field, value in colunas.items():
                if field not in _ROTULO_COLUNAS_KEYS or value is None:
                    continue
                target_colunas[field] = str(value).strip() if isinstance(value, str) else value

        resumo = rotulos.get("resumo")
        if isinstance(resumo, dict):
            target_resumo = current.setdefault("resumo", {})
            if not isinstance(target_resumo, dict):
                target_resumo = {}
                current["resumo"] = target_resumo
            for field, value in resumo.items():
                if field not in _ROTULO_RESUMO_KEYS or value is None:
                    continue
                target_resumo[field] = str(value).strip() if isinstance(value, str) else value

        if "total_proposta" in rotulos and rotulos["total_proposta"] is not None:
            current["total_proposta"] = str(rotulos["total_proposta"]).strip()
