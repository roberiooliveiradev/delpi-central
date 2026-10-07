"""Contrato do bloco ``input`` — owner único de shape, validação e contexto de variáveis.

Legado (sem ``binding``): ``paramKey`` + ``targetScope``/``targetSourceIds``
contribuem param de rota (``comunicado_input_filters_service``) — semântica
inalterada.

Variável: ``binding: {kind: "variable", key}`` + ``valueSchema`` (shape de
paramSchema) publica ``input.<key>`` para ExpressionSpec do **mesmo slide**.
O valor nunca entra no wire; o paramSchema da rota segue o contrato final.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable, Mapping

from tv_app.application.services.data.value_expression_service import (
    INPUT_VARIABLE_KEY_PATTERN,
    InputVariableScope,
    expression_input_refs,
)
from tv_app.application.services.tv_dashboard_content_service import message
from tv_app.application.services.tv_data_route_catalog_service import DATA_BLOCK_TYPES

INPUT_BINDING_VARIABLE = "variable"
# Overrides de sessão de variáveis já recortados para UM slide (inputBlockId → valor).
SLIDE_INPUT_OVERRIDES_KEY = "byInputId"
VALUE_TYPES = frozenset({"string", "integer", "number", "boolean"})
VALUE_FORMATS = frozenset({"date"})
_VALUE_SCHEMA_KEYS = frozenset({"type", "format", "enum", "enumLabels"})
_MAX_ENUM_ITEMS = 100
_MAX_ENUM_LABEL_CHARS = 120
_INTEGER_TEXT = re.compile(r"^[+-]?\d+$")
_ISO_DATE_TEXT = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class InputContractError(ValueError):
    def __init__(self, code: str, text: str) -> None:
        super().__init__(text)
        self.code = code


@dataclass(frozen=True, slots=True)
class InputVariableDeclaration:
    block_id: str
    key: str
    value_schema: dict[str, Any]
    default_value: Any


def _fail(code: str, key: str, default: str, **fmt: Any) -> None:
    raise InputContractError(code, message(key, default, **fmt))


def is_variable_input(input_cfg: Any) -> bool:
    if not isinstance(input_cfg, Mapping):
        return False
    binding = input_cfg.get("binding")
    return isinstance(binding, Mapping) and binding.get("kind") == INPUT_BINDING_VARIABLE


def coerce_input_value(value: Any, value_schema: Mapping[str, Any]) -> Any:
    """Valor bruto (persistido ou de sessão) → escalar tipado do valueSchema."""
    value_type = str(value_schema.get("type") or "")
    coerced: Any
    if value_type == "integer":
        if isinstance(value, bool):
            coerced = None
        elif isinstance(value, int):
            coerced = value
        elif isinstance(value, float) and math.isfinite(value) and value.is_integer():
            coerced = int(value)
        elif isinstance(value, str) and _INTEGER_TEXT.match(value.strip()):
            coerced = int(value.strip())
        else:
            coerced = None
    elif value_type == "number":
        if isinstance(value, bool):
            coerced = None
        elif isinstance(value, (int, float)) and math.isfinite(float(value)):
            coerced = value
        elif isinstance(value, str):
            try:
                parsed = float(value.strip())
            except ValueError:
                parsed = math.nan
            coerced = parsed if math.isfinite(parsed) else None
            if coerced is not None and float(coerced).is_integer():
                coerced = int(coerced)
        else:
            coerced = None
    elif value_type == "boolean":
        if isinstance(value, bool):
            coerced = value
        elif value in ("true", "false"):
            coerced = value == "true"
        else:
            coerced = None
    elif value_type == "string":
        coerced = value if isinstance(value, str) and value != "" else None
        if coerced is not None and value_schema.get("format") == "date":
            try:
                if not _ISO_DATE_TEXT.match(coerced):
                    raise ValueError
                date.fromisoformat(coerced)
            except ValueError:
                coerced = None
    else:
        coerced = None
    if coerced is None:
        _fail(
            "input.value_invalid",
            "inputVariableValueInvalid",
            "Valor incompatível com o tipo declarado da variável.",
        )
    enum_values = value_schema.get("enum")
    if isinstance(enum_values, list) and enum_values and coerced not in enum_values:
        _fail(
            "input.value_invalid",
            "inputVariableValueInvalid",
            "Valor incompatível com o tipo declarado da variável.",
        )
    return coerced


def normalize_value_schema(raw: Any) -> dict[str, Any]:
    """Valida ``valueSchema`` (fail closed) e devolve a forma canônica persistida."""
    if not isinstance(raw, Mapping):
        _fail("input.value_schema_invalid", "inputValueSchemaRequired", "Variável exige valueSchema.")
    unknown = sorted(str(key) for key in raw if key not in _VALUE_SCHEMA_KEYS)
    if unknown:
        _fail(
            "input.value_schema_invalid",
            "inputValueSchemaUnknownFields",
            "valueSchema com campos não suportados: {fields}.",
            fields=", ".join(unknown),
        )
    value_type = raw.get("type")
    if value_type not in VALUE_TYPES:
        _fail(
            "input.value_schema_invalid",
            "inputValueSchemaTypeInvalid",
            "Tipo da variável deve ser string, integer, number ou boolean.",
        )
    schema: dict[str, Any] = {"type": value_type}
    fmt = raw.get("format")
    if fmt is not None:
        if fmt not in VALUE_FORMATS or value_type != "string":
            _fail(
                "input.value_schema_invalid",
                "inputValueSchemaFormatInvalid",
                'Formato suportado: "date" com type "string".',
            )
        schema["format"] = fmt
    enum_raw = raw.get("enum")
    if enum_raw is not None:
        if (
            not isinstance(enum_raw, list)
            or not enum_raw
            or len(enum_raw) > _MAX_ENUM_ITEMS
            or value_type == "boolean"
        ):
            _fail(
                "input.value_schema_invalid",
                "inputValueSchemaEnumInvalid",
                "Opções (enum) inválidas para o tipo da variável.",
            )
        base = {key: schema[key] for key in ("type", "format") if key in schema}
        items: list[Any] = []
        for item in enum_raw:
            if isinstance(item, str) and value_type in {"integer", "number"}:
                _fail(
                    "input.value_schema_invalid",
                    "inputValueSchemaEnumInvalid",
                    "Opções (enum) inválidas para o tipo da variável.",
                )
            try:
                coerced = coerce_input_value(item, base)
            except InputContractError:
                _fail(
                    "input.value_schema_invalid",
                    "inputValueSchemaEnumInvalid",
                    "Opções (enum) inválidas para o tipo da variável.",
                )
            if coerced in items:
                _fail(
                    "input.value_schema_invalid",
                    "inputValueSchemaEnumInvalid",
                    "Opções (enum) inválidas para o tipo da variável.",
                )
            items.append(coerced)
        schema["enum"] = items
    labels_raw = raw.get("enumLabels")
    if labels_raw is not None:
        allowed = {str(item) for item in schema.get("enum") or []}
        if not isinstance(labels_raw, Mapping) or not allowed:
            _fail(
                "input.value_schema_invalid",
                "inputValueSchemaEnumLabelsInvalid",
                "enumLabels exige enum e rótulos por valor declarado.",
            )
        labels: dict[str, str] = {}
        for key, label in labels_raw.items():
            if (
                str(key) not in allowed
                or not isinstance(label, str)
                or not label.strip()
                or len(label) > _MAX_ENUM_LABEL_CHARS
            ):
                _fail(
                    "input.value_schema_invalid",
                    "inputValueSchemaEnumLabelsInvalid",
                    "enumLabels exige enum e rótulos por valor declarado.",
                )
            labels[str(key)] = label.strip()
        schema["enumLabels"] = labels
    return schema


def read_input_variable(block: Mapping[str, Any]) -> InputVariableDeclaration | None:
    """Declaração de variável do bloco; ``None`` = legado. Shape inválido → erro."""
    input_cfg = block.get("input")
    if not isinstance(input_cfg, Mapping) or "binding" not in input_cfg:
        return None
    binding = input_cfg.get("binding")
    if not isinstance(binding, Mapping) or binding.get("kind") != INPUT_BINDING_VARIABLE:
        _fail(
            "input.binding_invalid",
            "inputBindingInvalid",
            'binding.kind suportado: "variable" (parâmetro de rota usa paramKey).',
        )
    unknown_binding = sorted(str(key) for key in binding if key not in {"kind", "key"})
    if unknown_binding:
        _fail(
            "input.binding_invalid",
            "inputBindingInvalid",
            'binding.kind suportado: "variable" (parâmetro de rota usa paramKey).',
        )
    key = binding.get("key")
    if not isinstance(key, str) or not INPUT_VARIABLE_KEY_PATTERN.match(key):
        _fail(
            "input.variable_key_invalid",
            "inputVariableKeyInvalid",
            "Chave da variável inválida (letras, números e _; começa por letra ou _).",
        )
    if str(input_cfg.get("paramKey") or "").strip():
        _fail(
            "input.binding_ambiguous",
            "inputBindingAmbiguous",
            "Input não pode ter paramKey e binding de variável ao mesmo tempo.",
        )
    if input_cfg.get("targetScope") == "sources" or input_cfg.get("targetSourceIds"):
        _fail(
            "input.binding_ambiguous",
            "inputVariableTargetNotApplicable",
            "Variável do slide não usa targetScope/targetSourceIds.",
        )
    schema = normalize_value_schema(input_cfg.get("valueSchema"))
    default_raw = input_cfg.get("defaultValue")
    default_value = None if default_raw is None else coerce_input_value(default_raw, schema)
    return InputVariableDeclaration(
        block_id=str(block.get("id") or ""),
        key=key,
        value_schema=schema,
        default_value=default_value,
    )


def _input_blocks(blocks: Iterable[Any]) -> list[Mapping[str, Any]]:
    return [
        block
        for block in blocks
        if isinstance(block, Mapping) and str(block.get("type") or "") == "input"
    ]


def collect_input_variables(
    blocks: Iterable[Any],
) -> tuple[list[InputVariableDeclaration], list[dict[str, str]]]:
    """Declarações válidas + issues (shape inválido, chave duplicada no slide)."""
    declarations: list[InputVariableDeclaration] = []
    issues: list[dict[str, str]] = []
    seen: dict[str, str] = {}
    for block in _input_blocks(blocks):
        block_id = str(block.get("id") or "")
        try:
            declaration = read_input_variable(block)
        except InputContractError as exc:
            issues.append({"field": f"input:{block_id}", "message": str(exc), "code": exc.code})
            continue
        if declaration is None:
            continue
        if declaration.key in seen:
            issues.append(
                {
                    "field": f"input:{block_id}",
                    "message": message(
                        "inputVariableKeyDuplicate",
                        'Variável "{variable}" já declarada neste slide.',
                        variable=declaration.key,
                    ),
                    "code": "input.variable_key_duplicate",
                }
            )
            continue
        seen[declaration.key] = block_id
        declarations.append(declaration)
    return declarations, issues


def build_input_variable_scope(
    blocks: Iterable[Any],
    *,
    overrides_by_input_id: Mapping[str, Any] | None = None,
) -> InputVariableScope:
    """Contexto ``input.*`` do slide: override de sessão válido → default → ausente.

    Chave explícita com ``null`` = sem valor (não cai no default). Override
    inválido marca a variável como inválida — quem a referencia falha fechado.
    Chaves duplicadas/inválidas ficam fora do escopo (refs falham fechado).
    """
    block_list = list(blocks)
    declarations, _issues = collect_input_variables(block_list)
    key_counts = Counter(
        block["input"]["binding"].get("key")
        for block in _input_blocks(block_list)
        if is_variable_input(block.get("input"))
    )
    overrides = overrides_by_input_id if isinstance(overrides_by_input_id, Mapping) else {}
    schemas: dict[str, Mapping[str, Any]] = {}
    values: dict[str, Any] = {}
    invalid: dict[str, str] = {}
    for declaration in declarations:
        if key_counts[declaration.key] > 1:
            continue
        schemas[declaration.key] = declaration.value_schema
        if declaration.block_id in overrides:
            raw = overrides[declaration.block_id]
            if raw is None:
                continue
            try:
                values[declaration.key] = coerce_input_value(raw, declaration.value_schema)
            except InputContractError as exc:
                invalid[declaration.key] = exc.code
            continue
        if declaration.default_value is not None:
            values[declaration.key] = declaration.default_value
    return InputVariableScope(schemas=schemas, values=values, invalid=invalid)


def iter_config_expression_params(cfg: Mapping[str, Any]) -> Iterable[tuple[str, str, Any, str | None]]:
    """(field, paramKey, value, operationId) de todo param que pode conter ExpressionSpec."""
    blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
    for index, block in enumerate(blocks):
        if not isinstance(block, Mapping) or str(block.get("type") or "") not in DATA_BLOCK_TYPES:
            continue
        binding = block.get("dataBinding")
        if not isinstance(binding, Mapping) or not isinstance(binding.get("params"), Mapping):
            continue
        operation_id = str(binding.get("operationId") or "").strip() or None
        for key, value in binding["params"].items():
            yield f"blocks[{index}].dataBinding.params.{key}", str(key), value, operation_id
    models = cfg.get("dataModels") if isinstance(cfg.get("dataModels"), list) else []
    for m_index, model in enumerate(models):
        inputs = model.get("inputs") if isinstance(model, Mapping) else None
        for i_index, item in enumerate(inputs if isinstance(inputs, list) else []):
            if not isinstance(item, Mapping) or not isinstance(item.get("params"), Mapping):
                continue
            operation_id = str(item.get("operationId") or "").strip() or None
            for key, value in item["params"].items():
                yield (
                    f"dataModels[{m_index}].inputs[{i_index}].params.{key}",
                    str(key),
                    value,
                    operation_id,
                )
    filters = cfg.get("dataFilters")
    if isinstance(filters, Mapping):
        for key, value in filters.items():
            yield f"dataFilters.{key}", str(key), value, None


def undeclared_input_reference_issues(
    cfg: Mapping[str, Any], declared_keys: Iterable[str]
) -> list[dict[str, str]]:
    """Refs ``input.<key>`` sem declaração no nativeConfig candidato."""
    declared = set(declared_keys)
    issues: list[dict[str, str]] = []
    for field_path, _param, value, _operation_id in iter_config_expression_params(cfg):
        for key in sorted(expression_input_refs(value) - declared):
            issues.append(
                {
                    "field": field_path,
                    "message": message(
                        "inputVariableReferenceUndeclared",
                        'A expressão referencia input.{variable}, que não está declarada neste slide.',
                        variable=key,
                    ),
                    "code": "input.reference_undeclared",
                }
            )
    return issues
