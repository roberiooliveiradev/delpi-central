"""Deterministic OpenAPI -> CapabilityProjection adapter for C3-T5.

OpenAPI supplies technical contract metadata. Semantic capability identity and
operation character come from an explicit governed declaration, never from HTTP
verb/path/operationId heuristics. Missing or ambiguous semantics fail closed.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from app.domain.capability_catalog.model import (
    CapabilityProjection,
    ErrorDescriptor,
    InputDescriptor,
    OperationCharacter,
    OutputDescriptor,
    SecurityRequirementDescriptor,
    SourceContractRef,
)

_HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "options", "head", "trace"})
_SUPPORTED_PARAMETER_LOCATIONS = frozenset({"query", "path"})
_AUTH_INPUT_NAMES = frozenset({"authorization", "proxy-authorization", "x-api-key", "api-key", "apikey"})


class OpenApiCapabilityProjectionError(ValueError):
    """Invalid source contract or deterministic projection failure."""


@dataclass(frozen=True, slots=True)
class CapabilityDeclaration:
    """Governed semantic declaration external to transport heuristics."""

    operation_id: str
    capability_id: str
    semantic_name: str
    operation_character: OperationCharacter
    idempotency_semantics: str | None = None
    reversible: bool | None = None
    required_postcondition: str | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("operation_id", self.operation_id),
            ("capability_id", self.capability_id),
            ("semantic_name", self.semantic_name),
        ):
            if not value.strip():
                raise ValueError(f"CapabilityDeclaration.{name} is required")


@dataclass(frozen=True, slots=True)
class ProjectionRejection:
    operation_id: str | None
    http_method: str
    http_path: str
    reason: str


@dataclass(frozen=True, slots=True)
class OpenApiCatalogProjection:
    source_contract: SourceContractRef
    capabilities: tuple[CapabilityProjection, ...]
    rejected: tuple[ProjectionRejection, ...]

    def grants_authorization(self) -> bool:
        return False


def project_openapi_document(
    document: Mapping[str, Any],
    *,
    source_owner: str,
    source_contract_id: str,
    declarations: Sequence[CapabilityDeclaration],
) -> OpenApiCatalogProjection:
    """Project a bounded OpenAPI document into semantic capabilities.

    This function never executes the described operations and never resolves
    current-user permission. A declaration is required for semantic identity and
    operation character; HTTP method alone is never sufficient.
    """

    source = _source_contract_ref(document, source_owner, source_contract_id)
    declaration_map = _declaration_map(declarations)
    operations = list(_iter_operations(document))
    duplicate_ids = {
        op_id
        for op_id, count in Counter(op_id for _, _, _, op_id in operations if op_id).items()
        if count > 1
    }

    capabilities: list[CapabilityProjection] = []
    rejected: list[ProjectionRejection] = []

    for path, method, operation, operation_id in operations:
        if not operation_id:
            rejected.append(ProjectionRejection(None, method.upper(), path, "missing_operation_id"))
            continue
        if operation_id in duplicate_ids:
            rejected.append(
                ProjectionRejection(operation_id, method.upper(), path, "duplicate_operation_id")
            )
            continue
        declaration = declaration_map.get(operation_id)
        if declaration is None:
            rejected.append(
                ProjectionRejection(operation_id, method.upper(), path, "missing_semantic_declaration")
            )
            continue
        try:
            inputs = _input_descriptors(document, path, operation)
            outputs, errors = _response_descriptors(operation)
            security = _security_descriptors(document, operation)
        except OpenApiCapabilityProjectionError as exc:
            rejected.append(ProjectionRejection(operation_id, method.upper(), path, str(exc)))
            continue

        capabilities.append(
            CapabilityProjection(
                capability_id=declaration.capability_id,
                semantic_name=declaration.semantic_name,
                owner=source.owner,
                operation_character=declaration.operation_character,
                source_contract=source,
                operation_id=operation_id,
                http_method=method.upper(),
                http_path=path,
                inputs=inputs,
                outputs=outputs,
                errors=errors,
                security_requirements=security,
                idempotency_semantics=declaration.idempotency_semantics,
                reversible=declaration.reversible,
                required_postcondition=declaration.required_postcondition,
            )
        )

    return OpenApiCatalogProjection(source, tuple(capabilities), tuple(rejected))


def _source_contract_ref(
    document: Mapping[str, Any], source_owner: str, source_contract_id: str
) -> SourceContractRef:
    if not source_owner.strip():
        raise OpenApiCapabilityProjectionError("ambiguous_source_owner")
    if not source_contract_id.strip():
        raise OpenApiCapabilityProjectionError("missing_source_contract_id")
    info = document.get("info")
    if not isinstance(info, Mapping):
        raise OpenApiCapabilityProjectionError("missing_openapi_info")
    version = info.get("version")
    if not isinstance(version, str) or not version.strip():
        raise OpenApiCapabilityProjectionError("missing_source_contract_version")
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return SourceContractRef(
        owner=source_owner,
        contract_id=source_contract_id,
        version=version,
        content_hash=f"sha256:{digest}",
    )


def _declaration_map(
    declarations: Sequence[CapabilityDeclaration],
) -> dict[str, CapabilityDeclaration]:
    counts = Counter(item.operation_id for item in declarations)
    duplicate = sorted(op_id for op_id, count in counts.items() if count > 1)
    if duplicate:
        raise OpenApiCapabilityProjectionError(
            "duplicate_semantic_declaration:" + ",".join(duplicate)
        )
    return {item.operation_id: item for item in declarations}


def _iter_operations(document: Mapping[str, Any]):
    paths = document.get("paths")
    if not isinstance(paths, Mapping):
        raise OpenApiCapabilityProjectionError("missing_openapi_paths")
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, Mapping):
            continue
        for method, operation in path_item.items():
            if str(method).lower() not in _HTTP_METHODS or not isinstance(operation, Mapping):
                continue
            raw_id = operation.get("operationId")
            operation_id = raw_id.strip() if isinstance(raw_id, str) and raw_id.strip() else None
            yield path, str(method).lower(), operation, operation_id


def _input_descriptors(
    document: Mapping[str, Any], path: str, operation: Mapping[str, Any]
) -> tuple[InputDescriptor, ...]:
    descriptors: list[InputDescriptor] = []
    path_item = document.get("paths", {}).get(path, {})
    params = []
    for source in (path_item.get("parameters", ()), operation.get("parameters", ())):
        if source is None:
            continue
        if not isinstance(source, Sequence) or isinstance(source, (str, bytes)):
            raise OpenApiCapabilityProjectionError("unsupported_parameter_semantics")
        params.extend(source)

    for param in params:
        if not isinstance(param, Mapping) or "$ref" in param:
            raise OpenApiCapabilityProjectionError("unsupported_parameter_semantics")
        name = param.get("name")
        location = param.get("in")
        if not isinstance(name, str) or not name.strip() or not isinstance(location, str):
            raise OpenApiCapabilityProjectionError("unsupported_parameter_semantics")
        location = location.lower()
        if name.strip().lower() in _AUTH_INPUT_NAMES or location not in _SUPPORTED_PARAMETER_LOCATIONS:
            raise OpenApiCapabilityProjectionError("unsupported_transport_or_auth_parameter")
        schema = param.get("schema", {})
        schema_type, schema_ref = _schema_identity(schema)
        descriptors.append(
            InputDescriptor(
                name=name,
                location=location,
                required=bool(param.get("required", False)),
                schema_type=schema_type,
                schema_ref=schema_ref,
            )
        )

    request_body = operation.get("requestBody")
    if request_body is not None:
        if not isinstance(request_body, Mapping) or "$ref" in request_body:
            raise OpenApiCapabilityProjectionError("unsupported_request_body_semantics")
        content = request_body.get("content")
        if not isinstance(content, Mapping):
            raise OpenApiCapabilityProjectionError("unsupported_request_body_semantics")
        json_body = content.get("application/json")
        if not isinstance(json_body, Mapping):
            raise OpenApiCapabilityProjectionError("unsupported_request_body_media_type")
        schema_type, schema_ref = _schema_identity(json_body.get("schema", {}))
        descriptors.append(
            InputDescriptor(
                name="body",
                location="body",
                required=bool(request_body.get("required", False)),
                schema_type=schema_type,
                schema_ref=schema_ref,
            )
        )
    return tuple(descriptors)


def _response_descriptors(
    operation: Mapping[str, Any],
) -> tuple[tuple[OutputDescriptor, ...], tuple[ErrorDescriptor, ...]]:
    responses = operation.get("responses")
    if not isinstance(responses, Mapping) or not responses:
        raise OpenApiCapabilityProjectionError("missing_response_contract")
    outputs: list[OutputDescriptor] = []
    errors: list[ErrorDescriptor] = []
    for raw_status, response in responses.items():
        status = str(raw_status)
        if not isinstance(response, Mapping) or "$ref" in response:
            raise OpenApiCapabilityProjectionError("unsupported_response_semantics")
        schema_type, schema_ref = _response_schema_identity(response)
        if status.startswith("2"):
            outputs.append(OutputDescriptor(status, schema_type, schema_ref))
        elif status == "default" or status.startswith(("4", "5")):
            errors.append(ErrorDescriptor(status, schema_ref))
    if not outputs:
        raise OpenApiCapabilityProjectionError("missing_success_response_contract")
    return tuple(outputs), tuple(errors)


def _response_schema_identity(response: Mapping[str, Any]) -> tuple[str | None, str | None]:
    content = response.get("content")
    if content is None:
        return None, None
    if not isinstance(content, Mapping):
        raise OpenApiCapabilityProjectionError("unsupported_response_semantics")
    json_body = content.get("application/json")
    if json_body is None:
        return None, None
    if not isinstance(json_body, Mapping):
        raise OpenApiCapabilityProjectionError("unsupported_response_semantics")
    return _schema_identity(json_body.get("schema", {}))


def _schema_identity(schema: Any) -> tuple[str | None, str | None]:
    if not isinstance(schema, Mapping):
        raise OpenApiCapabilityProjectionError("unsupported_schema_semantics")
    ref = schema.get("$ref")
    if ref is not None:
        if not isinstance(ref, str) or not ref.strip():
            raise OpenApiCapabilityProjectionError("unsupported_schema_semantics")
        return None, ref
    schema_type = schema.get("type")
    if schema_type is None:
        return None, None
    if not isinstance(schema_type, str):
        raise OpenApiCapabilityProjectionError("unsupported_schema_semantics")
    return schema_type, None


def _security_descriptors(
    document: Mapping[str, Any], operation: Mapping[str, Any]
) -> tuple[SecurityRequirementDescriptor, ...]:
    raw_security = operation.get("security", document.get("security", ()))
    if raw_security in (None, []):
        return ()
    if not isinstance(raw_security, Sequence) or isinstance(raw_security, (str, bytes)):
        raise OpenApiCapabilityProjectionError("unsupported_security_metadata")
    descriptors: list[SecurityRequirementDescriptor] = []
    for requirement in raw_security:
        if not isinstance(requirement, Mapping):
            raise OpenApiCapabilityProjectionError("unsupported_security_metadata")
        for scheme, scopes in requirement.items():
            if not isinstance(scheme, str) or not scheme.strip():
                raise OpenApiCapabilityProjectionError("unsupported_security_metadata")
            if scopes is None:
                scope_values: tuple[str, ...] = ()
            elif isinstance(scopes, Sequence) and not isinstance(scopes, (str, bytes)):
                if not all(isinstance(scope, str) for scope in scopes):
                    raise OpenApiCapabilityProjectionError("unsupported_security_metadata")
                scope_values = tuple(scopes)
            else:
                raise OpenApiCapabilityProjectionError("unsupported_security_metadata")
            descriptors.append(SecurityRequirementDescriptor(scheme, scope_values))
    return tuple(descriptors)
