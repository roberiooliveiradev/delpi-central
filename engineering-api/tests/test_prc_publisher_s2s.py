"""PRC publisher S2S — verificador OC-1 (r1): o contrato BFF deve levar
``X-Delpi-Service-Authorization`` em toda chamada api-delpi, e a ausência
da credencial falha fechado (``unavailable``) antes de qualquer HTTP.
"""

from __future__ import annotations

import pytest

from engineering_app.infrastructure.gateways.delegated_auxiliary import (
    ApiDelpiDelegatedAuxiliary,
)
from engineering_app.infrastructure.gateways.product_publisher import (
    ApiDelpiProductPublisher,
)
from engineering_app.application.ports.product_registration import (
    ProductPublisherError,
)


class _RecordingClient:
    """DownstreamClient fake — registra método/path/service_token."""

    def __init__(self, response=None):
        self.calls = []
        self._response = response if response is not None else {}

    async def post(self, path, *, json_body, access_token, request_id, service_token=None):
        self.calls.append(("POST", path, service_token))
        return self._response

    async def put(self, path, *, json_body, access_token, request_id, service_token=None):
        self.calls.append(("PUT", path, service_token))
        return self._response

    async def delete(self, path, *, json_body, access_token, request_id, service_token=None):
        self.calls.append(("DELETE", path, service_token))
        return self._response

    async def get(self, path, *, params=None, access_token, request_id, service_token=None):
        self.calls.append(("GET", path, service_token))
        return self._response


def _publisher(client, getter=lambda: "svc-jwt"):
    return ApiDelpiProductPublisher(client, service_token_getter=getter)


class TestPublisherSendsS2S:
    @pytest.mark.asyncio
    async def test_create_product_sends_service_token(self):
        client = _RecordingClient()
        await _publisher(client).create_product(
            fields={"B1_COD": "X"}, access_token="user", request_id="r"
        )
        assert client.calls == [("POST", "/integrations/protheus/products", "svc-jwt")]

    @pytest.mark.asyncio
    async def test_update_product_sends_service_token(self):
        client = _RecordingClient()
        await _publisher(client).update_product(
            product_code="X", fields={"B1_DESC": "d"},
            access_token="user", request_id="r",
        )
        assert client.calls == [("PUT", "/integrations/protheus/products/X", "svc-jwt")]

    @pytest.mark.asyncio
    async def test_supplier_link_ops_send_service_token(self):
        client = _RecordingClient()
        pub = _publisher(client)
        kw = dict(product_code="X", identity={"A5_FORNECE": "1"}, attributes={},
                  access_token="user", request_id="r")
        await pub.create_supplier_link(**kw)
        await pub.update_supplier_link(**kw)
        await pub.delete_supplier_link(
            product_code="X", identity={"A5_FORNECE": "1"},
            access_token="user", request_id="r",
        )
        assert [c[2] for c in client.calls] == ["svc-jwt"] * 3
        assert {c[0] for c in client.calls} == {"POST", "PUT", "DELETE"}

    @pytest.mark.asyncio
    async def test_resolve_supplier_name_sends_service_token(self):
        client = _RecordingClient({"items": []})
        result = await _publisher(client).resolve_supplier_name(
            supplier_code="000001", store="01",
            access_token="user", request_id="r",
        )
        assert result is None
        assert client.calls[0][0] == "GET"
        assert client.calls[0][2] == "svc-jwt"


class TestPublisherFailClosed:
    @pytest.mark.asyncio
    async def test_getter_failure_raises_unavailable_without_http(self):
        client = _RecordingClient()

        def _broken():
            raise RuntimeError("kc down")

        with pytest.raises(ProductPublisherError) as exc:
            await _publisher(client, _broken).create_product(
                fields={}, access_token="u", request_id="r"
            )
        assert exc.value.kind == "unavailable"
        assert client.calls == []


class _Ctx:
    def __init__(self):
        self.access_token = "user"
        self.request_id = "r"
        self.user_id = ""


class TestAuxiliaryS2SPropagation:
    @pytest.mark.asyncio
    async def test_auxiliary_with_getter_propagates_service_token(self):
        client = _RecordingClient({"product": {}})
        aux = ApiDelpiDelegatedAuxiliary(
            client, service_token_getter=lambda: "svc-jwt"
        )
        out = await aux.fetch_product_detail(_Ctx(), code="X")
        assert out["status"] == "available"
        assert client.calls == [("GET", "/products/X", "svc-jwt")]

    @pytest.mark.asyncio
    async def test_auxiliary_without_getter_sends_no_service_token(self):
        client = _RecordingClient({"product": {}})
        aux = ApiDelpiDelegatedAuxiliary(client)
        await aux.fetch_product_detail(_Ctx(), code="X")
        assert client.calls[0][2] is None


class TestDelegatedGetS2S:
    """OC (r2): helpers _delegated_get (REST 16b/16c e ações semânticas
    EVA) devem enviar X-Delpi-Service-Authorization nas rotas S2S."""

    @pytest.mark.asyncio
    async def test_rest_delegated_get_sends_service_token(self, monkeypatch):
        from engineering_app.interface.http.routes import (
            product_registration_routes as routes,
        )

        captured = {}

        class _FakeClient:
            def __init__(self, *a, **kw):
                pass

            async def get(self, path, *, params=None, access_token, request_id, service_token=None):
                captured["service_token"] = service_token
                return {"items": []}

        monkeypatch.setattr(
            "engineering_app.infrastructure.gateways.downstream_client.DownstreamClient",
            _FakeClient,
        )
        monkeypatch.setattr(
            "engineering_app.infrastructure.gateways.s2s_token.get_s2s_service_token",
            lambda: "svc-jwt",
        )

        class _User:
            access_token = "user-jwt"

        data, err = await routes._delegated_get(
            _User(), "op", "/engineering/product-registration/suppliers", {}
        )
        assert err is None and data == {"items": []}
        assert captured["service_token"] == "svc-jwt"

    @pytest.mark.asyncio
    async def test_semantic_delegated_get_sends_service_token(self, monkeypatch):
        from engineering_app.interface.mcp import prc_semantic

        captured = {}

        class _FakeClient:
            def __init__(self, *a, **kw):
                pass

            async def get(self, path, *, params=None, access_token, service_token=None):
                captured["service_token"] = service_token
                return {"items": []}

        monkeypatch.setattr(
            "engineering_app.infrastructure.gateways.downstream_client.DownstreamClient",
            _FakeClient,
        )
        monkeypatch.setattr(
            "engineering_app.infrastructure.gateways.s2s_token.get_s2s_service_token",
            lambda: "svc-jwt",
        )

        class _Entry:
            action = "supplier_search"

        class _Context:
            class user:
                access_token = "user-jwt"

        out = await prc_semantic._delegated_get(
            _Context(), _Entry(), {"query": "forn"}
        )
        assert out.structured_content["success"] is True
        assert captured["service_token"] == "svc-jwt"

    @pytest.mark.asyncio
    async def test_semantic_delegated_get_s2s_failure_is_unavailable(self, monkeypatch):
        from engineering_app.interface.mcp import prc_semantic

        def _broken():
            raise RuntimeError("kc down")

        monkeypatch.setattr(
            "engineering_app.infrastructure.gateways.s2s_token.get_s2s_service_token",
            _broken,
        )

        class _Entry:
            action = "catalog_items"

        class _Context:
            class user:
                access_token = "user-jwt"

        out = await prc_semantic._delegated_get(
            _Context(), _Entry(), {"catalog": "units"}
        )
        assert out.structured_content["success"] is False
        assert out.structured_content["error_code"] == "unavailable"
