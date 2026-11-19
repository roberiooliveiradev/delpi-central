"""ApiDelpiProductPublisher — escrita governada no TOTVS via api-delpi.

Adapter do port ``ProductPublisherPort``: encaminha o Bearer humano às
rotas oficiais ``/integrations/protheus/*`` (owner do contrato TOTVS).
A api-delpi resolve ``codusr`` a partir do ``sub`` do JWT — a
Engineering API nunca envia identidade Protheus no body —, aplica os
gates/pins de escrita e invoca a rotina oficial com read-back.

Falhas downstream viram ``ProductPublisherError`` com kind honesto; o
service traduz para ``PrcOfficialError`` preservando a taxonomia do
contrato PRC.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

from engineering_app.application.ports.product_registration import (
    ProductPublisherError,
)
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
    DownstreamError,
)

_BASE = "/integrations/protheus/products"


def _map_error(exc: Exception) -> ProductPublisherError:
    if isinstance(exc, DownstreamError):
        if exc.kind == "timeout":
            return ProductPublisherError("timeout", exc.detail)
        if exc.kind == "contract_error":
            return ProductPublisherError("contract_error", exc.detail)
        if exc.kind == "http":
            kind = {
                400: "official_validation",
                401: "forbidden",
                403: "forbidden",
                404: "not_found",
                409: "conflict",
                422: "official_validation",
            }.get(exc.status_code, "unavailable")
            return ProductPublisherError(kind, exc.detail)
        return ProductPublisherError("unavailable", exc.detail)
    return ProductPublisherError(
        "unavailable", f"{type(exc).__name__}: {exc}"
    )


logger = logging.getLogger(__name__)


class ApiDelpiProductPublisher:
    """Delegação de escrita: engineering-api → api-delpi → rotina oficial.

    A autorização é o contrato BFF/S2S (``X-Delpi-Service-Authorization``
    com escopo products.* do cliente ``engineering-api``) — o Bearer
    humano delegado permanece ator de negócio (``codusr``); nenhuma
    permissão api-delpi é exigida do usuário.
    """

    def __init__(
        self,
        client: DownstreamClient,
        service_token_getter: Callable[[], str],
    ) -> None:
        self._client = client
        self._service_token_getter = service_token_getter

    def _service_token(self) -> str:
        try:
            return self._service_token_getter()
        except Exception as exc:
            logger.warning("prc_publisher_s2s_token_unavailable")
            raise ProductPublisherError(
                "unavailable", "s2s token unavailable"
            ) from exc

    async def _send(
        self,
        method: str,
        path: str,
        body: dict[str, Any],
        *,
        access_token: str,
        request_id: str,
    ) -> dict[str, Any]:
        try:
            service_token = self._service_token()
            if method == "POST":
                data = await self._client.post(
                    path,
                    json_body=body,
                    access_token=access_token,
                    request_id=request_id,
                    service_token=service_token,
                )
            elif method == "PUT":
                data = await self._client.put(
                    path,
                    json_body=body,
                    access_token=access_token,
                    request_id=request_id,
                    service_token=service_token,
                )
            else:
                data = await self._client.delete(
                    path,
                    json_body=body,
                    access_token=access_token,
                    request_id=request_id,
                    service_token=service_token,
                )
        except Exception as exc:
            raise _map_error(exc) from exc
        return data if isinstance(data, dict) else {"result": data}

    async def create_product(
        self,
        *,
        fields: dict[str, str],
        access_token: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._send(
            "POST",
            _BASE,
            {"product": fields},
            access_token=access_token,
            request_id=request_id,
        )

    async def update_product(
        self,
        *,
        product_code: str,
        fields: dict[str, str],
        access_token: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._send(
            "PUT",
            f"{_BASE}/{product_code}",
            fields,
            access_token=access_token,
            request_id=request_id,
        )

    async def resolve_supplier_name(
        self,
        *,
        supplier_code: str,
        store: str,
        access_token: str,
        request_id: str,
    ) -> str | None:
        try:
            data = await self._client.get(
                "/engineering/product-registration/suppliers",
                params={
                    "query": supplier_code,
                    "page_size": 100,
                },
                access_token=access_token,
                request_id=request_id,
                service_token=self._service_token(),
            )
        except Exception as exc:
            raise _map_error(exc) from exc
        items = (data or {}).get("items") or []
        for item in items:
            if (
                str(item.get("supplier_code") or "").strip()
                == supplier_code
                and str(item.get("supplier_store") or "").strip() == store
            ):
                name = str(item.get("supplier_name") or "").strip()
                return name or None
        return None

    async def create_supplier_link(
        self,
        *,
        product_code: str,
        identity: dict[str, str],
        attributes: dict[str, str],
        access_token: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._send(
            "POST",
            f"{_BASE}/{product_code}/suppliers",
            {"supplier": identity, "attributes": attributes},
            access_token=access_token,
            request_id=request_id,
        )

    async def update_supplier_link(
        self,
        *,
        product_code: str,
        identity: dict[str, str],
        attributes: dict[str, str],
        access_token: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._send(
            "PUT",
            f"{_BASE}/{product_code}/suppliers",
            {"supplier": identity, "attributes": attributes},
            access_token=access_token,
            request_id=request_id,
        )

    async def delete_supplier_link(
        self,
        *,
        product_code: str,
        identity: dict[str, str],
        access_token: str,
        request_id: str,
    ) -> dict[str, Any]:
        return await self._send(
            "DELETE",
            f"{_BASE}/{product_code}/suppliers",
            {"supplier": identity},
            access_token=access_token,
            request_id=request_id,
        )
