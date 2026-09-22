from __future__ import annotations

from dataclasses import fields

import pytest

from app.domain.capability_catalog.model import CapabilityProjection, OperationCharacter
from app.infrastructure.openapi.capability_catalog_adapter import (
    CapabilityDeclaration,
    OpenApiCapabilityProjectionError,
    project_openapi_document,
)


def _doc():
    return {
        "openapi": "3.1.0",
        "info": {"title": "C3-T5 fixture", "version": "1.0.0"},
        "components": {
            "securitySchemes": {"oauth": {"type": "oauth2"}},
            "schemas": {
                "SearchRequest": {"type": "object"},
                "SearchResult": {"type": "object"},
                "PreparedRequest": {"type": "object"},
                "ActionReceipt": {"type": "object"},
                "Error": {"type": "object"},
            },
        },
        "paths": {
            "/search": {
                "post": {
                    "operationId": "searchProducts",
                    "security": [{"oauth": ["products.read"]}],
                    "requestBody": {
                        "required": True,
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/SearchRequest"}}},
                    },
                    "responses": {
                        "200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/SearchResult"}}}},
                        "403": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/Error"}}}},
                    },
                }
            },
            "/purchase-requests/prepare": {
                "get": {
                    "operationId": "preparePurchaseRequest",
                    "parameters": [{"name": "itemId", "in": "query", "required": True, "schema": {"type": "string"}}],
                    "responses": {"200": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/PreparedRequest"}}}}},
                }
            },
            "/purchase-requests": {
                "post": {
                    "operationId": "createPurchaseRequest",
                    "responses": {"201": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/ActionReceipt"}}}}},
                }
            },
            "/ambiguous": {
                "delete": {
                    "operationId": "ambiguousDelete",
                    "responses": {"200": {"description": "ok"}},
                }
            },
        },
    }


def _declarations():
    return (
        CapabilityDeclaration(
            operation_id="searchProducts",
            capability_id="inventory.product.search",
            semantic_name="search_products",
            operation_character=OperationCharacter.READ,
        ),
        CapabilityDeclaration(
            operation_id="preparePurchaseRequest",
            capability_id="purchasing.request.prepare",
            semantic_name="prepare_purchase_request",
            operation_character=OperationCharacter.PREPARE,
        ),
        CapabilityDeclaration(
            operation_id="createPurchaseRequest",
            capability_id="purchasing.request.create",
            semantic_name="create_purchase_request",
            operation_character=OperationCharacter.ACT,
            idempotency_semantics="idempotency-key-required",
            reversible=None,
            required_postcondition="purchase_request_exists_in_authoritative_domain",
        ),
    )


def _project(document=None, declarations=None):
    return project_openapi_document(
        document or _doc(),
        source_owner="purchasing-domain-api",
        source_contract_id="purchasing.openapi",
        declarations=_declarations() if declarations is None else declarations,
    )


def test_projects_semantic_capabilities_with_source_identity():
    result = _project()
    assert [c.semantic_name for c in result.capabilities] == [
        "search_products",
        "prepare_purchase_request",
        "create_purchase_request",
    ]
    assert {c.source_contract.owner for c in result.capabilities} == {"purchasing-domain-api"}
    assert {c.source_contract.version for c in result.capabilities} == {"1.0.0"}
    assert all(c.source_contract.content_hash.startswith("sha256:") for c in result.capabilities)
    assert result.rejected[0].operation_id == "ambiguousDelete"
    assert result.rejected[0].reason == "missing_semantic_declaration"


def test_http_method_does_not_determine_operation_character():
    result = _project()
    by_id = {c.operation_id: c for c in result.capabilities}
    assert by_id["searchProducts"].http_method == "POST"
    assert by_id["searchProducts"].operation_character is OperationCharacter.READ
    assert by_id["preparePurchaseRequest"].http_method == "GET"
    assert by_id["preparePurchaseRequest"].operation_character is OperationCharacter.PREPARE


def test_read_prepare_act_are_distinct():
    chars = {c.operation_id: c.operation_character for c in _project().capabilities}
    assert chars["searchProducts"] is OperationCharacter.READ
    assert chars["preparePurchaseRequest"] is OperationCharacter.PREPARE
    assert chars["createPurchaseRequest"] is OperationCharacter.ACT
    assert OperationCharacter.PREPARE is not OperationCharacter.ACT


def test_projection_and_security_metadata_never_grant_authorization():
    result = _project()
    read = next(c for c in result.capabilities if c.operation_id == "searchProducts")
    assert read.security_requirements[0].scheme == "oauth"
    assert read.security_requirements[0].scopes == ("products.read",)
    assert read.security_requirements[0].grants_authorization() is False
    assert result.grants_authorization() is False
    assert read.grants_authorization() is False
    assert read.grants_source_access() is False
    assert read.grants_execution() is False
    assert read.authorizes_act() is False


def test_projection_has_no_current_user_authorization_field():
    names = {field.name for field in fields(CapabilityProjection)}
    assert not names.intersection({"is_authorized", "can_execute", "rbac_granted", "allowed_for_current_user"})


def test_act_projection_does_not_execute_or_authorize_act():
    act = next(c for c in _project().capabilities if c.operation_character is OperationCharacter.ACT)
    assert act.required_postcondition == "purchase_request_exists_in_authoritative_domain"
    assert act.idempotency_semantics == "idempotency-key-required"
    assert act.reversible is None
    assert act.authorizes_act() is False
    assert act.grants_execution() is False


def test_unknown_operation_character_fails_closed_by_missing_declaration():
    result = _project(declarations=())
    assert result.capabilities == ()
    assert {r.reason for r in result.rejected} == {"missing_semantic_declaration"}


def test_missing_operation_id_is_not_projectable():
    doc = _doc()
    del doc["paths"]["/search"]["post"]["operationId"]
    result = _project(document=doc)
    assert any(r.reason == "missing_operation_id" for r in result.rejected)
    assert all(c.http_path != "/search" for c in result.capabilities)


def test_duplicate_operation_id_fails_closed():
    doc = _doc()
    doc["paths"]["/duplicate"] = {
        "get": {"operationId": "searchProducts", "responses": {"200": {"description": "ok"}}}
    }
    result = _project(document=doc)
    assert all(c.operation_id != "searchProducts" for c in result.capabilities)
    duplicate_rejections = [r for r in result.rejected if r.operation_id == "searchProducts"]
    assert len(duplicate_rejections) == 2
    assert all(r.reason == "duplicate_operation_id" for r in duplicate_rejections)


def test_duplicate_semantic_declaration_fails_closed():
    duplicate = _declarations() + (_declarations()[0],)
    with pytest.raises(OpenApiCapabilityProjectionError, match="duplicate_semantic_declaration"):
        _project(declarations=duplicate)


def test_unsupported_auth_parameter_is_not_planner_input():
    doc = _doc()
    doc["paths"]["/search"]["post"]["parameters"] = [
        {"name": "Authorization", "in": "header", "required": True, "schema": {"type": "string"}}
    ]
    result = _project(document=doc)
    assert all(c.operation_id != "searchProducts" for c in result.capabilities)
    assert any(r.reason == "unsupported_transport_or_auth_parameter" for r in result.rejected)


def test_input_output_error_contracts_are_normalized_not_raw_openapi():
    read = next(c for c in _project().capabilities if c.operation_id == "searchProducts")
    assert read.inputs[0].name == "body"
    assert read.inputs[0].schema_ref == "#/components/schemas/SearchRequest"
    assert read.outputs[0].schema_ref == "#/components/schemas/SearchResult"
    assert read.errors[0].status_code == "403"
    assert read.errors[0].schema_ref == "#/components/schemas/Error"
    assert not isinstance(read.inputs[0], dict)


def test_contract_hash_is_stable_across_mapping_reordering():
    doc_a = _doc()
    doc_b = {"paths": doc_a["paths"], "components": doc_a["components"], "info": doc_a["info"], "openapi": doc_a["openapi"]}
    assert _project(doc_a).source_contract.content_hash == _project(doc_b).source_contract.content_hash
