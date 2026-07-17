"""Compilador seguro M DELPI v1 → TransformPlan, sem execução."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from tv_app.application.services.data.m_query.m_formatter import (
    format_m_document,
    format_m_expression,
)
from tv_app.application.services.data.m_query.m_function_registry import get_function_registry
from tv_app.application.services.data.m_query.m_parser import MParseError, parse_m_script
from tv_app.application.services.data.m_query.m_semantic_analyzer import (
    MSemanticAnalyzer,
    ast_metrics,
)
from tv_app.application.services.tv_dashboard_content_service import m_query_setting
from tv_app.domain.data_query.m_ast import (
    MBinaryExpression,
    MCallExpression,
    MEachExpression,
    MExpression,
    MFieldAccess,
    MFunctionExpression,
    MIdentifier,
    MIfExpression,
    MListExpression,
    MLiteral,
    MParenthesizedExpression,
    MRecordExpression,
    MTypeExpression,
    MUnaryExpression,
)
from tv_app.domain.data_query.m_diagnostics import Diagnostic, DiagnosticSeverity, SourceRange
from tv_app.domain.data_query.transform_plan import (
    CompiledExpression,
    CompiledMPlanStep,
    TransformPlan,
)


@dataclass(frozen=True, slots=True)
class MCompileRequest:
    profile: str
    script: str
    source_schema: tuple[Mapping[str, Any], ...] = ()
    query_bindings: tuple[Mapping[str, Any], ...] = ()
    target_step_name: str | None = None
    culture: str = "pt-BR"


@dataclass(frozen=True, slots=True)
class MCompileResult:
    profile: str
    canonical_script: str | None
    script_hash: str
    output_step_name: str | None
    plan: TransformPlan | None
    diagnostics: tuple[Diagnostic, ...]
    referenced_queries: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        return self.plan is not None and not any(
            item.severity == DiagnosticSeverity.ERROR for item in self.diagnostics
        )

    def to_dict(self) -> dict[str, Any]:
        steps = []
        if self.plan is not None:
            for step in self.plan.steps:
                operation = (
                    step.function_name
                    if isinstance(step, CompiledMPlanStep)
                    else str(step.operation)
                )
                formula = operation
                if isinstance(step, CompiledMPlanStep):
                    source = parse_m_script(self.canonical_script or "")
                    binding = next(
                        (item for item in source.expression.bindings if item.name == step.name),
                        None,
                    )
                    if binding is not None:
                        formula = format_m_expression(binding.expression)
                steps.append(
                    {
                        "name": step.name,
                        "operation": operation,
                        "label": step.name,
                        "formula": formula,
                    }
                )
        return {
            "profile": self.profile,
            "canonicalScript": self.canonical_script,
            "scriptHash": self.script_hash,
            "outputStepName": self.output_step_name,
            "steps": steps,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "referencedQueries": list(self.referenced_queries),
        }


def _whole_script_range(script: str) -> SourceRange | None:
    if not script:
        return None
    lines = script.splitlines(keepends=True)
    if not lines:
        return None
    return SourceRange(
        1,
        1,
        len(lines),
        len(lines[-1].rstrip("\r\n")) + 1,
        0,
        len(script),
    )


def _diagnostic(code: str, message: str, script: str = "") -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=DiagnosticSeverity.ERROR,
        message=message,
        source_range=_whole_script_range(script),
    )


def _compile_expression(expression: MExpression) -> CompiledExpression:
    if isinstance(expression, MLiteral):
        return CompiledExpression("literal", expression.value)
    if isinstance(expression, MIdentifier):
        return CompiledExpression("identifier", expression.name)
    if isinstance(expression, MFieldAccess):
        return CompiledExpression("field", expression.field_name)
    if isinstance(expression, MTypeExpression):
        return CompiledExpression("type", expression.name)
    if isinstance(expression, MListExpression):
        return CompiledExpression(
            "list",
            children=tuple(_compile_expression(item) for item in expression.items),
        )
    if isinstance(expression, MRecordExpression):
        return CompiledExpression(
            "record",
            children=tuple(
                CompiledExpression(
                    "recordField",
                    field.name,
                    (_compile_expression(field.value),),
                )
                for field in expression.fields
            ),
        )
    if isinstance(expression, MCallExpression):
        return CompiledExpression(
            "call",
            expression.function_name,
            tuple(_compile_expression(item) for item in expression.arguments),
        )
    if isinstance(expression, MEachExpression):
        return CompiledExpression("each", children=(_compile_expression(expression.body),))
    if isinstance(expression, MIfExpression):
        return CompiledExpression(
            "if",
            children=(
                _compile_expression(expression.condition),
                _compile_expression(expression.then_value),
                _compile_expression(expression.else_value),
            ),
        )
    if isinstance(expression, MBinaryExpression):
        return CompiledExpression(
            "binary",
            expression.operator,
            (
                _compile_expression(expression.left),
                _compile_expression(expression.right),
            ),
        )
    if isinstance(expression, MUnaryExpression):
        return CompiledExpression(
            "unary",
            expression.operator,
            (_compile_expression(expression.operand),),
        )
    if isinstance(expression, MParenthesizedExpression):
        return _compile_expression(expression.expression)
    if isinstance(expression, MFunctionExpression):
        return CompiledExpression("forbiddenFunction")
    raise TypeError(f"Expressão M desconhecida: {type(expression).__name__}")


def _binding_names(bindings: Iterable[Mapping[str, Any]]) -> tuple[str, ...]:
    return tuple(
        str(item.get("name") or "").strip()
        for item in bindings
        if str(item.get("name") or "").strip()
    )


class MQueryCompiler:
    def compile(self, request: MCompileRequest) -> MCompileResult:
        script_hash = f"sha256:{hashlib.sha256(request.script.encode('utf-8')).hexdigest()}"
        diagnostics: list[Diagnostic] = []
        expected_profile = str(m_query_setting("profile", "m-delpi-v1"))
        max_bytes = int(m_query_setting("maxScriptBytes", 65536))
        max_steps = int(m_query_setting("maxSteps", 100))
        max_nodes = int(m_query_setting("maxAstNodes", 5000))
        max_depth = int(m_query_setting("maxExpressionDepth", 40))
        sample_limit = int(m_query_setting("diagnosticSampleLimit", 20))

        if request.profile != expected_profile:
            diagnostics.append(
                _diagnostic(
                    "m.profile_not_supported",
                    f"O profile {request.profile} não é suportado.",
                    request.script,
                )
            )
        if len(request.script.encode("utf-8")) > max_bytes:
            diagnostics.append(
                _diagnostic(
                    "m.limit_script_bytes",
                    f"O script excede o limite de {max_bytes} bytes.",
                )
            )
        if diagnostics:
            return MCompileResult(
                request.profile,
                None,
                script_hash,
                None,
                None,
                tuple(diagnostics[:sample_limit]),
            )

        try:
            document = parse_m_script(request.script)
        except MParseError as exc:
            return MCompileResult(
                request.profile,
                None,
                script_hash,
                None,
                None,
                (exc.diagnostic,),
            )

        bindings = document.expression.bindings
        if len(bindings) > max_steps:
            diagnostics.append(
                _diagnostic(
                    "m.limit_steps",
                    f"O script excede o limite de {max_steps} etapas.",
                    request.script,
                )
            )
        node_count, expression_depth = ast_metrics(document)
        if node_count > max_nodes:
            diagnostics.append(
                _diagnostic(
                    "m.limit_ast_nodes",
                    f"A AST excede o limite de {max_nodes} nós.",
                    request.script,
                )
            )
        if expression_depth > max_depth:
            diagnostics.append(
                _diagnostic(
                    "m.limit_expression_depth",
                    f"A expressão excede a profundidade máxima de {max_depth}.",
                    request.script,
                )
            )
        if diagnostics:
            return MCompileResult(
                request.profile,
                None,
                script_hash,
                None,
                None,
                tuple(diagnostics[:sample_limit]),
            )

        source_columns = tuple(
            str(item.get("key") or "").strip()
            for item in request.source_schema
            if str(item.get("key") or "").strip()
        )
        duplicate_columns = sorted(
            {name for name in source_columns if source_columns.count(name) > 1}
        )
        if duplicate_columns:
            diagnostics.append(
                _diagnostic(
                    "m.duplicate_source_column",
                    f"Colunas duplicadas no sourceSchema: {', '.join(duplicate_columns)}.",
                    request.script,
                )
            )
        allowed_schema_types = {
            "any",
            "null",
            "text",
            "number",
            "logical",
            "date",
            "datetime",
            "duration",
        }
        invalid_schema_types = sorted(
            {
                str(item.get("type") or "any")
                for item in request.source_schema
                if str(item.get("type") or "any") not in allowed_schema_types
            }
        )
        if invalid_schema_types:
            diagnostics.append(
                _diagnostic(
                    "m.source_schema_type_invalid",
                    f"Tipos inválidos no sourceSchema: {', '.join(invalid_schema_types)}.",
                    request.script,
                )
            )
        query_names = _binding_names(request.query_bindings)
        duplicate_queries = sorted(
            {name for name in query_names if query_names.count(name) > 1}
        )
        if duplicate_queries:
            diagnostics.append(
                _diagnostic(
                    "m.duplicate_query_binding",
                    f"Bindings de consulta duplicados: {', '.join(duplicate_queries)}.",
                    request.script,
                )
            )

        analysis = MSemanticAnalyzer(get_function_registry()).analyze(
            document,
            source_columns=source_columns if request.source_schema else None,
            query_bindings=query_names,
        )
        diagnostics.extend(analysis.diagnostics)
        canonical = format_m_document(document)
        if diagnostics:
            return MCompileResult(
                request.profile,
                canonical,
                script_hash,
                None,
                None,
                tuple(diagnostics[:sample_limit]),
                analysis.referenced_queries,
            )

        target_name = request.target_step_name
        all_names = [binding.name for binding in bindings]
        if target_name is not None and target_name != "Fonte" and target_name not in all_names:
            diagnostic = _diagnostic(
                "m.unknown_target_step",
                f'A etapa alvo "{target_name}" não foi encontrada.',
                request.script,
            )
            return MCompileResult(
                request.profile,
                canonical,
                script_hash,
                None,
                None,
                (diagnostic,),
                analysis.referenced_queries,
            )
        output_name = (
            target_name
            or (
                document.expression.output.name
                if isinstance(document.expression.output, MIdentifier)
                else None
            )
        )
        if output_name == "Fonte":
            plan = TransformPlan(
                version=1,
                profile=request.profile,
                steps=(),
                output="Fonte",
                referenced_queries=analysis.referenced_queries,
            )
            return MCompileResult(
                request.profile,
                canonical,
                script_hash,
                "Fonte",
                plan,
                tuple(diagnostics[:sample_limit]),
                analysis.referenced_queries,
            )

        compiled_steps: list[CompiledMPlanStep] = []
        for binding in bindings:
            if isinstance(binding.expression, MCallExpression):
                call = binding.expression
                combine = call.function_name == "Table.Combine"
                combine_items = (
                    call.arguments[0].items
                    if combine and call.arguments and isinstance(call.arguments[0], MListExpression)
                    else ()
                )
                input_name = (
                    call.arguments[0].name
                    if call.arguments and isinstance(call.arguments[0], MIdentifier)
                    else next(
                        (
                            item.name
                            for item in combine_items
                            if isinstance(item, MIdentifier)
                        ),
                        "Fonte",
                    )
                )
                compiled_steps.append(
                    CompiledMPlanStep(
                        name=binding.name,
                        input_name=input_name,
                        function_name=call.function_name,
                        arguments=tuple(
                            _compile_expression(item)
                            for item in (call.arguments if combine else call.arguments[1:])
                        ),
                    )
                )
            elif isinstance(binding.expression, MIdentifier):
                compiled_steps.append(
                    CompiledMPlanStep(
                        name=binding.name,
                        input_name=binding.expression.name,
                        function_name="#identity",
                        arguments=(),
                    )
                )
            if output_name == binding.name:
                break

        if output_name is None or not compiled_steps:
            diagnostic = _diagnostic(
                "m.output_table_required",
                "O script deve produzir ao menos uma etapa de tabela.",
                request.script,
            )
            return MCompileResult(
                request.profile,
                canonical,
                script_hash,
                None,
                None,
                (diagnostic,),
                analysis.referenced_queries,
            )
        plan = TransformPlan(
            version=1,
            profile=request.profile,
            steps=tuple(compiled_steps),
            output=compiled_steps[-1].name,
            referenced_queries=analysis.referenced_queries,
        )
        return MCompileResult(
            request.profile,
            canonical,
            script_hash,
            plan.output,
            plan,
            (),
            analysis.referenced_queries,
        )
