"""S2S Core identity gateway — read-only mapping lookup."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import httpx
import pytest

from app.domain.integrations.protheus_rest import ProtheusRestError
from app.infrastructure.gateways.core_protheus_identity_gateway import (
    CoreProtheusIdentityGateway,
)

USER = UUID("401b25fa-ccd1-4800-8a12-a767909956b4")


def test_not_configured() -> None:
    gw = CoreProtheusIdentityGateway(base_url="", service_token="")
    with pytest.raises(ProtheusRestError) as exc:
        gw.get_identity_for_user(USER)
    assert exc.value.code == "PROTHEUS_IDENTITY_CORE_UNAVAILABLE"


def test_404_unmapped() -> None:
    client = MagicMock()
    client.get.return_value = httpx.Response(
        404,
        json={"error": "not_found"},
        request=httpx.Request("GET", "http://core/x"),
    )
    gw = CoreProtheusIdentityGateway(
        base_url="http://core-api:8000",
        service_token="tok",
        client=client,
    )
    with pytest.raises(ProtheusRestError) as exc:
        gw.get_identity_for_user(USER)
    assert exc.value.code == "PROTHEUS_IDENTITY_UNMAPPED"


def test_ok_returns_mapping() -> None:
    client = MagicMock()
    client.get.return_value = httpx.Response(
        200,
        json={
            "mapping": {
                "user_id": str(USER),
                "protheus_user_id": "000161",
                "mapping_status": "mapped",
                "verified": True,
            }
        },
        request=httpx.Request("GET", "http://core/x"),
    )
    gw = CoreProtheusIdentityGateway(
        base_url="http://core-api:8000",
        service_token="tok",
        client=client,
    )
    mapping = gw.get_identity_for_user(USER)
    assert mapping["protheus_user_id"] == "000161"
    headers = client.get.call_args.kwargs["headers"]
    assert headers["X-Delpi-Caller-App"] == "api-delpi"
    assert headers["X-Delpi-Service-Token"] == "tok"
