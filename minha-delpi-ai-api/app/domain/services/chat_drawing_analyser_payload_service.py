"""Desembrulho canônico do payload `/analyser` a partir de tool calls."""

from __future__ import annotations

import json
from typing import Any


class ChatDrawingAnalyserPayloadService:
    @classmethod
    def resolve_root_from_tool_call(cls, tool_call: dict[str, Any] | None) -> dict[str, Any]:
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
