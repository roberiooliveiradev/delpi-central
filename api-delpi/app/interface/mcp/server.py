"""FastMCP server exposing governed DAVI dynamic READ tools only."""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import CallToolResult, TextContent, Tool as MCPTool, ToolAnnotations
from pydantic import ValidationError

from app.application.external_capabilities.constants import (
    EXTERNAL_INTERNAL_ERROR_MESSAGE,
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_DISCOVER_DELPI_INFORMATION_TITLE,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION_TITLE,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    CandidateTokenError,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)
from app.composition.davi_dynamic_read_composer import execute_delpi_information_wired
from app.interface.mcp.branding import DAVI_MCP_INSTRUCTIONS
from app.interface.mcp.document_transport_spike import (
    document_transport_spike_enabled,
    register_document_transport_spike,
)
from app.interface.mcp.oauth_contract import (
    DAVI_MCP_SECURITY_SCHEMES,
    mcp_www_authenticate_meta,
)
from app.interface.mcp.resource_metadata import public_host_allowed_for_mcp
from app.interface.mcp.schemas import (
    DiscoverDelpiInformationInput,
    ExecuteDelpiInformationInput,
    discover_delpi_information_input_json_schema,
    discover_delpi_information_output_json_schema,
    execute_delpi_information_input_json_schema,
    execute_delpi_information_output_json_schema,
)
from app.utils.logger import log_error

__all__ = [
    "ApiDelpiFastMCP",
    "VALIDATION_ERROR_CODE",
    "VALIDATION_ERROR_MESSAGE",
    "create_mcp_server",
    "validation_error_tool_result",
]

logger = logging.getLogger(__name__)

VALIDATION_ERROR_CODE = "VALIDATION_ERROR"
VALIDATION_ERROR_MESSAGE = "Invalid search parameters."


def validation_error_tool_result(message: str = VALIDATION_ERROR_MESSAGE) -> CallToolResult:
    """Stable external validation failure — no Pydantic/framework details."""
    return CallToolResult(
        content=[TextContent(type="text", text=message)],
        structuredContent={
            "code": VALIDATION_ERROR_CODE,
            "message": message,
        },
        isError=True,
    )


def _actor_id() -> str | None:
    try:
        from delpi_auth.request_context import get_current_user

        user = get_current_user()
        return str(getattr(user, "id", None) or "") or None
    except Exception:
        return None


def _authorization() -> str | None:
    try:
        from delpi_auth.request_context import get_request_authorization

        return get_request_authorization()
    except Exception:
        return None


def _authz_error_result(exc: PermissionError) -> CallToolResult:
    message = str(exc) or "Forbidden"
    if message == "Unauthorized":
        return CallToolResult.model_validate(
            {
                "content": [{"type": "text", "text": "Authentication required."}],
                "isError": True,
                "_meta": mcp_www_authenticate_meta(
                    error="invalid_token",
                    error_description="Authentication required",
                ),
            }
        )
    return CallToolResult(
        content=[TextContent(type="text", text="Forbidden")],
        isError=True,
    )


class ApiDelpiFastMCP(FastMCP):
    """Promote OpenAI securitySchemes and project canonical input/output schemas."""

    async def list_tools(self) -> list[MCPTool]:
        tools = self._tool_manager.list_tools()
        listed: list[MCPTool] = []
        for info in tools:
            meta = dict(info.meta or {})
            schemes = meta.get("securitySchemes")
            input_schema = info.parameters
            output_schema = info.output_schema
            if info.name == MCP_TOOL_DISCOVER_DELPI_INFORMATION:
                input_schema = discover_delpi_information_input_json_schema()
                output_schema = discover_delpi_information_output_json_schema()
            elif info.name == MCP_TOOL_EXECUTE_DELPI_INFORMATION:
                input_schema = execute_delpi_information_input_json_schema()
                output_schema = execute_delpi_information_output_json_schema()
            payload: dict[str, Any] = {
                "name": info.name,
                "title": info.title,
                "description": info.description or "",
                "inputSchema": input_schema,
                "outputSchema": output_schema,
                "annotations": info.annotations,
                "icons": info.icons,
                "_meta": meta or None,
            }
            if schemes:
                payload["securitySchemes"] = schemes
            listed.append(MCPTool.model_validate(payload))
        return listed

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        try:
            if name == MCP_TOOL_DISCOVER_DELPI_INFORMATION:
                DiscoverDelpiInformationInput.model_validate(arguments or {})
            elif name == MCP_TOOL_EXECUTE_DELPI_INFORMATION:
                ExecuteDelpiInformationInput.model_validate(arguments or {})
        except ValidationError as exc:
            log_error(f"mcp {name} validation rejected error_count={exc.error_count()}")
            return validation_error_tool_result()
        return await super().call_tool(name, arguments)


def create_mcp_server() -> FastMCP:
    try:
        from app.composition.davi_dynamic_read_composer import (
            refresh_davi_action_index_from_live_openapi,
        )

        refresh_davi_action_index_from_live_openapi()
    except Exception as exc:
        logger.warning("DAVI action index live OpenAPI refresh skipped: %s", exc)

    hosts, origins = public_host_allowed_for_mcp()
    mcp = ApiDelpiFastMCP(
        name="api-delpi",
        instructions=DAVI_MCP_INSTRUCTIONS,
        streamable_http_path="/",
        stateless_http=True,
        json_response=True,
        transport_security=TransportSecuritySettings(
            enable_dns_rebinding_protection=True,
            allowed_hosts=hosts,
            allowed_origins=origins,
        ),
    )

    @mcp.tool(
        name=MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        title=MCP_TOOL_DISCOVER_DELPI_INFORMATION_TITLE,
        description=(
            "Find the governed DELPI READ capability that best matches the user's "
            "natural-language information need. Call this first. Returns opaque "
            "candidate_token values for execute_delpi_information. "
            "Does not accept URL, path, method, operationId, or SQL."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
            title=MCP_TOOL_DISCOVER_DELPI_INFORMATION_TITLE,
        ),
        meta={"securitySchemes": DAVI_MCP_SECURITY_SCHEMES},
        structured_output=True,
    )
    def discover_delpi_information_tool(
        query: str,
        top_k: int | None = None,
    ) -> CallToolResult:
        try:
            params = DiscoverDelpiInformationInput(query=query, top_k=top_k)
        except ValidationError:
            return validation_error_tool_result("Invalid discovery parameters.")
        try:
            data = discover_delpi_information(
                query=params.query,
                top_k=params.top_k,
                actor_id=_actor_id(),
            )
            return CallToolResult(
                content=[TextContent(type="text", text="Discovery completed.")],
                structuredContent=data,
                isError=False,
            )
        except Exception as exc:
            log_error(f"mcp discover_delpi_information failed: {exc}")
            raise RuntimeError(EXTERNAL_INTERNAL_ERROR_MESSAGE) from exc

    @mcp.tool(
        name=MCP_TOOL_EXECUTE_DELPI_INFORMATION,
        title=MCP_TOOL_EXECUTE_DELPI_INFORMATION_TITLE,
        description=(
            "Execute one candidate returned by the current discover_delpi_information "
            "call. Requires that candidate_token. Does not accept URL, path, method, "
            "free operationId, or SQL. Backend AuthZ remains authoritative."
        ),
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            openWorldHint=False,
            title=MCP_TOOL_EXECUTE_DELPI_INFORMATION_TITLE,
        ),
        meta={"securitySchemes": DAVI_MCP_SECURITY_SCHEMES},
        structured_output=True,
    )
    def execute_delpi_information_tool(
        candidate_token: str,
        arguments: dict[str, Any] | None = None,
    ) -> CallToolResult:
        try:
            params = ExecuteDelpiInformationInput(
                candidate_token=candidate_token,
                arguments=arguments,
            )
        except ValidationError:
            return validation_error_tool_result("Invalid execute parameters.")
        try:
            data = execute_delpi_information_wired(
                candidate_token=params.candidate_token,
                arguments=params.arguments,
                actor_id=_actor_id(),
                authorization=_authorization(),
            )
            return CallToolResult(
                content=[TextContent(type="text", text="Execution completed.")],
                structuredContent=data,
                isError=False,
            )
        except PermissionError as exc:
            return _authz_error_result(exc)
        except CandidateTokenError as exc:
            return validation_error_tool_result(str(exc) or "Invalid candidate token.")
        except GovernedExecutionError as exc:
            return validation_error_tool_result(str(exc) or "Execution rejected.")
        except Exception as exc:
            log_error(f"mcp execute_delpi_information failed: {exc}")
            raise RuntimeError(EXTERNAL_INTERNAL_ERROR_MESSAGE) from exc

    if document_transport_spike_enabled():
        from app.interface.mcp.document_transport_spike import (
            DocumentTransportSpikeMisconfigError,
            assert_spike_environment_isolated,
        )

        try:
            assert_spike_environment_isolated()
        except DocumentTransportSpikeMisconfigError as exc:
            logger.error("DAVI document transport spike refused: %s", exc)
            raise
        logger.warning(
            "DAVI document transport spike ENABLED — experimental MCP surface active; "
            "not a production document capability"
        )
        register_document_transport_spike(mcp)

    return mcp
