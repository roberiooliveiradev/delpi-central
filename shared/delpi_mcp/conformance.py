"""Reusable MCP conformance runner for DELPI apps.

Each app supplies:

- the serialized wire ``tools/list`` payload (plain dicts — the app test
  adapter dumps ``types.Tool.model_dump(mode="json", by_alias=True)``);
- an :class:`McpConformanceConfig` describing the app's declared contract.

The runner returns a :class:`ConformanceReport` of per-gate results and
never imports domain code, so the same suite exercises VISTA, TÉO and DAVI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable, Mapping

from .protocol import DELPI_MCP_PROTOCOL_MINIMUM, check_protocol_minimum
from .tool_validation import ValidationLayer, validate_tools_wire


class ConformanceStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class GateResult:
    gate: str
    status: ConformanceStatus
    message: str
    component: str = ""
    details: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class McpConformanceConfig:
    """Declared contract of one DELPI MCP server (per-app manifest)."""

    name: str
    expected_tool_names: tuple[str, ...] = ()
    expected_tool_count: int | None = None
    expected_resources_count: int | None = None
    expected_prompts_count: int | None = None
    provider_profile: str = "core"  # "core" | "openai"
    sdk_latest_protocol: str | None = None  # e.g. runtime LATEST_PROTOCOL_VERSION
    protocol_minimum: str = DELPI_MCP_PROTOCOL_MINIMUM


@dataclass
class ConformanceReport:
    server: str
    results: list[GateResult]

    @property
    def failures(self) -> list[GateResult]:
        return [r for r in self.results if r.status is ConformanceStatus.FAIL]

    @property
    def passed(self) -> bool:
        return not self.failures

    def summary(self) -> str:
        parts = [f"{r.gate}={r.status.value}" for r in self.results]
        return f"{self.server}: " + ", ".join(parts)


def _gate(
    name: str,
    ok: bool | None,
    message: str,
    *,
    details: Mapping[str, Any] | None = None,
) -> GateResult:
    if ok is None:
        status = ConformanceStatus.INCONCLUSIVE
    else:
        status = ConformanceStatus.PASS if ok else ConformanceStatus.FAIL
    return GateResult(
        gate=name,
        status=status,
        message=message,
        details=details or {},
    )


def run_mcp_conformance(
    tools_wire: Iterable[Mapping[str, Any]],
    config: McpConformanceConfig,
) -> ConformanceReport:
    """Run the S0 gate set over one serialized tools/list payload."""
    tools = list(tools_wire)
    results: list[GateResult] = []

    issues = validate_tools_wire(tools, profile=config.provider_profile)
    issues_by_code = {}
    for issue in issues:
        issues_by_code.setdefault(issue.code, []).append(issue)

    def issues_gate(gate: str, codes: tuple[str, ...], ok_message: str) -> None:
        found = [i for c in codes for i in issues_by_code.get(c, [])]
        if found:
            results.append(
                _gate(
                    gate,
                    False,
                    "; ".join(f"{i.path or i.code}: {i.message}" for i in found[:5]),
                    details={"issues": [f"{i.layer.value}:{i.code}:{i.path}" for i in found]},
                )
            )
        else:
            results.append(_gate(gate, True, ok_message))

    # C1 — every tool definition is a JSON-serializable object.
    issues_gate(
        "tool_serialization",
        ("TOOL_NOT_OBJECT", "TOOL_NOT_SERIALIZABLE", "META_NOT_SERIALIZABLE"),
        "all tool definitions serialize to JSON",
    )

    # C3 — unique tool names.
    issues_gate(
        "unique_tool_names",
        ("TOOL_NAME_DUPLICATE",),
        "all tool names unique",
    )

    # C2/C8 — inputSchema present, object-shaped, serializable.
    issues_gate(
        "input_schema",
        ("TOOL_INPUT_SCHEMA_MISSING", "TOOL_INPUT_SCHEMA_NOT_OBJECT", "TOOL_SCHEMA_INVALID"),
        "all inputSchema objects valid",
    )

    # C9 — outputSchema shape when present.
    output_issues = [
        i
        for i in issues_by_code.get("TOOL_SCHEMA_INVALID", [])
        if i.path.startswith("outputSchema")
    ]
    results.append(
        _gate(
            "output_schema",
            not output_issues,
            "outputSchema objects valid" if not output_issues else str(output_issues[0].message),
        )
    )

    # C6 — annotations shape.
    issues_gate(
        "annotations",
        ("ANNOTATIONS_NOT_OBJECT", "ANNOTATION_HINT_TYPE_INVALID", "ANNOTATION_TITLE_TYPE_INVALID"),
        "annotations valid",
    )

    # C7/C10 — reserved _meta validity: namespacing + reserved-key shape
    # (the VISTA string-list defect class surfaces here).
    meta_issues = [
        i
        for i in issues
        if i.code in ("META_NOT_OBJECT", "META_KEY_NOT_STRING")
        or i.path.startswith("_meta")
    ]
    results.append(
        _gate(
            "reserved_meta",
            not meta_issues,
            "all _meta keys reserved-valid or namespaced"
            if not meta_issues
            else "; ".join(f"{i.path}: {i.code}" for i in meta_issues[:5]),
            details={"issues": [f"{i.layer.value}:{i.code}:{i.path}" for i in meta_issues]},
        )
    )

    # Named regression gate for the VISTA incident — surface it even when
    # rolled into reserved_meta so the report is unambiguous.
    ss_issues = issues_by_code.get("RESERVED_META_SECURITY_SCHEMES_INVALID", [])
    results.append(
        _gate(
            "security_schemes_shape",
            not ss_issues,
            "no schema-invalid reserved securitySchemes (VISTA incident regression)"
            if not ss_issues
            else "; ".join(f"{i.path}: {i.message}" for i in ss_issues[:5]),
        )
    )

    # Non-meta wire findings (name validity, unknown top-level fields, etc).
    other_issues = [
        i
        for i in issues
        if not i.path.startswith("_meta")
        and i.code
        not in (
            "TOOL_NAME_DUPLICATE",
            "TOOL_NOT_OBJECT",
            "TOOL_NOT_SERIALIZABLE",
            "META_NOT_SERIALIZABLE",
            "TOOL_INPUT_SCHEMA_MISSING",
            "TOOL_INPUT_SCHEMA_NOT_OBJECT",
            "ANNOTATIONS_NOT_OBJECT",
            "ANNOTATION_HINT_TYPE_INVALID",
            "ANNOTATION_TITLE_TYPE_INVALID",
        )
        and not (i.code == "TOOL_SCHEMA_INVALID" and i.path.startswith("outputSchema"))
        and not i.code.startswith("OPENAI_")
    ]
    results.append(
        _gate(
            "wire_shape",
            not other_issues,
            "wire shape conforms to spec + profile"
            if not other_issues
            else "; ".join(f"{i.path or i.code}: {i.message}" for i in other_issues[:5]),
            details={"issues": [f"{i.layer.value}:{i.code}:{i.path}" for i in other_issues]},
        )
    )

    # C4 — expected tool count.
    if config.expected_tool_count is not None:
        results.append(
            _gate(
                "expected_tool_count",
                len(tools) == config.expected_tool_count,
                f"expected {config.expected_tool_count}, got {len(tools)}",
            )
        )

    # C5 — expected tool manifest (exact set, order-insensitive).
    if config.expected_tool_names:
        actual = {t.get("name") for t in tools if isinstance(t, Mapping)}
        expected = set(config.expected_tool_names)
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        results.append(
            _gate(
                "expected_tool_manifest",
                not missing and not extra,
                "manifest matches registered tools"
                if not missing and not extra
                else f"missing={missing} extra={extra}",
                details={"missing": missing, "extra": extra},
            )
        )

    # C10/C11 — protocol-era minimum vs the server's declared latest.
    if config.sdk_latest_protocol is None:
        results.append(
            _gate(
                "protocol_minimum",
                None,
                "sdk_latest_protocol not declared — cannot evaluate",
            )
        )
    else:
        check = check_protocol_minimum(
            config.sdk_latest_protocol,
            platform_minimum=config.protocol_minimum,
        )
        if check.support == "SUPPORTED":
            results.append(_gate("protocol_minimum", True, check.message))
        else:
            results.append(
                _gate(
                    "protocol_minimum",
                    False,
                    check.message,
                    details={"sdk_latest": check.sdk_latest_protocol},
                )
            )

    return ConformanceReport(server=config.name, results=results)


__all__ = [
    "ConformanceReport",
    "ConformanceStatus",
    "GateResult",
    "McpConformanceConfig",
    "run_mcp_conformance",
]
