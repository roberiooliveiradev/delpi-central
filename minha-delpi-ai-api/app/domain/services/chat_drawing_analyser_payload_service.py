"""Desembrulho canônico do payload `/analyser` a partir de tool calls."""

from __future__ import annotations

import json
from typing import Any


class ChatDrawingAnalyserPayloadService:
    @classmethod
    def flatten_guide_rows(cls, guide_items: list) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for item in guide_items:
            if not isinstance(item, dict):
                continue

            product_code = str(item.get("product_code") or "?").strip()
            bom_level = item.get("bom_level", 0)
            operations = item.get("operations")

            if not isinstance(operations, list) or not operations:
                op_desc = str(item.get("operation_description") or "").strip()

                if not op_desc:
                    continue

                rows.append(
                    {
                        "product_code": product_code,
                        "bom_level": bom_level,
                        "operation_code": item.get("operation_code") or "",
                        "operation_description": op_desc,
                        "work_center": item.get("work_center") or "",
                    }
                )
                continue

            for operation in operations:
                if not isinstance(operation, dict):
                    continue

                op_desc = str(operation.get("operation_description") or "").strip()

                if not op_desc:
                    continue

                rows.append(
                    {
                        "product_code": product_code,
                        "bom_level": bom_level,
                        "operation_code": operation.get("operation_code") or "",
                        "operation_description": op_desc,
                        "work_center": operation.get("work_center") or "",
                    }
                )

        return rows

    @classmethod
    def resolve_root_from_data(cls, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            return {}

        from app.domain.services.external_actions.external_action_result_presenter import (
            ExternalActionResultPresenter,
        )

        presenter = ExternalActionResultPresenter()
        root = presenter._unwrap_data(data)

        if not isinstance(root, dict):
            return {}

        return presenter._normalize_analyser_root(root)

    @classmethod
    def resolve_root_from_tool_call(
        cls,
        tool_call: dict[str, Any] | None,
        *,
        external_action_data: Any = None,
    ) -> dict[str, Any]:
        if external_action_data is not None:
            root = cls.resolve_root_from_data(external_action_data)

            if root:
                return root

        if not isinstance(tool_call, dict):
            return {}

        metadata = tool_call.get("metadata") if isinstance(tool_call.get("metadata"), dict) else {}
        data = tool_call.get("data")

        if data is None:
            data = metadata.get("authorizedResult")

        if data is None:
            preview = str(metadata.get("responsePreview") or "").strip()

            if preview:
                try:
                    data = json.loads(preview)
                except json.JSONDecodeError:
                    data = None

        return cls.resolve_root_from_data(data)
