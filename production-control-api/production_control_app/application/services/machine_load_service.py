from __future__ import annotations

import json
import logging
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from production_control_app.core.security import PC_MACHINE_LOAD_VIEW, can
from production_control_app.domain.errors import DelpiGatewayError, SnapshotNotFound
from production_control_app.domain.ports.machine_load_snapshot_repository import (
    MachineLoadSnapshotRepositoryPort,
)
from production_control_app.domain.ports.production_orders_gateway import ProductionOrdersGateway
from production_control_app.domain.services.machine_load_delivery_sequencing import (
    optimize_by_delivery_date,
)
from production_control_app.domain.services.machine_load_delivery_window import (
    delivery_bounds,
    filter_by_delivery_window,
    missing_due_date_count,
)
from production_control_app.domain.services.machine_load_priority import (
    prioritize_conjunto as prioritize_conjunto_in_queue,
)
from production_control_app.domain.services.machine_load_queue_slots import (
    is_started_operation,
)
from production_control_app.domain.services.machine_load_transfer import (
    TRANSFERRED_OPERATIONS_KEY,
    apply_transfers,
    find_operation,
    move_conjunto_at_work_center,
    move_operation,
    normalize_work_center,
    original_work_center,
    register_transfer,
    transfer_entries,
)
from production_control_app.domain.services.machine_load_withdrawal import (
    WITHDRAWN_CONJUNTOS_KEY,
    is_withdrawn,
    restore_conjunto as restore_conjunto_from_queue,
    visible_operations,
    withdraw_conjunto as withdraw_conjunto_from_queue,
    withdrawn_entries,
    withdrawn_order_numbers,
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
    get_live_status_cache,
    put_live_status_cache,
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
}

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
)


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


def _parse_iso_date(value: str | None) -> date | None:
    text = str(value or "").strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _dict_items(payload: dict[str, Any] | list[Any] | None) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    items = payload.get("items")
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)]


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
        branch_access: BranchAccessService | None = None,
        change_notifier: Callable[..., None] | None = None,
    ) -> None:
        self._gateway = gateway
        self._snapshots = snapshots
        self._branch_access = branch_access or BranchAccessService()
        self._change_notifier = change_notifier

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
        )

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
        row = self._snapshots.get(branch=code)
        if row is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi publicada pelo PCP."
            )
        payload = self._present(
            row,
            work_center=work_center,
            seeded=False,
            branch=code,
        )
        return self._strip_internal_identity(payload)

    def public_snapshot_contains_pa(self, *, branch: str, pa_code: str) -> bool:
        """Confere se o PA aparece na fila congelada da filial — sem puxar o TOTVS."""
        code = self._branch_access.assert_valid_branch(branch)
        wanted = str(pa_code or "").strip()
        if not wanted:
            return False
        row = self._snapshots.get(branch=code)
        if row is None:
            raise SnapshotNotFound(
                "A fila desta filial ainda não foi publicada pelo PCP."
            )
        payload = self._decode_payload(row)
        operations = _dict_items(payload.get("operations"))
        if not operations and isinstance(payload.get("operations"), list):
            operations = _dict_items(payload["operations"])
        operations = visible_operations(operations, withdrawn_order_numbers(payload))
        wanted_key = wanted.upper()
        for item in operations:
            pa = str(item.get("pa_product_code") or "").strip()
            if pa.upper() == wanted_key:
                return True
        return False

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
        self._notify_change(branch=branch, reason="refresh")
        return presented

    def reorder_sequence(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str,
        ordered_keys: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Reordena as operações de um CT no snapshot sem puxar o TOTVS."""
        self._assert_can_view(user, branch)
        center = str(work_center or "").strip()
        if not center:
            raise ValueError("workCenter é obrigatório para reordenar a sequência.")

        row, payload = self._load_snapshot_payload(branch=branch)
        operations = _dict_items(payload.get("operations"))
        if not operations and isinstance(payload.get("operations"), list):
            operations = _dict_items(payload["operations"])

        reordered = self._apply_center_order(
            operations,
            work_center=center,
            ordered_keys=ordered_keys,
            withdrawn_keys=withdrawn_order_numbers(payload),
        )
        now = datetime.now(timezone.utc).isoformat()
        payload["operations"] = reordered
        payload["sequence_updated_at"] = now
        payload["sequence_updated_by"] = _user_label(user)

        updated = self._snapshots.update_payload(branch=branch, payload=payload)
        presented = self._present(
            updated,
            work_center=center,
            seeded=False,
            branch=branch,
        )
        self._notify_change(branch=branch, reason="sequence", work_center=center)
        return presented

    def prioritize_conjunto(
        self,
        user: object | None,
        *,
        branch: str,
        order_number: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Leva todas as OPs do conjunto (C2_NUM) ao topo da fila de cada centro.

        Operações já iniciadas não são ultrapassadas: o conjunto entra logo depois delas.
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
        stored_operations = _dict_items(payload.get("operations"))
        if not stored_operations and isinstance(payload.get("operations"), list):
            stored_operations = _dict_items(payload["operations"])

        # Conjunto fora da programação não participa da fila — nem para priorizar.
        withdrawn_keys = withdrawn_order_numbers(payload)
        operations = visible_operations(stored_operations, withdrawn_keys)

        if not any(
            order_belongs_to_conjunto(item.get("production_order"), conjunto_key)
            for item in operations
        ):
            template = str(
                messages.get("notInQueue")
                or "Nenhuma operação do conjunto «{conjunto}» está na fila deste período."
            )
            raise ValueError(template.format(conjunto=conjunto_key))

        # O status vivo (HZA) decide quem já começou; o snapshot congelado guarda só a ordem.
        started_keys = {
            _operation_key(item)
            for item in self._enrich_live_status(branch=branch, operations=operations)
            if is_started_operation(item)
        }
        result = prioritize_conjunto_in_queue(
            operations,
            conjunto_key=conjunto_key,
            started_keys=started_keys,
        )

        target_row = row
        if result.work_centers:
            payload["operations"] = self._merge_visible_order(
                stored_operations,
                withdrawn_keys=withdrawn_keys,
                reordered_visible=result.operations,
            )
            payload["sequence_updated_at"] = datetime.now(timezone.utc).isoformat()
            payload["sequence_updated_by"] = _user_label(user)
            target_row = self._snapshots.update_payload(branch=branch, payload=payload)

        presented = self._present(
            target_row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        if result.work_centers:
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
            "work_centers": result.work_centers,
            "operation_count": result.prioritized_operation_count,
            "kept_ahead_count": result.kept_ahead_count,
            "message": template.format(
                conjunto=conjunto_key,
                centers=len(result.work_centers),
                operations=result.prioritized_operation_count,
            ),
        }
        if result.work_centers:
            self._notify_change(branch=branch, reason="priority")
        return presented

    def optimize_delivery_sequence(
        self,
        user: object | None,
        *,
        branch: str,
        work_center: str | None = None,
    ) -> dict[str, Any]:
        """Resequencia a fila de todos os centros pela entrega do PA.

        O carga máquina do TOTVS às vezes deixa material de entrega distante à
        frente do que está vencendo. Operações já iniciadas continuam onde estão.
        """
        self._assert_can_view(user, branch)
        cfg = _machine_load_settings()
        messages = (
            cfg.get("optimizeDelivery")
            if isinstance(cfg.get("optimizeDelivery"), dict)
            else {}
        )

        row, payload = self._load_snapshot_payload(branch=branch)
        stored_operations = self._payload_operations(payload)

        # Conjunto fora da programação não participa da fila — nem para otimizar.
        withdrawn_keys = withdrawn_order_numbers(payload)
        operations = visible_operations(stored_operations, withdrawn_keys)
        if not operations:
            raise ValueError(
                str(
                    messages.get("emptyQueue")
                    or "Não há operações na fila desta filial para otimizar."
                )
            )

        # O status vivo (HZA) decide quem já começou; o snapshot guarda só a ordem.
        started_keys = {
            _operation_key(item)
            for item in self._enrich_live_status(branch=branch, operations=operations)
            if is_started_operation(item)
        }
        result = optimize_by_delivery_date(operations, started_keys=started_keys)

        target_row = row
        if result.work_centers:
            payload["operations"] = self._merge_visible_order(
                stored_operations,
                withdrawn_keys=withdrawn_keys,
                reordered_visible=result.operations,
            )
            payload["sequence_updated_at"] = datetime.now(timezone.utc).isoformat()
            payload["sequence_updated_by"] = _user_label(user)
            target_row = self._snapshots.update_payload(branch=branch, payload=payload)

        presented = self._present(
            target_row,
            work_center=work_center,
            seeded=False,
            branch=branch,
        )
        if result.work_centers:
            template = str(
                messages.get("applied")
                or "Fila reordenada por entrega do PA em {centers} centro(s) de trabalho."
            )
        else:
            template = str(
                messages.get("nothingToDo")
                or "A fila já está ordenada pela entrega do PA em todos os centros."
            )
        presented["optimization"] = {
            "work_centers": result.work_centers,
            "moved_operation_count": result.moved_operation_count,
            "kept_ahead_count": result.kept_ahead_count,
            "missing_due_date_count": result.missing_due_date_count,
            "message": template.format(
                centers=len(result.work_centers),
                operations=result.moved_operation_count,
                kept_ahead=result.kept_ahead_count,
                missing=result.missing_due_date_count,
            ),
        }
        if result.work_centers:
            self._notify_change(branch=branch, reason="delivery_sequence")
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
        row, payload = self._load_snapshot_payload(branch=branch)

        operations = self._payload_operations(payload)
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
                self._format_withdrawal_message(messages, "notInQueue", conjunto=conjunto_key)
            )

        now = datetime.now(timezone.utc).isoformat()
        next_entries, changed = withdraw_conjunto_from_queue(
            entries,
            order_number=conjunto_key,
            operations=operations,
            withdrawn_at=now,
            withdrawn_by=_user_label(user),
        )
        return self._store_withdrawal(
            row,
            branch=branch,
            payload=payload,
            entries=next_entries,
            entry=next(
                (item for item in next_entries if item.get("order_number") == conjunto_key),
                None,
            ),
            changed=changed,
            updated_by=_user_label(user),
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
        row, payload = self._load_snapshot_payload(branch=branch)

        current_entries = withdrawn_entries(payload)
        removed = next(
            (item for item in current_entries if item.get("order_number") == conjunto_key), None
        )
        next_entries, changed = restore_conjunto_from_queue(
            current_entries,
            order_number=conjunto_key,
        )
        if not changed:
            raise ValueError(
                self._format_withdrawal_message(messages, "notWithdrawn", conjunto=conjunto_key)
            )
        return self._store_withdrawal(
            row,
            branch=branch,
            payload=payload,
            entries=next_entries,
            entry=removed,
            changed=changed,
            updated_by=_user_label(user),
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

        row, payload = self._load_snapshot_payload(branch=branch)
        operations = self._payload_operations(payload)
        centers = {
            str(item.get("work_center") or "").strip(): str(item.get("work_center_name") or "").strip()
            for item in _dict_items(payload.get("work_centers"))
            if str(item.get("work_center") or "").strip()
        }
        if target not in centers:
            raise ValueError(
                self._format_transfer_message(messages, "unknownTarget", center=target)
            )

        current = find_operation(operations, production_order=order, operation_code=operation)
        if current is None:
            raise ValueError(
                self._format_transfer_message(
                    messages, "notInQueue", order=order, operation=operation
                )
            )
        if is_withdrawn(current, withdrawn_order_numbers(payload)):
            raise ValueError(self._format_transfer_message(messages, "withdrawn", order=order))
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
        updated = self._snapshots.update_payload(branch=branch, payload=payload)

        presented = self._present(
            updated,
            work_center=work_center or target,
            seeded=False,
            branch=branch,
        )
        presented["transfer"] = {
            "production_order": order,
            "operation_code": operation,
            "source_work_center": source,
            "target_work_center": target,
            "target_work_center_name": centers.get(target) or None,
            "returned_to_origin": target == origin,
            "message": self._format_transfer_message(
                messages,
                "applied",
                order=order,
                operation=operation,
                source=source,
                target=target,
            ),
        }
        self._notify_change(branch=branch, reason="transfer", work_center=target)
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

        row, payload = self._load_snapshot_payload(branch=branch)
        operations = self._payload_operations(payload)
        withdrawn_keys = withdrawn_order_numbers(payload)
        if conjunto_key in withdrawn_keys:
            raise ValueError(
                self._format_transfer_message(
                    messages, "withdrawn", order=conjunto_key
                )
            )

        centers = {
            str(item.get("work_center") or "").strip(): str(item.get("work_center_name") or "").strip()
            for item in _dict_items(payload.get("work_centers"))
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
        updated = self._snapshots.update_payload(branch=branch, payload=payload)

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
            "operation_count": len(moved.moved),
            "source_work_center": source,
            "target_work_center": target,
            "target_work_center_name": centers.get(target) or None,
            "returned_to_origin": False,
            "scope": "conjunto_at_center",
            "message": self._format_transfer_message(
                messages,
                "conjuntoApplied",
                conjunto=conjunto_key,
                operations=len(moved.moved),
                source=source,
                target=target,
            ),
        }
        self._notify_change(branch=branch, reason="transfer", work_center=target)
        return presented

    @staticmethod
    def _transfer_messages() -> dict[str, Any]:
        cfg = _machine_load_settings()
        raw = cfg.get("transfer")
        return raw if isinstance(raw, dict) else {}

    @staticmethod
    def _format_transfer_message(messages: dict[str, Any], key: str, **values: Any) -> str:
        template = str(messages.get(key) or _TRANSFER_FALLBACK_MESSAGES.get(key, ""))
        return template.format(**values)

    def _store_withdrawal(
        self,
        row: dict[str, Any],
        *,
        branch: str,
        payload: dict[str, Any],
        entries: list[dict[str, Any]],
        entry: dict[str, Any] | None,
        changed: bool,
        updated_by: str | None,
        work_center: str | None,
        conjunto_key: str,
        action: str,
        message_key: str,
        messages: dict[str, Any],
    ) -> dict[str, Any]:
        target_row = row
        if changed:
            payload[WITHDRAWN_CONJUNTOS_KEY] = entries
            payload["withdrawal_updated_at"] = datetime.now(timezone.utc).isoformat()
            payload["withdrawal_updated_by"] = updated_by
            target_row = self._snapshots.update_payload(branch=branch, payload=payload)

        presented = self._present(
            target_row,
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
        if changed:
            self._notify_change(branch=branch, reason="withdrawal")
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
        row = self._snapshots.get(branch=branch)
        if row is None:
            raise SnapshotNotFound(
                "Não há carga máquina congelada nesta filial. Atualize a partir do TOTVS."
            )
        return row, self._decode_payload(row)

    @staticmethod
    def _payload_operations(payload: dict[str, Any]) -> list[dict[str, Any]]:
        operations = _dict_items(payload.get("operations"))
        if not operations and isinstance(payload.get("operations"), list):
            operations = _dict_items(payload["operations"])
        return operations

    @staticmethod
    def _merge_visible_order(
        operations: list[dict[str, Any]],
        *,
        withdrawn_keys: set[str],
        reordered_visible: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Reaplica a nova ordem só nos slots visíveis; retiradas ficam onde estavam."""
        if not withdrawn_keys:
            return reordered_visible
        merged = list(operations)
        slots = [
            index
            for index, item in enumerate(operations)
            if not is_withdrawn(item, withdrawn_keys)
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
        operations = self._payload_operations(payload)
        operations = self._enrich_live_status(branch=branch, operations=operations)
        # Rastreio ainda encontra conjunto retirado — marcado como fora da programação.
        withdrawn_keys = withdrawn_order_numbers(payload)
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
                    withdrawn_keys=withdrawn_keys,
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
        withdrawn_keys: set[str] | None = None,
    ) -> dict[str, Any]:
        hidden = withdrawn_keys or set()
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
                    "unit": item.get("unit"),
                    "tool": str(item.get("tool") or "").strip(),
                    "production_status": item.get("production_status") or "not_started",
                    "is_in_production": bool(item.get("is_in_production")),
                    "production_started_time": item.get("production_started_time"),
                    "active_operator_name": item.get("active_operator_name"),
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
        snapshot = public_payload.get("snapshot")
        if isinstance(snapshot, dict):
            public_payload["snapshot"] = {
                key: value
                for key, value in snapshot.items()
                if key not in _INTERNAL_IDENTITY_FIELDS
            }
        return public_payload

    @staticmethod
    def _decode_payload(row: dict[str, Any]) -> dict[str, Any]:
        raw_payload = row.get("payload_json")
        if isinstance(raw_payload, str):
            payload = json.loads(raw_payload)
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = {}
        return dict(payload)

    @staticmethod
    def _apply_center_order(
        operations: list[dict[str, Any]],
        *,
        work_center: str,
        ordered_keys: list[dict[str, Any]],
        withdrawn_keys: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Reordena um CT. Operações retiradas não entram na permutação e ficam na posição atual."""
        hidden = withdrawn_keys or set()
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
            previous_payload = self._decode_payload(previous)
            entries = withdrawn_entries(previous_payload)
            if entries:
                frozen[WITHDRAWN_CONJUNTOS_KEY] = entries
                frozen["withdrawal_updated_at"] = previous_payload.get("withdrawal_updated_at")
                frozen["withdrawal_updated_by"] = previous_payload.get("withdrawal_updated_by")
            transfers = transfer_entries(previous_payload)
            if transfers:
                frozen[TRANSFERRED_OPERATIONS_KEY] = transfers
                frozen["operations"] = apply_transfers(
                    _dict_items(frozen.get("operations")),
                    transfers,
                    work_center_names={
                        str(item.get("work_center") or "").strip(): str(
                            item.get("work_center_name") or ""
                        ).strip()
                        for item in _dict_items(frozen.get("work_centers"))
                    },
                )
        # Início aberto vira a entrega mais antiga que realmente veio — é o que a
        # tela mostra no campo «De» e o que descreve a janela puxada.
        oldest_due, _newest = delivery_bounds(_dict_items(frozen.get("operations")))
        effective_start = start or _parse_iso_date(oldest_due) or end
        # Fila nova do TOTVS: status HZA em cache não vale mais.
        clear_live_status_cache(branch)
        return self._snapshots.upsert(
            branch=branch,
            start_date=effective_start,
            end_date=end,
            payload=frozen,
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

        try:
            centers_payload = _unwrap_data(
                self._gateway.fetch_machine_load_work_centers(
                    branch=branch,
                    delivery_start=start_s,
                    delivery_end=end_s,
                )
            )
        except DelpiGatewayError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise DelpiGatewayError(
                "Não foi possível carregar os centros de trabalho."
            ) from exc

        work_centers = _dict_items(centers_payload)
        operations = self._fetch_all_operations(
            branch=branch,
            delivery_start=start_s,
            delivery_end=end_s,
            page_size=page_size,
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

            batch = _dict_items(payload)
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
    ) -> dict[str, Any]:
        raw_payload = row.get("payload_json")
        if isinstance(raw_payload, str):
            payload = json.loads(raw_payload)
        elif isinstance(raw_payload, dict):
            payload = raw_payload
        else:
            payload = {}

        work_centers = _dict_items(payload.get("work_centers"))
        if not work_centers and isinstance(payload.get("work_centers"), list):
            work_centers = _dict_items(payload["work_centers"])
        operations = _dict_items(payload.get("operations"))
        if not operations and isinstance(payload.get("operations"), list):
            operations = _dict_items(payload["operations"])

        operations = self._enrich_live_status(branch=branch, operations=operations)
        # Conjunto retirado continua no snapshot (posição original preservada), mas some da fila.
        withdrawn_keys = withdrawn_order_numbers(payload)
        operations = visible_operations(operations, withdrawn_keys)
        # A fila congelada é uma só; o período pedido na tela é lente de leitura.
        filtered = view_start is not None or view_end is not None
        if filtered:
            operations = filter_by_delivery_window(
                operations, start=view_start, end=view_end
            )
        # Retirada, transferência e lente mudam quantas operações cada centro tem de fato.
        moved_operations = bool(withdrawn_keys) or bool(transfer_entries(payload))
        work_centers = self._recompute_center_counts(
            work_centers,
            operations,
            recount_totals=moved_operations or filtered,
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
        if withdrawn_keys or filtered:
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
            },
            "work_centers": work_centers,
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

    def _enrich_live_status(
        self,
        *,
        branch: str,
        operations: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not operations:
            return operations

        cached = get_live_status_cache(branch)
        if cached is not None:
            return self._apply_status_map(operations, cached)

        keys = [
            {
                "production_order": order,
                "operation_code": operation,
            }
            for order, operation in {_operation_key(item) for item in operations}
            if order and operation
        ]
        if not keys:
            return operations

        try:
            status_payload = _unwrap_data(
                self._gateway.fetch_machine_load_appointment_status(
                    branch=branch,
                    items=keys,
                )
            )
        except DelpiGatewayError:
            # Snapshot continua útil mesmo se o enrich HZA falhar.
            return operations
        except Exception:
            return operations

        status_by_key = {
            _operation_key(item): item for item in _dict_items(status_payload)
        }
        put_live_status_cache(branch, status_by_key)
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
                enriched.append(item)
                continue
            merged = dict(item)
            for field in _STATUS_FIELDS:
                if field in status:
                    merged[field] = status[field]
            enriched.append(merged)
        return enriched

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
