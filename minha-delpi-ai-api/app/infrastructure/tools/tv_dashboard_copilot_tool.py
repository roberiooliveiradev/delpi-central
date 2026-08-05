"""Tool: preview/apply TvCopilotPatchV1 no TV Dashboard BFF."""

from __future__ import annotations

from app.application.security.chat_permissions import CHAT_TOOLS_USE_PERMISSION
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.tool_exceptions import InvalidToolInputError
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.infrastructure.gateways.tv_dashboard_api_gateway import TvDashboardApiGateway


class TvDashboardCopilotTool(InternalToolPort):
    name = "tv_dashboard_copilot"
    description = str(
        ChatAssistantContentService.get(
            "tv_dashboard_copilot_intent",
            "toolDescription",
        )
        or ""
    )
    required_permission = CHAT_TOOLS_USE_PERMISSION

    def __init__(self, gateway: TvDashboardApiGateway | None = None) -> None:
        self.gateway = gateway or TvDashboardApiGateway()

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        mode = str(arguments.get("mode") or "preview").strip().lower()
        if mode not in {"preview", "apply"}:
            raise InvalidToolInputError("mode must be preview or apply")

        target = arguments.get("target")
        ops = arguments.get("ops")
        if not isinstance(ops, list) or not ops:
            raise InvalidToolInputError("ops is required (non-empty list)")
        if target is not None and not isinstance(target, dict):
            raise InvalidToolInputError("target must be an object")

        envelope = {
            "target": target if isinstance(target, dict) else {},
            "ops": ops,
        }

        if not access_token:
            raise InvalidToolInputError("access_token is required")

        if mode == "preview":
            include_fp = arguments.get("includeFingerprint")
            payload = self.gateway.preview_patch(
                envelope,
                access_token=access_token,
                include_fingerprint=True if include_fp is None else bool(include_fp),
            )
        else:
            payload = self.gateway.apply_patch(envelope, access_token=access_token)

        http_ok = bool(payload.get("_ok", True))
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        # Envelope TV usa { ok, data, message } via core.responses.ok
        if isinstance(payload.get("data"), dict) and "appliedOps" in payload["data"]:
            data = payload["data"]
        elif isinstance(payload.get("data"), dict) and payload.get("ok") is not None:
            data = payload["data"]

        return ToolResult(
            name=self.name,
            data=data if isinstance(data, dict) else {"result": data},
            metadata={
                "ok": http_ok and bool((data or {}).get("ok", http_ok)),
                "mode": mode,
                "path": f"/data/copilot/{mode}-patch",
                "sensitivity": "write" if mode == "apply" else "read",
                "httpStatus": payload.get("_httpStatus"),
                "persisted": (data or {}).get("persisted") if isinstance(data, dict) else None,
            },
        )
