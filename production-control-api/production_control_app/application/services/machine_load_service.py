from __future__ import annotations

import json
import logging
import uuid
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Sequence

from production_control_app.core.security import PC_MACHINE_LOAD_VIEW, can
from production_control_app.domain.errors import (
    DelpiGatewayError,
    MachineLoadSequenceConflict,
    SnapshotNotFound,
)
from production_control_app.domain.ports.machine_load_publication_repository import (
    MachineLoadPublicationRepositoryPort,
)
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.machine_load_optimization import (
    MachineLoadOptimizationCriteria,
    optimize_machine_load_queue,
)
from production_control_app.domain.services.machine_load_delivery_window import (
    delivery_bounds,
    filter_by_delivery_window,
    missing_due_date_count,
)
from production_control_app.domain.services.machine_load_snapshot_payload import (
    decode_snapshot_payload,
    dict_items,
    payload_operations,
    payload_work_centers,
)
from production_control_app.domain.services.machine_load_priority import (
    prioritize_conjunto as prioritize_conjunto_in_queue,
)
from production_control_app.domain.services.machine_load_queue_slots import (
    ProtectedOperationKey,
    protected_operation_key,
)
from production_control_app.domain.services.machine_load_transfer import (
    TRANSFERRED_OPERATIONS_KEY,
    apply_transfers,
    find_operation,
    move_conjunto_at_work_center,
    move_operation,
    move_operations_at_work_center,
    normalize_work_center,
    operation_matches_in_center,
    original_work_center,
    register_transfer,
    transfer_entries,
)
from production_control_app.domain.services.machine_load_withdrawal import (
    WITHDRAWN_CONJUNTOS_KEY,
    WithdrawnMarks,
    is_withdrawn,
    restore_conjunto as restore_conjunto_from_queue,
    visible_operations,
    withdraw_conjunto as withdraw_conjunto_from_queue,
    withdrawn_entries,
    withdrawn_marks,
    withdrawn_operation_entries,
    restore_operation_entries,
    withdraw_operation_entries,
    WITHDRAWN_OPERATIONS_KEY,
)
from production_control_app.domain.services.production_order_key import (
    ORDER_NUMBER_LENGTH,
    conjunto_key_from_order,
    normalize_order_code,
    order_belongs_to_conjunto,
)
from production_control_app.domain.services.branch_access_service import BranchAccessService
from production_control_app.domain.services.current_month_period import today_in_timezone
from production_control_app.application.services.machine_load_live_status_cache import (
    clear_live_status_cache,
    get_live_status_many,
    put_live_status_many,
)

logger = logging.getLogger(__name__)

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "machine_load.json"
_SNAPSHOT_SCHEMA_VERSION = 1

# Campos com identidade interna do PCP — não expostos no cockpit público do operador.
_INTERNAL_IDENTITY_FIELDS = ("refreshed_by", "sequence_updated_by")

# Fallback só para snapshot de conteúdo ausente; o texto canônico é o machine_load.json.
_WITHDRAWAL_FALLBACK_MESSAGES = {
    "orderNumberRequired": "Informe o número do conjunto (C2_NUM) com ao menos 6 dígitos.",
    "notInQueue": "Nenhuma operação do conjunto «{conjunto}» está na fila deste período.",
    "alreadyWithdrawn": "O conjunto {conjunto} já está fora da programação.",
    "notWithdrawn": "O conjunto {conjunto} não está fora da programação.",
    "applied": "Conjunto {conjunto} retirado da programação.",
    "restored": "Conjunto {conjunto} devolvido à fila.",
    "mixedCenters": "A seleção precisa pertencer a um único centro de trabalho.",
    "emptyBatch": "Selecione ao menos uma operação para retirada.",
    "operationNotInQueue": "Operação {order}/{operation} não está na fila deste centro.",
    "operationAlreadyWithdrawn": "Operação {order}/{operation} já está fora da programação.",
    "operationNotWithdrawn": "Operação {order}/{operation} não está retirada.",
    "operationsWithdrawn": "{operations} operação(ões) retirada(s) da programação.",
    "operationsRestored": "{operations} operação(ões) devolvida(s) à fila.",
}

# Lote máximo das ações coletivas (transferência/retirada/restauração) —
# uma página de fila é 300; o lote nunca pode exceder o que a tela seleciona.
_BATCH_OPERATIONS_LIMIT = 200

_TRANSFER_FALLBACK_MESSAGES = {
    "operationRequired": "Informe a OP e a operação que serão transferidas.",
    "orderNumberRequired": "Informe o número do conjunto (C2_NUM) com ao menos 6 dígitos.",
    "sourceRequired": "Informe o centro de trabalho de origem.",
    "targetRequired": "Escolha o centro de trabalho de destino.",
    "unknownTarget": "Centro de trabalho «{center}» não existe neste período.",
    "sameCenter": "A operação já está no centro {center}.",
    "notInQueue": "Operação {order}/{operation} não está na fila deste período.",
    "conjuntoNotInCenter": (
        "Nenhuma operação do conjunto «{conjunto}» está na fila do centro {source}."
    ),
    "withdrawn": "O conjunto da OP {order} está fora da programação. Devolva-o à fila antes de transferir.",
    "unknownSource": "Centro de trabalho «{center}» não existe neste período.",
    "operationNotInSource": (
        "Operação {order}/{operation} não está na fila do centro {source}."
    ),
    "operationsNotInSource": "Operações selecionadas não estão na fila do centro {source}.",
    "operationsApplied": (
        "{operations} operação(ões) movida(s) de {source} para {target}."
    ),
    "applied": "OP {order} operação {operation} movida de {source} para {target}.",
    "conjuntoApplied": (
        "Conjunto {conjunto}: {operations} operação(ões) movida(s) de {source} para {target} "
        "(só as que estavam neste centro)."
    ),
}

_STATUS_FIELDS = (
    "production_status",
    "is_in_production",
    "production_started_date",
    "production_started_time",
    "active_operator_code",
    "active_operator_name",
    "active_operator_count",
    "appointment_count",
    "last_appointment_date",
    # Saldo da bancada anda a cada apontamento: não pode ficar congelado no snapshot.
    "operation_produced_qty",
    "operation_pending_qty",
)

# Fila completa da filial no payload apresentado. A fila é uma só: o centro de
# trabalho ativo é recorte de apresentação, então quem já tem a fila troca de aba
# sem nova leitura. Consumidor que não precisa dela usa `strip_all_operations`.
ALL_OPERATIONS_KEY = "operations"


def strip_all_operations(payload: dict[str, Any]) -> dict[str, Any]:
    """Remove a fila completa do payload apresentado, mantendo `selected` intacto."""
    if ALL_OPERATIONS_KEY not in payload:
        return payload
    scoped = dict(payload)
    scoped.pop(ALL_OPERATIONS_KEY, None)
    return scoped


@lru_cache(maxsize=1)
def _machine_load_settings() -> dict[str, Any]:
    return json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _unwrap_data(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return data
    return payload if isinstance(payload, dict) else {}


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _has_open_operation_balance(item: dict[str, Any]) -> bool:
    """Regra canônica da fila do operador: a operação ainda tem saldo a produzir.

    Fonte: operation_pending_qty (saldo da própria operação); pending_qty
    (cabeçalho da OP) só entra quando o saldo por operação não veio. Saldo
    conhecido <= 1e-9 remove da fila; saldo desconhecido mantém — falha de
    enriquecimento não pode esconder trabalho do operador.
    """
    pending = _optional_float(item.get("operation_pending_qty"))
    if pending is None:
        pending = _optional_float(item.get("pending_qty"))
    return pending is None or pending > 1e-9


def _parse_iso_date(value: str | None) -> date | None:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _user_label(user: object | None) -> str | None:
    if user is None:
        return None
    for attr in ("id", "username", "email", "preferred_username"):
        value = getattr(user, attr, None)
        if value:
            return str(value)[:120]
    return None


def _operation_key(item: dict[str, Any]) -> tuple[str, str]:
    return (
        str(item.get("production_order") or "").strip(),
        str(item.get("operation_code") or "").strip(),
    )


def _norm_code(value: Any) -> str:
    return str(value or "").strip().upper()


def _operation_matches_query(item: dict[str, Any], needle: str) -> bool:
    if not needle:
        return False
    for field in ("production_order", "pa_product_code", "product_code"):
        haystack = _norm_code(item.get(field))
        if haystack and needle in haystack:
            return True
    return False


def _schedule_sort_key(item: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(item.get("scheduled_date") or "9999-99-99"),
        str(item.get("scheduled_start_time") or "99:99"),
        _as_int(item.get("_queue_position"), 10_000),
    )


def _iso_timestamp(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def _row_date(value: Any) -> str | None:
    """Data da janela puxada, gravada na linha do snapshot."""
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    text = str(value).strip()[:10]
    return text or None


class MachineLoadService:
    """Snapshot congelado da fila + status HZA vivo a cada leitura."""

    def __init__(
        self,
        gateway: ProductionOrdersGateway,
        *,
        snapshots: MachineLoadSnapshotRepositoryPort,
        publications: MachineLoadPublicationRepositoryPort,
        branch_access: BranchAccessService | None = None,
        change_notifier: Callable[..., None] | None = None,
        list_open_runs: Callable[[str], list[dict[str, Any]]] | None = None,
        open_run_items: Callable[..., list[dict[str, Any]]] | None = None,
    ) -> None:
        self._gateway = gateway
        self._snapshots = snapshots
        self._publications = publications
        self._branch_access = branch_access or BranchAccessService()
        self._change_notifier = change_notifier
        self._list_open_runs = list_open_runs
        self._open_run_items = open_run_items

    def resolve_delivery_window(
        self,
        *,
        start_date: str | None,
        end_date: str | None,
        today: date | None = None,
    ) -> tuple[date | None, date]:
        """Janela de **entrega do PA**: início aberto por padrão, fim em hoje + N dias.

        O PCP planeja por entrega, não por programação. O início fica aberto para
        que OP atrasada continue na fila — na tela ele aparece como a entrega mais
        antiga encontrada.
        """
        cfg = _machine_load_settings()
        timezone = str(cfg.get("timezone") or "America/Sao_Paulo")
        window_days = _as_int(cfg.get("defaultDeliveryWindowDays"), 14)

        reference = today or today_in_timezone(timezone)
        parsed_start = _parse_iso_date(start_date)
        parsed_end = _parse_iso_date(end_date) or reference + timedelta(days=window_days)
        if parsed_start is not None and parsed_start > parsed_end:
            raise ValueError("A data inicial não pode ser posterior à data final.")
        return parsed_start, parsed_end

    def build(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        self._assert_can_view(user, branch)
        row = self._snapshots.get(branch=branch)
        seeded = False
        if row is None:
            # Primeira visita da filial: sem fila congelada não há o que mostrar.
            start, end = self.resolve_delivery_window(
                start_date=start_date, end_date=end_date
            )
            row = self._pull_and_store(user, branch=branch, start=start, end=end)
            seeded = True
        return self._present(
            row,
            work_center=work_center,
            seeded=seeded,
            branch=branch,
            view_start=_parse_iso_date(start_date),
            view_end=_parse_iso_date(end_date),
            # A fila não espera o chão de fábrica: o status vivo chega por
            # `live_status`, que é quem consulta o TOTVS e alimenta o cache.
            allow_remote_status=False,
        )

    def live_status(self, user: object | None, *, branch: str) -> dict[str, Any]:
        """Status de apontamento vivo (HZA) das operações da fila congelada.

        É a única leitura do PCP que toca o TOTVS: a fila aparece na tela sem
        esperar o chão de fábrica e o status chega em seguida.

        Devolve a **diferença** entre o chão de fábrica e a fila congelada. O
        TOTVS responde por todas as chaves pedidas, inclusive as ~1780 sem nada
        acontecendo; mandar isso a cada 30 s seria repetir o que a tela já tem.
        Operação ausente significa «mantém o valor do snapshot», mesma semântica
        de ``_apply_status_map``.
        """
        self._assert_can_view(user, branch)
        _row, payload = self._load_snapshot_payload(branch=branch)
        operations = visible_operations(
            payload_operations(payload), withdrawn_marks(payload)
        )
        status_by_key = self._live_status_map(branch=branch, operations=operations)
        enriched = self._apply_status_map(operations, status_by_key)

        items: list[dict[str, Any]] = []
        in_production_count = 0
        for frozen, live in zip(operations, enriched, strict=True):
            if live.get("is_in_production"):
                in_production_count += 1
            if live is frozen:
                # `_apply_status_map` devolve o mesmo objeto quando não há status.
                continue
            changed = {
                field: live[field]
                for field in _STATUS_FIELDS
                if field in live and live[field] != frozen.get(field)
            }
            if not changed:
                continue
            order, operation = _operation_key(frozen)
            items.append(
                {"production_order": order, "operation_code": operation, **changed}
            )

        return {
            "branch": branch,
            "as_of": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "operation_count": len(operations),
                "in_production_count": in_production_count,
            },
            "items": items,
        }

    def operation_balances(self, user: object | None, *, branch: str) -> dict[str, Any]:
        """Saldos SH6/SC2 das operações da fila congelada — sem HZA.

        Fonte de quantidades do PCP depois que a execução migrou para o
        cockpit: produzido e saldo por operação, limitados às OPs da fila
        visível, numa chamada em lote à api-delpi (que chunkeia internamente
        para respeitar o limite de parâmetros do SQL Server). Nunca consulta
        apontamentos HZA — execução vem de ``/machine-load/cockpit-status``.
        """
        self._assert_can_view(user, branch)
        _row, payload = self._load_snapshot_payload(branch=branch)
        operations = visible_operations(
            payload_operations(payload), withdrawn_marks(payload)
        )
        balance_by_key = self._operation_balances_map(
            branch=branch, operations=operations, strict=True
        )
        items = [
            {
                "production_order": order,
                "operation_code": operation,
                "operation_produced_qty": raw.get("operation_produced_qty"),
                "operation_pending_qty": raw.get("operation_pending_qty"),
            }
            for (order, operation), raw in sorted(balance_by_key.items())
        ]
        return {
            "branch": branch,
            "as_of": datetime.now(timezone.utc).isoformat(),
            "summary": {"item_count": len(items)},
            "items": items,
        }

    def build_public(
        self,
        *,
        branch: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Cockpit do operador: leitura anônima do snapshot congelado, sem puxar o TOTVS.

        Diferente de ``build``, nunca faz seed: um link público não pode disparar carga
        no ERP nem materializar snapshot novo.
        """
        code = self._branch_access.assert_valid_branch(branch)
        row = self._publication_as_snapshot_row(self._get_publication(branch=code))
        payload = self._present(
            row,
            work_center=work_center,
            seeded=False,
            branch=code,
            production_source="cockpit",
            open_only=True,
        )
        return self._strip_internal_identity(payload)

    def public_snapshot_contains_pa(self, *, branch: str, pa_code: str) -> bool:
        """Confere se o PA aparece na fila congelada da filial — sem puxar o TOTVS."""
        code = self._branch_access.assert_valid_branch(branch)
        wanted = str(pa_code or "").strip()
        if not wanted:
            return False
        row = self._get_publication(branch=code)
        payload = decode_snapshot_payload(row)
        operations = payload_operations(payload)
        operations = visible_operations(operations, withdrawn_marks(payload))
        wanted_key = wanted.upper()
        for item in operations:
            pa = str(item.get("pa_product_code") or "").strip()
            if pa.upper() == wanted_key:
                return True
        return False

    def public_snapshot_contains_operation(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> bool:
        """Confere se a OP+operação está na fila publicada — sem puxar o TOTVS."""
        return (
            self._public_operation_item(
                branch=branch,
                production_order=production_order,
                operation_code=operation_code,
            )
            is not None
        )

    def public_operation_balance(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, float | None] | None:
        """Produzido/saldo da operação na fila publicada — mesma fonte do cockpit.

        O detalhe e o card precisam do mesmo número: somar a janela de histórico
        do modal daria outro total quando o apontamento é mais antigo que ela.
        """
        item = self._public_operation_item(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
            enrich=True,
        )
        if item is None:
            return None
        produced = _optional_float(item.get("operation_produced_qty"))
        if produced is None:
            return None
        return {
            "operation_produced_qty": produced,
            "operation_pending_qty": _optional_float(item.get("operation_pending_qty")),
        }

    def public_operation_run_quantity(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, float | None] | None:
        """Saldo pendente + fator de conversão em peças para congelar no start do run.

        A mesma fonte do cockpit: snapshot publicado enriquecido com o saldo vivo.
        """
        context = self.public_operation_run_context(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
        if context is None:
            return None
        context.pop("is_manual_operation", None)
        return context

    def public_operation_run_context(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any] | None:
        """Contexto completo para congelar no Play: saldo, fator de peças e flag manual.

        Estende ``public_operation_run_quantity`` com ``is_manual_operation``
        (H8_FERRAM=MOD) — única classificação de posto confiável hoje.
        """
        item = self._public_operation_item(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
            enrich=True,
        )
        if item is None:
            return None
        produced = _optional_float(item.get("operation_produced_qty"))
        if produced is None:
            produced = _optional_float(item.get("produced_qty"))
        return {
            "operation_pending_qty": _optional_float(item.get("operation_pending_qty")),
            "pending_qty": _optional_float(item.get("pending_qty")),
            "operation_produced_qty": produced,
            "pieces_conversion_factor": _optional_float(
                item.get("pieces_conversion_factor")
            ),
            "is_manual_operation": bool(item.get("is_manual_operation")),
        }

    def public_operation_feedback_context(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any] | None:
        """Contexto da operação na fila PUBLISHED para o Operator Feedback.

        Mesma fonte do cockpit (fila congelada), sem enrich live e sem TOTVS:
        devolve a identidade canônica da OP/operação mais o snapshot de
        produto/PA/entrega a congelar no registro histórico do impedimento.
        """
        item = self._public_operation_item(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
        if item is None:
            return None
        return {
            "production_order": str(item.get("production_order") or "").strip(),
            "operation_code": str(item.get("operation_code") or "").strip(),
            "work_center": str(item.get("work_center") or "").strip(),
            "product_code": item.get("product_code"),
            "product_description": item.get("product_description"),
            "pa_product_code": item.get("pa_product_code"),
            "due_date": item.get("pa_due_date"),
        }

    def public_operation_process_issue_context(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any] | None:
        """Snapshot completo da operação PUBLISHED para o Problema de Processo.

        Mesma fonte do cockpit (fila congelada + saldo vivo) — nunca WORKING
        nem TOTVS. Congela produto/PA/ferramenta para o analista de Processos
        ver exatamente o que a bancada via no momento do reporte.
        """
        item = self._public_operation_item(
            branch=branch,
            production_order=production_order,
            operation_code=operation_code,
        )
        if item is None:
            return None
        return {
            "production_order": str(item.get("production_order") or "").strip(),
            "operation_code": str(item.get("operation_code") or "").strip(),
            "operation_description": str(
                item.get("operation_description") or ""
            ).strip(),
            "work_center": str(item.get("work_center") or "").strip(),
            "work_center_name": str(item.get("work_center_name") or "").strip(),
            "product_code": item.get("product_code"),
            "product_description": item.get("product_description"),
            "pa_product_code": item.get("pa_product_code"),
            "pa_product_description": item.get("pa_product_description"),
            "tool": str(item.get("tool") or "").strip(),
            "resource": str(item.get("resource") or "").strip() or None,
        }

    def _public_operation_item(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
        enrich: bool = False,
    ) -> dict[str, Any] | None:
        code = self._branch_access.assert_valid_branch(branch)
        order = str(production_order or "").strip()
        operation = str(operation_code or "").strip()
        if not order or not operation:
            return None
        row = self._get_publication(branch=code)
        payload = decode_snapshot_payload(row)
        operations = visible_operations(
            payload_operations(payload), withdrawn_marks(payload)
        )
        if enrich:
            operations = self._enrich_live_status(branch=code, operations=operations)
        order_key = order.upper()
        operation_key = operation.lstrip("0") or "0"
        for item in operations:
            item_order = str(item.get("production_order") or "").strip().upper()
            item_op = str(item.get("operation_code") or "").strip().lstrip("0") or "0"
            if item_order == order_key and item_op == operation_key:
                return item
        return None

    def public_snapshot_contains_product(self, *, branch: str, product_code: str) -> bool:
        """Confere se o produto da OP aparece na fila congelada — sem puxar o TOTVS."""
        code = self._branch_access.assert_valid_branch(branch)
        wanted = str(product_code or "").strip()
        if not wanted:
            return False
        row = self._get_publication(branch=code)
        payload = decode_snapshot_payload(row)
        operations = visible_operations(
            payload_operations(payload), withdrawn_marks(payload)
        )
        wanted_key = wanted.upper()
        for item in operations:
            product = str(item.get("product_code") or "").strip()
            if product.upper() == wanted_key:
                return True
        return False

    def public_snapshot_work_center_resources(
        self, *, branch: str, work_center: str
    ) -> tuple[str, ...] | None:
        """Recursos (``H8_RECURSO``) do CT na fila publicada, ou ``None`` se o CT não está nela.

        O snapshot é a única fonte que liga centro de trabalho a recurso sem
        reconsultar o TOTVS; as paradas do BI são filtradas por recurso, não por CT.
        """
        code = self._branch_access.assert_valid_branch(branch)
        wanted = str(work_center or "").strip()
        if not wanted:
            return None
        row = self._get_publication(branch=code)
        payload = decode_snapshot_payload(row)
        operations = visible_operations(
            payload_operations(payload), withdrawn_marks(payload)
        )
        center_operations = [
            item
            for item in operations
            if str(item.get("work_center") or "").strip() == wanted
        ]
        if not center_operations:
            return None
        resources: list[str] = []
        for item in center_operations:
            resource = str(item.get("resource") or "").strip()
            if resource and resource not in resources:
                resources.append(resource)
        # Sem recurso cadastrado na operação, o próprio código do CT é o melhor palpite.
        return tuple(resources) or (wanted,)

    def refresh(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> dict[str, Any]:
        self._assert_can_view(user, branch)
        start, end = self.resolve_delivery_window(
            start_date=start_date, end_date=end_date
        )
        row = self._pull_and_store(user, branch=branch, start=start, end=end)
        presented = self._present(
            row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        # Refresh só prepara o WORKING: o cockpit continua lendo a publicação
        # vigente, então nada é notificado aqui (publicar = E3).
        return presented

    def publish(self, user: object | None, *, branch: str) -> dict[str, Any]:
        """«Enviar para máquinas»: promove a fila WORKING vigente para a PUBLISHED.

        Transacional: SELECT ... FOR UPDATE no WORKING + upsert da
        publicação na mesma conexão — mutações concorrentes (reorder,
        transfer, withdraw) serializam no lock da linha. O cockpit só é
        avisado depois do commit; republicar a mesma geração é idempotente
        (sem write, sem broadcast). Publish nunca consulta o TOTVS.
        """
        self._assert_can_view(user, branch)
        code = self._branch_access.assert_valid_branch(branch)

        with self._snapshots.transaction() as conn:
            working = self._snapshots.get_for_update(branch=code, conn=conn)
            if working is None:
                raise SnapshotNotFound(
                    "Não há carga máquina atualizada para enviar às máquinas."
                )
            generation = str(working.get("generation_id") or "")
            existing = self._publications.get(branch=code, conn=conn)
            if existing is not None and str(
                existing.get("generation_id") or ""
            ) == generation:
                return {
                    "publication": self._present_publication(existing, changed=False)
                }
            published = self._publications.upsert(
                branch=code,
                generation_id=generation,
                start_date=working["start_date"],
                end_date=working["end_date"],
                payload=decode_snapshot_payload(working),
                source_refreshed_at=working.get("refreshed_at"),
                source_refreshed_by=working.get("refreshed_by"),
                published_by=_user_label(user),
                schema_version=_as_int(
                    working.get("schema_version"), _SNAPSHOT_SCHEMA_VERSION
                ),
                source=str(working.get("source") or "api-delpi"),
                conn=conn,
            )

        # Só depois do commit: avisar antes ligaria o cockpit a uma fila que
        # poderia não ter sido persistida.
        self._notify_change(branch=code, reason="publish")
        return {"publication": self._present_publication(published, changed=True)}

    def _publication_state(
        self, *, branch: str, working_row: dict[str, Any]
    ) -> dict[str, Any]:
        """Estado semantico da programacao para a UI autenticada (E5).

        Derivado — nunca persistido — das geracoes E1-E4:

          sem publicacao                     → unpublished
          generation WORKING == PUBLISHED    → live
          generation WORKING <> PUBLISHED    → draft

        O frontend nao compara UUIDs: recebe o significado, nao o mecanismo.
        """
        published = self._publications.get(branch=branch)
        if published is None:
            return {
                "state": "unpublished",
                "published_at": None,
                "published_by": None,
            }
        live = str(published.get("generation_id") or "") == str(
            working_row.get("generation_id") or ""
        )
        return {
            "state": "live" if live else "draft",
            "published_at": _iso_timestamp(published.get("published_at")),
            "published_by": published.get("published_by"),
        }

    @staticmethod
    def _present_publication(row: dict[str, Any], *, changed: bool) -> dict[str, Any]:
        """Recorte enxuto da publicação para a resposta autenticada do PCP."""
        return {
            "generation_id": str(row.get("generation_id") or ""),
            "published_at": _iso_timestamp(row.get("published_at")),
            "published_by": row.get("published_by"),
            "changed": changed,
            # Apos o publish a geracao publicada e sempre a do WORKING → live.
            "state": "live",
        }

    def _persist_queue_change(
        self,
        *,
        branch: str,
        mutate: Any,
        reason: str,
        work_center: str | None = None,
    ) -> tuple[dict[str, Any], Any]:
        """Persistência única das mutações da fila — WORKING + PUBLISHED quando LIVE.

        mutate(row, payload) recebe a linha WORKING bloqueada
        (SELECT ... FOR UPDATE) e seu payload decodificado; devolve o
        resultado da operação ou None quando nada mudou (no-op: sem write,
        sem broadcast). Se WORKING e PUBLISHED estão na mesma generation_id
        (LIVE), o mesmo payload vai para machine_load_publications na mesma
        transação e o cockpit é avisado após o commit. Em DRAFT só o WORKING
        muda — nenhuma mutação manual atravessa a comporta antes do publish.
        """
        code = self._branch_access.assert_valid_branch(branch)
        live = False
        with self._snapshots.transaction() as conn:
            row = self._snapshots.get_for_update(branch=code, conn=conn)
            if row is None:
                raise SnapshotNotFound(
                    "Não há carga máquina congelada nesta filial. "
                    "Atualize a partir do TOTVS."
                )
            payload = decode_snapshot_payload(row)
            result = mutate(row, payload)
            if result is None:
                return row, None
            updated = self._snapshots.update_payload(
                branch=code, payload=payload, conn=conn
            )
            published = self._publications.get(branch=code, conn=conn)
            live = published is not None and str(
                published.get("generation_id") or ""
            ) == str(row.get("generation_id") or "")
            if live:
                self._publications.update_payload(
                    branch=code, payload=payload, conn=conn
                )

        # Broadcast só depois do commit e só quando a bancada realmente muda.
        if live:
            self._notify_change(branch=code, reason=reason, work_center=work_center)
        return updated, result

    def reorder_sequence(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str,
        ordered_keys: list[dict[str, Any]],
        expected_keys: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        """Reordena as operações de um CT no snapshot sem puxar o TOTVS.

        ``expected_keys`` é a ordem completa do centro que o cliente tinha na
        tela ao montar a permutação — validada contra o estado vigente dentro
        do lock, antes de gravar. Divergência vira 409: ninguém sobrescreve
        silenciosamente a programação gravada por outro analista. Operações
        com run aberto no cockpit ficam travadas na posição (mesma regra
        canônica de priorizar/otimizar — deslocamento direto ou indireto
        rejeita a mutação inteira).
        """
        self._assert_can_view(user, branch)
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("workCenter é obrigatório para reordenar a sequência.")
        if expected_keys is None:
            # Cliente de antes do contrato de concorrência — fail-closed com
            # instrução de recarga: nunca grava sem a ordem-base.
            raise MachineLoadSequenceConflict(
                "A programação foi atualizada. Recarregue a página e tente reordenar novamente."
            )

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> list[dict[str, Any]]:
            # Leitura da fonte oficial de execução já dentro do lock do
            # snapshot — estreita a janela entre consulta e gravação; falha
            # propaga como erro controlado, nunca fallback.
            protected_keys = self._protected_operation_keys(branch=branch)
            reordered = self._apply_center_order(
                payload_operations(payload),
                work_center=center,
                ordered_keys=ordered_keys,
                expected_keys=expected_keys,
                protected_keys=protected_keys,
                withdrawn_marks=withdrawn_marks(payload),
            )
            now = datetime.now(timezone.utc).isoformat()
            payload["operations"] = reordered
            payload["sequence_updated_at"] = now
            payload["sequence_updated_by"] = _user_label(user)
            return reordered

        updated, _result = self._persist_queue_change(
            branch=branch,
            mutate=mutate,
            reason="sequence",
            work_center=center,
        )
        return self._present(
            updated,
            work_center=center,
            seeded=False,
            branch=branch,
        )

    def prioritize_conjunto(
        self,
        user: object | None,
        *,
        branch: str,
        order_number: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Leva todas as OPs do conjunto (C2_NUM) ao topo da fila de cada centro.

        Operações com run aberto no cockpit não são ultrapassadas: o conjunto
        entra logo depois delas. Status HZA/flags do snapshot não protegem.
        """
        self._assert_can_view(user, branch)
        cfg = _machine_load_settings()
        messages = cfg.get("prioritize") if isinstance(cfg.get("prioritize"), dict) else {}

        conjunto_key = conjunto_key_from_order(order_number)
        if not conjunto_key:
            raise ValueError(
                str(
                    messages.get("orderNumberRequired")
                    or "Informe o número do conjunto (C2_NUM) com ao menos 6 dígitos."
                )
            )

        row, payload = self._load_snapshot_payload(branch=branch)
        stored_operations = payload_operations(payload)

        # Conjunto fora da programação não participa da fila — nem para priorizar.
        withdrawn_keys = withdrawn_marks(payload)
        operations = visible_operations(stored_operations, withdrawn_keys)

        template_not_in_queue = str(
            messages.get("notInQueue")
            or "Nenhuma operação do conjunto «{conjunto}» está na fila deste período."
        )
        if not any(
            order_belongs_to_conjunto(item.get("production_order"), conjunto_key)
            for item in operations
        ):
            raise ValueError(template_not_in_queue.format(conjunto=conjunto_key))

        # Quem trava posição é o run aberto no cockpit (fonte oficial local) —
        # nunca o status HZA nem flags congeladas no snapshot. A leitura fica
        # fora da transação e qualquer falha propaga como erro controlado:
        # sequenciar com proteção vazia seria corromper a fila.
        protected_keys = self._protected_operation_keys(branch=branch)

        def mutate(_row: dict[str, Any], locked_payload: dict[str, Any]) -> Any:
            stored = payload_operations(locked_payload)
            withdrawn = withdrawn_marks(locked_payload)
            visible = visible_operations(stored, withdrawn)
            if not any(
                order_belongs_to_conjunto(item.get("production_order"), conjunto_key)
                for item in visible
            ):
                raise ValueError(
                    template_not_in_queue.format(conjunto=conjunto_key)
                )
            result = prioritize_conjunto_in_queue(
                visible,
                conjunto_key=conjunto_key,
                protected_keys=protected_keys,
            )
            visible_keys = [_operation_key(item) for item in visible]
            if not result.work_centers or [
                _operation_key(item) for item in result.operations
            ] == visible_keys:
                return None
            locked_payload["operations"] = self._merge_visible_order(
                stored,
                withdrawn_marks=withdrawn,
                reordered_visible=result.operations,
            )
            locked_payload["sequence_updated_at"] = datetime.now(timezone.utc).isoformat()
            locked_payload["sequence_updated_by"] = _user_label(user)
            return result

        target_row, result = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="priority"
        )

        presented = self._present(
            target_row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        work_centers = result.work_centers if result else []
        if work_centers:
            template = str(
                messages.get("applied")
                or "Conjunto {conjunto} priorizado em {centers} centro(s) de trabalho."
            )
        else:
            template = str(
                messages.get("nothingToDo")
                or "Conjunto {conjunto} já está no topo possível da fila."
            )
        presented["prioritization"] = {
            "order_number": conjunto_key,
            "work_centers": work_centers,
            "operation_count": result.prioritized_operation_count if result else 0,
            "kept_ahead_count": result.kept_ahead_count if result else 0,
            "message": template.format(
                conjunto=conjunto_key,
                centers=len(work_centers),
                operations=result.prioritized_operation_count if result else 0,
            ),
        }
        return presented

    def optimize_delivery_sequence(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Compatibilidade do endpoint legado: otimização só por entrega do PA."""
        return self.optimize_sequence(
            user,
            branch=branch,
            criteria=MachineLoadOptimizationCriteria(group_by_tool=False),
            work_center=work_center,
        )

    def optimize_sequence(
        self,
        user: object | None,
        *,
        branch: str,
        criteria: MachineLoadOptimizationCriteria,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Resequencia a fila de todos os centros pela entrega do PA (+critérios).

        O carga máquina do TOTVS às vezes deixa material de entrega distante à
        frente do que está vencendo. Operações com run aberto no cockpit
        continuam onde estão.
        """
        self._assert_can_view(user, branch)
        cfg = _machine_load_settings()
        messages = (
            cfg.get("optimizeDelivery")
            if isinstance(cfg.get("optimizeDelivery"), dict)
            else {}
        )

        row, payload = self._load_snapshot_payload(branch=branch)
        stored_operations = payload_operations(payload)

        # Conjunto fora da programação não participa da fila — nem para otimizar.
        withdrawn_keys = withdrawn_marks(payload)
        operations = visible_operations(stored_operations, withdrawn_keys)
        template_empty_queue = str(
            messages.get("emptyQueue")
            or "Não há operações na fila desta filial para otimizar."
        )
        if not operations:
            raise ValueError(template_empty_queue)

        # Quem trava posição é o run aberto no cockpit (fonte oficial local) —
        # nunca o status HZA nem flags congeladas no snapshot. A leitura fica
        # fora da transação e qualquer falha propaga como erro controlado:
        # sequenciar com proteção vazia seria corromper a fila.
        protected_keys = self._protected_operation_keys(branch=branch)

        def mutate(_row: dict[str, Any], locked_payload: dict[str, Any]) -> Any:
            stored = payload_operations(locked_payload)
            withdrawn = withdrawn_marks(locked_payload)
            visible = visible_operations(stored, withdrawn)
            if not visible:
                raise ValueError(
                    template_empty_queue
                )
            result = optimize_machine_load_queue(
                visible, criteria=criteria, protected_keys=protected_keys
            )
            visible_keys = [_operation_key(item) for item in visible]
            if not result.work_centers or [
                _operation_key(item) for item in result.operations
            ] == visible_keys:
                return None
            locked_payload["operations"] = self._merge_visible_order(
                stored,
                withdrawn_marks=withdrawn,
                reordered_visible=result.operations,
            )
            locked_payload["sequence_updated_at"] = datetime.now(timezone.utc).isoformat()
            locked_payload["sequence_updated_by"] = _user_label(user)
            return result

        target_row, result = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="delivery_sequence"
        )

        presented = self._present(
            target_row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        work_centers = result.work_centers if result else []
        if not work_centers:
            template = str(
                messages.get("nothingToDo")
                or "A fila já está otimizada pelos critérios selecionados."
            )
        elif criteria.group_by_tool:
            template = str(
                messages.get("appliedWithTool")
                or "Fila otimizada por data de entrega e ferramenta."
            )
        else:
            template = str(
                messages.get("applied")
                or "Fila reordenada por entrega do PA em {centers} centro(s) de trabalho."
            )
        presented["optimization"] = {
            "criteria": {
                "delivery_date": True,
                "group_by_tool": criteria.group_by_tool,
            },
            "work_centers": work_centers,
            "moved_operation_count": result.moved_operation_count if result else 0,
            "kept_ahead_count": result.kept_ahead_count if result else 0,
            "missing_due_date_count": result.missing_due_date_count if result else 0,
            "message": template.format(
                centers=len(work_centers),
                operations=result.moved_operation_count if result else 0,
                kept_ahead=result.kept_ahead_count if result else 0,
                missing=result.missing_due_date_count if result else 0,
            ),
        }
        return presented

    def withdraw_conjunto(
        self,
        user: object | None,
        *,
        branch: str,
        order_number: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Tira o conjunto (C2_NUM) da programação: some da fila do PCP e do cockpit.

        As operações continuam no snapshot, na posição original, para que devolver à
        fila seja apenas remover a chave da lista de retirados.
        """
        self._assert_can_view(user, branch)
        messages = self._withdrawal_messages()
        conjunto_key = self._require_conjunto_key(order_number, messages)

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any] | None:
            operations = payload_operations(payload)
            entries = withdrawn_entries(payload)
            if any(item.get("order_number") == conjunto_key for item in entries):
                raise ValueError(
                    self._format_withdrawal_message(
                        messages, "alreadyWithdrawn", conjunto=conjunto_key
                    )
                )
            if not any(
                order_belongs_to_conjunto(item.get("production_order"), conjunto_key)
                for item in operations
            ):
                raise ValueError(
                    self._format_withdrawal_message(
                        messages, "notInQueue", conjunto=conjunto_key
                    )
                )

            now = datetime.now(timezone.utc).isoformat()
            next_entries, changed = withdraw_conjunto_from_queue(
                entries,
                order_number=conjunto_key,
                operations=operations,
                withdrawn_at=now,
                withdrawn_by=_user_label(user),
            )
            if not changed:
                return None
            payload[WITHDRAWN_CONJUNTOS_KEY] = next_entries
            payload["withdrawal_updated_at"] = now
            payload["withdrawal_updated_by"] = _user_label(user)
            return next(
                (
                    item
                    for item in next_entries
                    if item.get("order_number") == conjunto_key
                ),
                None,
            )

        row, entry = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="withdrawal"
        )
        return self._present_withdrawal(
            row,
            branch=branch,
            entry=entry,
            work_center=work_center,
            conjunto_key=conjunto_key,
            action="withdrawn",
            message_key="applied",
            messages=messages,
        )

    def restore_conjunto(
        self,
        user: object | None,
        *,
        branch: str,
        order_number: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Devolve o conjunto à fila, na posição original que ele ocupava no snapshot."""
        self._assert_can_view(user, branch)
        messages = self._withdrawal_messages()
        conjunto_key = self._require_conjunto_key(order_number, messages)

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any] | None:
            current_entries = withdrawn_entries(payload)
            removed = next(
                (
                    item
                    for item in current_entries
                    if item.get("order_number") == conjunto_key
                ),
                None,
            )
            next_entries, changed = restore_conjunto_from_queue(
                current_entries,
                order_number=conjunto_key,
            )
            if not changed:
                raise ValueError(
                    self._format_withdrawal_message(
                        messages, "notWithdrawn", conjunto=conjunto_key
                    )
                )
            payload[WITHDRAWN_CONJUNTOS_KEY] = next_entries
            payload["withdrawal_updated_at"] = datetime.now(timezone.utc).isoformat()
            payload["withdrawal_updated_by"] = _user_label(user)
            return removed

        row, entry = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="withdrawal"
        )
        return self._present_withdrawal(
            row,
            branch=branch,
            entry=entry,
            work_center=work_center,
            conjunto_key=conjunto_key,
            action="restored",
            message_key="restored",
            messages=messages,
        )

    def transfer_operation(
        self,
        user: object | None,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
        target_work_center: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Move uma operação para o fim da fila de outro centro de trabalho.

        Decisão local do PCP: reescreve o snapshot e guarda a transferência para
        reaplicá-la depois do «Atualizar» do TOTVS.
        """
        self._assert_can_view(user, branch)
        messages = self._transfer_messages()
        order = normalize_order_code(production_order)
        operation = normalize_order_code(operation_code)
        target = normalize_work_center(target_work_center)
        if not order or not operation:
            raise ValueError(self._format_transfer_message(messages, "operationRequired"))
        if not target:
            raise ValueError(self._format_transfer_message(messages, "targetRequired"))

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
            operations = payload_operations(payload)
            centers = {
                str(item.get("work_center") or "").strip(): str(
                    item.get("work_center_name") or ""
                ).strip()
                for item in dict_items(payload.get("work_centers"))
                if str(item.get("work_center") or "").strip()
            }
            if target not in centers:
                raise ValueError(
                    self._format_transfer_message(messages, "unknownTarget", center=target)
                )

            current = find_operation(
                operations, production_order=order, operation_code=operation
            )
            if current is None:
                raise ValueError(
                    self._format_transfer_message(
                        messages, "notInQueue", order=order, operation=operation
                    )
                )
            if is_withdrawn(current, withdrawn_marks(payload)):
                raise ValueError(
                    self._format_transfer_message(messages, "withdrawn", order=order)
                )
            source = normalize_work_center(current.get("work_center"))
            if source == target:
                raise ValueError(
                    self._format_transfer_message(messages, "sameCenter", center=target)
                )

            entries = transfer_entries(payload)
            origin = original_work_center(
                entries, production_order=order, operation_code=operation, fallback=source
            )
            moved = move_operation(
                operations,
                production_order=order,
                operation_code=operation,
                target_work_center=target,
                target_work_center_name=centers.get(target) or None,
                origin_work_center=origin,
            )
            if moved is None:
                raise ValueError(
                    self._format_transfer_message(
                        messages, "notInQueue", order=order, operation=operation
                    )
                )

            now = datetime.now(timezone.utc).isoformat()
            payload["operations"] = moved.operations
            payload[TRANSFERRED_OPERATIONS_KEY] = register_transfer(
                entries,
                production_order=order,
                operation_code=operation,
                origin_work_center=origin,
                target_work_center=target,
                transferred_at=now,
                transferred_by=_user_label(user),
            )
            payload["sequence_updated_at"] = now
            payload["sequence_updated_by"] = _user_label(user)
            return {
                "source": source,
                "origin": origin,
                "centers": centers,
                "moved_count": 1,
            }

        updated, info = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="transfer", work_center=target
        )

        presented = self._present(
            updated,
            work_center=work_center or target,
            seeded=False,
            branch=branch,
        )
        presented["transfer"] = {
            "production_order": order,
            "operation_code": operation,
            "source_work_center": info["source"],
            "target_work_center": target,
            "target_work_center_name": info["centers"].get(target) or None,
            "returned_to_origin": target == info["origin"],
            "message": self._format_transfer_message(
                messages,
                "applied",
                order=order,
                operation=operation,
                source=info["source"],
                target=target,
            ),
        }
        return presented

    def transfer_conjunto(
        self,
        user: object | None,
        *,
        branch: str,
        order_number: str,
        source_work_center: str,
        target_work_center: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Move as OPs do conjunto que estão no centro de origem para o destino.

        OPs do mesmo C2_NUM em outros centros **não** saem da fila deles.
        """
        self._assert_can_view(user, branch)
        messages = self._transfer_messages()
        conjunto_key = self._require_conjunto_key(order_number, messages)
        source = normalize_work_center(source_work_center)
        target = normalize_work_center(target_work_center)
        if not source:
            raise ValueError(self._format_transfer_message(messages, "sourceRequired"))
        if not target:
            raise ValueError(self._format_transfer_message(messages, "targetRequired"))
        if source == target:
            raise ValueError(
                self._format_transfer_message(messages, "sameCenter", center=target)
            )

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
            operations = payload_operations(payload)
            marks = withdrawn_marks(payload)
            if conjunto_key in marks.conjuntos:
                raise ValueError(
                    self._format_transfer_message(
                        messages, "withdrawn", order=conjunto_key
                    )
                )

            centers = {
                str(item.get("work_center") or "").strip(): str(
                    item.get("work_center_name") or ""
                ).strip()
                for item in dict_items(payload.get("work_centers"))
                if str(item.get("work_center") or "").strip()
            }
            if target not in centers:
                raise ValueError(
                    self._format_transfer_message(messages, "unknownTarget", center=target)
                )

            entries = transfer_entries(payload)
            moved = move_conjunto_at_work_center(
                operations,
                conjunto_key=conjunto_key,
                source_work_center=source,
                target_work_center=target,
                target_work_center_name=centers.get(target) or None,
                transfer_log=entries,
            )
            if moved is None:
                raise ValueError(
                    self._format_transfer_message(
                        messages,
                        "conjuntoNotInCenter",
                        conjunto=conjunto_key,
                        source=source,
                    )
                )

            now = datetime.now(timezone.utc).isoformat()
            next_entries = entries
            for item in moved.moved:
                order = normalize_order_code(item.get("production_order"))
                operation = normalize_order_code(item.get("operation_code"))
                origin = original_work_center(
                    next_entries,
                    production_order=order,
                    operation_code=operation,
                    fallback=source,
                )
                next_entries = register_transfer(
                    next_entries,
                    production_order=order,
                    operation_code=operation,
                    origin_work_center=origin,
                    target_work_center=target,
                    transferred_at=now,
                    transferred_by=_user_label(user),
                )

            payload["operations"] = moved.operations
            payload[TRANSFERRED_OPERATIONS_KEY] = next_entries
            payload["sequence_updated_at"] = now
            payload["sequence_updated_by"] = _user_label(user)
            return {"centers": centers, "moved_count": len(moved.moved)}

        updated, info = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="transfer", work_center=target
        )

        presented = self._present(
            updated,
            work_center=work_center or target,
            seeded=False,
            branch=branch,
        )
        presented["transfer"] = {
            "order_number": conjunto_key,
            "production_order": conjunto_key,
            "operation_code": None,
            "operation_count": info["moved_count"],
            "source_work_center": source,
            "target_work_center": target,
            "target_work_center_name": info["centers"].get(target) or None,
            "returned_to_origin": False,
            "scope": "conjunto_at_center",
            "message": self._format_transfer_message(
                messages,
                "conjuntoApplied",
                conjunto=conjunto_key,
                operations=info["moved_count"],
                source=source,
                target=target,
            ),
        }
        return presented

    def transfer_operations(
        self,
        user: object | None,
        *,
        branch: str,
        source_work_center: str,
        target_work_center: str,
        operations: list[dict[str, Any]],
        expected_keys: list[dict[str, Any]],
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Move as operações selecionadas (CT origem + OP + operação) para o destino.

        Uma única intenção de negócio = uma transação: qualquer item inválido,
        protegido ou fora da origem rejeita o lote inteiro. expected_keys é
        a ordem vigente do CT de origem que o analista tinha na tela — divergir
        do estado dentro do lock é 409, nunca write. Runs abertos do cockpit
        travam a operação (E3): lote com item protegido falha fechado.
        """
        self._assert_can_view(user, branch)
        messages = self._transfer_messages()
        source = normalize_work_center(source_work_center)
        target = normalize_work_center(target_work_center)
        keys = self._parse_operation_batch(
            operations, messages=messages, label="transferência"
        )
        if not source:
            raise ValueError(self._format_transfer_message(messages, "sourceRequired"))
        if not target:
            raise ValueError(self._format_transfer_message(messages, "targetRequired"))
        if source == target:
            raise ValueError(
                self._format_transfer_message(messages, "sameCenter", center=target)
            )

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
            stored = payload_operations(payload)
            marks = withdrawn_marks(payload)
            centers = {
                str(item.get("work_center") or "").strip(): str(
                    item.get("work_center_name") or ""
                ).strip()
                for item in dict_items(payload.get("work_centers"))
                if str(item.get("work_center") or "").strip()
            }
            if target not in centers:
                raise ValueError(
                    self._format_transfer_message(messages, "unknownTarget", center=target)
                )
            if source not in centers:
                raise ValueError(
                    self._format_transfer_message(
                        messages, "unknownSource", center=source
                    )
                )

            # Concorrência: a fila de origem tem de estar como o analista viu.
            self._assert_expected_center_order(
                stored, marks=marks, work_center=source, expected_keys=expected_keys
            )

            # Cada item precisa existir exatamente uma vez na origem —
            # duplicata OP+op no mesmo CT é erro de dados, nunca first-match.
            selected: list[dict[str, Any]] = []
            for order, op in keys:
                matches = [
                    item
                    for item in stored
                    if operation_matches_in_center(
                        item,
                        production_order=order,
                        operation_code=op,
                        work_center=source,
                    )
                ]
                if len(matches) != 1:
                    raise ValueError(
                        self._format_transfer_message(
                            messages,
                            "operationNotInSource",
                            order=order,
                            operation=op,
                            source=source,
                        )
                    )
                item = matches[0]
                if is_withdrawn(item, marks):
                    raise ValueError(
                        self._format_transfer_message(
                            messages, "withdrawn", order=order
                        )
                    )
                selected.append(item)

            # A origem ERP é resolvida ANTES do move — _apply_center_move limpa
            # transferred_from quando a operação volta ao centro original.
            entries = transfer_entries(payload)
            origins: dict[tuple[str, str], str] = {}
            for item in selected:
                identity = (
                    normalize_order_code(item.get("production_order")),
                    normalize_order_code(item.get("operation_code")),
                )
                hint = (
                    normalize_work_center(item.get("transferred_from")) or source
                )
                origins[identity] = original_work_center(
                    entries,
                    production_order=identity[0],
                    operation_code=identity[1],
                    fallback=source,
                    work_center=hint,
                )

            # Runs abertos protegem a operação — qualquer selecionada em
            # execução rejeita o lote inteiro (não há transferência parcial).
            protected_keys = self._protected_operation_keys(branch=branch)
            protected_hit = next(
                (
                    item
                    for item in selected
                    if protected_operation_key(item) in protected_keys
                ),
                None,
            )
            if protected_hit is not None:
                raise MachineLoadSequenceConflict(
                    f"Operação {protected_hit.get('production_order')}/"
                    f"{protected_hit.get('operation_code')} está em execução no "
                    "cockpit e não pode ser transferida. Atualize a fila e "
                    "ajuste a seleção."
                )

            moved = move_operations_at_work_center(
                stored,
                keys=keys,
                source_work_center=source,
                target_work_center=target,
                target_work_center_name=centers.get(target) or None,
                transfer_log=entries,
            )
            if moved is None:
                raise ValueError(
                    self._format_transfer_message(
                        messages,
                        "operationsNotInSource",
                        order="",
                        operation="",
                        source=source,
                    )
                )

            now = datetime.now(timezone.utc).isoformat()
            next_entries = entries
            for item in moved.moved:
                order = normalize_order_code(item.get("production_order"))
                operation = normalize_order_code(item.get("operation_code"))
                origin = origins.get((order, operation), source)
                next_entries = register_transfer(
                    next_entries,
                    production_order=order,
                    operation_code=operation,
                    origin_work_center=origin,
                    target_work_center=target,
                    transferred_at=now,
                    transferred_by=_user_label(user),
                )

            payload["operations"] = moved.operations
            payload[TRANSFERRED_OPERATIONS_KEY] = next_entries
            payload["sequence_updated_at"] = now
            payload["sequence_updated_by"] = _user_label(user)
            return {"centers": centers, "moved_count": len(moved.moved)}

        updated, info = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="transfer", work_center=target
        )
        presented = self._present(
            updated,
            work_center=work_center or source,
            seeded=False,
            branch=branch,
        )
        presented["transfer"] = {
            "production_order": None,
            "operation_code": None,
            "operation_count": info["moved_count"],
            "operations": [
                {"production_order": order, "operation_code": op}
                for order, op in keys
            ],
            "source_work_center": source,
            "target_work_center": target,
            "target_work_center_name": info["centers"].get(target) or None,
            "scope": "operations",
            "message": self._format_transfer_message(
                messages,
                "operationsApplied",
                operations=info["moved_count"],
                source=source,
                target=target,
            ),
        }
        return presented

    def withdraw_operations(
        self,
        user: object | None,
        *,
        branch: str,
        operations: list[dict[str, Any]],
        expected_keys: list[dict[str, Any]],
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Retira operações selecionadas da programação (não é retirada de conjunto).

        Tudo-ou-nada dentro do lock: item inexistente, já retirado ou com run
        aberto rejeita o lote inteiro. expected_keys é a ordem vigente do
        CT que o analista viu — divergência é 409, sem write.
        """
        self._assert_can_view(user, branch)
        messages = self._withdrawal_messages()
        refs = self._parse_operation_refs(operations, messages=messages)
        centers_in_batch = {center for center, _order, _op in refs}
        if len(centers_in_batch) != 1:
            raise ValueError(
                str(
                    messages.get("mixedCenters")
                    or "A seleção precisa pertencer a um único centro de trabalho."
                )
            )
        source = centers_in_batch.pop()

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
            stored = payload_operations(payload)
            marks = withdrawn_marks(payload)
            self._assert_expected_center_order(
                stored, marks=marks, work_center=source, expected_keys=expected_keys
            )
            protected_keys = self._protected_operation_keys(branch=branch)
            selected: list[dict[str, Any]] = []
            for center, order, op in refs:
                matches = [
                    candidate
                    for candidate in stored
                    if operation_matches_in_center(
                        candidate,
                        production_order=order,
                        operation_code=op,
                        work_center=center,
                    )
                ]
                if len(matches) != 1:
                    raise ValueError(
                        self._format_withdrawal_message(
                            messages,
                            "operationNotInQueue",
                            order=order,
                            operation=op,
                        )
                    )
                item = matches[0]
                if protected_operation_key(item) in protected_keys:
                    raise MachineLoadSequenceConflict(
                        f"Operação {order}/{op} está em execução no cockpit e "
                        "não pode sair da programação. Atualize a fila e ajuste a seleção."
                    )
                if is_withdrawn(item, marks):
                    raise ValueError(
                        self._format_withdrawal_message(
                            messages,
                            "operationAlreadyWithdrawn",
                            order=order,
                            operation=op,
                        )
                    )
                selected.append(item)

            now = datetime.now(timezone.utc).isoformat()
            next_entries, added = withdraw_operation_entries(
                withdrawn_operation_entries(payload),
                items=selected,
                withdrawn_at=now,
                withdrawn_by=_user_label(user),
            )
            if not added:
                return None
            payload[WITHDRAWN_OPERATIONS_KEY] = next_entries
            payload["withdrawal_updated_at"] = now
            payload["withdrawal_updated_by"] = _user_label(user)
            return {"added": added, "center": source}

        row, info = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="withdrawal", work_center=source
        )
        presented = self._present(
            row,
            work_center=work_center or source,
            seeded=False,
            branch=branch,
        )
        presented["withdrawal"] = {
            "scope": "operations",
            "operation_count": info["added"],
            "work_centers": [source],
            "operations": [
                {"work_center": c, "production_order": o, "operation_code": op}
                for c, o, op in refs
            ],
            "action": "withdrawn",
            "message": self._format_withdrawal_message(
                messages, "operationsWithdrawn", operations=info["added"]
            ),
        }
        return presented

    def restore_operations(
        self,
        user: object | None,
        *,
        branch: str,
        operations: list[dict[str, Any]],
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Devolve operações retiradas individualmente à programação.

        Precondição autoritativa por item: cada operação precisa constar em
        withdrawn_operations — item não retirado ou ausente rejeita o
        lote inteiro. A operação retirada pelo conjunto continua oculta até
        o conjunto ser restaurado (as marcas se somam).
        """
        self._assert_can_view(user, branch)
        messages = self._withdrawal_messages()
        refs = self._parse_operation_refs(operations, messages=messages)

        def mutate(_row: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
            entries = withdrawn_operation_entries(payload)
            stored_keys = {
                (
                    str(item.get("work_center") or "").strip().upper(),
                    normalize_order_code(item.get("production_order")),
                    normalize_order_code(item.get("operation_code")),
                )
                for item in entries
            }
            for center, order, op in refs:
                if (center.upper(), order, op) not in stored_keys:
                    raise ValueError(
                        self._format_withdrawal_message(
                            messages,
                            "operationNotWithdrawn",
                            order=order,
                            operation=op,
                        )
                    )
            next_entries, removed = restore_operation_entries(entries, keys=refs)
            if not removed:
                return None
            now = datetime.now(timezone.utc).isoformat()
            payload[WITHDRAWN_OPERATIONS_KEY] = next_entries
            payload["withdrawal_updated_at"] = now
            payload["withdrawal_updated_by"] = _user_label(user)
            return {"removed": removed}

        row, info = self._persist_queue_change(
            branch=branch, mutate=mutate, reason="withdrawal"
        )
        presented = self._present(
            row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        presented["withdrawal"] = {
            "scope": "operations",
            "operation_count": info["removed"],
            "operations": [
                {"work_center": c, "production_order": o, "operation_code": op}
                for c, o, op in refs
            ],
            "action": "restored",
            "message": self._format_withdrawal_message(
                messages, "operationsRestored", operations=info["removed"]
            ),
        }
        return presented

    def _assert_expected_center_order(
        self,
        operations: list[dict[str, Any]],
        *,
        marks: WithdrawnMarks,
        work_center: str,
        expected_keys: list[dict[str, Any]],
    ) -> None:
        """Frescor da decisão: a ordem visível do CT deve ser a que o analista viu.

        Mesma precondição do PATCH /sequence — qualquer divergência de conjunto
        ou posição é conflito 409, sem write.
        """
        center = str(work_center or "").strip()
        current = [
            _operation_key(item)
            for item in operations
            if str(item.get("work_center") or "").strip() == center
            and not is_withdrawn(item, marks)
        ]
        base = [
            (
                str(raw.get("production_order") or "").strip(),
                str(raw.get("operation_code") or "").strip(),
            )
            for raw in expected_keys
        ]
        if base != current:
            raise MachineLoadSequenceConflict(
                "A programação deste centro mudou desde a última leitura. "
                "Atualize a fila e confirme a nova seleção."
            )

    def _parse_operation_batch(
        self,
        operations: list[dict[str, Any]],
        *,
        messages: dict[str, Any],
        label: str,
    ) -> list[tuple[str, str]]:
        """Normaliza e valida um lote OP+operação: não vazio, ≤ limite, sem duplicatas."""
        if not operations:
            raise ValueError(
                str(
                    messages.get("emptyBatch")
                    or f"Selecione ao menos uma operação para {label}."
                )
            )
        if len(operations) > _BATCH_OPERATIONS_LIMIT:
            raise ValueError(
                f"A {label} aceita no máximo {_BATCH_OPERATIONS_LIMIT} operações por vez."
            )
        keys: list[tuple[str, str]] = []
        for raw in operations:
            key = (
                normalize_order_code(raw.get("production_order")),
                normalize_order_code(raw.get("operation_code")),
            )
            if not key[0] or not key[1]:
                raise ValueError(
                    "Cada item precisa de production_order e operation_code."
                )
            keys.append(key)
        if len(keys) != len(set(keys)):
            raise ValueError("A seleção contém operações duplicadas.")
        return keys

    def _parse_operation_refs(
        self,
        operations: list[dict[str, Any]],
        *,
        messages: dict[str, Any],
    ) -> list[tuple[str, str, str]]:
        """Lote CT+OP+op: valida lista, limite e identidade completa de cada item."""
        keys = self._parse_operation_batch(
            operations, messages=messages, label="retirada"
        )
        refs: list[tuple[str, str, str]] = []
        for raw, key in zip(operations, keys):
            center = str(raw.get("work_center") or "").strip()
            if not center:
                raise ValueError(
                    "Cada item precisa de work_center, production_order e operation_code."
                )
            refs.append((center, key[0], key[1]))
        return refs

    @staticmethod
    def _transfer_messages() -> dict[str, Any]:
        cfg = _machine_load_settings()
        raw = cfg.get("transfer")
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def _format_transfer_message(messages: dict[str, Any], key: str, **values: Any) -> str:
        template = str(messages.get(key) or _TRANSFER_FALLBACK_MESSAGES.get(key, ""))
        return template.format(**values)

    def _present_withdrawal(
        self,
        row: dict[str, Any],
        *,
        branch: str,
        entry: dict[str, Any] | None,
        work_center: str | None,
        conjunto_key: str,
        action: str,
        message_key: str,
        messages: dict[str, Any],
    ) -> dict[str, Any]:
        presented = self._present(
            row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        presented["withdrawal"] = {
            "order_number": conjunto_key,
            "action": action,
            "operation_count": _as_int((entry or {}).get("operation_count"), 0),
            "work_centers": list((entry or {}).get("work_centers") or []),
            "message": self._format_withdrawal_message(
                messages,
                message_key,
                conjunto=conjunto_key,
                operations=_as_int((entry or {}).get("operation_count"), 0),
                centers=len((entry or {}).get("work_centers") or []),
            ),
        }
        return presented

    @staticmethod
    def _withdrawal_messages() -> dict[str, Any]:
        cfg = _machine_load_settings()
        raw = cfg.get("withdrawal")
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def _format_withdrawal_message(
        messages: dict[str, Any],
        key: str,
        **values: Any,
    ) -> str:
        template = str(messages.get(key) or _WITHDRAWAL_FALLBACK_MESSAGES.get(key, ""))
        return template.format(**values)

    @staticmethod
    def _require_conjunto_key(order_number: str, messages: dict[str, Any]) -> str:
        key = conjunto_key_from_order(order_number)
        if not key:
            raise ValueError(
                str(
                    messages.get("orderNumberRequired")
                    or _WITHDRAWAL_FALLBACK_MESSAGES["orderNumberRequired"]
                )
            )
        return key

    def _load_snapshot_payload(
        self,
        *,
        branch: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        """Fila WORKING (planejamento do PCP)."""
        row = self._snapshots.get(branch=branch)
        if row is None:
            raise SnapshotNotFound(
                "Não há carga máquina congelada nesta filial. Atualize a partir do TOTVS."
            )
        return row, decode_snapshot_payload(row)

    def _get_publication(self, *, branch: str) -> dict[str, Any]:
        """Fila PUBLISHED da filial — única fonte do cockpit/chão de fábrica.

        Nunca faz fallback para o WORKING: sem publicação, a fila simplesmente
        não existe para o operador.
        """
        row = self._publications.get(branch=branch)
        if row is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi enviada pelo PCP."
            )
        return row

    def _load_published_payload(
        self,
        *,
        branch: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        row = self._get_publication(branch=branch)
        return row, decode_snapshot_payload(row)

    @staticmethod
    def _publication_as_snapshot_row(row: dict[str, Any]) -> dict[str, Any]:
        """Adapta metadados da publicação para o contrato do ``_present``.

        ``refreshed_*`` na apresentação significa «quando a fila veio do
        TOTVS» → ``source_refreshed_*``. ``published_at`` é outro fato e não
        entra no payload público nesta etapa.
        """
        return {
            **row,
            "refreshed_at": row.get("source_refreshed_at"),
            "refreshed_by": row.get("source_refreshed_by"),
        }

    @staticmethod
    def _merge_visible_order(
        operations: list[dict[str, Any]],
        *,
        withdrawn_marks: WithdrawnMarks,
        reordered_visible: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Reaplica a nova ordem só nos slots visíveis; retiradas ficam onde estavam."""
        if not withdrawn_marks.conjuntos and not withdrawn_marks.operations:
            return reordered_visible
        merged = list(operations)
        slots = [
            index
            for index, item in enumerate(operations)
            if not is_withdrawn(item, withdrawn_marks)
        ]
        for slot, item in zip(slots, reordered_visible, strict=True):
            merged[slot] = item
        return merged

    def locate(
        self,
        user: object | None,
        *,
        branch: str,
        query: str,
    ) -> dict[str, Any]:
        """Rastreia conjunto (C2_NUM) ou produto (PA) em todos os CTs do snapshot.

        Conjunto = todas as OPs cujo ``production_order`` (H8_OP / C2_OP, 11 posições)
        compartilha o mesmo ``C2_NUM`` (6 primeiros dígitos). Ex.: ``10840401003``
        rastreia tudo que começa com ``108404``.
        Produto (PA) lista cada C2_NUM daquele acabado.
        """
        self._assert_can_view(user, branch)
        cfg = _machine_load_settings()
        locate_cfg = cfg.get("locate") if isinstance(cfg.get("locate"), dict) else {}
        needle_raw = str(query or "").strip()
        if not needle_raw:
            raise ValueError(
                str(
                    locate_cfg.get("queryRequired")
                    or "Informe o número do conjunto (C2_NUM / OP) ou o código do produto (PA)."
                )
            )

        row, payload = self._load_snapshot_payload(branch=branch)
        operations = payload_operations(payload)
        operations = self._enrich_execution_state(branch=branch, operations=operations)
        # Rastreio ainda encontra conjunto retirado — marcado como fora da programação.
        withdrawn_keys = withdrawn_marks(payload)
        queue_index = self._queue_positions_by_center(
            visible_operations(operations, withdrawn_keys)
        )

        needle = _norm_code(needle_raw)
        hits = [item for item in operations if _operation_matches_query(item, needle)]

        exact_pas = {
            pa
            for item in operations
            if (pa := _norm_code(item.get("pa_product_code"))) and pa == needle
        }
        partial_pas = {
            pa
            for item in hits
            if (pa := _norm_code(item.get("pa_product_code"))) and needle in pa
        }

        def conjuntos_for_pas(pas: set[str]) -> list[str]:
            return sorted(
                {
                    ck
                    for item in operations
                    if (pa := _norm_code(item.get("pa_product_code"))) in pas
                    and (ck := conjunto_key_from_order(item.get("production_order")))
                }
            )

        def snapshot_has_conjunto(ck: str) -> bool:
            return any(
                order_belongs_to_conjunto(item.get("production_order"), ck)
                for item in operations
            )

        # Prioridade: C2_NUM derivado da OP/consulta → PA exato → prefixo parcial de conjunto → PA parcial.
        journey_specs: list[tuple[str, str]] = []
        needle_conjunto = (
            conjunto_key_from_order(needle) if len(needle) >= ORDER_NUMBER_LENGTH else None
        )
        if needle_conjunto and snapshot_has_conjunto(needle_conjunto):
            journey_specs = [("op", needle_conjunto)]
        elif exact_pas:
            journey_specs = [("op", ck) for ck in conjuntos_for_pas(exact_pas)]
        elif len(needle) < ORDER_NUMBER_LENGTH:
            partial_conjuntos = sorted(
                {
                    ck
                    for item in hits
                    if (ck := conjunto_key_from_order(item.get("production_order")))
                    and (needle in ck or ck.startswith(needle))
                }
            )
            if partial_conjuntos:
                journey_specs = [("op", ck) for ck in partial_conjuntos]
            elif partial_pas:
                journey_specs = [("op", ck) for ck in conjuntos_for_pas(partial_pas)]
            else:
                seen: set[str] = set()
                for item in hits:
                    ck = conjunto_key_from_order(item.get("production_order"))
                    if not ck or ck in seen:
                        continue
                    seen.add(ck)
                    journey_specs.append(("op", ck))
        elif partial_pas:
            journey_specs = [("op", ck) for ck in conjuntos_for_pas(partial_pas)]
        else:
            seen: set[str] = set()
            for item in hits:
                ck = conjunto_key_from_order(item.get("production_order"))
                if not ck or ck in seen:
                    continue
                seen.add(ck)
                journey_specs.append(("op", ck))

        journeys: list[dict[str, Any]] = []
        for kind, key in journey_specs:
            journey_ops = [
                item
                for item in operations
                if order_belongs_to_conjunto(item.get("production_order"), key)
            ]
            journeys.append(
                self._build_locate_journey(
                    kind=kind,
                    key=key,
                    operations=journey_ops,
                    queue_index=queue_index,
                    withdrawn_marks=withdrawn_keys,
                )
            )

        stop_count = sum(len(journey["stops"]) for journey in journeys)
        message = None
        if stop_count == 0:
            template = str(
                locate_cfg.get("noMatches")
                or "Nenhum conjunto ou produto encontrado para «{query}» neste período."
            )
            message = template.format(query=needle_raw)

        return {
            "query": needle_raw,
            "match_count": stop_count,
            "journey_count": len(journeys),
            "message": message,
            "period": {
                "start_date": _row_date(row.get("start_date")),
                "end_date": _row_date(row.get("end_date")),
                "field": "delivery_date",
            },
            "snapshot": {
                "refreshed_at": _iso_timestamp(row.get("refreshed_at")),
                "seeded": False,
                "schema_version": _as_int(row.get("schema_version"), _SNAPSHOT_SCHEMA_VERSION),
            },
            "journeys": journeys,
        }

    @staticmethod
    def _queue_positions_by_center(
        operations: list[dict[str, Any]],
    ) -> dict[tuple[str, str, str], tuple[int, int]]:
        by_center: dict[str, list[dict[str, Any]]] = {}
        for item in operations:
            center = str(item.get("work_center") or "").strip()
            if not center:
                continue
            by_center.setdefault(center, []).append(item)

        index: dict[tuple[str, str, str], tuple[int, int]] = {}
        for center, items in by_center.items():
            size = len(items)
            for position, item in enumerate(items, start=1):
                order, operation = _operation_key(item)
                if not order or not operation:
                    continue
                index[(center, order, operation)] = (position, size)
        return index

    @staticmethod
    def _build_locate_journey(
        *,
        kind: str,
        key: str,
        operations: list[dict[str, Any]],
        queue_index: dict[tuple[str, str, str], tuple[int, int]],
        withdrawn_marks: WithdrawnMarks | None = None,
    ) -> dict[str, Any]:
        hidden = withdrawn_marks or WithdrawnMarks(frozenset(), frozenset())
        decorated: list[dict[str, Any]] = []
        for item in operations:
            center = str(item.get("work_center") or "").strip()
            order, operation = _operation_key(item)
            position, size = queue_index.get((center, order, operation), (0, 0))
            next_item = dict(item)
            next_item["_queue_position"] = position
            next_item["_queue_size"] = size
            decorated.append(next_item)

        decorated.sort(key=_schedule_sort_key)
        stops: list[dict[str, Any]] = []
        for item in decorated:
            center = str(item.get("work_center") or "").strip()
            order, operation = _operation_key(item)
            stops.append(
                {
                    "work_center": center,
                    "work_center_name": str(item.get("work_center_name") or "").strip(),
                    "production_order": order,
                    "operation_code": operation,
                    "operation_description": str(item.get("operation_description") or "").strip(),
                    "product_code": str(item.get("product_code") or "").strip(),
                    "product_description": str(item.get("product_description") or "").strip(),
                    "pa_product_code": str(item.get("pa_product_code") or "").strip() or None,
                    "pa_due_date": item.get("pa_due_date"),
                    "scheduled_date": item.get("scheduled_date"),
                    "scheduled_start_time": item.get("scheduled_start_time"),
                    "pending_qty": item.get("pending_qty"),
                    "operation_pending_qty": item.get("operation_pending_qty"),
                    "unit": item.get("unit"),
                    "tool": str(item.get("tool") or "").strip(),
                    "execution_status": item.get("execution_status"),
                    "execution_integrity_status": item.get("execution_integrity_status"),
                    "execution_started_at": item.get("execution_started_at"),
                    "queue_position": _as_int(item.get("_queue_position"), 0),
                    "queue_size": _as_int(item.get("_queue_size"), 0),
                    "is_withdrawn": is_withdrawn(item, hidden),
                }
            )

        due_dates = [
            str(item.get("pa_due_date") or "").strip()[:10]
            for item in decorated
            if str(item.get("pa_due_date") or "").strip()
        ]
        due_dates.sort()
        pa_code = key if kind == "pa" else next(
            (
                str(item.get("pa_product_code") or "").strip()
                for item in decorated
                if str(item.get("pa_product_code") or "").strip()
            ),
            None,
        )

        return {
            "kind": kind,
            "key": key,
            "label": key,
            "pa_product_code": pa_code or None,
            "pa_due_date": due_dates[0] if due_dates else None,
            "stop_count": len(stops),
            "is_withdrawn": bool(stops) and all(stop["is_withdrawn"] for stop in stops),
            "stops": stops,
        }

    def _notify_change(
        self,
        *,
        branch: str,
        reason: str,
        work_center: str | None = None,
    ) -> None:
        if self._change_notifier is None:
            return
        try:
            self._change_notifier(branch=branch, reason=reason, work_center=work_center)
        except Exception:  # noqa: BLE001
            # Aviso de tempo real é best-effort: nunca derruba a escrita já persistida.
            logger.exception("machine_load_change_notify_failed")

    @staticmethod
    def _strip_internal_identity(payload: dict[str, Any]) -> dict[str, Any]:
        public_payload = dict(payload)
        # O operador não vê a lista de retirados (quem retirou e quando é uso interno do PCP).
        public_payload.pop("withdrawn", None)
        # O cockpit mostra um centro por tela; a fila inteira só inflaria o payload.
        public_payload.pop(ALL_OPERATIONS_KEY, None)
        snapshot = public_payload.get("snapshot")
        if isinstance(snapshot, dict):
            public_payload["snapshot"] = {
                key: value
                for key, value in snapshot.items()
                if key not in _INTERNAL_IDENTITY_FIELDS
            }
        return public_payload

    @staticmethod
    def _apply_center_order(
        operations: list[dict[str, Any]],
        *,
        work_center: str,
        ordered_keys: list[dict[str, Any]],
        expected_keys: list[dict[str, Any]],
        protected_keys: set[ProtectedOperationKey] | None = None,
        withdrawn_marks: WithdrawnMarks | None = None,
    ) -> list[dict[str, Any]]:
        """Reordena um CT. Operações retiradas não entram na permutação e ficam na posição atual."""
        hidden = withdrawn_marks or WithdrawnMarks(frozenset(), frozenset())
        center_ops = [
            item
            for item in operations
            if str(item.get("work_center") or "").strip() == work_center
            and not is_withdrawn(item, hidden)
        ]
        if not center_ops:
            raise ValueError(f"Centro de trabalho '{work_center}' sem operações neste snapshot.")

        by_key = {_operation_key(item): item for item in center_ops}
        if len(by_key) != len(center_ops):
            raise ValueError(
                "Há operações duplicadas (OP + operação) neste centro; não é possível reordenar."
            )

        current = [_operation_key(item) for item in center_ops]
        base: list[tuple[str, str]] = []
        for raw in expected_keys:
            base.append(
                (
                    str(raw.get("production_order") or "").strip(),
                    str(raw.get("operation_code") or "").strip(),
                )
            )
        # Ordem-base vista pelo cliente comparada ao estado vigente (dentro do
        # lock): qualquer divergência de conjunto ou de posição é conflito —
        # a fila mudou por outro analista ou por refresh/transferência/retirada.
        if base != current:
            raise MachineLoadSequenceConflict(
                "A programação deste centro mudou desde a última leitura. "
                "Atualize a fila e confirme a nova sequência."
            )

        requested: list[tuple[str, str]] = []
        for raw in ordered_keys:
            key = (
                str(raw.get("production_order") or "").strip(),
                str(raw.get("operation_code") or "").strip(),
            )
            if not key[0] or not key[1]:
                raise ValueError("Cada item de ordered_keys precisa de production_order e operation_code.")
            requested.append(key)

        if len(requested) != len(set(requested)):
            raise ValueError("ordered_keys contém chaves duplicadas.")
        expected = set(by_key.keys())
        if set(requested) != expected:
            raise ValueError(
                "ordered_keys deve ser a permutação exata das operações deste centro de trabalho."
            )

        # Runs abertos travam a posição — mesma mecânica canônica de
        # priorizar/otimizar (machine_load_queue_slots): deslocamento direto
        # ou indireto de operação protegida rejeita a mutação inteira.
        protected = protected_keys or set()
        moved_protected = [
            item
            for index, item in enumerate(center_ops)
            if protected_operation_key(item) in protected
            and requested[index] != current[index]
        ]
        if moved_protected:
            first = moved_protected[0]
            raise MachineLoadSequenceConflict(
                f"Operação {first.get('production_order')}/"
                f"{first.get('operation_code')} está em execução no cockpit e "
                "não pode mudar de posição. Atualize a fila e ajuste a seleção."
            )

        slots = [
            index
            for index, item in enumerate(operations)
            if str(item.get("work_center") or "").strip() == work_center
            and not is_withdrawn(item, hidden)
        ]
        next_ops = list(operations)
        for slot, key in zip(slots, requested, strict=True):
            next_ops[slot] = by_key[key]
        return next_ops

    def _assert_can_view(self, user: object | None, branch: str) -> None:
        self._branch_access.assert_can_view_branch(user, branch)
        if not can(user, PC_MACHINE_LOAD_VIEW):
            raise PermissionError("Você não tem permissão para ver a carga máquina.")

    def _pull_and_store(
        self,
        user: object | None,
        *,
        branch: str,
        start: date | None,
        end: date,
    ) -> dict[str, Any]:
        previous = self._snapshots.get(branch=branch)
        frozen = self._fetch_frozen_payload(branch=branch, start=start, end=end)
        if previous is not None:
            # Diferente da ordem manual, retirada e transferência sobrevivem ao «Atualizar».
            previous_payload = decode_snapshot_payload(previous)
            entries = withdrawn_entries(previous_payload)
            if entries:
                frozen[WITHDRAWN_CONJUNTOS_KEY] = entries
                frozen["withdrawal_updated_at"] = previous_payload.get("withdrawal_updated_at")
                frozen["withdrawal_updated_by"] = previous_payload.get("withdrawal_updated_by")
            op_entries = withdrawn_operation_entries(previous_payload)
            if op_entries:
                # Retirada por operação também sobrevive ao «Atualizar» —
                # independente de withdrawn_conjuntos e dos metadados dele.
                frozen[WITHDRAWN_OPERATIONS_KEY] = op_entries
            transfers = transfer_entries(previous_payload)
            if transfers:
                frozen[TRANSFERRED_OPERATIONS_KEY] = transfers
                frozen["operations"] = apply_transfers(
                    dict_items(frozen.get("operations")),
                    transfers,
                    work_center_names={
                        str(item.get("work_center") or "").strip(): str(
                            item.get("work_center_name") or ""
                        ).strip()
                        for item in dict_items(frozen.get("work_centers"))
                    },
                )
        # Início aberto vira a entrega mais antiga que realmente veio — é o que a
        # tela mostra no campo «De» e o que descreve a janela puxada.
        oldest_due, _newest = delivery_bounds(dict_items(frozen.get("operations")))
        effective_start = start or _parse_iso_date(oldest_due) or end
        # Fila nova do TOTVS: status HZA em cache não vale mais.
        clear_live_status_cache(branch)
        return self._snapshots.upsert(
            branch=branch,
            start_date=effective_start,
            end_date=end,
            payload=frozen,
            # Todo refresh abre uma geração nova do WORKING — mesmo com payload
            # idêntico. A geração marca o ciclo «Atualizar», não o conteúdo.
            generation_id=str(uuid.uuid4()),
            refreshed_by=_user_label(user),
            schema_version=_SNAPSHOT_SCHEMA_VERSION,
        )

    def _fetch_frozen_payload(
        self,
        *,
        branch: str,
        start: date | None,
        end: date,
    ) -> dict[str, Any]:
        cfg = _machine_load_settings()
        page_size = _as_int(cfg.get("operationsPageSize"), 300)
        start_s = start.isoformat() if start else None
        end_s = end.isoformat()
        # Exceção de período oficial: o escape HZA é desligado e quem sustenta a
        # inclusão fora da janela são os runs abertos do cockpit — OP antiga com
        # apontamento abandonado no coletor não volta para a fila nova.
        outside_period_operations = self._open_run_operation_pairs(branch=branch)

        try:
            centers_payload = _unwrap_data(
                self._gateway.fetch_machine_load_work_centers(
                    branch=branch,
                    delivery_start=start_s,
                    delivery_end=end_s,
                    include_in_production_outside_period=False,
                    include_operations_outside_period=outside_period_operations,
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível carregar os centros de trabalho."
            ) from exc

        work_centers = dict_items(centers_payload)
        operations = self._fetch_all_operations(
            branch=branch,
            delivery_start=start_s,
            delivery_end=end_s,
            page_size=page_size,
            include_operations_outside_period=outside_period_operations,
        )
        summary = centers_payload.get("summary")
        summary_dict = summary if isinstance(summary, dict) else {}

        return {
            "work_centers": work_centers,
            "operations": operations,
            "summary": {
                "work_center_count": len(work_centers),
                "operation_count": _as_int(
                    summary_dict.get("operation_count"), len(operations)
                ),
                "order_count": _as_int(summary_dict.get("order_count"), 0),
                "missing_due_date_count": _as_int(
                    summary_dict.get("missing_due_date_count"), 0
                ),
            },
        }

    def _fetch_all_operations(
        self,
        *,
        branch: str,
        delivery_start: str | None,
        delivery_end: str,
        page_size: int,
        include_operations_outside_period: Sequence[str] = (),
    ) -> list[dict[str, Any]]:
        page = 1
        collected: list[dict[str, Any]] = []
        total: int | None = None
        while True:
            try:
                payload = _unwrap_data(
                    self._gateway.fetch_machine_load_operations(
                        branch=branch,
                        delivery_start=delivery_start,
                        delivery_end=delivery_end,
                        work_center=None,
                        # Cronologia pura do SH8: quem está «em produção» é o run
                        # do cockpit, não o apontamento HZA — a fila nova não pode
                        # herdar a prioridade por coletor do sort legado nem
                        # incluir OPs antigas por apontamento abandonado.
                        sort="schedule_no_status_asc",
                        include_in_production_outside_period=False,
                        include_operations_outside_period=(
                            include_operations_outside_period
                        ),
                        page=page,
                        page_size=page_size,
                    )
                )
            except DelpiGatewayError:
                raise
            except Exception as exc:  # noqa: BLE001
                raise DelpiGatewayError(
                    "Não foi possível carregar a fila do centro de trabalho."
                ) from exc

            batch = dict_items(payload)
            collected.extend(batch)
            pagination = payload.get("pagination")
            if isinstance(pagination, dict):
                total = _as_int(pagination.get("total"), total or 0)
                if pagination.get("is_complete") is True:
                    break
            if not batch:
                break
            if total is not None and len(collected) >= total:
                break
            if len(batch) < page_size:
                break
            page += 1
            if page > 50:
                break
        return collected

    def _present(
        self,
        row: dict[str, Any],
        *,
        work_center: str | None,
        seeded: bool,
        branch: str,
        view_start: date | None = None,
        view_end: date | None = None,
        allow_remote_status: bool = True,
        production_source: str = "erp",
        open_only: bool = False,
    ) -> dict[str, Any]:
        payload = decode_snapshot_payload(row)
        work_centers = payload_work_centers(payload)
        operations = payload_operations(payload)

        # Conjunto retirado continua no snapshot (posição original preservada), mas some da fila.
        withdrawn_keys = withdrawn_marks(payload)
        if production_source == "cockpit":
            # Cockpit público: runs MES locais marcam a fila inteira (barato), mas o
            # enrich HZA só roda no centro de trabalho pedido — consultar a filial
            # inteira para exibir um posto desperdiça TOTVS e rede.
            operations = visible_operations(operations, withdrawn_keys)
            scope_center = _norm_code(work_center)
            if scope_center:
                scoped = [
                    item
                    for item in operations
                    if _norm_code(item.get("work_center")) == scope_center
                ]
                enriched = self._enrich_live_status(
                    branch=branch,
                    operations=scoped,
                    allow_remote=allow_remote_status,
                )
                enriched_iter = iter(enriched)
                operations = [
                    next(enriched_iter)
                    if _norm_code(item.get("work_center")) == scope_center
                    else item
                    for item in operations
                ]
            # Run MES sobrepõe o status HZA — quem decide «em produção» é o cockpit.
            operations = self._apply_cockpit_production_status(
                branch=branch, operations=operations
            )
        else:
            operations = self._enrich_live_status(
                branch=branch,
                operations=operations,
                allow_remote=allow_remote_status,
            )
            operations = visible_operations(operations, withdrawn_keys)
        if open_only:
            # Projeção do cockpit: só o que ainda tem saldo a produzir.
            operations = [
                item for item in operations if _has_open_operation_balance(item)
            ]
        # A fila congelada é uma só; o período pedido na tela é lente de leitura.
        filtered = view_start is not None or view_end is not None
        if filtered:
            operations = filter_by_delivery_window(
                operations, start=view_start, end=view_end
            )
        # Retirada, transferência e lente mudam quantas operações cada centro tem de fato.
        moved_operations = bool(withdrawn_keys.conjuntos or withdrawn_keys.operations) or bool(transfer_entries(payload))
        work_centers = self._recompute_center_counts(
            work_centers,
            operations,
            recount_totals=moved_operations or filtered or open_only,
            drop_empty=filtered,
        )

        available = [str(item.get("work_center") or "").strip() for item in work_centers]
        requested = str(work_center or "").strip()
        selected_center = (
            requested if requested in available else (available[0] if available else None)
        )
        selected_items = [
            item
            for item in operations
            if selected_center and str(item.get("work_center") or "").strip() == selected_center
        ]

        summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
        in_production = sum(1 for item in operations if item.get("is_in_production"))
        if withdrawn_keys.conjuntos or withdrawn_keys.operations or filtered or open_only:
            operation_count = len(operations)
            order_count = len(
                {order for item in operations if (order := _norm_code(item.get("production_order")))}
            )
        else:
            operation_count = _as_int(summary.get("operation_count"), len(operations))
            order_count = _as_int(summary.get("order_count"), 0)

        entries = withdrawn_entries(payload)
        oldest_due, _newest_due = delivery_bounds(operations)
        pulled_start = _row_date(row.get("start_date"))
        pulled_end = _row_date(row.get("end_date"))
        return {
            "branch": branch,
            "period": {
                # «De» é a entrega mais antiga que sobrou na fila; «até», o horizonte puxado.
                "start_date": (
                    view_start.isoformat() if view_start else (oldest_due or pulled_start)
                ),
                "end_date": (view_end.isoformat() if view_end else pulled_end),
                "field": "delivery_date",
                "pulled_start": pulled_start,
                "pulled_end": pulled_end,
                "oldest_due_date": oldest_due,
                "filtered": filtered,
            },
            "summary": {
                "work_center_count": len(work_centers),
                "operation_count": operation_count,
                "order_count": order_count,
                "in_production_count": in_production,
                "missing_due_date_count": missing_due_date_count(operations),
            },
            "snapshot": {
                "refreshed_at": _iso_timestamp(row.get("refreshed_at")),
                "refreshed_by": row.get("refreshed_by"),
                "seeded": seeded,
                "schema_version": _as_int(row.get("schema_version"), _SNAPSHOT_SCHEMA_VERSION),
                "sequence_updated_at": _iso_timestamp(payload.get("sequence_updated_at")),
                "sequence_updated_by": payload.get("sequence_updated_by"),
            },
            "withdrawn": {
                "conjunto_count": len(entries),
                "operation_count": sum(
                    _as_int(entry.get("operation_count"), 0) for entry in entries
                ),
                "items": entries,
                # Retiradas por operação (E4) — identidade canônica completa.
                "operations": withdrawn_operation_entries(payload),
            },
            "work_centers": work_centers,
            **(
                {
                    # Estado semantico da publicacao — so para o PCP autenticado;
                    # o cockpit conhece apenas a fila publicada.
                    "publication": self._publication_state(
                        branch=branch, working_row=row
                    )
                }
                if production_source != "cockpit"
                else {}
            ),
            # Fila inteira da filial: o centro ativo é recorte de apresentação, não
            # uma leitura diferente. Quem não precisa dela remove com `strip_all_operations`.
            ALL_OPERATIONS_KEY: operations,
            "selected": {
                "work_center": selected_center,
                "requested_work_center": requested or None,
                "items": selected_items,
                "pagination": {
                    "page": 1,
                    "page_size": len(selected_items),
                    "total": len(selected_items),
                    "is_complete": True,
                },
            },
        }

    def _apply_cockpit_production_status(
        self, *, branch: str, operations: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """«Em produção» do cockpit = run MES aberto no posto, não cronômetro TOTVS.

        O enrich HZA continua alimentando saldo e contagem de apontamentos; a
        flag de produção ativa e o operador exibido passam a vir dos runs locais
        — quem tem cronômetro aberto no coletor mas sem run do cockpit deixa de
        disputar o destaque da fila pública.
        """
        runs = self._list_open_runs(branch=branch) if self._list_open_runs else []
        runs_by_key = {
            (
                _norm_code(run.get("work_center")),
                _norm_code(run.get("production_order")),
                str(run.get("operation_code") or "").strip(),
            ): run
            for run in runs
        }
        projected: list[dict[str, Any]] = []
        for item in operations:
            key = (
                _norm_code(item.get("work_center")),
                _norm_code(item.get("production_order")),
                str(item.get("operation_code") or "").strip(),
            )
            run = runs_by_key.get(key)
            merged = dict(item)
            if run is None:
                merged["is_in_production"] = False
                merged["active_operator_code"] = None
                merged["active_operator_name"] = None
                merged["active_operator_count"] = 0
                merged["production_started_date"] = None
                merged["production_started_time"] = None
                if merged.get("production_status") == "in_progress":
                    merged["production_status"] = "started"
            else:
                merged["is_in_production"] = True
                merged["production_status"] = "in_progress"
                merged["active_operator_code"] = run.get("operator_code")
                merged["active_operator_name"] = run.get("operator_name")
                merged["active_operator_count"] = 1
                started_at = run.get("started_at")
                if isinstance(started_at, datetime):
                    merged["production_started_date"] = started_at.date().isoformat()
                    merged["production_started_time"] = started_at.strftime("%H:%M")
            projected.append(merged)
        return projected

    def _protected_operation_keys(self, *, branch: str) -> set[ProtectedOperationKey]:
        """Operações que nenhuma reordenação pode ultrapassar: runs abertos do cockpit.

        Fonte oficial única — a projeção canônica da Etapa 01
        (``MachineLoadCockpitStatusService.open_run_items``), lida do PostgreSQL
        local em consulta única por filial. Todo run aberto protege: producing,
        stopped, paused e também ``unknown``/``inconsistent`` — inconsistência
        nunca libera a posição nem é classificada como produção; ela é logada
        para diagnóstico sem dados pessoais. Falha da consulta propaga como
        erro controlado — a mutação nunca roda com proteção vazia nem com
        fallback HZA.
        """
        if self._open_run_items is None:
            raise RuntimeError(
                "Fonte oficial de execução do cockpit não configurada."
            )
        items = self._open_run_items(branch=branch)
        keys: set[ProtectedOperationKey] = set()
        for item in items:
            keys.add(protected_operation_key(item))
            if item.get("integrity_status") == "inconsistent":
                logger.warning(
                    "machine_load_protection_inconsistent_run",
                    extra={
                        "branch": branch,
                        "work_center": item.get("work_center"),
                        "production_order": item.get("production_order"),
                        "operation_code": item.get("operation_code"),
                        "run_status": item.get("run_status"),
                        "operational_state": item.get("operational_state"),
                    },
                )
        return keys

    def _open_run_operation_pairs(self, *, branch: str) -> list[str]:
        """Pares ``OP:operação`` com run aberto — exceção de período do refresh.

        Substitui o escape HZA (``include_in_production_outside_period``) que a
        api-delpi aplicava na montagem da fila: operação executando de verdade
        no cockpit continua visível mesmo fora da janela de entrega, enquanto
        apontamento antigo abandonado não traz mais a OP para a programação.
        Falha da fonte propaga como erro controlado — refresh nunca monta a
        fila assumindo que nenhum run existe. Sem provider configurado (bug de
        wiring), falha explícita como no sequenciamento.
        """
        if self._open_run_items is None:
            raise RuntimeError(
                "Fonte oficial de execução do cockpit não configurada."
            )
        pairs: list[str] = []
        seen: set[str] = set()
        for item in self._open_run_items(branch=branch):
            order = str(item.get("production_order") or "").strip()
            operation = str(item.get("operation_code") or "").strip()
            if not order or not operation:
                continue
            pair = f"{order}:{operation}"
            if pair not in seen:
                seen.add(pair)
                pairs.append(pair)
        return pairs

    def _live_status_map(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
        allow_remote: bool = True,
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """Mapa OP+operação → status HZA, do cache ou do TOTVS.

        Com ``allow_remote=False`` nunca consulta o ERP: serve para a leitura da
        fila não ficar presa ao chão de fábrica quando o cache está frio.
        """
        keys = sorted(
            {
                _operation_key(item)
                for item in operations
                if all(_operation_key(item))
            }
        )
        if not keys:
            return {}

        # F3: cache por operação — hits saem de graça, só misses vão à api-delpi.
        status_by_key, misses = get_live_status_many(branch, keys)
        logger.debug(
            "machine_load_live_cache branch=%s requested=%d hits=%d misses=%d remote=%s",
            branch,
            len(keys),
            len(status_by_key),
            len(misses),
            len(misses) if allow_remote else 0,
        )
        if not misses or not allow_remote:
            return status_by_key

        try:
            status_payload = _unwrap_data(
                self._gateway.fetch_machine_load_appointment_status(
                    branch=branch,
                    items=[
                        {"production_order": order, "operation_code": operation}
                        for order, operation in misses
                    ],
                )
            )
        except DelpiGatewayError:
            # Falha remota não vira cache: hits continuam aplicados e misses
            # ficam sem status novo (saldo desconhecido não esconde OP — F1).
            return status_by_key
        except Exception:
            return status_by_key

        fetched = {
            _operation_key(item): item for item in dict_items(status_payload)
        }
        put_live_status_many(branch, fetched)
        status_by_key.update(fetched)
        return status_by_key

    def _operation_balances_map(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
        strict: bool = False,
    ) -> dict[tuple[str, str], dict[str, Any]]:
        """Mapa OP+operação → saldo SH6/SC2, em lote único via api-delpi.

        Sem cache e sem HZA: o saldo é o fato que mais muda a cada apontamento
        e a consulta em lote já é barata. No modo tolerante (locate), falha
        remota devolve mapa vazio — saldo desconhecido nunca esconde operação.
        No modo ``strict`` (endpoint dedicado do PCP) a falha propaga como
        erro controlado: o MFE sinaliza indisponibilidade e mantém o último
        saldo conhecido, em vez de tratar silêncio como «sem saldo».
        """
        pairs: list[dict[str, str]] = []
        seen: set[tuple[str, str]] = set()
        for item in operations:
            key = _operation_key(item)
            if not all(key) or key in seen:
                continue
            seen.add(key)
            pairs.append(
                {"production_order": key[0], "operation_code": key[1]}
            )
        if not pairs:
            return {}
        try:
            payload = _unwrap_data(
                self._gateway.fetch_machine_load_operation_balances(
                    branch=branch,
                    items=pairs,
                )
            )
        except Exception:
            if strict:
                raise
            return {}
        result: dict[tuple[str, str], dict[str, Any]] = {}
        for raw in dict_items(payload):
            order = str(raw.get("production_order") or "").strip()
            code = str(raw.get("operation_code") or "").strip()
            if order and code:
                result[(order, code)] = raw
        return result

    def _enrich_execution_state(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Projeção do rastreio PCP: execução do cockpit + saldo SH6/SC2, sem HZA.

        ``execution_status`` recebe o ``display_status`` canônico do run aberto
        (producing/stopped/paused/unknown) ou ``None`` quando não há run —
        ausência nunca vira «produzindo». Falha da fonte do cockpit marca cada
        operação como ``unknown``/``inconsistent``: leitura não confirmada é
        honesta, «sem execução» seria um estado falso. O saldo vem do lote
        SH6/SC2 da api-delpi — apontamento HZA não participa.
        """
        if not operations:
            return operations
        # Identidade canônica da execução: centro + OP + operação — a mesma do
        # sequenciamento (Etapa 02). Casar só por OP+operação mostraria o run
        # de uma bancada na parada de outra após transferência.
        run_by_key: dict[ProtectedOperationKey, dict[str, Any]] = {}
        cockpit_failed = False
        if self._open_run_items is not None:
            try:
                for item in self._open_run_items(branch=branch):
                    key = protected_operation_key(item)
                    if key[0] and key[1] and key[2]:
                        run_by_key[key] = item
            except Exception:  # noqa: BLE001
                cockpit_failed = True
                logger.warning("machine_load_locate_cockpit_unavailable branch=%s", branch)
        balance_by_key = self._operation_balances_map(
            branch=branch, operations=operations
        )
        enriched: list[dict[str, Any]] = []
        for item in operations:
            merged = dict(item)
            key = _operation_key(item)
            run = run_by_key.get(protected_operation_key(item))
            if cockpit_failed:
                merged["execution_status"] = "unknown"
                merged["execution_integrity_status"] = "inconsistent"
                merged["execution_started_at"] = None
            elif run is not None:
                merged["execution_status"] = run.get("display_status") or "unknown"
                merged["execution_integrity_status"] = run.get("integrity_status")
                merged["execution_started_at"] = run.get("started_at")
            else:
                merged["execution_status"] = None
                merged["execution_integrity_status"] = None
                merged["execution_started_at"] = None
            balance = balance_by_key.get(key)
            if balance:
                merged["operation_produced_qty"] = balance.get("operation_produced_qty")
                merged["operation_pending_qty"] = balance.get("operation_pending_qty")
            enriched.append(merged)
        return enriched

    def _enrich_live_status(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
        allow_remote: bool = True,
    ) -> list[dict[str, Any]]:
        if not operations:
            return operations
        status_by_key = self._live_status_map(
            branch=branch,
            operations=operations,
            allow_remote=allow_remote,
        )
        if not status_by_key:
            return operations
        return self._apply_status_map(operations, status_by_key)

    @staticmethod
    def _apply_status_map(
        operations: list[dict[str, Any]],
        status_by_key: dict[tuple[str, str], dict[str, Any]],
    ) -> list[dict[str, Any]]:
        enriched: list[dict[str, Any]] = []
        for item in operations:
            status = status_by_key.get(_operation_key(item))
            if not status:
                merged = dict(item)
            else:
                merged = dict(item)
                for field in _STATUS_FIELDS:
                    if field in status:
                        merged[field] = status[field]
            MachineLoadService._coerce_status_when_balance_exhausted(merged)
            enriched.append(merged)
        return enriched

    @staticmethod
    def _coerce_status_when_balance_exhausted(item: dict[str, Any]) -> None:
        """Saldo zerado manda sobre HZA aberta (espelha a regra da api-delpi).

        O saldo da própria operação decide; o do cabeçalho da OP só entra quando
        o apontamento por operação não veio (snapshot antigo ou enrich sem ERP).
        """
        pending_val = _optional_float(item.get("operation_pending_qty"))
        if pending_val is None:
            pending_val = _optional_float(item.get("pending_qty"))
        if pending_val is None or pending_val > 1e-9:
            return
        if not item.get("is_in_production") and item.get("production_status") != "in_progress":
            if item.get("production_status") != "started":
                item["production_status"] = "started"
            return
        item["is_in_production"] = False
        item["production_status"] = "started"
        item["active_operator_count"] = 0

    @staticmethod
    def _recompute_center_counts(
        work_centers: list[dict[str, Any]],
        operations: list[dict[str, Any]],
        *,
        recount_totals: bool = False,
        drop_empty: bool = False,
    ) -> list[dict[str, Any]]:
        """Atualiza contadores do centro. ``recount_totals`` recontabiliza sobre as visíveis.

        ``drop_empty`` tira da lista o centro que ficou sem operação no recorte —
        uma aba vazia só atrapalha quem está olhando um período.
        """
        counts: dict[str, int] = {}
        totals: dict[str, int] = {}
        orders: dict[str, set[str]] = {}
        for item in operations:
            center = str(item.get("work_center") or "").strip()
            if not center:
                continue
            totals[center] = totals.get(center, 0) + 1
            order = _norm_code(item.get("production_order"))
            if order:
                orders.setdefault(center, set()).add(order)
            if item.get("is_in_production"):
                counts[center] = counts.get(center, 0) + 1
        updated: list[dict[str, Any]] = []
        for center in work_centers:
            code = str(center.get("work_center") or "").strip()
            if drop_empty and totals.get(code, 0) == 0:
                continue
            next_center = dict(center)
            next_center["in_production_count"] = counts.get(code, 0)
            if recount_totals:
                next_center["operation_count"] = totals.get(code, 0)
                next_center["order_count"] = len(orders.get(code, ()))
            updated.append(next_center)
        return updated
