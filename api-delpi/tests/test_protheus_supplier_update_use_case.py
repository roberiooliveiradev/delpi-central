"""Use-case tests — PUT identity + independent feature gate."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.integrations.update_protheus_rest_supplier_use_case import (
    UpdateProtheusRestSupplierUseCase,
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


def _uc(**overrides) -> UpdateProtheusRestSupplierUseCase:
    params = MagicMock()
    params.load_raw_params.return_value = {}
    token = MagicMock()
    token.get_valid_token.return_value = "tok"
    kwargs = dict(
        params_repository=params,
        token_service=token,
        gateway=MagicMock(),
        identity_gateway=MagicMock(),
    )
    kwargs.update(overrides)
    return UpdateProtheusRestSupplierUseCase(**kwargs)


def _mapped(usr: str = "000161", verified: bool = True, status: str = "mapped") -> dict:
    return {
        "mapping_status": status,
        "verified": verified,
        "protheus_user_id": usr,
    }


def test_gate_off_does_not_call_core_or_upstream(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_UPDATE_ENABLED", False)
    identity = MagicMock()
    gateway = MagicMock()
    params = MagicMock()
    token = MagicMock()
    with pytest.raises(ProtheusRestError) as exc:
        _uc(
            identity_gateway=identity,
            gateway=gateway,
            params_repository=params,
            token_service=token,
        ).execute(
            actor_user_id=ACTOR,
            supplier_id="00000101",
            fornecedor={"supplier_name": "NOME"},
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_UPDATE_DISABLED"
    identity.get_identity_for_user.assert_not_called()
    params.load_raw_params.assert_not_called()
    token.get_valid_token.assert_not_called()
    gateway.update_supplier.assert_not_called()


def test_invalid_id_precedes_feature_gate(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_UPDATE_ENABLED", False)
    identity = MagicMock()
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR,
            supplier_id="1",
            fornecedor={"supplier_name": "NOME"},
        )
    assert exc.value.code == "PROTHEUS_SUPPLIER_ID_INVALID"
    identity.get_identity_for_user.assert_not_called()


def test_enabled_sends_array_body(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        update_protheus_rest_supplier_use_case as uc_mod,
    )
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_UPDATE_ENABLED", True)
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.return_value = {
        "write_outcome": "accepted_by_upstream",
        "update_confirmed": False,
        "update_acknowledged": True,
        "persistence_proven": False,
    }
    result = _uc(identity_gateway=identity, gateway=gateway).execute(
        actor_user_id=ACTOR,
        supplier_id="00000101",
        fornecedor={"supplier_name": "NOME"},
    )
    body = gateway.update_supplier.call_args.kwargs["body"]
    assert body["codusr"] == "000161"
    assert body["fornecedor"] == [{"supplier_name": "NOME"}]
    assert result["supplier_id"] == "00000101"
    assert gateway.update_supplier.call_count == 1


def test_unmapped_and_unverified(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_UPDATE_ENABLED", True)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped(status="unmapped")
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR,
            supplier_id="00000101",
            fornecedor={"supplier_name": "NOME"},
        )
    assert exc.value.code == "PROTHEUS_IDENTITY_UNMAPPED"

    identity.get_identity_for_user.return_value = _mapped(verified=False)
    with pytest.raises(ProtheusRestError) as exc2:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR,
            supplier_id="00000101",
            fornecedor={"supplier_name": "NOME"},
        )
    assert exc2.value.code == "PROTHEUS_IDENTITY_NOT_VERIFIED"


def test_token_invalid_does_not_retry(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        update_protheus_rest_supplier_use_case as uc_mod,
    )
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_SUPPLIER_UPDATE_ENABLED", True)
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    gateway = MagicMock()
    gateway.update_supplier.side_effect = ProtheusRestError(
        "bad", code="PROTHEUS_TOKEN_INVALID", status_code=502
    )
    token = MagicMock()
    with pytest.raises(ProtheusRestError):
        _uc(identity_gateway=identity, gateway=gateway, token_service=token).execute(
            actor_user_id=ACTOR,
            supplier_id="00000101",
            fornecedor={"supplier_name": "NOME"},
        )
    assert gateway.update_supplier.call_count == 1
    token.invalidate.assert_called_once()
