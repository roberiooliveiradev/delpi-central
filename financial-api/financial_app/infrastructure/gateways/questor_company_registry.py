"""Uma sessão HTTP do Questor por filial. Os cookies não se misturam."""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from typing import Any

from financial_app.domain.errors import InvalidReceivedInvoiceQuery, QuestorNotConfigured

_BRANCHES = ("01", "02")
GatewayFactory = Callable[[str, str], Any]


class QuestorCompanyRegistry:
    def __init__(
        self,
        *,
        company_ids: Mapping[str, str],
        factory: GatewayFactory,
    ) -> None:
        self._company_ids = {branch: (company_ids.get(branch) or "").strip() for branch in _BRANCHES}
        self._factory = factory
        self._gateways: dict[str, Any] = {}
        self._lock = threading.Lock()

    def companies(self) -> dict[str, Any]:
        self._require_configuration()
        with self._lock:
            for branch in _BRANCHES:
                if branch not in self._gateways:
                    self._gateways[branch] = self._factory(branch, self._company_ids[branch])
            return dict(self._gateways)

    def gateway_for(self, branch_code: str) -> Any:
        branch = (branch_code or "").strip()
        if branch not in _BRANCHES:
            raise InvalidReceivedInvoiceQuery("Filial de origem inválida.")
        self._require_configuration()
        with self._lock:
            gateway = self._gateways.get(branch)
            if gateway is None:
                gateway = self._factory(branch, self._company_ids[branch])
                self._gateways[branch] = gateway
            return gateway

    def close(self) -> None:
        with self._lock:
            gateways = list(self._gateways.values())
            self._gateways.clear()
        for gateway in gateways:
            gateway.close()

    def _require_configuration(self) -> None:
        if any(not self._company_ids[branch] for branch in _BRANCHES):
            raise QuestorNotConfigured("A integração com o Questor Zen não está configurada.")
