"""Deprecated Chat tool — TV mutations moved to VISTA (gpt-actions).

Kept as an import-stable stub that refuses execution so residual shortlists
cannot silently call /data/copilot (410).
"""

from __future__ import annotations

from app.application.security.chat_permissions import CHAT_TOOLS_USE_PERMISSION
from app.domain.entities.tool_result import ToolResult
from app.domain.ports.internal_tool_port import InternalToolPort


_GONE_MESSAGE = (
    "A tool tv_dashboard_copilot foi desligada. "
    "Mutações de TV Dashboard usam o especialista VISTA "
    "(Custom GPT /gpt-actions: preview/commit) com PresentationMutation."
)


class TvDashboardCopilotTool(InternalToolPort):
    name = "tv_dashboard_copilot"
    required_permission = CHAT_TOOLS_USE_PERMISSION

    @property
    def description(self) -> str:
        return (
            "DEPRECATED — use VISTA gpt-actions for TV Dashboard presentation changes."
        )

    def execute(self, arguments: dict, access_token: str) -> ToolResult:
        return ToolResult(
            name=self.name,
            data={
                "ok": False,
                "gone": True,
                "message": _GONE_MESSAGE,
                "successor": "vista_gpt_actions",
                "mutationOwner": "PresentationMutation",
            },
            metadata={
                "ok": False,
                "gone": True,
                "mode": str((arguments or {}).get("mode") or "preview"),
                "path": "/data/copilot/*",
                "httpStatus": 410,
                "sensitivity": "read",
            },
        )
