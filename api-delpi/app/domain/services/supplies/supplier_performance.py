"""Supplier IDF: equal-scale indices, approved weights, explicit missing evidence."""

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Protocol


class SupplierPerformanceReadPort(Protocol):
    def read_counts(
        self, *, branches: list[str], date_from: str, date_to: str
    ) -> list[dict]: ...


def _round(value: Decimal) -> float:
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def compose_supplier_performance(rows: list[dict]) -> dict:
    suppliers: dict[tuple[str, str], dict] = {}
    for row in rows:
        code, store = (
            str(row.get("supplier_code") or "").strip(),
            str(row.get("supplier_store") or "").strip(),
        )
        if not code or not store:
            raise ValueError("A fonte retornou fornecedor sem código ou loja.")
        entry = suppliers.setdefault(
            (code, store),
            {
                "supplier_code": code,
                "supplier_store": store,
                "supplier_name": str(row.get("supplier_name") or code).strip(),
                "branches": set(),
                "quality": defaultdict(int),
                "delivery": defaultdict(int),
            },
        )
        entry["branches"].add(str(row["branch"]).strip())
        source = row["source"]
        if source not in {"quality", "delivery"}:
            raise ValueError("Fonte do indicador inválida.")
        target = entry[source]
        for key in (
            "assessed_count",
            "positive_count",
            "unknown_count",
            "conditional_count",
            "urgent_count",
        ):
            count = int(row.get(key) or 0)
            if count < 0:
                raise ValueError("Contagem negativa na fonte do indicador.")
            target[key] += count

    result = []
    scores = []
    quality_values, delivery_values = [], []
    for entry in suppliers.values():
        indices = {}
        for source in ("quality", "delivery"):
            counts = {
                key: entry[source].get(key, 0)
                for key in (
                    "assessed_count",
                    "positive_count",
                    "unknown_count",
                    "conditional_count",
                    "urgent_count",
                )
            }
            total, positive = counts.get("assessed_count", 0), counts.get(
                "positive_count", 0
            )
            if positive > total:
                raise ValueError("Contagem de aprovações maior que a base avaliada.")
            index = Decimal(positive) * 100 / total if total else None
            indices[source] = index
            counts.update(
                {
                    "index": _round(index) if index is not None else None,
                    "negative_count": total - positive,
                }
            )
            entry[source] = counts
        complete = all(
            indices[source] is not None and not entry[source].get("unknown_count")
            for source in indices
        )
        score = (
            indices["quality"] * Decimal("0.70") + indices["delivery"] * Decimal("0.30")
            if complete
            else None
        )
        quality_contribution = (
            indices["quality"] * Decimal("0.70")
            if indices["quality"] is not None
            else None
        )
        delivery_contribution = (
            indices["delivery"] * Decimal("0.30")
            if indices["delivery"] is not None
            else None
        )
        if score is not None:
            scores.append(score)
            quality_values.append(indices["quality"])
            delivery_values.append(indices["delivery"])
        entry.update(
            {
                "branches": sorted(entry["branches"]),
                "idf": _round(score) if score is not None else None,
                "quality_contribution": (
                    _round(quality_contribution)
                    if quality_contribution is not None
                    else None
                ),
                "delivery_contribution": (
                    _round(delivery_contribution)
                    if delivery_contribution is not None
                    else None
                ),
                "status": (
                    "complete"
                    if complete
                    else (
                        "inconsistent"
                        if any(entry[s].get("unknown_count") for s in indices)
                        else (
                            "missing_quality"
                            if indices["quality"] is None
                            else "missing_delivery"
                        )
                    )
                ),
            }
        )
        result.append(entry)
    result.sort(
        key=lambda item: (
            item["idf"] is None,
            -(item["idf"] or 0),
            item["supplier_name"].casefold(),
            item["supplier_code"],
            item["supplier_store"],
        )
    )
    return {
        "items": result,
        "summary": {
            "suppliers": len(result),
            "evaluated": len(scores),
            "incomplete": len(result) - len(scores),
            "average_idf": _round(sum(scores) / len(scores)) if scores else None,
            "average_quality": (
                _round(sum(quality_values) / len(scores)) if scores else None
            ),
            "average_delivery": (
                _round(sum(delivery_values) / len(scores)) if scores else None
            ),
            "inspection_count": sum(
                item["quality"].get("assessed_count", 0) for item in result
            ),
            "receipt_count": sum(
                item["delivery"].get("assessed_count", 0) for item in result
            ),
        },
        "methodology": {
            "quality_weight": 70,
            "delivery_weight": 30,
            "scale": 100,
            "quality": "approved_inspections_over_concluded",
            "quality_date": "report_date",
            "delivery": "on_time_receipt_lines_over_receipt_lines",
            "delivery_date": "receipt_entry_date",
            "product_scope": "supplies_otd",
            "classification_bands": None,
            "quality_includes_conditional_and_urgent": True,
        },
    }
