"""C2 — diretório de colaboradores Portal RH: serviço + gateway S2S."""

from __future__ import annotations

import pytest

import httpx

from production_control_app.application.services.operator_directory_service import (
    OperatorDirectoryService,
)
from production_control_app.domain.errors import (
    InvalidOperatorRegistration,
    OperatorDirectoryContractError,
    OperatorDirectoryUnauthorized,
    OperatorDirectoryUnavailable,
    OperatorNotFound,
)
from production_control_app.domain.operator_identity import OperatorIdentity
from production_control_app.infrastructure.gateways.portal_rh_operator_directory_gateway import (  # noqa: E501
    PortalRhOperatorDirectoryGateway,
)

BASE_URL = "http://portal-rh.test:8000"
TOKEN = "portal-rh-token-secreto"

VALID_PAYLOAD = {
    "id": 42,
    "registration": "20057",
    "full_name": "ALESSANDRA GAVA ROCHA",
    "branch_code": "02",
    "active": True,
}


def make_gateway(
    handler,
    *,
    base_url: str | None = BASE_URL,
    token: str | None = TOKEN,
    timeout: float = 5.0,
) -> tuple[PortalRhOperatorDirectoryGateway, list[httpx.Request]]:
    """Gateway com MockTransport injetado; retorna também os requests capturados."""
    requests: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record))
    gateway = PortalRhOperatorDirectoryGateway(
        base_url=base_url,
        timeout=timeout,
        service_token=token,
        client=client,
    )
    return gateway, requests


def make_service(handler, **kwargs) -> OperatorDirectoryService:
    gateway, _ = make_gateway(handler, **kwargs)
    return OperatorDirectoryService(gateway)


class TestOperatorDirectoryService:
    def test_resolves_active_collaborator(self) -> None:
        service = make_service(lambda r: httpx.Response(200, json=VALID_PAYLOAD))
        identity = service.find_by_registration("20057")
        assert identity == OperatorIdentity(
            external_id=42,
            registration="20057",
            full_name="ALESSANDRA GAVA ROCHA",
            branch_code="02",
            active=True,
        )

    def test_inactive_collaborator_is_valid_identity(self) -> None:
        payload = dict(VALID_PAYLOAD, active=False)
        service = make_service(lambda r: httpx.Response(200, json=payload))
        identity = service.find_by_registration("20057")
        assert identity.active is False
        assert identity.registration == "20057"

    def test_strips_outer_whitespace_only(self) -> None:
        service = make_service(lambda r: httpx.Response(200, json=VALID_PAYLOAD))
        assert service.find_by_registration("  20057  ").registration == "20057"

    @pytest.mark.parametrize("value", ["", "   ", "x" * 31])
    def test_rejects_invalid_registration(self, value: str) -> None:
        service = make_service(lambda r: httpx.Response(200, json=VALID_PAYLOAD))
        with pytest.raises(InvalidOperatorRegistration):
            service.find_by_registration(value)

    def test_accepts_30_char_registration(self) -> None:
        reg = "A" * 30
        payload = dict(VALID_PAYLOAD, registration=reg)
        service = make_service(lambda r: httpx.Response(200, json=payload))
        assert service.find_by_registration(reg).registration == reg


class TestPortalRhGatewayContract:
    def test_url_path_and_query(self) -> None:
        gateway, requests = make_gateway(
            lambda r: httpx.Response(200, json=VALID_PAYLOAD)
        )
        gateway.find_by_registration("20057")
        url = requests[0].url
        assert url.path == "/api/v1/integrations/collaborators/20057/"
        assert str(url).startswith(BASE_URL)

    def test_sends_service_token_and_accept_headers(self) -> None:
        gateway, requests = make_gateway(
            lambda r: httpx.Response(200, json=VALID_PAYLOAD)
        )
        gateway.find_by_registration("20057")
        headers = requests[0].headers
        assert headers["X-Delpi-Service-Token"] == TOKEN
        assert headers["Accept"] == "application/json"
        assert "Authorization" not in headers

    def test_uses_configured_timeout(self) -> None:
        seen: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(request.extensions.get("timeout") or {})
            return httpx.Response(200, json=VALID_PAYLOAD)

        gateway, _ = make_gateway(handler, timeout=2.5)
        gateway.find_by_registration("20057")
        assert seen.get("connect") == 2.5

    def test_leading_zeroes_preserved_as_text(self) -> None:
        payload = dict(
            VALID_PAYLOAD, registration="001", id=7, full_name="JOAO"
        )
        gateway, requests = make_gateway(
            lambda r: httpx.Response(200, json=payload)
        )
        identity = gateway.find_by_registration("001")
        assert requests[0].url.path.endswith("/collaborators/001/")
        assert identity.registration == "001"
        assert identity.registration != "1"
        assert identity.external_id == 7

    def test_url_encodes_registration(self) -> None:
        reg = "A/B C"
        payload = dict(VALID_PAYLOAD, registration=reg)
        gateway, requests = make_gateway(
            lambda r: httpx.Response(200, json=payload)
        )
        gateway.find_by_registration(reg)
        assert requests[0].url.raw_path == (
            b"/api/v1/integrations/collaborators/A%2FB%20C/"
        )

    def test_missing_config_raises_unavailable(self) -> None:
        gateway, _ = make_gateway(
            lambda r: httpx.Response(200), base_url="", token=TOKEN
        )
        with pytest.raises(OperatorDirectoryUnavailable):
            gateway.find_by_registration("20057")
        gateway2, _ = make_gateway(
            lambda r: httpx.Response(200), base_url=BASE_URL, token=""
        )
        with pytest.raises(OperatorDirectoryUnavailable):
            gateway2.find_by_registration("20057")


class TestPortalRhGatewayStatusMapping:
    def test_404_maps_to_not_found(self) -> None:
        gateway, _ = make_gateway(lambda r: httpx.Response(404, json={}))
        with pytest.raises(OperatorNotFound):
            gateway.find_by_registration("99999")

    @pytest.mark.parametrize("status", [401, 403])
    def test_auth_errors_not_not_found(self, status: int) -> None:
        gateway, _ = make_gateway(lambda r: httpx.Response(status))
        with pytest.raises(OperatorDirectoryUnauthorized) as exc:
            gateway.find_by_registration("20057")
        assert exc.value.status_code == status

    @pytest.mark.parametrize("status", [500, 502, 503])
    def test_5xx_maps_to_unavailable(self, status: int) -> None:
        gateway, _ = make_gateway(lambda r: httpx.Response(status))
        with pytest.raises(OperatorDirectoryUnavailable) as exc:
            gateway.find_by_registration("20057")
        assert exc.value.status_code == status

    def test_timeout_maps_to_unavailable(self) -> None:
        def boom(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow")

        gateway, _ = make_gateway(boom)
        with pytest.raises(OperatorDirectoryUnavailable):
            gateway.find_by_registration("20057")

    def test_connect_error_maps_to_unavailable(self) -> None:
        def boom(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        gateway, _ = make_gateway(boom)
        with pytest.raises(OperatorDirectoryUnavailable):
            gateway.find_by_registration("20057")

    def test_other_status_still_unavailable(self) -> None:
        gateway, _ = make_gateway(lambda r: httpx.Response(418))
        with pytest.raises(OperatorDirectoryUnavailable) as exc:
            gateway.find_by_registration("20057")
        assert exc.value.status_code == 418

    def test_errors_do_not_leak_token(self, caplog) -> None:
        gateway, _ = make_gateway(
            lambda r: httpx.Response(500), token="segredo-s2s"
        )
        with caplog.at_level("WARNING"):
            with pytest.raises(OperatorDirectoryUnavailable):
                gateway.find_by_registration("20057")
        for record in caplog.records:
            assert "segredo-s2s" not in record.getMessage()


class TestPortalRhGatewayContractValidation:
    def _gw(self, payload) -> PortalRhOperatorDirectoryGateway:
        gateway, _ = make_gateway(lambda r: httpx.Response(200, json=payload))
        return gateway

    @pytest.mark.parametrize(
        "payload",
        [
            {},
            {"registration": "20057"},
            {"id": "42", "registration": "20057", "full_name": "A",
             "branch_code": "02", "active": True},
            {"id": 42, "registration": "999", "full_name": "OUTRA",
             "branch_code": "01", "active": True},
            {"id": 42, "registration": "20057", "full_name": "",
             "branch_code": "02", "active": True},
            {"id": 42, "registration": "20057", "full_name": "A",
             "branch_code": "", "active": True},
            {"id": 42, "registration": "20057", "full_name": "A",
             "branch_code": "02", "active": "true"},
            {"id": 42, "registration": 20057, "full_name": "A",
             "branch_code": "02", "active": True},
        ],
    )
    def test_invalid_payloads_rejected(self, payload) -> None:
        with pytest.raises(OperatorDirectoryContractError):
            self._gw(payload).find_by_registration("20057")

    def test_non_json_body_rejected(self) -> None:
        gateway, _ = make_gateway(
            lambda r: httpx.Response(200, content=b"not-json")
        )
        with pytest.raises(OperatorDirectoryContractError):
            gateway.find_by_registration("20057")

    def test_extra_fields_ignored(self) -> None:
        payload = dict(
            VALID_PAYLOAD,
            salary="x",
            cpf="y",
            internal_debug="z",
        )
        identity = self._gw(payload).find_by_registration("20057")
        assert not hasattr(identity, "salary")
        assert not hasattr(identity, "cpf")
        assert identity.full_name == "ALESSANDRA GAVA ROCHA"


class TestGatewayClientLifecycle:
    def test_owned_client_closed(self) -> None:
        gateway = PortalRhOperatorDirectoryGateway(
            base_url=BASE_URL, service_token=TOKEN, timeout=1.0
        )
        client = gateway._client
        gateway.close()
        assert client.is_closed

    def test_injected_client_not_closed_by_gateway(self) -> None:
        client = httpx.Client(
            transport=httpx.MockTransport(
                lambda r: httpx.Response(200, json=VALID_PAYLOAD)
            )
        )
        gateway = PortalRhOperatorDirectoryGateway(
            base_url=BASE_URL,
            service_token=TOKEN,
            timeout=1.0,
            client=client,
        )
        gateway.close()
        assert not client.is_closed
        client.close()
