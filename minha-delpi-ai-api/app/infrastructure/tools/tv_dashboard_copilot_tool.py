"""Tool: preview/apply TvCopilotPatchV1 — persistência via CRUD HTTP /playlists."""

from __future__ import annotations

from typing import Any

from app.application.security.chat_permissions import CHAT_TOOLS_USE_PERMISSION
from app.domain.entities.tool_result import ToolResult
from app.domain.exceptions.tool_exceptions import InvalidToolInputError
from app.domain.ports.internal_tool_port import InternalToolPort
from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.infrastructure.gateways.tv_dashboard_api_gateway import TvDashboardApiGateway

_CREATE_PLAYLIST_OPS = frozenset({"create_playlist"})
_CREATE_SLIDE_OPS = frozenset({"add_blank_slide", "add_slide_from_preset"})


class TvDashboardCopilotTool(InternalToolPort):
    name = "tv_dashboard_copilot"
    required_permission = CHAT_TOOLS_USE_PERMISSION

    def __init__(self, gateway: TvDashboardApiGateway | None = None) -> None:
        self.gateway = gateway or TvDashboardApiGateway()

    @property
    def description(self) -> str:
        # Resolvido sob demanda: o import da tool acontece antes do wiring dos ports.
        return ChatAssistantContentService.get(
            "tv_dashboard_copilot_intent",
            "toolDescription",
        )

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

        include_fp = arguments.get("includeFingerprint")
        include_fingerprint = True if include_fp is None else bool(include_fp)

        if mode == "preview":
            payload = self.gateway.preview_patch(
                envelope,
                access_token=access_token,
                include_fingerprint=include_fingerprint,
            )
            return self._preview_result(payload)

        return self._apply_via_crud(
            envelope,
            access_token=access_token,
            include_fingerprint=include_fingerprint,
        )

    def _preview_result(self, payload: dict[str, Any]) -> ToolResult:
        http_ok = bool(payload.get("_ok", True))
        data = self._extract_plan_data(payload)
        return ToolResult(
            name=self.name,
            data=data if isinstance(data, dict) else {"result": data},
            metadata={
                "ok": http_ok and bool((data or {}).get("ok", http_ok)),
                "mode": "preview",
                "path": "/data/copilot/preview-patch",
                "sensitivity": "read",
                "httpStatus": payload.get("_httpStatus"),
                "persisted": (data or {}).get("persisted") if isinstance(data, dict) else None,
            },
        )

    def _apply_via_crud(
        self,
        envelope: dict[str, Any],
        *,
        access_token: str,
        include_fingerprint: bool,
    ) -> ToolResult:
        plan_payload = self.gateway.preview_patch(
            envelope,
            access_token=access_token,
            include_fingerprint=include_fingerprint,
        )
        plan_http_ok = bool(plan_payload.get("_ok", True))
        plan = self._extract_plan_data(plan_payload)

        if not plan_http_ok or not isinstance(plan, dict):
            return ToolResult(
                name=self.name,
                data={
                    "ok": False,
                    "persisted": False,
                    "message": "preview_patch failed; cannot execute CRUD plan",
                    "planHttpStatus": plan_payload.get("_httpStatus"),
                },
                metadata={
                    "ok": False,
                    "mode": "apply",
                    "path": "/playlists (crud)",
                    "sensitivity": "write",
                    "persisted": False,
                    "httpStatus": plan_payload.get("_httpStatus"),
                },
            )

        http_commands = plan.get("httpCommands")
        if not isinstance(http_commands, list) or not http_commands:
            return ToolResult(
                name=self.name,
                data={
                    "ok": False,
                    "persisted": False,
                    "target": plan.get("target"),
                    "message": "httpCommands missing or empty in preview plan",
                    "executionMode": plan.get("executionMode"),
                },
                metadata={
                    "ok": False,
                    "mode": "apply",
                    "path": "/playlists (crud)",
                    "sensitivity": "write",
                    "persisted": False,
                    "httpStatus": plan_payload.get("_httpStatus"),
                },
            )

        revision = plan.get("baseRevision")
        try:
            revision = int(revision) if revision is not None else None
        except (TypeError, ValueError):
            revision = None

        playlist_id: str | None = None
        slide_id: str | None = None
        target = plan.get("target") if isinstance(plan.get("target"), dict) else {}
        if target.get("playlistId") and not str(target["playlistId"]).startswith("{"):
            playlist_id = str(target["playlistId"])
        if target.get("slideId") and not str(target["slideId"]).startswith("{"):
            slide_id = str(target["slideId"])

        executed: list[dict[str, Any]] = []
        last_status: int | None = None
        all_ok = True
        error_message: str | None = None

        for raw_command in http_commands:
            if not isinstance(raw_command, dict):
                all_ok = False
                error_message = "invalid httpCommand entry (not an object)"
                break

            command = dict(raw_command)
            path = self._substitute_path_placeholders(
                str(command.get("path") or ""),
                playlist_id=playlist_id,
                slide_id=slide_id,
            )
            command["path"] = path
            op = str(command.get("op") or "")

            try:
                response = self.gateway.execute_crud_command(
                    command,
                    access_token=access_token,
                    expected_revision=revision,
                )
            except ValueError as exc:
                all_ok = False
                error_message = str(exc)
                executed.append(
                    {
                        "method": command.get("method"),
                        "path": path,
                        "status": None,
                        "op": op or None,
                        "error": error_message,
                    }
                )
                break

            status = response.get("_httpStatus")
            last_status = int(status) if isinstance(status, int) else status
            ok = bool(response.get("_ok"))
            executed.append(
                {
                    "method": command.get("method"),
                    "path": path,
                    "status": last_status,
                    "op": op or None,
                }
            )

            if not ok:
                all_ok = False
                error_message = self._response_error_message(response)
                break

            next_revision = response.get("playlistRevision")
            if next_revision is None:
                data = response.get("data")
                if isinstance(data, dict):
                    next_revision = data.get("playlistRevision")
            if next_revision is not None:
                try:
                    revision = int(next_revision)
                except (TypeError, ValueError):
                    pass

            created_id = self._extract_created_id(response)
            if created_id:
                if op in _CREATE_PLAYLIST_OPS:
                    playlist_id = created_id
                elif op in _CREATE_SLIDE_OPS:
                    slide_id = created_id

        data_out: dict[str, Any] = {
            "ok": all_ok,
            "persisted": all_ok,
            "target": {
                "playlistId": playlist_id or target.get("playlistId"),
                "slideId": slide_id or target.get("slideId"),
            },
            "httpCommands": executed,
            "executedRequests": executed,
            "revision": revision,
            "sideEffectHints": plan.get("sideEffectHints"),
            "message": (
                "CRUD plan applied"
                if all_ok
                else (error_message or "CRUD plan stopped on error")
            ),
        }
        if isinstance(plan.get("nativeConfig"), dict):
            data_out["nativeConfig"] = plan["nativeConfig"]
        if plan.get("sideEffects") is not None:
            data_out["sideEffects"] = plan.get("sideEffects")
        if plan.get("appliedOps") is not None:
            data_out["appliedOps"] = plan.get("appliedOps")

        return ToolResult(
            name=self.name,
            data=data_out,
            metadata={
                "ok": all_ok,
                "mode": "apply",
                "path": "/playlists (crud)",
                "sensitivity": "write",
                "persisted": all_ok,
                "httpStatus": last_status,
            },
        )

    @staticmethod
    def _extract_plan_data(payload: dict[str, Any]) -> dict[str, Any]:
        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if isinstance(payload.get("data"), dict):
            inner = payload["data"]
            if "appliedOps" in inner or "httpCommands" in inner or payload.get("ok") is not None:
                data = inner
        return data if isinstance(data, dict) else {"result": data}

    @staticmethod
    def _substitute_path_placeholders(
        path: str,
        *,
        playlist_id: str | None,
        slide_id: str | None,
    ) -> str:
        out = path
        if playlist_id:
            out = out.replace("{playlistId}", playlist_id)
        if slide_id:
            out = out.replace("{slideId}", slide_id)
        return out

    @staticmethod
    def _extract_created_id(response: dict[str, Any]) -> str | None:
        data = response.get("data")
        if not isinstance(data, dict):
            return None
        raw = data.get("id")
        if raw is None and isinstance(data.get("data"), dict):
            raw = data["data"].get("id")
        if raw is None:
            return None
        text = str(raw).strip()
        return text or None

    @staticmethod
    def _response_error_message(response: dict[str, Any]) -> str:
        for key in ("message", "detail", "error"):
            value = response.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        data = response.get("data")
        if isinstance(data, dict):
            for key in ("message", "detail", "error"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        status = response.get("_httpStatus")
        return f"CRUD request failed with HTTP {status}"
