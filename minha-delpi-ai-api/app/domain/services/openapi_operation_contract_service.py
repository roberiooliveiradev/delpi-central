"""Contratos operationId → entity/shape sincronizados do api-delpi."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


class OpenApiOperationContractService:
    @classmethod
    @lru_cache(maxsize=1)
    def _contracts(cls) -> dict[str, dict[str, str]]:
        path = (
            Path(__file__).resolve().parents[2]
            / "content"
            / "pt-BR"
            / "assistant"
            / "openapi_operation_contracts.json"
        )

        if not path.is_file():
            return {}

        payload = json.loads(path.read_text(encoding="utf-8"))

        if not isinstance(payload, dict):
            return {}

        return {
            str(operation_id).strip(): {
                "entity": str(contract.get("entity") or "").strip(),
                "shape": str(contract.get("shape") or "").strip(),
            }
            for operation_id, contract in payload.items()
            if isinstance(contract, dict)
            and str(operation_id).strip()
            and str(contract.get("entity") or "").strip()
            and str(contract.get("shape") or "").strip()
        }

    @classmethod
    def contract_for_operation(cls, operation_id: str | None) -> dict[str, str] | None:
        token = str(operation_id or "").strip()

        if not token:
            return None

        contract = cls._contracts().get(token)

        return dict(contract) if contract else None

    @classmethod
    def contract_for_entity(cls, entity: str | None) -> dict[str, str] | None:
        token = str(entity or "").strip()

        if not token:
            return None

        for contract in cls._contracts().values():
            if contract.get("entity") == token:
                return dict(contract)

        return None

    @classmethod
    def shape_for_entity(cls, entity: str | None) -> str | None:
        contract = cls.contract_for_entity(entity)

        if not contract:
            return None

        shape = str(contract.get("shape") or "").strip()

        return shape or None

    @classmethod
    def shape_for_operation(cls, operation_id: str | None) -> str | None:
        contract = cls.contract_for_operation(operation_id)

        if not contract:
            return None

        shape = str(contract.get("shape") or "").strip()

        return shape or None
