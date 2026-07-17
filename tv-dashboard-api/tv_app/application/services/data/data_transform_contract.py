"""Contrato versionado, sanitização e dual-read de dataTransform."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from tv_app.application.services.data.m_query.m_formatter import format_transform_plan_as_m
from tv_app.application.services.data.m_query.m_legacy_adapter import (
    legacy_steps_to_plan,
    normalize_legacy_transform,
)
from tv_app.application.services.tv_dashboard_content_service import m_query_setting
from tv_app.domain.data_query.m_diagnostics import Diagnostic, DiagnosticSeverity
from tv_app.domain.data_query.transform_plan import TransformPlan

DATA_TRANSFORM_V1 = 1
DATA_TRANSFORM_V2 = 2
M_DELPI_V1 = "m-delpi-v1"


class DataTransformReadStatus(StrEnum):
    ABSENT = "absent"
    READY = "ready"
    FEATURE_DISABLED = "feature_disabled"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class DataTransformReadResult:
    version: int | None
    status: DataTransformReadStatus
    normalized: dict[str, Any] | None
    plan: TransformPlan | None
    canonical_script: str | None
    diagnostics: tuple[Diagnostic, ...] = ()

    @property
    def executable(self) -> bool:
        return self.status == DataTransformReadStatus.READY and self.plan is not None

    def public_metadata(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "status": self.status.value,
            "diagnostics": [diagnostic.to_dict() for diagnostic in self.diagnostics],
        }


def _diagnostic(code: str, message: str, *, severity: DiagnosticSeverity) -> Diagnostic:
    return Diagnostic(code=code, severity=severity, message=message)


def _normalize_v2(raw: dict[str, Any]) -> tuple[dict[str, Any] | None, tuple[Diagnostic, ...]]:
    language = str(raw.get("language") or "").strip()
    script_raw = raw.get("script")
    if language != M_DELPI_V1:
        return None, (
            _diagnostic(
                "m.profile_not_supported",
                "O perfil informado não é suportado.",
                severity=DiagnosticSeverity.ERROR,
            ),
        )
    if not isinstance(script_raw, str):
        return None, (
            _diagnostic(
                "m.script_required",
                "O script M é obrigatório.",
                severity=DiagnosticSeverity.ERROR,
            ),
        )
    script = script_raw.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    if not script:
        return None, (
            _diagnostic(
                "m.script_required",
                "O script M é obrigatório.",
                severity=DiagnosticSeverity.ERROR,
            ),
        )
    max_bytes = int(m_query_setting("maxScriptBytes", 65536))
    if len(script.encode("utf-8")) > max_bytes:
        return None, (
            _diagnostic(
                "m.limit_script_bytes",
                "O script excede o limite configurado.",
                severity=DiagnosticSeverity.ERROR,
            ),
        )
    return {
        "version": DATA_TRANSFORM_V2,
        "language": M_DELPI_V1,
        "script": script,
    }, ()


def read_data_transform(
    raw: Any,
    *,
    query_bindings: tuple[dict[str, Any], ...] = (),
    source_schema: tuple[dict[str, Any], ...] = (),
    target_step_name: str | None = None,
    culture: str | None = None,
) -> DataTransformReadResult:
    """Dual-read: v1 usa adapter; v2 compila sob a flag de runtime."""

    if not isinstance(raw, dict):
        return DataTransformReadResult(
            version=None,
            status=DataTransformReadStatus.ABSENT,
            normalized=None,
            plan=None,
            canonical_script=None,
        )
    declared_version = raw.get("version")
    if declared_version in (None, DATA_TRANSFORM_V1) and "steps" in raw:
        normalized = normalize_legacy_transform(raw)
        if normalized is None:
            return DataTransformReadResult(
                version=DATA_TRANSFORM_V1,
                status=DataTransformReadStatus.INVALID,
                normalized=None,
                plan=None,
                canonical_script=None,
                diagnostics=(
                    _diagnostic(
                        "data_transform.v1_invalid",
                        "A transformação legada não contém etapas válidas.",
                        severity=DiagnosticSeverity.ERROR,
                    ),
                ),
            )
        plan = legacy_steps_to_plan(normalized)
        return DataTransformReadResult(
            version=DATA_TRANSFORM_V1,
            status=DataTransformReadStatus.READY,
            normalized=normalized,
            plan=plan,
            canonical_script=format_transform_plan_as_m(plan) if plan else None,
        )
    if declared_version == DATA_TRANSFORM_V2:
        normalized, diagnostics = _normalize_v2(raw)
        if normalized is None:
            return DataTransformReadResult(
                version=DATA_TRANSFORM_V2,
                status=DataTransformReadStatus.INVALID,
                normalized=None,
                plan=None,
                canonical_script=None,
                diagnostics=diagnostics,
            )
        if not bool(m_query_setting("enabled", False)):
            return DataTransformReadResult(
                version=DATA_TRANSFORM_V2,
                status=DataTransformReadStatus.FEATURE_DISABLED,
                normalized=normalized,
                plan=None,
                canonical_script=normalized["script"],
                diagnostics=(
                    _diagnostic(
                        "m.execution_feature_disabled",
                        "A execução de scripts M ainda não está habilitada.",
                        severity=DiagnosticSeverity.WARNING,
                    ),
                ),
            )
        from tv_app.application.services.data.m_query.m_compiler import (
            MCompileRequest,
            MQueryCompiler,
        )

        compiled = MQueryCompiler().compile(
            MCompileRequest(
                profile=M_DELPI_V1,
                script=normalized["script"],
                query_bindings=query_bindings,
                source_schema=source_schema,
                target_step_name=target_step_name,
                culture=culture or str(m_query_setting("defaultCulture", "pt-BR")),
            )
        )
        return DataTransformReadResult(
            version=DATA_TRANSFORM_V2,
            status=DataTransformReadStatus.READY if compiled.valid else DataTransformReadStatus.INVALID,
            normalized=normalized,
            plan=compiled.plan,
            canonical_script=compiled.canonical_script or normalized["script"],
            diagnostics=compiled.diagnostics,
        )
    return DataTransformReadResult(
        version=None,
        status=DataTransformReadStatus.INVALID,
        normalized=None,
        plan=None,
        canonical_script=None,
        diagnostics=(
            _diagnostic(
                "data_transform.version_not_supported",
                "A versão de dataTransform não é suportada.",
                severity=DiagnosticSeverity.ERROR,
            ),
        ),
    )


def sanitize_data_transform_for_persistence(
    raw: Any,
    *,
    write_v2_enabled: bool | None = None,
) -> dict[str, Any] | None:
    """Single-write v2 somente sob flag; nunca persiste plano, AST ou linhas."""

    result = read_data_transform(raw)
    if result.normalized is None:
        return None
    enabled = (
        bool(m_query_setting("writeV2Enabled", False))
        if write_v2_enabled is None
        else write_v2_enabled
    )
    if result.version == DATA_TRANSFORM_V1:
        if enabled and result.canonical_script:
            return {
                "version": DATA_TRANSFORM_V2,
                "language": M_DELPI_V1,
                "script": result.canonical_script,
            }
        return {"steps": [dict(step) for step in result.normalized["steps"]]}
    return dict(result.normalized)
