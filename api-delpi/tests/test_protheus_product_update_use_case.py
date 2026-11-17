"""Use-case tests — product PUT identity, gate and write-target guard."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from app.application.use_cases.integrations.update_protheus_product_use_case import (
    UpdateProtheusProductUseCase,
)
from app.domain.integrations.protheus_rest import ProtheusRestConfig, ProtheusRestError

ACTOR = UUID("401b25fa-ccd1-4800-8a12-a767909956b4")
_CONFIG = ProtheusRestConfig(
    username="u",
    password="p",
    base_url="http://192.168.1.233:8701/rest",
    auth_path="/api/oauth2/v1/token",
    suppliers_path="/delpi/api/v1/suppliers",
)

FULL_PRODUCT = {
    "B1_GRUPO": "1045",
    "B1_DESC": "PESO PARA TESTE 6KG",
    "B1_REFEREN": "",
    "B1_REFCANT": "",
    "B1_CODDES": "",
    "B1_TIPO": "MC",
    "B1_YHOHS": "N",
    "B1_POSIPI": "72141010",
    "B1_LOCPAD": "01",
    "B1_UM": "PC",
    "B1_SEGUM": "",
    "B1_TE": "001",
    "B1_TS": "",
    "B1_PICMRET": "0.0",
    "B1_CONV": "0.0",
    "B1_TIPCONV": "M",
    "B1_TPMAT": "1",
    "B1_ESPECIE": "0",
    "B1_EX_NCM": "",
    "B1_EX_NBM": "",
    "B1_ORIGEM": "0",
}


def _uc(**overrides) -> UpdateProtheusProductUseCase:
    params = MagicMock()
    params.load_raw_params.return_value = {}
    token = MagicMock()
    token.get_valid_token.return_value = "tok"
    kwargs = dict(
        params_repository=params,
        token_service=token,
        gateway=MagicMock(),
        identity_gateway=MagicMock(),
        tracker=MagicMock(),
    )
    kwargs.update(overrides)
    return UpdateProtheusProductUseCase(**kwargs)


def _mapped(usr: str = "000161", verified: bool = True, status: str = "mapped") -> dict:
    return {
        "mapping_status": status,
        "verified": verified,
        "protheus_user_id": usr,
    }


def _enabled_uc(monkeypatch, gateway) -> UpdateProtheusProductUseCase:
    from app.application.use_cases.integrations import (
        update_protheus_product_use_case as uc_mod,
    )
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_PRODUCT_UPDATE_ENABLED", True)
    monkeypatch.setattr(
        settings, "PROTHEUS_REST_EXPECTED_BASE_URL", _CONFIG.base_url
    )
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    return _uc(identity_gateway=identity, gateway=gateway)


def test_gate_off_does_not_call_core_or_upstream(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_PRODUCT_UPDATE_ENABLED", False)
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
            product_code="ABC123",
            product=FULL_PRODUCT,
        )
    assert exc.value.code == "PROTHEUS_PRODUCT_UPDATE_DISABLED"
    identity.get_identity_for_user.assert_not_called()
    params.load_raw_params.assert_not_called()
    token.get_valid_token.assert_not_called()
    gateway.update_product.assert_not_called()


def test_invalid_code_precedes_feature_gate(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_PRODUCT_UPDATE_ENABLED", False)
    identity = MagicMock()
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR,
            product_code="A B!",
            product=FULL_PRODUCT,
        )
    assert exc.value.code == "PROTHEUS_PRODUCT_ID_INVALID"
    identity.get_identity_for_user.assert_not_called()


def test_enabled_sends_flat_b1_body_without_codusr(monkeypatch) -> None:
    gateway = MagicMock()
    gateway.update_product.return_value = {
        "write_outcome": "accepted_by_upstream",
        "update_acknowledged": True,
        "persistence_proven": False,
    }
    result = _enabled_uc(monkeypatch, gateway).execute(
        actor_user_id=ACTOR,
        product_code="ABC123",
        product={**FULL_PRODUCT, "B1_DESC": "NOVO"},
    )
    call = gateway.update_product.call_args
    body = call.kwargs["body"]
    assert body["B1_COD"] == "ABC123"
    assert body["B1_DESC"] == "NOVO"
    assert body["B1_TIPO"] == "MC"
    assert len(body) == 22  # full representation: B1_COD + 21 client fields
    assert "codusr" not in body
    assert call.kwargs["url"].endswith("/delpiproduto/v1/IncProduto/alterar")
    assert result["product_code"] == "ABC123"
    assert result["codusr"] == "000161"
    assert gateway.update_product.call_count == 1


def test_unmapped_and_unverified(monkeypatch) -> None:
    from app.config import settings

    monkeypatch.setattr(settings, "PROTHEUS_PRODUCT_UPDATE_ENABLED", True)
    monkeypatch.setattr(
        settings, "PROTHEUS_REST_EXPECTED_BASE_URL", _CONFIG.base_url
    )
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped(status="unmapped")
    with pytest.raises(ProtheusRestError) as exc:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR,
            product_code="ABC123",
            product=FULL_PRODUCT,
        )
    assert exc.value.code == "PROTHEUS_IDENTITY_UNMAPPED"

    identity.get_identity_for_user.return_value = _mapped(verified=False)
    with pytest.raises(ProtheusRestError) as exc2:
        _uc(identity_gateway=identity).execute(
            actor_user_id=ACTOR,
            product_code="ABC123",
            product=FULL_PRODUCT,
        )
    assert exc2.value.code == "PROTHEUS_IDENTITY_NOT_VERIFIED"


def test_token_invalid_does_not_retry(monkeypatch) -> None:
    gateway = MagicMock()
    gateway.update_product.side_effect = ProtheusRestError(
        "bad", code="PROTHEUS_TOKEN_INVALID", status_code=502
    )
    uc = _enabled_uc(monkeypatch, gateway)
    token = uc._token_service  # noqa: SLF001 — inspect injected mock
    with pytest.raises(ProtheusRestError):
        uc.execute(
            actor_user_id=ACTOR,
            product_code="ABC123",
            product=FULL_PRODUCT,
        )
    assert gateway.update_product.call_count == 1
    token.invalidate.assert_called_once()


def _identity_mapped() -> MagicMock:
    identity = MagicMock()
    identity.get_identity_for_user.return_value = _mapped()
    return identity


def test_write_target_unverified_blocks_before_upstream(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        update_protheus_product_use_case as uc_mod,
    )
    from app.config import settings

    identity = _identity_mapped()
    gateway = MagicMock()
    params = MagicMock()
    params.load_raw_params.return_value = {}
    tracker = MagicMock()
    uc = UpdateProtheusProductUseCase(
        params_repository=params,
        token_service=MagicMock(),
        gateway=gateway,
        identity_gateway=identity,
        tracker=tracker,
    )
    monkeypatch.setattr(settings, "PROTHEUS_PRODUCT_UPDATE_ENABLED", True)
    monkeypatch.setattr(settings, "PROTHEUS_REST_EXPECTED_BASE_URL", None)
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    with pytest.raises(ProtheusRestError) as exc:
        uc.execute(
            actor_user_id=ACTOR,
            product_code="ABC123",
            product=FULL_PRODUCT,
        )
    assert exc.value.code == "PROTHEUS_REST_TARGET_UNVERIFIED"
    gateway.update_product.assert_not_called()


def test_write_target_mismatch_blocks_before_upstream(monkeypatch) -> None:
    from app.application.use_cases.integrations import (
        update_protheus_product_use_case as uc_mod,
    )
    from app.config import settings

    identity = _identity_mapped()
    gateway = MagicMock()
    params = MagicMock()
    params.load_raw_params.return_value = {}
    uc = UpdateProtheusProductUseCase(
        params_repository=params,
        token_service=MagicMock(),
        gateway=gateway,
        identity_gateway=identity,
        tracker=MagicMock(),
    )
    monkeypatch.setattr(settings, "PROTHEUS_PRODUCT_UPDATE_ENABLED", True)
    monkeypatch.setattr(
        settings,
        "PROTHEUS_REST_EXPECTED_BASE_URL",
        "http://192.168.1.231:8061",
    )
    monkeypatch.setattr(uc_mod, "resolve_protheus_rest_config", lambda _raw: _CONFIG)
    with pytest.raises(ProtheusRestError) as exc:
        uc.execute(
            actor_user_id=ACTOR,
            product_code="ABC123",
            product=FULL_PRODUCT,
        )
    assert exc.value.code == "PROTHEUS_REST_TARGET_MISMATCH"
    gateway.update_product.assert_not_called()
