"""Gate de integridade do contrato executável do catálogo do Copiloto TV."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)


class TvCopilotCatalogAuditService:
    CONTRACT_FIELDS = frozenset(
        {
            "requiresPlaylist",
            "requiresSlide",
            "risk",
            "confirmationPolicy",
            "sideEffectHints",
            "inputSchema",
        }
    )

    @classmethod
    def errors(cls) -> list[str]:
        errors: list[str] = []
        operations = TvCopilotContentService.operations()
        referenced: set[str] = set()

        for capability in TvCopilotContentService.capabilities():
            key = str(capability.get("key") or capability.get("op") or "?")
            duplicated = cls.CONTRACT_FIELDS.intersection(capability)
            if duplicated:
                errors.append(
                    f"capability {key}: contrato duplicado ({', '.join(sorted(duplicated))})"
                )
            referenced.update(cls._template_ops(capability))

        for op_name in sorted(referenced):
            spec = operations.get(op_name)
            if not isinstance(spec, dict):
                errors.append(f"op {op_name}: spec ausente")
                continue
            missing = cls.CONTRACT_FIELDS.difference(spec)
            if missing:
                errors.append(
                    f"op {op_name}: campos ausentes ({', '.join(sorted(missing))})"
                )
            if spec.get("risk") not in {"additive", "mutation", "destructive"}:
                errors.append(f"op {op_name}: risk inválido")
            if spec.get("confirmationPolicy") not in {"direct", "confirm"}:
                errors.append(f"op {op_name}: confirmationPolicy inválida")

        unreferenced = set(operations).difference(referenced)
        for op_name in sorted(unreferenced):
            errors.append(f"op {op_name}: nenhuma capability referencia a spec")
        return errors

    @classmethod
    def assert_valid(cls) -> None:
        errors = cls.errors()
        if errors:
            raise ValueError("Catálogo Copiloto TV inválido:\n- " + "\n- ".join(errors))

    @staticmethod
    def _template_ops(capability: dict[str, Any]) -> set[str]:
        names: set[str] = set()
        single = capability.get("payloadTemplate")
        if isinstance(single, dict) and single.get("op"):
            names.add(str(single["op"]))
        multi = capability.get("payloadTemplates")
        if isinstance(multi, list):
            for item in multi:
                if isinstance(item, dict) and item.get("op"):
                    names.add(str(item["op"]))
        op_name = str(capability.get("op") or "").strip()
        if op_name:
            names.add(op_name)
        return names
