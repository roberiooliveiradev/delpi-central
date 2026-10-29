"""Port de persistência do bounded context NC (E-NC-*).

O adapter real é Postgres dedicado (principal próprio — NUNCA o usuário
compartilhado ``PLUGINS_DB_*``). Até a aprovação do ADR-NC-OWNERSHIP,
apenas bancos isolados/sandbox são alvos válidos de escrita.

Payloads seguem o contrato legado (doc 47 §8): os use cases retornam
dicts prontos para o envelope ``ok()`` do edge.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Protocol

from engineering_app.domain.nonconformity.models import NcActor


class NonconformityRepository(Protocol):
    """Persistência de NCs — owner funcional: Engineering API."""

    def list_records(
        self,
        *,
        status: str | None = None,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        product_code: str | None = None,
        problem_tag: str | None = None,
        date_start: str | None = None,
        date_end: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]: ...

    def get_record(self, record_id: str) -> dict[str, Any] | None: ...

    def export_records(self) -> list[dict[str, Any]]: ...

    def list_history(self, record_id: str) -> list[dict[str, Any]] | None:
        """Eventos append-only; ``None`` quando a NC não existe."""
        ...

    def list_problem_tag_catalog(self) -> list[dict[str, Any]]: ...

    def list_occurrence_dates(self) -> list[date]: ...

    def create_record(
        self,
        *,
        status: str = "open",
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        occurrence_date: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        registered_at: str | None = None,
        actor: NcActor,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]: ...

    def update_record(
        self,
        *,
        record_id: str,
        status: str,
        sale_number: str | None = None,
        lmp_number: str | None = None,
        customer_name: str | None = None,
        occurrence_date: str | None = None,
        launch_date: str | None = None,
        last_revision_date: str | None = None,
        executed_by: str | None = None,
        released_by: str | None = None,
        defect_description: str | None = None,
        corrective_actions: str | None = None,
        technical_opinion: str | None = None,
        products: list[dict[str, Any]] | None = None,
        problem_tags: list[str] | None = None,
        actor: NcActor,
        expected_updated_at: str | None = None,
    ) -> dict[str, Any] | None:
        """Full-replace; ``expected_updated_at`` ativa optimistic locking."""
        ...

    def delete_record(self, record_id: str) -> bool: ...

    def delete_all_records(self) -> int:
        """Substituição total (import). Adapter Postgres exige opt-in de
        ambiente (``ENG_NC_IMPORT_REPLACE_ENABLED``) — nunca implícito."""
        ...


class EarliestOvDateSource(Protocol):
    """Âncora «primeira OV» para o streak sem NCs — fato oficial TOTVS.

    Transição: adapter delega ao contrato oficial api-delpi; alvo: contrato
    facts dedicado (F-LMP-xx) — dependência registrada no ADR (doc 49).
    """

    async def get_reference_start_date(self, access_token: str) -> date | None: ...
