"""Resposta direta formatada a partir de tools internas da plataforma (bypass LLM)."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_platform_internal_tools_service import (
    ChatPlatformInternalToolsService,
)
from app.domain.services.chat_platform_tools_content_service import (
    ChatPlatformToolsContentService,
)


class ChatPlatformToolDirectAnswerService:
    @classmethod
    def format(
        cls,
        tool_name: str,
        *,
        data: Any,
        metadata: dict | None = None,
        message: str = "",
    ) -> str | None:
        del message

        if not ChatPlatformInternalToolsService.is_direct_answer_tool(tool_name):
            return None

        if tool_name == "get_allowed_routes":
            return cls._format_routes(data, metadata=metadata)

        if tool_name == "get_allowed_apps":
            return cls._format_apps(data, metadata=metadata)

        if tool_name == "get_current_user":
            return cls._format_current_user(data)

        return None

    @classmethod
    def _format_routes(cls, data: Any, *, metadata: dict | None) -> str | None:
        routes = data if isinstance(data, list) else []

        if not routes:
            return ChatPlatformToolsContentService.get(
                "directAnswer",
                "routes",
                "empty",
            )

        lines: list[str] = []
        count = int((metadata or {}).get("count") or len(routes))
        lines.append(
            ChatPlatformToolsContentService.format(
                "directAnswer",
                "routes",
                "title",
                default="**Rotas autorizadas ({count}):**",
                count=str(count),
            )
        )
        lines.append("")

        for route in routes:
            if not isinstance(route, dict):
                continue

            path = str(route.get("path") or "").strip()
            if not path:
                continue

            label = str(route.get("label") or "").strip()
            app_name = str(route.get("appName") or route.get("appId") or "").strip()

            if label:
                lines.append(
                    ChatPlatformToolsContentService.format(
                        "directAnswer",
                        "routes",
                        "lineWithLabel",
                        default="- `{path}` — {label} ({appName})",
                        path=path,
                        label=label,
                        appName=app_name or "app",
                    )
                )
            else:
                lines.append(
                    ChatPlatformToolsContentService.format(
                        "directAnswer",
                        "routes",
                        "linePathOnly",
                        default="- `{path}` ({appName})",
                        path=path,
                        appName=app_name or "app",
                    )
                )

        if not lines or len(lines) <= 2:
            return ChatPlatformToolsContentService.get(
                "directAnswer",
                "routes",
                "empty",
            )

        if (metadata or {}).get("truncated"):
            total = count
            shown = len(routes)
            lines.append("")
            lines.append(
                ChatPlatformToolsContentService.format(
                    "directAnswer",
                    "routes",
                    "truncatedNotice",
                    default="_Mostrando as primeiras {shown} de {total} rotas._",
                    shown=str(shown),
                    total=str(total),
                )
            )

        return "\n".join(lines).strip()

    @classmethod
    def _format_apps(cls, data: Any, *, metadata: dict | None) -> str | None:
        apps = data if isinstance(data, list) else []

        if not apps:
            return ChatPlatformToolsContentService.get(
                "directAnswer",
                "apps",
                "empty",
            )

        lines: list[str] = []
        count = int((metadata or {}).get("count") or len(apps))
        lines.append(
            ChatPlatformToolsContentService.format(
                "directAnswer",
                "apps",
                "title",
                default="**Aplicativos autorizados ({count}):**",
                count=str(count),
            )
        )
        lines.append("")

        for app in apps:
            if not isinstance(app, dict):
                continue

            name = str(app.get("name") or app.get("id") or "").strip()
            if not name:
                continue

            base_path = str(app.get("basePath") or "").strip()
            route_count = int(app.get("routeCount") or 0)

            if base_path:
                lines.append(
                    ChatPlatformToolsContentService.format(
                        "directAnswer",
                        "apps",
                        "line",
                        default="- **{name}** — `{basePath}` ({routeCount} rota(s))",
                        name=name,
                        basePath=base_path,
                        routeCount=str(route_count),
                    )
                )
            else:
                lines.append(
                    ChatPlatformToolsContentService.format(
                        "directAnswer",
                        "apps",
                        "lineWithoutBasePath",
                        default="- **{name}** ({routeCount} rota(s))",
                        name=name,
                        routeCount=str(route_count),
                    )
                )

        if len(lines) <= 2:
            return ChatPlatformToolsContentService.get(
                "directAnswer",
                "apps",
                "empty",
            )

        if (metadata or {}).get("truncated"):
            total = count
            shown = len(apps)
            lines.append("")
            lines.append(
                ChatPlatformToolsContentService.format(
                    "directAnswer",
                    "apps",
                    "truncatedNotice",
                    default="_Mostrando os primeiros {shown} de {total} aplicativos._",
                    shown=str(shown),
                    total=str(total),
                )
            )

        return "\n".join(lines).strip()

    @classmethod
    def _format_current_user(cls, data: Any) -> str | None:
        if not isinstance(data, dict):
            return ChatPlatformToolsContentService.get(
                "directAnswer",
                "currentUser",
                "empty",
            )

        name = str(data.get("name") or "").strip()
        email = str(data.get("email") or "").strip()
        is_superadmin = bool(data.get("isSuperadmin"))

        if not name and not email:
            return ChatPlatformToolsContentService.get(
                "directAnswer",
                "currentUser",
                "empty",
            )

        lines = [
            ChatPlatformToolsContentService.get(
                "directAnswer",
                "currentUser",
                "title",
            )
        ]

        if name:
            lines.append(
                ChatPlatformToolsContentService.format(
                    "directAnswer",
                    "currentUser",
                    "nameLine",
                    default="- **Nome:** {name}",
                    name=name,
                )
            )

        if email:
            lines.append(
                ChatPlatformToolsContentService.format(
                    "directAnswer",
                    "currentUser",
                    "emailLine",
                    default="- **Email:** {email}",
                    email=email,
                )
            )

        if is_superadmin:
            lines.append(
                ChatPlatformToolsContentService.get(
                    "directAnswer",
                    "currentUser",
                    "superadminLine",
                )
            )

        return "\n".join(lines).strip()
