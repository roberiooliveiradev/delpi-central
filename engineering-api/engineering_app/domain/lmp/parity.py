"""Comparador de paridade shadow — tolerância 0 (doc 33/34, G3.7).

Compara campos determinísticos entre o resultado legado (api-delpi
dashboard) e o resultado migrado (Engineering API sobre facts).
Determinístico: após normalização de tipos, qualquer diferença é
divergência — nunca tolerância genérica mascarando semântica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

# Campos de comparação por regra — cada divergência registra o rule id.
ITEM_PARITY_FIELDS: dict[str, tuple[str, ...]] = {
    "R02": ("nivel",),
    "R01": ("dias_uteis_sla", "sla_minutos"),
    "R01+R03": ("data_limite",),
    "R05": ("lead_time_util",),
    "R04": ("status",),
    "S05": ("listing_kind",),
    "SOURCE": (
        "branch",
        "sale_number",
        "sale_description",
        "start_date",
        "end_date",
        "engineering_status",
        "engineering_total_minutes",
        "qtd_pi",
        "homolog_revision",
        "measurement_revision",
        "homolog_date",
        "cycle_index",
    ),
}

SUMMARY_PARITY_FIELDS: dict[str, tuple[str, ...]] = {
    "R09": ("percent_dentro_prazo",),
    "R10": ("avg_lead_time",),
    "COUNT": ("total_lmps", "total_items"),
}


@dataclass(frozen=True)
class ParityDivergence:
    rule_id: str
    field: str
    key: str
    expected: Any
    actual: Any
    status: str = "open"


@dataclass
class ParityReport:
    compared: int = 0
    matched_keys: int = 0
    divergences: list[ParityDivergence] = field(default_factory=list)
    missing_in_actual: list[str] = field(default_factory=list)
    missing_in_expected: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return (
            not self.divergences
            and not self.missing_in_actual
            and not self.missing_in_expected
        )


def _normalize(value: Any) -> Any:
    """Normalização determinística: tipos e representação — não semântica."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    return text if text else None


def _item_key(item: Mapping[str, Any]) -> str:
    branch = str(item.get("branch") or "").strip()
    sale_number = str(item.get("sale_number") or "").strip()
    revision = str(item.get("homolog_revision") or item.get("measurement_revision") or "").strip()
    cycle = str(item.get("cycle_index") or "1").strip()
    return f"{branch}|{sale_number}|{revision}|{cycle}"


def compare_items(
    expected: Iterable[Mapping[str, Any]],
    actual: Iterable[Mapping[str, Any]],
    *,
    field_map: Mapping[str, str] | None = None,
) -> ParityReport:
    """Compara itens por chave (branch|ov|rev|cycle), tolerância 0.

    `field_map` traduz nome-de-campo esperado → nome no payload atual
    (ex.: facts `residence_minutes` ↔ legado `engineering_total_minutes`).
    """
    report = ParityReport()
    field_map = field_map or {}

    expected_by_key = {_item_key(item): item for item in expected}
    actual_by_key = {_item_key(item): item for item in actual}
    report.compared = len(expected_by_key)

    for key in sorted(expected_by_key.keys() | actual_by_key.keys()):
        exp = expected_by_key.get(key)
        act = actual_by_key.get(key)
        if exp is None:
            report.missing_in_expected.append(key)
            continue
        if act is None:
            report.missing_in_actual.append(key)
            continue

        matched = True
        for rule_id, fields in ITEM_PARITY_FIELDS.items():
            for field_name in fields:
                expected_value = _normalize(exp.get(field_name))
                actual_value = _normalize(
                    act.get(field_map.get(field_name, field_name))
                )
                if expected_value != actual_value:
                    matched = False
                    report.divergences.append(
                        ParityDivergence(
                            rule_id=rule_id,
                            field=field_name,
                            key=key,
                            expected=exp.get(field_name),
                            actual=act.get(field_map.get(field_name, field_name)),
                        )
                    )
        if matched:
            report.matched_keys += 1

    return report


def compare_summary(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    field_map: Mapping[str, str] | None = None,
) -> ParityReport:
    """Compara KPIs de summary, tolerância 0 após normalização."""
    report = ParityReport(compared=1)
    field_map = field_map or {}
    for rule_id, fields in SUMMARY_PARITY_FIELDS.items():
        for field_name in fields:
            expected_value = _normalize(expected.get(field_name))
            actual_value = _normalize(actual.get(field_map.get(field_name, field_name)))
            if expected_value != actual_value:
                report.divergences.append(
                    ParityDivergence(
                        rule_id=rule_id,
                        field=field_name,
                        key="summary",
                        expected=expected.get(field_name),
                        actual=actual.get(field_map.get(field_name, field_name)),
                    )
                )
    if not report.divergences:
        report.matched_keys = 1
    return report
