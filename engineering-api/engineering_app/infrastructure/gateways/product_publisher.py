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


class ApiDelpiProductPublisher:
    """Delegação de escrita: engineering-api → api-delpi → rotina oficial."""

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

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
            if method == "POST":
                data = await self._client.post(
                    path,
                    json_body=body,
                    access_token=access_token,
                    request_id=request_id,
                )
            elif method == "PUT":
                data = await self._client.put(
                    path,
                    json_body=body,
                    access_token=access_token,
                    request_id=request_id,
                )
            else:
                data = await self._client.delete(
                    path,
                    json_body=body,
                    access_token=access_token,
                    request_id=request_id,
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
