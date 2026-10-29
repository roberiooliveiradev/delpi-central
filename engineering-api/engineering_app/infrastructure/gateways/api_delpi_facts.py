"""Adapter oficial — contrato facts LMP F-LMP-01..04 (owner: api-delpi).

Autenticação interserviços (G4.A.R1 — boundary corrigido): a operação
técnica é autorizada pela credencial S2S individual
(`X-Delpi-Service-Authorization` = client-credentials Keycloak do client
`engineering-api`, scope `engineering-facts.read`, audience `api-delpi`).
O Bearer humano permanece em `Authorization` como ator delegado para
auditoria — nunca como autoridade do contrato facts, nunca substituído
pela identidade de serviço. Sem credencial provisionada o adapter falha
fechado (`unavailable`), sem fallback para o token legado compartilhado.

A api-delpi não conhece permissões funcionais `engineering.*` — a
autorização funcional (`engineering.access`) já foi aplicada nesta API
pela Core antes de qualquer chamada downstream.

Erros viram estados honestos de fonte: forbidden (401/403),
unavailable (timeout/transporte/contrato/service-auth) — nunca lista
vazia falsa.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from delpi_auth.service_errors import ServiceAuthError

from engineering_app.application.models.lmp import (
    LmpFact,
    LmpFactDetailResult,
    LmpFactsResult,
    LmpHistoryResult,
    LmpPiCountsResult,
)
from engineering_app.application.ports.home_sources import HomeSourceContext
from engineering_app.infrastructure.gateways.downstream_client import (
    DownstreamClient,
    DownstreamError,
)

logger = logging.getLogger(__name__)

_SYSTEM = "api-delpi"
_FACTS_PATH = "/engineering/lmps/facts"
_PI_COUNTS_PATH = "/engineering/lmps/facts/pi-counts"
_PI_BATCH_MAX = 500


def _map_fetch_error(exc: DownstreamError) -> tuple[str, str | None]:
    if exc.status_code in (401, 403):
        return "forbidden", None
    return "unavailable", (exc.kind if exc.kind != "http" else "upstream_error")


class ApiDelpiFactsSource:
    """LmpFactsSource sobre DownstreamClient (S2S individual + Bearer humano).

    `service_token_getter` retorna o JWT client-credentials desta API —
    configurado na composition root; falha de configuração/emissão vira
    `unavailable` (fail-closed), nunca bypass.
    """

    system = _SYSTEM
    endpoint = f"GET {_FACTS_PATH}"

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
        except ServiceAuthError as exc:
            logger.warning("lmp_facts_s2s_token_unavailable code=%s", exc.code)
            raise DownstreamError(
                "service_auth_unavailable",
                f"s2s credential unavailable ({exc.code})",
            ) from exc

    async def fetch_facts(
        self,
        ctx: HomeSourceContext,
        *,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        listing_type: str | None,
        page: int,
        page_size: int,
        include_qtd_pi: bool,
    ) -> LmpFactsResult:
        try:
            data = await self._client.get(
                _FACTS_PATH,
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "branch": branch,
                    "listing_type": listing_type,
                    "page": page,
                    "page_size": page_size,
                    "include_qtd_pi": include_qtd_pi,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
                service_token=self._service_token(),
            )
        except DownstreamError as exc:
            status, reason = _map_fetch_error(exc)
            return LmpFactsResult(status=status, reason=reason)
        except Exception:
            logger.warning("api_delpi_facts_unexpected_error", exc_info=True)
            return LmpFactsResult(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            return LmpFactsResult(status="unavailable", reason="contract_error")

        try:
            facts = tuple(LmpFact.from_dict(raw) for raw in data["items"])
        except (ValueError, TypeError):
            return LmpFactsResult(status="unavailable", reason="contract_error")

        total = data.get("total") if isinstance(data.get("total"), int) else None
        provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
        policy = data.get("policy") if isinstance(data.get("policy"), dict) else {}

        if not facts:
            return LmpFactsResult(
                status="empty",
                total=total or 0,
                provenance=provenance,
                policy=policy,
            )
        return LmpFactsResult(
            status="available",
            facts=facts,
            total=total,
            provenance=provenance,
            policy=policy,
        )

    async def fetch_pi_counts(
        self,
        ctx: HomeSourceContext,
        *,
        ov_keys: list[dict[str, str]],
        branch: str | None,
    ) -> LmpPiCountsResult:
        if len(ov_keys) > _PI_BATCH_MAX:
            return LmpPiCountsResult(status="unavailable", reason="batch_limit")

        try:
            data = await self._client.post(
                _PI_COUNTS_PATH,
                json_body={"ovs": ov_keys, "branch": branch},
                access_token=ctx.access_token,
                request_id=ctx.request_id,
                service_token=self._service_token(),
            )
        except DownstreamError as exc:
            status, reason = _map_fetch_error(exc)
            return LmpPiCountsResult(status=status, reason=reason)
        except Exception:
            logger.warning("api_delpi_pi_counts_unexpected_error", exc_info=True)
            return LmpPiCountsResult(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            return LmpPiCountsResult(status="unavailable", reason="contract_error")

        try:
            counts = tuple(
                (
                    (
                        str(item["branch"]),
                        str(item["sale_number"]),
                        str(item["revision"]),
                    ),
                    int(item["qtd_pi"]),
                )
                for item in data["items"]
            )
        except (KeyError, TypeError, ValueError):
            return LmpPiCountsResult(status="unavailable", reason="contract_error")

        provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
        if not counts:
            return LmpPiCountsResult(status="empty", provenance=provenance)
        return LmpPiCountsResult(status="available", counts=counts, provenance=provenance)

    async def fetch_fact(
        self,
        ctx: HomeSourceContext,
        *,
        sale_number: str,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        include: str | None,
    ) -> LmpFactDetailResult:
        try:
            data = await self._client.get(
                f"{_FACTS_PATH}/{sale_number}",
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "branch": branch,
                    "include": include,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
                service_token=self._service_token(),
            )
        except DownstreamError as exc:
            if exc.status_code == 400:
                # OV inexistente na listagem de engenharia → erro de
                # validação upstream; estado honesto dedicado.
                return LmpFactDetailResult(status="not_found", reason="lmp_not_found")
            status, reason = _map_fetch_error(exc)
            return LmpFactDetailResult(status=status, reason=reason)
        except Exception:
            logger.warning("api_delpi_fact_detail_unexpected_error", exc_info=True)
            return LmpFactDetailResult(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not data.get("sale_number"):
            return LmpFactDetailResult(status="unavailable", reason="contract_error")
        provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
        fact = {k: v for k, v in data.items() if k != "provenance"}
        return LmpFactDetailResult(
            status="available", fact=fact, provenance=provenance
        )

    async def fetch_history(
        self,
        ctx: HomeSourceContext,
        *,
        sale_number: str,
        view: str,
        start_date: str | None,
        end_date: str | None,
        branch: str | None,
        revision: str | None,
    ) -> LmpHistoryResult:
        try:
            data = await self._client.get(
                f"{_FACTS_PATH}/{sale_number}/history/{view}",
                params={
                    "start_date": start_date,
                    "end_date": end_date,
                    "branch": branch,
                    "revision": revision,
                },
                access_token=ctx.access_token,
                request_id=ctx.request_id,
                service_token=self._service_token(),
            )
        except DownstreamError as exc:
            status, reason = _map_fetch_error(exc)
            return LmpHistoryResult(status=status, reason=reason)
        except Exception:
            logger.warning("api_delpi_facts_history_unexpected_error", exc_info=True)
            return LmpHistoryResult(status="unavailable", reason="upstream_error")

        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            return LmpHistoryResult(status="unavailable", reason="contract_error")

        provenance = data.get("provenance") if isinstance(data.get("provenance"), dict) else {}
        status = "available" if data["items"] else "empty"
        return LmpHistoryResult(
            status=status,
            items=tuple(item for item in data["items"] if isinstance(item, dict)),
            branch=data.get("branch") if isinstance(data.get("branch"), str) else None,
            reference_revision=(
                data.get("reference_revision")
                if isinstance(data.get("reference_revision"), str)
                else None
            ),
            panel_start_date=(
                data.get("panel_start_date")
                if isinstance(data.get("panel_start_date"), str)
                else None
            ),
            provenance=provenance,
        )
