from __future__ import annotations

from typing import Any

from requests_app.application.errors import ApplicationError
from requests_app.application.security.requests_permissions import actor_for
from requests_app.domain.ports import RequestTypeRepositoryPort
from requests_app.domain.ports.operational_lookup_port import OperationalLookupPort


class InvoiceIssuanceLookupUseCases:
    TYPE_CODE = "invoice-issuance"

    def __init__(
        self,
        types: RequestTypeRepositoryPort,
        lookups: OperationalLookupPort,
    ) -> None:
        self._types = types
        self._lookups = lookups

    def _authorize(self, user) -> str | None:
        request_type = self._types.get_by_code(self.TYPE_CODE)
        if request_type is None:
            raise ApplicationError(code="type_not_found", status_code=404)
        actor = actor_for(user, request_type)
        if not (actor.has_create or actor.has_process or actor.has_manage or actor.has_access):
            raise ApplicationError(code="lookup_forbidden", status_code=403)
        token = getattr(user, "access_token", None) or getattr(user, "token", None)
        return str(token) if token else None

    def search_parties(self, *, user, party_type: str, query: str, limit: int = 20) -> dict[str, Any]:
        auth = self._authorize(user)
        if len(str(query or "").strip()) < 2:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                detail="Informe ao menos 2 caracteres para pesquisar.",
            )
        return self._lookups.search_parties(
            party_type=party_type, query=query, limit=limit, authorization=auth
        )

    def search_products(self, *, user, query: str, limit: int = 20) -> dict[str, Any]:
        auth = self._authorize(user)
        if len(str(query or "").strip()) < 2:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                detail="Informe ao menos 2 caracteres para pesquisar itens.",
            )
        return self._lookups.search_products(query=query, limit=limit, authorization=auth)

    def search_carriers(self, *, user, query: str, limit: int = 20) -> dict[str, Any]:
        auth = self._authorize(user)
        if len(str(query or "").strip()) < 2:
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                detail="Informe ao menos 2 caracteres para pesquisar.",
            )
        return self._lookups.search_carriers(query=query, limit=limit, authorization=auth)

    def list_open_sales_orders(
        self, *, user, branch: str, party_code: str, party_store: str
    ) -> dict[str, Any]:
        auth = self._authorize(user)
        return self._lookups.list_open_sales_orders(
            branch=branch,
            party_code=party_code,
            party_store=party_store,
            authorization=auth,
        )

    def warehouse_balance(self, *, user, product_code: str, branch: str) -> dict[str, Any]:
        auth = self._authorize(user)
        return self._lookups.get_warehouse_01_balance(
            product_code=product_code, branch=branch, authorization=auth
        )
