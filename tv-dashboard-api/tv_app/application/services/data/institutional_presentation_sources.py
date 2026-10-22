"""Fontes cujo dado de apresentação já é institucional.

O editor só herda essa identidade depois que a programação persistida
autoriza a fonte. O operationId do body, sozinho, não entra neste conjunto.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

INSTITUTIONAL_PRESENTATION_OPERATIONS = frozenset({"get_helpdesk_dashboard_summary"})


def institutional_operations_from_configs(
    configs: list[dict[str, Any]],
) -> frozenset[str]:
    found: set[str] = set()
    for config in configs:
        if not isinstance(config, dict):
            continue
        for operation_id in _operation_ids(config):
            if operation_id in INSTITUTIONAL_PRESENTATION_OPERATIONS:
                found.add(operation_id)
    return frozenset(found)


def persisted_institutional_operations(
    playlist_id: UUID,
    *,
    repository: Any | None = None,
) -> frozenset[str]:
    from tv_app.infrastructure.persistence.repositories.playlist_repository import (
        PlaylistRepository,
    )

    repo = repository or PlaylistRepository()
    configs: list[dict[str, Any]] = []
    for slide in repo.list_slides(playlist_id):
        if not isinstance(slide, dict):
            continue
        config = slide.get("nativeConfig")
        if isinstance(config, dict):
            configs.append(config)
    return institutional_operations_from_configs(configs)


def _operation_ids(config: dict[str, Any]):
    blocks = config.get("blocks")
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict):
                continue
            binding = block.get("dataBinding")
            if isinstance(binding, dict):
                operation_id = str(binding.get("operationId") or "").strip()
                if operation_id:
                    yield operation_id
    models = config.get("dataModels")
    if isinstance(models, list):
        for model in models:
            if not isinstance(model, dict):
                continue
            inputs = model.get("inputs")
            if not isinstance(inputs, list):
                continue
            for item in inputs:
                if not isinstance(item, dict):
                    continue
                operation_id = str(item.get("operationId") or "").strip()
                if operation_id:
                    yield operation_id
