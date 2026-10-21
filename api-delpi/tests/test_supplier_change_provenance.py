"""Supplier write provenance — domain validation, tracking link and reads.

v1 policy is fail-closed for external-official claims: GOVERNMENT_API,
THIRD_PARTY_API and AUTOMATION_RULE sources, suggestion-based modes and
AUTOMATED_BY_APPROVED_POLICY are rejected until a server-verifiable
evidence/policy contract exists.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.application.services.integration_tracking.tracking_service import (
    IntegrationTrackingService,
)
from app.domain.integrations.protheus_rest import ProtheusRestError
from app.domain.integrations.supplier_change_provenance import (
    build_supplier_field_provenance,
    parse_change_context,
)

ACTOR_UUID = "401b25fa-ccd1-4800-8a12-a767909956b4"
SENT = {"supplier_name": "X", "district": "CENTRO", "phone": "4733330000"}


def _context(**overrides):
    base = {
        "schema_version": "1",
        "change_mode": "MANUAL_DIRECT",
        "field_provenance": [
            {"field_key": "supplier_name", "source_type": "MANUAL_USER_INPUT"}
        ],
    }
    base.update(overrides)
    return base


def _code(exc: ProtheusRestError) -> str:
    return exc.code or ""


# --------------------------------------------------------------------- parse


def test_valid_manual_provenance() -> None:
    ctx = parse_change_context(_context(), sent_fields=set(SENT))
    assert ctx.change_mode.value == "MANUAL_DIRECT"
    assert ctx.field_provenance[0].field_key == "supplier_name"


def test_internal_system_requires_source_id() -> None:
    ctx = _context(
        change_mode="SYSTEM_SYNC",
        field_provenance=[
            {
                "field_key": "phone",
                "source_type": "INTERNAL_SYSTEM",
                "source_id": "erp_directory",
            }
        ],
    )
    parsed = parse_change_context(ctx, sent_fields=set(SENT))
    assert parsed.field_provenance[0].source_id == "erp_directory"

    missing = _context(
        change_mode="SYSTEM_SYNC",
        field_provenance=[
            {"field_key": "phone", "source_type": "INTERNAL_SYSTEM"}
        ],
    )
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(missing, sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_SOURCE_ID_REQUIRED"


def test_mixed_source_fields_accepted() -> None:
    ctx = _context(
        change_mode="IMPORT_JOB",
        field_provenance=[
            {"field_key": "supplier_name", "source_type": "MANUAL_USER_INPUT"},
            {
                "field_key": "district",
                "source_type": "IMPORT",
                "source_id": "migration_xlsx",
                "source_reference": "batch-77",
            },
        ],
    )
    parsed = parse_change_context(ctx, sent_fields=set(SENT))
    assert {p.field_key for p in parsed.field_provenance} == {
        "supplier_name",
        "district",
    }


# -------------------------------------------------------------- fail-closed


@pytest.mark.parametrize(
    "source_type",
    ["GOVERNMENT_API", "THIRD_PARTY_API", "AUTOMATION_RULE", "UNKNOWN_LEGACY"],
)
def test_unverifiable_source_types_rejected(source_type: str) -> None:
    ctx = _context(
        field_provenance=[
            {
                "field_key": "supplier_name",
                "source_type": source_type,
                "source_id": "serpro",
                "source_reference": "doc-1",
            }
        ]
    )
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(ctx, sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_SOURCE_NOT_VERIFIABLE"


@pytest.mark.parametrize(
    "mode",
    [
        "EXTERNAL_SUGGESTION_USER_APPROVED",
        "BULK_SUGGESTION_USER_APPROVED",
        "AUTOMATED_BY_APPROVED_POLICY",
    ],
)
def test_non_claimable_change_modes_rejected(mode: str) -> None:
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(_context(change_mode=mode), sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_CHANGE_MODE_NOT_AUTHORIZED"


def test_provenance_for_field_not_sent_rejected() -> None:
    ctx = _context(
        field_provenance=[
            {"field_key": "email", "source_type": "MANUAL_USER_INPUT"}
        ]
    )
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(ctx, sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_FIELD_NOT_IN_PAYLOAD"


def test_duplicate_field_key_rejected() -> None:
    ctx = _context(
        field_provenance=[
            {"field_key": "supplier_name", "source_type": "MANUAL_USER_INPUT"},
            {"field_key": "supplier_name", "source_type": "MANUAL_USER_INPUT"},
        ]
    )
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(ctx, sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_FIELD_DUPLICATED"


@pytest.mark.parametrize(
    "key",
    ["actor_subject", "initiating_client_id", "caller_app", "policy_id"],
)
def test_client_cannot_declare_identity_or_policy(key: str) -> None:
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(
            _context(**{key: "spoofed"}), sent_fields=set(SENT)
        )
    assert _code(exc.value) == "PROVENANCE_IDENTITY_CLIENT_FORBIDDEN"


def test_schema_version_enforced() -> None:
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(
            _context(schema_version="2"), sent_fields=set(SENT)
        )
    assert _code(exc.value) == "PROVENANCE_SCHEMA_VERSION_UNSUPPORTED"


def test_missing_field_provenance_rejected() -> None:
    ctx = _context()
    del ctx["field_provenance"]
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(ctx, sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_FIELD_METADATA_REQUIRED"


def test_invalid_retrieved_at_rejected() -> None:
    ctx = _context(
        field_provenance=[
            {
                "field_key": "supplier_name",
                "source_type": "MANUAL_USER_INPUT",
                "source_retrieved_at": "not-a-date",
            }
        ]
    )
    with pytest.raises(ProtheusRestError) as exc:
        parse_change_context(ctx, sent_fields=set(SENT))
    assert _code(exc.value) == "PROVENANCE_METADATA_INVALID"


# ------------------------------------------------------------------- legacy


def test_legacy_write_gets_unknown_legacy_per_field() -> None:
    rows = build_supplier_field_provenance(
        None,
        sent_fields=SENT,
        supplier_code="003878",
        supplier_store="01",
        environment_key="ambiente:1@host",
        caller_app="supplies-api",
        actor_subject="user-1",
    )
    assert len(rows) == 3
    assert all(r["source_type"] == "UNKNOWN_LEGACY" for r in rows)
    assert all(r["change_mode"] is None for r in rows)
    assert all(r["source_id"] is None for r in rows)
    assert all(r["supplier_code"] == "003878" for r in rows)
    assert all(r["initiating_client_id"] == "supplies-api" for r in rows)


def test_declared_context_produces_records_with_mode() -> None:
    rows = build_supplier_field_provenance(
        _context(
            reason_code="CADASTRAL_REVIEW",
            field_provenance=[
                {
                    "field_key": "district",
                    "source_type": "MANUAL_USER_INPUT",
                    "decision_id": "dec-1",
                }
            ],
        ),
        sent_fields=SENT,
        supplier_code="003878",
        supplier_store="01",
        environment_key="ambiente:1@host",
        caller_app="supplies-api",
        actor_subject="user-1",
    )
    assert len(rows) == 1
    assert rows[0]["field_key"] == "district"
    assert rows[0]["change_mode"] == "MANUAL_DIRECT"
    assert rows[0]["reason_code"] == "CADASTRAL_REVIEW"
    assert rows[0]["decision_id"] == "dec-1"
    assert rows[0]["actor_subject"] == "user-1"


# ---------------------------------------------------------- tracking service


class _FakeRepo:
    """In-memory adapter honoring the repository contract."""

    def __init__(self) -> None:
        self.operations: dict[str, dict] = {}
        self.provenance: list[dict] = []
        self._seq = 0

    def insert_operation(self, data, *, schema_version: int) -> None:
        self.operations[data.operation_id] = {
            "operation_id": data.operation_id,
            "status": "CREATED",
            "version": 0,
            "caller_app": data.caller_app,
            "actor_subject": data.actor_subject,
            "resource_key": data.resource_key,
            "correlation_id": data.correlation_id,
        }
        for record in data.field_provenance:
            row = dict(record)
            row["operation_id"] = data.operation_id
            row["provenance_id"] = f"prov-{len(self.provenance)}"
            self._seq += 1
            row["created_at"] = self._seq
            self.provenance.append(row)

    def apply_transition(self, operation_id, *, expected_version,
                         expected_status, patch, correlation_id):
        row = self.operations[operation_id]
        row["status"] = patch.status_to
        if patch.confirmed_at:
            row["confirmed_at"] = f"confirmed-{operation_id}"
        row["version"] += 1

    def get_operation(self, operation_id):
        return self.operations.get(operation_id)

    def list_events(self, operation_id, *, limit, offset):
        return []

    def list_supplier_field_provenance(
        self, *, resource_key, supplier_code, supplier_store,
        caller_app, actor_subject, field_key, limit, offset,
    ) -> list[dict]:
        rows = []
        for item in self.provenance:
            op = self.operations[item["operation_id"]]
            if not (
                op["resource_key"] == resource_key
                or (
                    item.get("supplier_code") == supplier_code
                    and item.get("supplier_store") == supplier_store
                )
            ):
                continue
            if caller_app is not None and op["caller_app"] != caller_app:
                continue
            if caller_app is None and (
                op["caller_app"] is not None
                or op["actor_subject"] != actor_subject
            ):
                continue
            if field_key and item["field_key"] != field_key:
                continue
            row = dict(item)
            row["operation_status"] = op["status"]
            row["operation_confirmed_at"] = op.get("confirmed_at")
            rows.append(row)
        rows.sort(key=lambda r: r["created_at"], reverse=True)
        return rows[offset:offset + limit]


def _begin(service: IntegrationTrackingService, *, caller="supplies-api",
           actor="user-1", provenance=None, resource_key="00387801") -> str:
    return service.begin_operation(
        integration="protheus",
        resource="supplier",
        action="update",
        resource_key=resource_key,
        environment_key="ambiente:1@host",
        company_scope=None,
        caller_app=caller,
        actor_subject=actor,
        protheus_user_id="000311",
        authorization_context=None,
        request_payload=None,
        outbound_payload=None,
        request_hash=None,
        outbound_hash=None,
        correlation_id="corr-1",
        request_id=None,
        field_provenance=provenance,
    )


def _provenance_rows(fields, source="MANUAL_USER_INPUT"):
    return [
        {
            "field_key": key,
            "source_type": source,
            "change_mode": "MANUAL_DIRECT",
            "supplier_code": "003878",
            "supplier_store": "01",
            "environment_key": "ambiente:1@host",
            "initiating_client_id": "supplies-api",
            "actor_subject": "user-1",
            "source_id": None,
            "source_reference": None,
            "source_retrieved_at": None,
            "reason_code": None,
            "review_id": None,
            "decision_id": None,
        }
        for key in fields
    ]


def test_begin_persists_provenance_atomically() -> None:
    repo = _FakeRepo()
    service = IntegrationTrackingService(repository=repo)
    op_id = _begin(service, provenance=_provenance_rows(["supplier_name"]))
    assert repo.provenance[0]["operation_id"] == op_id
    assert repo.provenance[0]["field_key"] == "supplier_name"


def test_latest_confirmed_only_counts_confirmed_operations() -> None:
    repo = _FakeRepo()
    service = IntegrationTrackingService(repository=repo)

    op1 = _begin(service, provenance=_provenance_rows(["supplier_name"]))
    service.mark_sending(op1)
    service.record_acknowledged(op1, http_status=200, response_payload=None)
    service.confirm(op1, evidence={"method": "READ_AFTER_WRITE"})

    op2 = _begin(
        service,
        provenance=[
            {**_provenance_rows(["supplier_name"])[0], "source_type": "INTERNAL_SYSTEM"}
        ],
    )
    # op2 stays CREATED/SENDING — never promoted to latest_confirmed.
    result = service.list_supplier_provenance(
        supplier_id="00387801",
        caller_app="supplies-api",
        actor_subject="user-1",
    )
    field = result["fields"][0]
    assert field["latest_confirmed"]["source_type"] == "MANUAL_USER_INPUT"
    assert field["latest_confirmed"]["operation_status"] == "CONFIRMED"
    assert field["has_unconfirmed_newer_attempts"] is True
    assert field["attempt_count"] == 2


def test_acknowledged_is_not_confirmed_origin() -> None:
    repo = _FakeRepo()
    service = IntegrationTrackingService(repository=repo)
    op = _begin(service, provenance=_provenance_rows(["district"]))
    service.mark_sending(op)
    service.record_acknowledged(op, http_status=200, response_payload=None)
    result = service.list_supplier_provenance(
        supplier_id="00387801",
        caller_app="supplies-api",
        actor_subject="user-1",
    )
    assert result["fields"][0]["latest_confirmed"] is None
    assert result["fields"][0]["has_unconfirmed_newer_attempts"] is True


def test_other_consumer_cannot_read_provenance() -> None:
    repo = _FakeRepo()
    service = IntegrationTrackingService(repository=repo)
    _begin(service, provenance=_provenance_rows(["supplier_name"]))
    result = service.list_supplier_provenance(
        supplier_id="00387801",
        caller_app="other-bff",
        actor_subject="user-1",
    )
    assert result["fields"] == []
    assert result["attempts"] == []


def test_field_filter_and_pagination() -> None:
    repo = _FakeRepo()
    service = IntegrationTrackingService(repository=repo)
    _begin(service, provenance=_provenance_rows(["supplier_name", "district"]))
    result = service.list_supplier_provenance(
        supplier_id="00387801",
        caller_app="supplies-api",
        actor_subject="user-1",
        field_key="district",
    )
    assert [f["field_key"] for f in result["fields"]] == ["district"]


# --------------------------------------------------------------- use case


def _update_uc(tracker, identity, gateway, token):
    from app.application.use_cases.integrations.update_protheus_rest_supplier_use_case import (
        UpdateProtheusRestSupplierUseCase,
    )

    params = MagicMock()
    params.load_raw_params.return_value = {}
    return UpdateProtheusRestSupplierUseCase(
        params_repository=params,
        token_service=token,
        gateway=gateway,
        identity_gateway=identity,
        tracker=tracker,
    )


def _enabled_update_deps(monkeypatch):
    from app.application.use_cases.integrations import (
        update_protheus_rest_supplier_use_case as uc_mod,
    )
    from app.config import settings
    from app.domain.integrations.protheus_rest import ProtheusRestConfig

    monkeypatch.setattr(settings, 'PROTHEUS_SUPPLIER_UPDATE_ENABLED', True)
    config = ProtheusRestConfig(
        username='u', password='p', base_url='https://p.example/rest',
        auth_path='/t', suppliers_path='/s',
    )
    monkeypatch.setattr(
        uc_mod, 'resolve_protheus_rest_config', lambda _raw: config
    )
    identity = MagicMock()
    identity.get_identity_for_user.return_value = {
        'mapping_status': 'mapped',
        'verified': True,
        'protheus_user_id': '000161',
    }
    gateway = MagicMock()
    gateway.update_supplier.return_value = {
        'write_outcome': 'accepted_by_upstream',
        'update_acknowledged': True,
        'update_confirmed': False,
        'persistence_proven': False,
    }
    tracker = MagicMock()
    tracker.begin_operation.return_value = 'op-1'
    token = MagicMock()
    token.get_valid_token.return_value = 'tok'
    return tracker, identity, gateway, token


def test_update_uc_passes_provenance_to_tracker(monkeypatch) -> None:
    tracker, identity, gateway, token = _enabled_update_deps(monkeypatch)
    _update_uc(tracker, identity, gateway, token).execute(
        actor_user_id=UUID(ACTOR_UUID),
        supplier_id='00387801',
        fornecedor={'supplier_name': 'NOVO NOME'},
        caller_app='supplies-api',
        change_context={
            'schema_version': '1',
            'change_mode': 'MANUAL_DIRECT',
            'field_provenance': [
                {
                    'field_key': 'supplier_name',
                    'source_type': 'MANUAL_USER_INPUT',
                }
            ],
        },
    )
    prov = tracker.begin_operation.call_args.kwargs['field_provenance']
    assert len(prov) == 1
    assert prov[0]['field_key'] == 'supplier_name'
    assert prov[0]['source_type'] == 'MANUAL_USER_INPUT'
    assert prov[0]['supplier_code'] == '003878'
    assert prov[0]['supplier_store'] == '01'
    assert prov[0]['initiating_client_id'] == 'supplies-api'
    # upstream body stays untouched — provenance never reaches MATA020
    body = gateway.update_supplier.call_args.kwargs['body']
    assert body['fornecedor'] == {'supplier_name': 'NOVO NOME'}


def test_update_uc_legacy_write_marks_unknown_legacy(monkeypatch) -> None:
    tracker, identity, gateway, token = _enabled_update_deps(monkeypatch)
    _update_uc(tracker, identity, gateway, token).execute(
        actor_user_id=UUID(ACTOR_UUID),
        supplier_id='00387801',
        fornecedor={'supplier_name': 'X', 'district': 'Y'},
        caller_app='supplies-api',
    )
    prov = tracker.begin_operation.call_args.kwargs['field_provenance']
    assert len(prov) == 2
    assert all(r['source_type'] == 'UNKNOWN_LEGACY' for r in prov)


def test_update_uc_rejects_government_claim_before_any_send(
    monkeypatch,
) -> None:
    tracker, identity, gateway, token = _enabled_update_deps(monkeypatch)
    with pytest.raises(ProtheusRestError) as exc:
        _update_uc(tracker, identity, gateway, token).execute(
            actor_user_id=UUID(ACTOR_UUID),
            supplier_id='00387801',
            fornecedor={'supplier_name': 'X'},
            caller_app='supplies-api',
            change_context={
                'schema_version': '1',
                'change_mode': 'MANUAL_DIRECT',
                'field_provenance': [
                    {
                        'field_key': 'supplier_name',
                        'source_type': 'GOVERNMENT_API',
                        'source_id': 'serpro',
                        'source_reference': 'doc',
                    }
                ],
            },
        )
    assert exc.value.code == 'PROVENANCE_SOURCE_NOT_VERIFIABLE'
    tracker.begin_operation.assert_not_called()
    gateway.update_supplier.assert_not_called()
    token.get_valid_token.assert_not_called()
