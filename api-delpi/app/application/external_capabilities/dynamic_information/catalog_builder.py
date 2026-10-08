"""Technical Action Catalog derived from OpenAPI (not semantic capability authority)."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping

from app.application.external_capabilities.dynamic_information.eligibility import (
    classify_operation,
    is_dynamically_executable,
    load_allowlist_operation_ids,
)
from app.application.external_capabilities.dynamic_information.projection import (
    _SIMPLE_KEY,
)

_HTTP = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})


class _InvalidNameBindings:
    """Marker for present-but-malformed trusted binding metadata.

    Distinct from ABSENT (metadata key missing → empty mapping): INVALID must
    never normalize to "no binding requested", which would let owner payload
    keys satisfy approved external fields implicitly. An action carrying this
    marker is non-executable and the projection layer drops everything.
    """

    def __repr__(self) -> str:
        return "<INVALID_NAME_BINDINGS>"


INVALID_NAME_BINDINGS = _InvalidNameBindings()


@dataclass(frozen=True)
class TechnicalAction:
    action_id: str
    operation_id: str
    method: str
    path: str
    summary: str
    description: str
    tags: tuple[str, ...]
    davi_status: str
    entity: str | None = None
    shape: str | None = None
    parameters: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    searchable_text: str = ""
    execution_mode: str | None = None
    approved_response_fields: tuple[str, ...] = field(default_factory=tuple)
    approved_input_fields: tuple[str, ...] = field(default_factory=tuple)
    semantic_aliases: tuple[str, ...] = field(default_factory=tuple)
    argument_constraints: Mapping[str, Any] = field(default_factory=dict)
    semantic_transport: str | None = None
    request_body: Mapping[str, Any] | None = None
    argument_bindings: Mapping[str, Any] = field(default_factory=dict)
    response_bindings: Mapping[str, Any] | _InvalidNameBindings = field(
        default_factory=dict
    )
    negative_aliases: tuple[str, ...] = field(default_factory=tuple)
    response_contract: str | None = None

    @property
    def executable(self) -> bool:
        # Invalid trusted binding metadata fails closed before execution:
        # the action is excluded from retrieval/discovery/token/execution
        # rather than running with silently degraded governance config.
        return is_dynamically_executable(self.davi_status) and not isinstance(
            self.response_bindings, _InvalidNameBindings
        )

    @property
    def body_fields(self) -> frozenset[str]:
        body = self.request_body or {}
        props = body.get("properties")
        if not isinstance(props, Mapping):
            return frozenset()
        return frozenset(str(k) for k in props)


def _param_names(parameters: list[dict[str, Any]] | None) -> list[str]:
    names: list[str] = []
    for p in parameters or []:
        if isinstance(p, dict) and p.get("name"):
            names.append(str(p["name"]))
    return names


def _param_descriptions(parameters: list[dict[str, Any]] | None) -> list[str]:
    texts: list[str] = []
    for p in parameters or []:
        if isinstance(p, dict) and p.get("description"):
            texts.append(str(p["description"]))
    return texts


def _allowlist_entry(allowlist: dict[str, Any], operation_id: str) -> dict[str, Any]:
    for item in allowlist.get("operations") or []:
        if isinstance(item, dict) and (item.get("operationId") or "").strip() == operation_id:
            return item
    return {}


def _normalize_name_bindings(raw: Any, *, owner_key: str | None = None) -> Mapping[str, str]:
    """Normalize trusted external→owner name bindings from allowlist metadata.

    Accepts ``{"external": "owner"}`` or ``{"external": {"ownerName": "owner"}}``.
    Non-string names are dropped (fail closed); empty output is an empty map.
    """
    if not isinstance(raw, dict):
        return MappingProxyType({})
    out: dict[str, str] = {}
    for external, spec in raw.items():
        if not isinstance(external, str) or not external.strip():
            continue
        owner = spec.get(owner_key) if isinstance(spec, dict) and owner_key else spec
        if not isinstance(owner, str) or not owner.strip():
            continue
        out[external.strip()] = owner.strip()
    return MappingProxyType(out)


def _normalize_response_bindings(raw: Any) -> Mapping[str, str] | _InvalidNameBindings:
    """Normalize trusted external←source response bindings.

    Three-state contract:
      ABSENT  — metadata key missing/``None`` → empty mapping, no translation;
      VALID   — a non-empty mapping of safe ``external: source`` (or
                ``external: {"source": source}``) identifier pairs;
      INVALID — present but malformed (non-dict, empty dict, invalid
                identifier, wildcard, source == external) →
                :data:`INVALID_NAME_BINDINGS`, never downgraded to
                "no binding".
    """
    if raw is None:
        return MappingProxyType({})
    if not isinstance(raw, dict) or not raw:
        # Present but not a valid non-empty mapping: an empty ``{}`` is not
        # "no binding requested" — only a missing/None key is ABSENT.
        return INVALID_NAME_BINDINGS
    out: dict[str, str] = {}
    for external, spec in raw.items():
        source = spec.get("source") if isinstance(spec, dict) else spec
        if not (
            isinstance(external, str)
            and isinstance(source, str)
            and external.strip()
            and source.strip()
            and _SIMPLE_KEY.fullmatch(external.strip())
            and _SIMPLE_KEY.fullmatch(source.strip())
            and external.strip() != source.strip()
        ):
            return INVALID_NAME_BINDINGS
        out[external.strip()] = source.strip()
    return MappingProxyType(out)


def _enrich_from_allowlist(
    allowlist: dict[str, Any],
    operation_id: str,
) -> tuple[
    str | None,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    Mapping[str, Any],
    str | None,
    Mapping[str, Any],
    Mapping[str, Any] | _InvalidNameBindings,
    tuple[str, ...],
    str | None,
]:
    entry = _allowlist_entry(allowlist, operation_id)
    mode = entry.get("executionMode")
    response_fields = tuple(str(f) for f in (entry.get("approvedResponseFields") or []) if f)
    input_fields = tuple(str(f) for f in (entry.get("approvedInputFields") or []) if f)
    aliases = tuple(str(a) for a in (entry.get("semanticAliases") or []) if a)
    negative_aliases = tuple(
        str(a) for a in (entry.get("retrievalNegativePhrases") or []) if a
    )
    raw_constraints = entry.get("argumentConstraints")
    constraints: Mapping[str, Any] = (
        MappingProxyType(dict(raw_constraints))
        if isinstance(raw_constraints, dict)
        else MappingProxyType({})
    )
    transport = (entry.get("semanticTransport") or "").strip() or None
    argument_bindings = _normalize_name_bindings(
        entry.get("argumentBindings"), owner_key="ownerName"
    )
    response_bindings = _normalize_response_bindings(entry.get("responseBindings"))
    response_contract = (entry.get("responseContract") or "").strip() or None
    return (
        str(mode) if mode else None,
        response_fields,
        input_fields,
        aliases,
        constraints,
        transport,
        argument_bindings,
        response_bindings,
        negative_aliases,
        response_contract,
    )


def _resolve_local_ref(schema: Any, openapi: dict[str, Any]) -> dict[str, Any] | None:
    """Resolve one local ``#/components/schemas/X`` ref. Fail closed otherwise."""
    if not isinstance(schema, dict):
        return None
    ref = schema.get("$ref")
    if not ref:
        return schema
    if not isinstance(ref, str) or not ref.startswith("#/components/schemas/"):
        return None
    name = ref[len("#/components/schemas/"):]
    target = ((openapi.get("components") or {}).get("schemas") or {}).get(name)
    if not isinstance(target, dict):
        return None
    if isinstance(target.get("$ref"), str):
        return None
    return target


def _normalize_body_property(prop: Any, openapi: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize one top-level body property (string / array<string> …)."""
    spec = _resolve_local_ref(prop, openapi)
    if spec is None:
        return None
    ptype = spec.get("type")
    out: dict[str, Any] = {}
    if ptype == "string":
        out["type"] = "string"
    elif ptype == "array":
        items = _resolve_local_ref(spec.get("items"), openapi)
        if not isinstance(items, dict) or items.get("type") != "string":
            return None
        out["type"] = "array"
        out["items"] = {"type": "string"}
    else:
        return None
    for key in ("default", "minItems", "maxItems", "minLength", "maxLength", "pattern", "enum"):
        if key in spec:
            out[key] = spec[key]
    return out


def _extract_request_body(
    op: dict[str, Any], openapi: dict[str, Any]
) -> Mapping[str, Any] | None:
    """Normalize a trusted top-level JSON requestBody schema.

    Returns ``None`` when there is no JSON body, and a mapping with
    ``supported=False`` when the shape cannot be normalized fail-closed.
    """
    request_body = op.get("requestBody")
    if not isinstance(request_body, dict):
        return None
    content = request_body.get("content")
    if not isinstance(content, dict):
        return {"properties": {}, "required": (), "supported": False}
    media = content.get("application/json")
    if not isinstance(media, dict):
        return {"properties": {}, "required": (), "supported": False}
    schema = _resolve_local_ref(media.get("schema"), openapi)
    if not isinstance(schema, dict) or schema.get("type") not in (None, "object"):
        return {"properties": {}, "required": (), "supported": False}
    raw_props = schema.get("properties")
    if not isinstance(raw_props, dict):
        return {"properties": {}, "required": (), "supported": False}
    properties: dict[str, Any] = {}
    for name, prop in raw_props.items():
        normalized = _normalize_body_property(prop, openapi)
        if normalized is None:
            return {"properties": {}, "required": (), "supported": False}
        properties[str(name)] = normalized
    required = tuple(str(n) for n in (schema.get("required") or []) if isinstance(n, str))
    return {"properties": properties, "required": required, "supported": True}


def _build_searchable_text(
    *,
    oid: str,
    summary: str,
    description: str,
    path: str,
    tags: tuple[str, ...],
    params: tuple[dict[str, Any], ...],
    entity: Any,
    shape: Any,
    aliases: tuple[str, ...],
) -> str:
    return " ".join(
        [
            oid,
            summary,
            description,
            path,
            " ".join(tags),
            " ".join(_param_names(list(params))),
            " ".join(_param_descriptions(list(params))),
            str(entity or ""),
            str(shape or ""),
            " ".join(aliases),
        ]
    ).lower()


def build_technical_actions_from_openapi(
    openapi: dict[str, Any],
    *,
    allowlist: dict[str, Any],
) -> list[TechnicalAction]:
    allowlisted = load_allowlist_operation_ids(allowlist)
    actions: list[TechnicalAction] = []
    paths = openapi.get("paths") or {}
    for path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for method, op in item.items():
            if method.lower() not in _HTTP or not isinstance(op, dict):
                continue
            oid = op.get("operationId") or f"{method.upper()}:{path}"
            summary = str(op.get("summary") or "")
            description = str(op.get("description") or "")
            tags = tuple(str(t) for t in (op.get("tags") or []) if t)
            x_delpi = op.get("x-delpi") or {}
            if not isinstance(x_delpi, dict):
                x_delpi = {}
            request_body = _extract_request_body(op, openapi)
            status = classify_operation(
                method=method,
                path=path,
                operation_id=op.get("operationId"),
                allowlisted_operation_ids=allowlisted,
                summary=summary,
                tags=list(tags),
                shape=str(x_delpi.get("shape") or "") or None,
                allowlist=allowlist,
                request_body_supported=bool(
                    request_body and request_body.get("supported") is True
                ),
            )
            params = tuple(p for p in (op.get("parameters") or []) if isinstance(p, dict))
            (
                mode,
                response_fields,
                input_fields,
                aliases,
                constraints,
                transport,
                argument_bindings,
                response_bindings,
                negative_aliases,
                response_contract,
            ) = _enrich_from_allowlist(allowlist, str(oid))
            actions.append(
                TechnicalAction(
                    action_id=str(oid),
                    operation_id=str(oid),
                    method=method.upper(),
                    path=path,
                    summary=summary,
                    description=description,
                    tags=tags,
                    davi_status=status,
                    entity=x_delpi.get("entity"),
                    shape=x_delpi.get("shape"),
                    parameters=params,
                    searchable_text=_build_searchable_text(
                        oid=str(oid),
                        summary=summary,
                        description=description,
                        path=path,
                        tags=tags,
                        params=params,
                        entity=x_delpi.get("entity"),
                        shape=x_delpi.get("shape"),
                        aliases=aliases,
                    ),
                    execution_mode=mode,
                    approved_response_fields=response_fields,
                    approved_input_fields=input_fields,
                    semantic_aliases=aliases,
                    argument_constraints=constraints,
                    semantic_transport=transport,
                    request_body=request_body,
                    argument_bindings=argument_bindings,
                    response_bindings=response_bindings,
                    negative_aliases=negative_aliases,
                    response_contract=response_contract,
                )
            )
    return actions


def build_technical_actions_from_baseline(
    baseline: dict[str, Any],
    *,
    allowlist: dict[str, Any],
) -> list[TechnicalAction]:
    """Fallback when full OpenAPI is unavailable (tests / offline inventory)."""
    allowlisted = load_allowlist_operation_ids(allowlist)
    actions: list[TechnicalAction] = []
    for row in baseline.get("operations") or []:
        if not isinstance(row, dict):
            continue
        method = str(row.get("method") or "")
        path = str(row.get("path") or "")
        oid = row.get("operationId")
        summary = str(row.get("summary") or "")
        description = str(row.get("description") or "")
        tags = tuple(str(t) for t in (row.get("tags") or []) if t)
        x_delpi = row.get("xDelpi") or row.get("x-delpi") or {}
        if not isinstance(x_delpi, dict):
            x_delpi = {}
        # Baseline rows carry no requestBody contract: a governed semantic
        # POST therefore cannot prove body support in this fallback and must
        # never become eligible from it.
        status = classify_operation(
            method=method,
            path=path,
            operation_id=oid,
            allowlisted_operation_ids=allowlisted,
            summary=summary,
            tags=list(tags),
            shape=str(x_delpi.get("shape") or "") or None,
            allowlist=allowlist,
            request_body_supported=False,
        )
        oid_s = str(oid or f"{method}:{path}")
        params = tuple(p for p in (row.get("parameters") or []) if isinstance(p, dict))
        (
            mode,
            response_fields,
            input_fields,
            aliases,
            constraints,
            transport,
            argument_bindings,
            response_bindings,
            negative_aliases,
            response_contract,
        ) = _enrich_from_allowlist(allowlist, oid_s)
        actions.append(
            TechnicalAction(
                action_id=oid_s,
                operation_id=oid_s,
                method=method.upper(),
                path=path,
                summary=summary,
                description=description,
                tags=tags,
                davi_status=status,
                entity=x_delpi.get("entity"),
                shape=x_delpi.get("shape"),
                parameters=params,
                searchable_text=_build_searchable_text(
                    oid=oid_s,
                    summary=summary,
                    description=description,
                    path=path,
                    tags=tags,
                    params=params,
                    entity=x_delpi.get("entity"),
                    shape=x_delpi.get("shape"),
                    aliases=aliases,
                ),
                execution_mode=mode,
                approved_response_fields=response_fields,
                approved_input_fields=input_fields,
                semantic_aliases=aliases,
                argument_constraints=constraints,
                semantic_transport=transport,
                argument_bindings=argument_bindings,
                response_bindings=response_bindings,
                negative_aliases=negative_aliases,
                response_contract=response_contract,
            )
        )
    return actions
