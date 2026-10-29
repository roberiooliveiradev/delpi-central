"""Adapter oficial — contrato facts LMP F-LMP-01..04 (owner: api-delpi).

Delegação humana (mesma política das fontes atuais): `Authorization:
Bearer <JWT do usuário>`; o downstream revalida via Core
(`ENGINEERING_LMP_ACCESS`). O caminho S2S (`engineering-facts.read` +
allowlist `engineering-api`) já existe na api-delpi, mas o client/
audience/scope ainda aguardam provisionamento oficial (doc 34 §11) —
não há fallback permissivo: sem credencial S2S provisionada, este
adapter usa somente o Bearer humano.

Erros viram estados honestos de fonte: forbidden (401/403),
unavailable (timeout/transporte/contrato) — nunca lista vazia falsa.
"""

from __future__ import annotations

import logging

from engineering_app.application.models.lmp import (
    LmpFact,
    LmpFactsResult,
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
    """LmpFactsSource sobre DownstreamClient (delegação humana)."""

    system = _SYSTEM
    endpoint = f"GET {_FACTS_PATH}"

    def __init__(self, client: DownstreamClient) -> None:
        self._client = client

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
