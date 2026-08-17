"""Motor de consolidação CAPEX — agregações puras sobre linhas filtradas."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Any

from app.domain.services.planejamento_orcamentario.capex_consolidation_constants import (
    DEFAULT_CURRENCY,
    GROUP_BY_AREA,
    GROUP_BY_CATEGORY,
    GROUP_BY_COST_CENTER,
    GROUP_BY_MONTH,
    GROUP_BY_ORIGIN,
    GROUP_BY_PLAN_STATUS,
    GROUP_BY_PRIORITY,
    GROUP_BY_UNIT,
    ORIGIN_LABELS,
    PLAN_STATUS_LABELS,
    PRIORITY_LABELS,
)
from app.domain.services.planejamento_orcamentario.capex_investment_constants import (
    COMPLETENESS_FIELDS,
    REVIEW_PENDING,
    REVIEW_REJECTED,
    REVIEW_APPROVED,
)
from app.domain.services.planejamento_orcamentario.capex_plan_constants import (
    STATUS_APPROVED,
    STATUS_CHANGES_REQUESTED,
    STATUS_DRAFT,
    STATUS_REJECTED,
    STATUS_SUBMITTED,
)
from app.domain.services.planejamento_orcamentario.exceptions import (
    CapexConsolidationCurrencyConflictError,
)

_ZERO = Decimal("0.00")
_CENT = Decimal("0.01")
_HUNDRED = Decimal("100")


def _as_decimal(value: Any) -> Decimal:
    if value is None or value == "":
        return _ZERO
    try:
        return Decimal(str(value)).quantize(_CENT, rounding=ROUND_HALF_UP)
    except Exception:
        return _ZERO


def _money_str(value: Decimal) -> str:
    return str(value.quantize(_CENT, rounding=ROUND_HALF_UP))


def _percent(part: Decimal, whole: Decimal) -> str | None:
    if whole <= 0:
        return None
    pct = (part * _HUNDRED / whole).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return str(pct)


def _compute_completeness(row: dict[str, Any]) -> dict[str, Any]:
    missing: list[str] = []
    for field in COMPLETENESS_FIELDS:
        value = row.get(field)
        if field == "estimated_amount":
            if value is None or value == "":
                missing.append(field)
                continue
            try:
                if Decimal(str(value)) <= 0:
                    missing.append(field)
            except (InvalidOperation, ValueError):
                missing.append(field)
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    return {"is_complete": len(missing) == 0, "missing_fields": missing}


def normalize_currency(value: Any) -> str:
    raw = str(value or "").strip().upper() or DEFAULT_CURRENCY
    return raw


def assert_single_currency(rows: list[dict[str, Any]]) -> str:
    """Exige uma única moeda no conjunto (BRL por padrão). Não soma moedas distintas."""
    currencies = {normalize_currency(r.get("currency")) for r in rows}
    if not currencies:
        return DEFAULT_CURRENCY
    if len(currencies) > 1:
        raise CapexConsolidationCurrencyConflictError(
            "Há investimentos com moedas diferentes no filtro. "
            "A consolidação não soma moedas distintas. Filtre por uma moeda "
            f"ou normalize os registros. Moedas encontradas: {', '.join(sorted(currencies))}."
        )
    return next(iter(currencies))


def enrich_row(row: dict[str, Any]) -> dict[str, Any]:
    """Copia linha com plan_status efetivo e completude."""
    out = dict(row)
    plan_status = str(out.get("plan_status") or STATUS_DRAFT)
    out["plan_status"] = plan_status
    completeness = _compute_completeness(out)
    out["is_complete"] = completeness["is_complete"]
    out["missing_fields"] = completeness["missing_fields"]
    out["currency"] = normalize_currency(out.get("currency"))
    out["estimated_amount_decimal"] = _as_decimal(out.get("estimated_amount"))
    return out


def _plan_status_of(row: dict[str, Any]) -> str:
    return str(row.get("plan_status") or STATUS_DRAFT)


def build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    currency = assert_single_currency(rows)
    enriched = [enrich_row(r) for r in rows]

    total_amount = _ZERO
    incomplete = 0
    cost_centers: set[str] = set()
    plans_by_status: dict[str, set[str]] = defaultdict(set)
    amount_approved = _ZERO
    amount_in_review = _ZERO

    for row in enriched:
        amount = row["estimated_amount_decimal"]
        total_amount += amount
        unit = str(row.get("unit_id") or "").strip()
        cc = str(row.get("cost_center_id") or "").strip()
        cost_centers.add(f"{unit}|{cc}" if unit and cc else cc)
        if not row["is_complete"]:
            incomplete += 1
        status = _plan_status_of(row)
        cc_key = f"{row.get('exercise_id')}|{unit}|{cc}"
        plans_by_status[status].add(cc_key)
        if status == STATUS_APPROVED:
            if str(row.get("review_status") or REVIEW_PENDING) != REVIEW_REJECTED:
                amount_approved += amount
        elif str(row.get("review_status") or "") == REVIEW_APPROVED:
            amount_approved += amount
        elif status in {STATUS_SUBMITTED, STATUS_CHANGES_REQUESTED}:
            if str(row.get("review_status") or REVIEW_PENDING) == REVIEW_PENDING:
                amount_in_review += amount

    def _plan_count(status: str) -> int:
        return len(plans_by_status.get(status, set()))

    return {
        "currency": currency,
        "total_estimated_amount": _money_str(total_amount),
        "investment_count": len(enriched),
        "cost_center_count": len({c for c in cost_centers if c}),
        "plans_draft_count": _plan_count(STATUS_DRAFT),
        "plans_submitted_count": _plan_count(STATUS_SUBMITTED),
        "plans_changes_requested_count": _plan_count(STATUS_CHANGES_REQUESTED),
        "plans_rejected_count": _plan_count(STATUS_REJECTED),
        "plans_approved_count": _plan_count(STATUS_APPROVED),
        "approved_amount": _money_str(amount_approved),
        "in_review_amount": _money_str(amount_in_review),
        "incomplete_investment_count": incomplete,
    }


def _group_key_and_label(
    row: dict[str, Any], *, group_by: str
) -> tuple[str, str]:
    if group_by == GROUP_BY_UNIT:
        code = str(row.get("unit_id") or "")
        name = str(row.get("unit_name") or code or "—")
        return code or "—", name
    if group_by == GROUP_BY_AREA:
        code = str(row.get("area_id") or "") or "—"
        name = str(row.get("area_name") or code)
        return code, name
    if group_by == GROUP_BY_COST_CENTER:
        # Identidade = filial + código (mesmo CC em 01 e 02 não pode somar junto).
        unit = str(row.get("unit_id") or "").strip()
        code = str(row.get("cost_center_id") or "").strip() or "—"
        key = f"{unit}::{code}" if unit else code
        name = str(row.get("cost_center_name") or code)
        return key, name
    if group_by == GROUP_BY_CATEGORY:
        code = str(row.get("category_id") or "") or "—"
        name = str(row.get("category_name") or row.get("category_code") or code)
        return code, name
    if group_by == GROUP_BY_PRIORITY:
        code = str(row.get("priority") or "") or "—"
        return code, PRIORITY_LABELS.get(code, code)
    if group_by == GROUP_BY_ORIGIN:
        code = str(row.get("origin") or "") or "—"
        return code, ORIGIN_LABELS.get(code, code)
    if group_by == GROUP_BY_PLAN_STATUS:
        code = _plan_status_of(row)
        return code, PLAN_STATUS_LABELS.get(code, code)
    if group_by == GROUP_BY_MONTH:
        raw = row.get("required_date")
        if raw is None or raw == "":
            return "sem_data", "Sem data de recebimento"
        if isinstance(raw, datetime):
            key = raw.strftime("%Y-%m")
        elif isinstance(raw, date):
            key = raw.strftime("%Y-%m")
        else:
            text = str(raw)[:7]
            key = text if len(text) == 7 else "sem_data"
        if key == "sem_data":
            return key, "Sem data de recebimento"
        try:
            year, month = key.split("-")
            label = f"{month}/{year}"
        except ValueError:
            label = key
        return key, label
    return "—", "—"


def build_grouping(
    rows: list[dict[str, Any]], *, group_by: str
) -> dict[str, Any]:
    currency = assert_single_currency(rows)
    enriched = [enrich_row(r) for r in rows]
    total_amount = sum((r["estimated_amount_decimal"] for r in enriched), _ZERO)

    buckets: dict[str, dict[str, Any]] = {}
    for row in enriched:
        key, label = _group_key_and_label(row, group_by=group_by)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = {
                "code": key,
                "description": label,
                "investment_count": 0,
                "total_amount": _ZERO,
                "plan_statuses": set(),
                "unit_id": row.get("unit_id"),
                "area_id": row.get("area_id"),
                "cost_center_id": row.get("cost_center_id"),
            }
            buckets[key] = bucket
        bucket["investment_count"] += 1
        bucket["total_amount"] += row["estimated_amount_decimal"]
        bucket["plan_statuses"].add(_plan_status_of(row))
        # Preferir descrição mais rica se disponível
        if label and label != key:
            bucket["description"] = label

    items: list[dict[str, Any]] = []
    for key in sorted(buckets.keys()):
        bucket = buckets[key]
        amount = bucket["total_amount"]
        item: dict[str, Any] = {
            "code": bucket["code"],
            "description": bucket["description"],
            "investment_count": bucket["investment_count"],
            "total_amount": _money_str(amount),
            "percent_of_total": _percent(amount, total_amount),
        }
        if group_by == GROUP_BY_COST_CENTER:
            statuses = sorted(bucket["plan_statuses"])
            unit_id = bucket.get("unit_id")
            cost_center_id = bucket.get("cost_center_id")
            item["unit_id"] = unit_id
            item["area_id"] = bucket.get("area_id")
            item["cost_center_id"] = cost_center_id or key
            # `code` permanece o código do CC (UI); unicidade vem do par unit+cc.
            item["code"] = str(cost_center_id or key)
            item["plan_status"] = statuses[0] if len(statuses) == 1 else ",".join(statuses)
            item["plan_status_label"] = (
                PLAN_STATUS_LABELS.get(statuses[0], statuses[0])
                if len(statuses) == 1
                else ", ".join(PLAN_STATUS_LABELS.get(s, s) for s in statuses)
            )
        items.append(item)

    return {
        "group_by": group_by,
        "currency": currency,
        "total_estimated_amount": _money_str(total_amount),
        "items": items,
    }


def build_detail_item(row: dict[str, Any]) -> dict[str, Any]:
    enriched = enrich_row(row)
    required = enriched.get("required_date")
    if isinstance(required, (date, datetime)):
        required_out = required.date().isoformat() if isinstance(required, datetime) else required.isoformat()
    else:
        required_out = str(required)[:10] if required else None
    return {
        "id": enriched.get("id"),
        "exercise_id": enriched.get("exercise_id"),
        "unit_id": enriched.get("unit_id"),
        "unit_name": enriched.get("unit_name"),
        "area_id": enriched.get("area_id"),
        "area_name": enriched.get("area_name"),
        "cost_center_id": enriched.get("cost_center_id"),
        "cost_center_name": enriched.get("cost_center_name"),
        "responsible": enriched.get("responsible") or enriched.get("plan_submitted_by"),
        "description": enriched.get("description"),
        "category_id": enriched.get("category_id"),
        "category_code": enriched.get("category_code"),
        "category_name": enriched.get("category_name"),
        "priority": enriched.get("priority"),
        "priority_label": PRIORITY_LABELS.get(str(enriched.get("priority") or ""), enriched.get("priority")),
        "origin": enriched.get("origin"),
        "origin_label": ORIGIN_LABELS.get(str(enriched.get("origin") or ""), enriched.get("origin")),
        "probable_supplier_name": enriched.get("probable_supplier_name"),
        "probable_supplier_code": enriched.get("probable_supplier_code"),
        "estimated_amount": _money_str(enriched["estimated_amount_decimal"]),
        "currency": enriched.get("currency"),
        "required_date": required_out,
        "is_complete": enriched["is_complete"],
        "missing_fields": enriched["missing_fields"],
        "plan_status": enriched["plan_status"],
        "plan_status_label": PLAN_STATUS_LABELS.get(enriched["plan_status"], enriched["plan_status"]),
        "plan_id": enriched.get("plan_id"),
        "updated_at": str(enriched.get("updated_at") or "") or None,
        "created_at": str(enriched.get("created_at") or "") or None,
    }
