from __future__ import annotations

import re
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError

CRITERION_CODE_PATTERN = re.compile(r"^[A-Z]\d{2}$")


class CatalogPublishNoChangesError(Exception):
    """Payload idêntico ao catálogo ativo da filial."""


class CatalogPublishValidationError(PluginsRepositoryError):
    """Erro de validação do payload de publicação."""


def _normalize_description(value: str) -> str:
    return " ".join(value.strip().split())


def normalize_criteria_snapshot(criteria: list[dict[str, Any]]) -> tuple[tuple[Any, ...], ...]:
    normalized: list[tuple[Any, ...]] = []
    for item in criteria:
        normalized.append(
            (
                int(item["senso_order"]),
                int(item["sort_order"]),
                str(item["code"]).strip().upper(),
                _normalize_description(str(item["description"])),
            )
        )
    return tuple(sorted(normalized))


def normalize_senso_names_snapshot(
    senso_names: list[dict[str, Any]] | None,
) -> tuple[tuple[int, str], ...]:
    if not senso_names:
        return ()
    pairs = [
        (int(item["senso_sort_order"]), _normalize_description(str(item["name"])))
        for item in senso_names
    ]
    return tuple(sorted(pairs))


def validate_publish_payload(
    *,
    criteria: list[dict[str, Any]],
    senso_names: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if not criteria:
        raise CatalogPublishValidationError("Informe ao menos um critério.")

    normalized: list[dict[str, Any]] = []
    codes: set[str] = set()
    positions: set[tuple[int, int]] = set()
    sensos_present: set[int] = set()

    for index, raw in enumerate(criteria, start=1):
        try:
            senso_order = int(raw["senso_order"])
            sort_order = int(raw["sort_order"])
        except (KeyError, TypeError, ValueError) as exc:
            raise CatalogPublishValidationError(
                f"Critério #{index}: senso e ordem são obrigatórios."
            ) from exc

        if senso_order < 1 or senso_order > 5:
            raise CatalogPublishValidationError(
                f"Critério #{index}: senso deve estar entre 1 e 5."
            )
        if sort_order < 1:
            raise CatalogPublishValidationError(
                f"Critério #{index}: ordem deve ser maior que zero."
            )

        code = str(raw.get("code", "")).strip().upper()
        description = _normalize_description(str(raw.get("description", "")))

        if not CRITERION_CODE_PATTERN.match(code):
            raise CatalogPublishValidationError(
                f"Critério #{index}: código inválido ({code!r}). Use o padrão U01, O02, etc."
            )
        if len(description) < 3:
            raise CatalogPublishValidationError(
                f"Critério #{index}: descrição deve ter ao menos 3 caracteres."
            )
        if code in codes:
            raise CatalogPublishValidationError(
                f"Código duplicado no catálogo: {code}."
            )
        position = (senso_order, sort_order)
        if position in positions:
            raise CatalogPublishValidationError(
                f"Ordem duplicada no senso {senso_order}: posição {sort_order}."
            )

        codes.add(code)
        positions.add(position)
        sensos_present.add(senso_order)
        normalized.append(
            {
                "senso_order": senso_order,
                "sort_order": sort_order,
                "code": code,
                "description": description,
            }
        )

    missing_sensos = {1, 2, 3, 4, 5} - sensos_present
    if missing_sensos:
        missing = ", ".join(str(item) for item in sorted(missing_sensos))
        raise CatalogPublishValidationError(
            f"Cada senso deve ter ao menos um critério. Faltando: {missing}."
        )

    if senso_names:
        seen_orders: set[int] = set()
        for item in senso_names:
            try:
                order = int(item["senso_sort_order"])
            except (KeyError, TypeError, ValueError) as exc:
                raise CatalogPublishValidationError(
                    "Nome de senso inválido no payload."
                ) from exc
            if order < 1 or order > 5:
                raise CatalogPublishValidationError(
                    "Nome de senso deve referenciar sensos entre 1 e 5."
                )
            name = _normalize_description(str(item.get("name", "")))
            if len(name) < 2:
                raise CatalogPublishValidationError(
                    f"Nome do senso {order} deve ter ao menos 2 caracteres."
                )
            if order in seen_orders:
                raise CatalogPublishValidationError(
                    f"Nome duplicado para o senso {order}."
                )
            seen_orders.add(order)

    return normalized


def catalogs_are_equal(
    *,
    current_criteria: list[dict[str, Any]],
    next_criteria: list[dict[str, Any]],
    current_senso_names: list[dict[str, Any]] | None,
    next_senso_names: list[dict[str, Any]] | None,
) -> bool:
    current_snapshot = normalize_criteria_snapshot(current_criteria)
    next_snapshot = normalize_criteria_snapshot(next_criteria)
    if current_snapshot != next_snapshot:
        return False
    return normalize_senso_names_snapshot(current_senso_names) == normalize_senso_names_snapshot(
        next_senso_names
    )
