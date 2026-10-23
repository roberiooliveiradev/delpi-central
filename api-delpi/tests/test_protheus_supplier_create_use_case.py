"""Use-case tests — Core identity gates + feature gate (no live Protheus write)."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.integrations.create_protheus_rest_supplier_use_case import (
    CreateProtheusRestSupplierUseCase,
)
from app.domain.integrations.protheus_rest import ProtheusRestConfig, ProtheusRestError

ACTOR = UUID("401b25fa-ccd1-4800-8a12-a767909956b4")
_CONFIG = ProtheusRestConfig(
    username="u",
    password="p",
    base_url="https://protheus.example/rest",
    auth_path="/api/oauth2/v1/token",
    suppliers_path="/delpi/api/v1/suppliers",
)


def _uc(**overrides) -> CreateProtheusRestSupplierUseCase:
    params = MagicMock()
    params.load_raw_params.return_value = {"ok": True}
    token = MagicMock()
    token.get_valid_token.return_value = "tok"
    gateway = MagicMock()
    identity = MagicMock()
    kwargs = dict(
        params_repository=params,
        token_service=token,
        gateway=gateway,
        identity_gateway=identity,
        tracker=MagicMock(),
    )
    kwargs.update(overrides)
    return CreateProtheusRestSupplierUseCase(**kwargs)


def _mapped(verified: bool = True, status: str = "mapped", usr: str = "000161") -> dict:
    return {
        "mapping_status": status,
        "verified": verified,
        "protheus_user_id": usr,
    }


def test_feature_gate_blocks_before_core_and_upstream(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", False)
    identity = MagicMock()
    identity.get_identity_for_user.side_effect = AssertionError("core must not be called")
    gateway = MagicMock()
    params = MagicMock()
    token = MagicMock()
    uc = _uc(
        identity_gateway=identity,
        gateway=gateway,
        params_repository=params,
        token_service=token,
    )

    with pytest.raises(ProtheusRestError) as exc:
        uc.execute(actor_user_id=ACTOR, fornecedor={"supplier_store": "01"})
    assert exc.value.code == "PROTHEUS_SUPPLIER_CREATE_DISABLED"
    identity.get_identity_for_user.assert_not_called()
    params.load_raw_params.assert_not_called()
    token.get_valid_token.assert_not_called()
    gateway.create_supplier.assert_not_called()


def test_invalid_payload_precedes_feature_gate(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", False)
    identity = MagicMock()
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_name": "SEM LOJA"}
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
    identity.get_identity_for_user.assert_not_called()


def test_mapped_verified_calls_gateway_when_enabled(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        create_protheus_rest_supplier_use_case as uc_mod,
    )
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.create_supplier.return_value = {
        "write_outcome": "accepted_by_upstream",
        "creation_confirmed": False,
        "supplier_code": None,
        "supplier_store": None,
        "upstream": {"ok": True},
    }
    uc = _uc(identity_gateway=identity, gateway=gateway)
    result = uc.execute(
        actor_user_id=ACTOR,
        fornecedor={"supplier_store": "01", "supplier_name": "ACME"},
    )
    assert result["codusr"] == "000161"
    gateway.create_supplier.assert_called_once()
    call_kwargs = gateway.create_supplier.call_args.kwargs
    assert call_kwargs["body"]["codusr"] == "000161"
    assert isinstance(call_kwargs["body"]["fornecedor"], dict)
    assert "codusr" not in call_kwargs["body"]["fornecedor"]


def test_unmapped_blocked(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped(status="unmapped", usr=None)
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_store": "01"}
        )
    assert exc.value.code == "PROTHEUS_IDENTITY_UNMAPPED"


def test_ambiguous_blocked(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped(status="ambiguous")
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_store": "01"}
        )
    assert exc.value.code == "PROTHEUS_IDENTITY_AMBIGUOUS"


def test_not_verified_blocked(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped(verified=False)
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_store": "01"}
        )
    assert exc.value.code == "PROTHEUS_IDENTITY_NOT_VERIFIED"


def test_invalid_usr_id_format_blocked(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped(usr="161")
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_store": "01"}
        )
    assert exc.value.code == "PROTHEUS_IDENTITY_INVALID"


def test_core_unavailable_propagates_only_when_gate_open(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", False)
    identity = MagicMock()
    identity.get_identity_for_user.side_effect = ProtheusRestError(
        "Core down",
        code="PROTHEUS_IDENTITY_CORE_UNAVAILABLE",
        status_code=503,
    )
    with pytest.raises(ProtheusRestError) as closed:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_store": "01"}
        )
    assert closed.value.code == "PROTHEUS_SUPPLIER_CREATE_DISABLED"
    identity.get_identity_for_user.assert_not_called()

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    with pytest.raises(ProtheusRestError) as opened:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR, fornecedor={"supplier_store": "01"}
        )
    assert opened.value.code == "PROTHEUS_IDENTITY_CORE_UNAVAILABLE"


def test_token_invalid_does_not_retry_write(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        create_protheus_rest_supplier_use_case as uc_mod,
    )
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.create_supplier.side_effect = ProtheusRestError(
        "bad token", code="PROTHEUS_TOKEN_INVALID", status_code=502
    )
    token = MagicMock()
    token.get_valid_token.return_value = "tok"
    uc = _uc(identity_gateway=identity, gateway=gateway, token_service=token)
    with pytest.raises(ProtheusRestError) as exc:
        uc.execute(actor_user_id=ACTOR, fornecedor={"supplier_store": "01"})
    assert exc.value.code == "PROTHEUS_TOKEN_INVALID"
    assert gateway.create_supplier.call_count == 1
    token.invalidate.assert_called_once()


def test_injected_field_normalizer_widens_allowlist(monkeypatch) -> None:
    """E2 — experimental normalizer only via explicit injection (assay path)."""
    from app.application.services.integrations.protheus_supplier_extended_fields import (
        normalize_experimental_supplier_fields,
    )
    from app.application.use_cases.integrations import (
        create_protheus_rest_supplier_use_case as uc_mod,
    )
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_CREATE_ENABLED", True)
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.create_supplier.return_value = {}
    token = MagicMock()
    token.get_valid_token.return_value = "tok"
    uc = _uc(
        identity_gateway=identity,
        gateway=gateway,
        token_service=token,
        field_normalizer=normalize_experimental_supplier_fields,
    )
    uc.execute(
        actor_user_id=ACTOR,
        fornecedor={"supplier_store": "01", "website": "www.example.test"},
    )
    sent = gateway.create_supplier.call_args.kwargs["body"]["fornecedor"]
    assert sent["website"] == "www.example.test"


def test_default_normalizer_still_rejects_extended_fields(monkeypatch) -> None:
    """Public path keeps the published 24-field contract untouched."""
    uc = _uc()
    with pytest.raises(ProtheusRestError) as exc:
        uc.execute(
            actor_user_id=ACTOR,
            fornecedor={"supplier_store": "01", "website": "www.example.test"},
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_PAYLOAD_INVALID"
