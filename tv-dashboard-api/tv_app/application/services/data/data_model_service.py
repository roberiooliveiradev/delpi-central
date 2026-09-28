"""DataModel — contrato persistido + projeção para o runtime de fontes.

Contrato congelado (DM0): ``nativeConfig.dataModels[]`` — objeto lógico
não-visual composto de 1..N inputs embutidos e um transform do modelo.
Este módulo valida/normaliza a definição e a projeta nos nós
``data_source`` sintéticos que o runtime canônico (dependency DAG +
transform executor) já sabe executar. Nenhuma engine nova aqui.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable


MODEL_CONTRACT_INVALID = "data_model.contract_invalid"
MODEL_IN_USE = "data_model.in_use"


class DataModelContractError(ValueError):
    """Violação do contrato persistido de DataModel."""

    def __init__(
        self,
        message: str,
        *,
        code: str = MODEL_CONTRACT_INVALID,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details or {}


def new_data_model_id() -> str:
    return f"mdl_{uuid.uuid4().hex[:10]}"


def _fail(
    message: str,
    *,
    code: str = MODEL_CONTRACT_INVALID,
    model_id: str = "",
    **details: Any,
) -> None:
    payload = {k: v for k, v in details.items() if v is not None}
    if model_id:
        payload.setdefault("modelId", model_id)
    raise DataModelContractError(message, code=code, details=payload)


def _merge_source_refs(transform: Any) -> list[str]:
    if not isinstance(transform, dict):
        return []
    steps = transform.get("steps")
    if not isinstance(steps, list):
        return []
    refs: list[str] = []
    for step in steps:
        if isinstance(step, dict) and str(step.get("op") or "") == "merge":
            ref = str(step.get("sourceId") or "").strip()
            if ref:
                refs.append(ref)
    return refs


def _sanitize_transform_value(
    transform: Any,
    *,
    sanitize: Callable[[dict[str, Any]], dict[str, Any]] | None,
    model_id: str,
    field: str,
) -> dict[str, Any] | None:
    if transform is None:
        return None
    if not isinstance(transform, dict):
        _fail(
            f"{field} deve ser um objeto de transformação.",
            model_id=model_id,
            field=field,
        )
    if sanitize is not None:
        return sanitize(transform)
    return dict(transform)


def normalize_data_model(
    raw: Any,
    *,
    catalog: Any | None = None,
    sanitize_transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    generate_id: bool = False,
) -> dict[str, Any]:
    """Valida e normaliza a definição persistida de um DataModel.

    ``sanitize_transform`` é o validator canônico de TransformPlan do
    chamador (ex.: ``PresentationPatchService.sanitize_vista_data_transform``);
    quando omitido, transforms passam sem sanitização (path de leitura).
    """
    if not isinstance(raw, dict):
        _fail("DataModel deve ser um objeto.")
    model_id = str(raw.get("id") or "").strip()
    if not model_id and generate_id:
        model_id = new_data_model_id()
    if not model_id:
        _fail("DataModel.id é obrigatório.", field="id")
    label = str(raw.get("label") or "").strip()

    inputs_raw = raw.get("inputs")
    if not isinstance(inputs_raw, list) or not inputs_raw:
        _fail(
            "DataModel.inputs é obrigatório e não pode ser vazio.",
            model_id=model_id,
            field="inputs",
        )

    inputs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    seen_query_names: set[str] = set()
    for index, item in enumerate(inputs_raw):
        if not isinstance(item, dict):
            _fail(
                "Cada input do DataModel deve ser um objeto.",
                model_id=model_id,
                field=f"inputs[{index}]",
            )
        input_id = str(item.get("id") or "").strip()
        if not input_id:
            _fail(
                "Todo input do DataModel precisa de id.",
                code="m.query_identity_required",
                model_id=model_id,
                inputIndex=index,
            )
        if input_id in seen_ids:
            _fail(
                f'Input id "{input_id}" duplicado no modelo.',
                model_id=model_id,
                inputId=input_id,
            )
        seen_ids.add(input_id)
        query_name = str(item.get("queryName") or "").strip() or input_id
        if query_name in seen_query_names:
            _fail(
                f'A consulta "{query_name}" foi declarada mais de uma vez.',
                code="m.duplicate_query_name",
                model_id=model_id,
                inputId=input_id,
            )
        seen_query_names.add(query_name)
        operation_id = str(item.get("operationId") or "").strip()
        if not operation_id:
            _fail(
                "Todo input do DataModel precisa de operationId.",
                model_id=model_id,
                inputId=input_id,
                field="operationId",
            )
        if catalog is not None:
            route = (
                catalog.get_route(operation_id)
                if hasattr(catalog, "get_route")
                else None
            )
            if not route:
                _fail(
                    f"operationId não está no catálogo TV allowlist: {operation_id}",
                    model_id=model_id,
                    inputId=input_id,
                    operationId=operation_id,
                )
        params = item.get("params")
        if params is None:
            params = {}
        if not isinstance(params, dict):
            _fail(
                "Input params deve ser um objeto.",
                model_id=model_id,
                inputId=input_id,
                field="params",
            )
        transform = _sanitize_transform_value(
            item.get("transform"),
            sanitize=sanitize_transform,
            model_id=model_id,
            field=f"inputs[{index}].transform",
        )
        normalized_input: dict[str, Any] = {
            "id": input_id,
            "label": str(item.get("label") or "").strip(),
            "queryName": query_name,
            "operationId": operation_id,
            "params": dict(params),
            "transform": transform,
        }
        inputs.append(normalized_input)

    primary_input_id = str(raw.get("primaryInputId") or "").strip()
    if not primary_input_id:
        _fail(
            "DataModel.primaryInputId é obrigatório.",
            model_id=model_id,
            field="primaryInputId",
        )
    if primary_input_id not in seen_ids:
        _fail(
            f'primaryInputId "{primary_input_id}" não existe em inputs.',
            model_id=model_id,
            primaryInputId=primary_input_id,
        )

    model_transform = _sanitize_transform_value(
        raw.get("transform"),
        sanitize=sanitize_transform,
        model_id=model_id,
        field="transform",
    )

    input_ids = seen_ids
    for index, item in enumerate(inputs):
        for ref in _merge_source_refs(item.get("transform")):
            if ref not in input_ids:
                _fail(
                    f'A fonte "{ref}" do merge não está disponível.',
                    code="m.merge_source_unavailable",
                    model_id=model_id,
                    inputId=item["id"],
                    sourceId=ref,
                )
    for ref in _merge_source_refs(model_transform):
        if ref not in input_ids:
            _fail(
                f'A fonte "{ref}" do merge não está disponível.',
                code="m.merge_source_unavailable",
                model_id=model_id,
                sourceId=ref,
            )

    # Ordem congelada: input.transform → model.transform no input primário.
    # Composição é concat de steps v1; script (v2) no modelo exige
    # input primário sem transform próprio.
    if isinstance(model_transform, dict) and model_transform.get("script"):
        primary = next(i for i in inputs if i["id"] == primary_input_id)
        if primary.get("transform"):
            _fail(
                "transform de modelo em script exige input primário sem transform.",
                model_id=model_id,
                inputId=primary_input_id,
                field="transform",
            )

    normalized: dict[str, Any] = {
        "id": model_id,
        "label": label,
        "primaryInputId": primary_input_id,
        "inputs": inputs,
        "transform": model_transform,
    }
    field_labels = raw.get("fieldLabels")
    if isinstance(field_labels, dict):
        normalized["fieldLabels"] = {
            str(k): str(v)
            for k, v in field_labels.items()
            if str(k).strip() and str(v).strip()
        }
    return normalized


def data_model_source_blocks(
    model: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """Projeta o DataModel nos nós ``data_source`` sintéticos do runtime.

    Cada input vira um nó com ``dataBinding``/``dataTransform`` próprios;
    o nó do ``primaryInputId`` recebe o transform do modelo concatenado
    após o transform local (ordem congelada: input.transform → model.transform).
    Retorna ``(nodes, primary_node_id)``.
    """
    nodes: list[dict[str, Any]] = []
    primary_id = str(model.get("primaryInputId") or "").strip()
    for item in model.get("inputs") or []:
        if not isinstance(item, dict):
            continue
        node: dict[str, Any] = {
            "id": str(item.get("id") or ""),
            "type": "data_source",
            "queryName": str(item.get("queryName") or item.get("id") or ""),
            "dataBinding": {
                "operationId": str(item.get("operationId") or ""),
                "params": dict(item.get("params") or {}),
                "displayMode": "auto",
                "label": str(item.get("label") or item.get("id") or ""),
            },
        }
        if isinstance(item.get("transform"), dict):
            node["dataTransform"] = dict(item["transform"])
        nodes.append(node)

    model_transform = model.get("transform")
    if isinstance(model_transform, dict) and (
        model_transform.get("steps") or model_transform.get("script")
    ):
        for node in nodes:
            if node["id"] != primary_id:
                continue
            prior = node.get("dataTransform")
            prior_steps = (
                prior.get("steps") if isinstance(prior, dict) else None
            )
            model_steps = model_transform.get("steps")
            if isinstance(prior_steps, list) and isinstance(model_steps, list):
                merged = dict(model_transform)
                merged["steps"] = [*prior_steps, *model_steps]
                node["dataTransform"] = merged
            elif prior is None:
                node["dataTransform"] = dict(model_transform)
            else:
                raise DataModelContractError(
                    "transform de modelo não combinável com o transform do "
                    "input primário.",
                    code=MODEL_CONTRACT_INVALID,
                    details={"modelId": model.get("id"), "inputId": primary_id},
                )
    return nodes, primary_id


def find_data_model(cfg: dict[str, Any], model_id: str) -> dict[str, Any] | None:
    for model in cfg.get("dataModels") or []:
        if isinstance(model, dict) and str(model.get("id") or "") == model_id:
            return model
    return None
