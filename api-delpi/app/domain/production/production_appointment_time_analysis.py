"""Diagnóstico canônico da análise de tempos de apontamento produtivo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

from app.domain.production.production_efficiency_valid_range import (
    PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD,
    PRODUCTION_EFFICIENCY_VALID_MAX_PCT,
    PRODUCTION_EFFICIENCY_VALID_MIN_PCT,
    is_low_production_efficiency_pct,
    is_valid_production_efficiency_pct,
)

FindingSeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True)
class AppointmentTimeFinding:
    code: str
    severity: FindingSeverity
    message: str
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_real_hours_source(appointment: dict[str, Any]) -> str:
    start_date = _text(appointment.get("start_date"))
    end_date = _text(appointment.get("end_date"))
    if start_date and end_date:
        return "interval"
    return "h6_tempo"


def build_appointment_time_findings(
    appointment: dict[str, Any],
    *,
    real_hours_source: str | None = None,
) -> list[AppointmentTimeFinding]:
    findings: list[AppointmentTimeFinding] = []

    oee_pct = _float(appointment.get("oee_pct"))
    efficiency_from_times_pct = _float(appointment.get("efficiency_from_times_pct"))
    planned_hours = _float(appointment.get("planned_hours"))
    real_hours = _float(appointment.get("real_hours"))
    setup_hours = _float(appointment.get("setup_hours"))
    standard_time_factor = _float(appointment.get("standard_time_factor"))
    produced_qty = _float(appointment.get("produced_qty"))
    lost_qty = _float(appointment.get("lost_qty"))
    order_planned_qty = _float(appointment.get("order_planned_qty"))
    status = _text(appointment.get("status")).lower()
    source = real_hours_source or resolve_real_hours_source(appointment)

    if status == "outlier" or _is_out_of_range(oee_pct):
        findings.append(
            AppointmentTimeFinding(
                code="oee_out_of_range",
                severity="warning",
                message="OEE registrado (H6_ZEFICI) fora da faixa 0–199%.",
                detail=_format_pct_detail(oee_pct),
            )
        )
    elif is_low_production_efficiency_pct(oee_pct):
        findings.append(
            AppointmentTimeFinding(
                code="low_efficiency_reported",
                severity="warning",
                message=(
                    f"Eficiência abaixo de {PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD}% "
                    "— verifique o motivo da baixa performance."
                ),
                detail=_build_low_efficiency_detail(
                    appointment,
                    metric_label="H6_ZEFICI",
                    efficiency_pct=oee_pct,
                ),
            )
        )

    if _is_out_of_range(efficiency_from_times_pct):
        findings.append(
            AppointmentTimeFinding(
                code="efficiency_times_out_of_range",
                severity="warning",
                message="Eficiência calculada pelos tempos está fora da faixa 0–199%.",
                detail=_format_pct_detail(efficiency_from_times_pct),
            )
        )
    elif is_low_production_efficiency_pct(efficiency_from_times_pct):
        findings.append(
            AppointmentTimeFinding(
                code="low_efficiency_from_times",
                severity="warning",
                message=(
                    f"Eficiência por tempos abaixo de "
                    f"{PRODUCTION_EFFICIENCY_LOW_PCT_THRESHOLD}% — confira horários e roteiro."
                ),
                detail=_build_low_efficiency_detail(
                    appointment,
                    metric_label="tempos",
                    efficiency_pct=efficiency_from_times_pct,
                ),
            )
        )

    if (
        oee_pct is not None
        and efficiency_from_times_pct is not None
        and abs(oee_pct - efficiency_from_times_pct) >= 20
    ):
        findings.append(
            AppointmentTimeFinding(
                code="efficiency_divergence",
                severity="warning",
                message="OEE registrado e eficiência por tempos divergem significativamente.",
                detail=(
                    f"H6_ZEFICI: {_format_pct(oee_pct)} · "
                    f"tempos: {_format_pct(efficiency_from_times_pct)}"
                ),
            )
        )

    if planned_hours is None or planned_hours <= 0:
        findings.append(
            AppointmentTimeFinding(
                code="missing_planned_hours",
                severity="error",
                message="Tempo previsto indisponível ou zerado.",
                detail="Verifique roteiro SG2/SHY010 (setup e fator padrão) e quantidade da OP.",
            )
        )

    if real_hours is None or real_hours <= 0:
        findings.append(
            AppointmentTimeFinding(
                code="missing_real_hours",
                severity="error",
                message="Tempo real indisponível ou zerado.",
                detail="Confira início/fim (H6_DATAINI/HORAINI → H6_DATAFIN/HORAFIN) ou H6_TEMPO.",
            )
        )

    if source == "h6_tempo":
        findings.append(
            AppointmentTimeFinding(
                code="real_hours_from_h6_tempo",
                severity="info",
                message="Tempo real veio de H6_TEMPO (sem intervalo início/fim completo).",
                detail="A eficiência por tempos pode diferir do apontamento manual no chão de fábrica.",
            )
        )

    if (
        real_hours is not None
        and planned_hours is not None
        and real_hours < 0.05
        and planned_hours >= 0.08
    ):
        findings.append(
            AppointmentTimeFinding(
                code="very_short_real_interval",
                severity="warning",
                message="Intervalo real muito curto em relação ao tempo previsto.",
                detail=(
                    f"Real: {_format_hours(real_hours)} · "
                    f"previsto: {_format_hours(planned_hours)} — "
                    "confira horários de início/fim."
                ),
            )
        )

    if standard_time_factor is None or standard_time_factor <= 0:
        findings.append(
            AppointmentTimeFinding(
                code="routing_standard_time_missing",
                severity="warning",
                message="Fator padrão do roteiro ausente ou zerado.",
                detail="SHY010/SG2 sem tempo padrão para a operação do apontamento.",
            )
        )

    if (setup_hours is None or setup_hours <= 0) and (standard_time_factor or 0) > 0:
        findings.append(
            AppointmentTimeFinding(
                code="routing_setup_missing",
                severity="info",
                message="Setup do roteiro zerado; previsto usa apenas fator padrão × quantidade.",
            )
        )

    if produced_qty is not None and produced_qty <= 0 and (real_hours or 0) > 0:
        findings.append(
            AppointmentTimeFinding(
                code="produced_qty_zero_with_runtime",
                severity="warning",
                message="Quantidade apontada zerada com tempo real informado.",
                detail="Pode distorcer o previsto (divisão por qtd_OP) e a eficiência.",
            )
        )

    if lost_qty is not None and lost_qty > 0:
        findings.append(
            AppointmentTimeFinding(
                code="lost_quantity_reported",
                severity="info",
                message="Há quantidade perdida registrada no apontamento.",
                detail=f"Qtd. perdida: {lost_qty:g}",
            )
        )

    if order_planned_qty is not None and order_planned_qty <= 0:
        findings.append(
            AppointmentTimeFinding(
                code="order_planned_qty_missing",
                severity="warning",
                message="Quantidade planejada da OP ausente ou zerada.",
                detail="O previsto pode ter sido calculado só com qtd. apontada.",
            )
        )

    severity_order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda item: (severity_order[item.severity], item.code))
    return findings


def build_appointment_time_analysis(appointment: dict[str, Any]) -> dict[str, Any]:
    real_hours_source = resolve_real_hours_source(appointment)
    findings = build_appointment_time_findings(
        appointment,
        real_hours_source=real_hours_source,
    )

    return {
        "setup_hours": appointment.get("setup_hours"),
        "standard_time_factor": appointment.get("standard_time_factor"),
        "order_planned_qty": appointment.get("order_planned_qty"),
        "produced_qty": appointment.get("produced_qty"),
        "planned_hours": appointment.get("planned_hours"),
        "real_hours": appointment.get("real_hours"),
        "real_hours_source": real_hours_source,
        "time_variance_hours": appointment.get("time_variance_hours"),
        "time_gained_lost_hours": appointment.get("time_gained_lost_hours"),
        "efficiency_from_times_pct": appointment.get("efficiency_from_times_pct"),
        "oee_pct": appointment.get("oee_pct"),
        "formula_planned": (
            "setup + fator_padrão × (qtd_apontada / qtd_OP) — SHY010/roteiro SG2"
        ),
        "formula_real": (
            "início/fim do apontamento (H6_DATAINI/HORAINI → H6_DATAFIN/HORAFIN), "
            "com fallback em H6_TEMPO"
        ),
        "formula_efficiency": "(tempo_previsto / tempo_real) × 100",
        "findings": [finding.to_dict() for finding in findings],
        "has_findings": bool(findings),
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _is_out_of_range(value: float | None) -> bool:
    if value is None:
        return False
    return value < PRODUCTION_EFFICIENCY_VALID_MIN_PCT or value > PRODUCTION_EFFICIENCY_VALID_MAX_PCT


def _format_pct(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}%".replace(".", ",")


def _format_pct_detail(value: float | None) -> str:
    if value is None:
        return "Valor indisponível."
    return f"Valor calculado: {_format_pct(value)}."


def _format_hours(value: float | None) -> str:
    if value is None:
        return "—"
    return f"{value:.2f} h".replace(".", ",")


def _build_low_efficiency_detail(
    appointment: dict[str, Any],
    *,
    metric_label: str,
    efficiency_pct: float | None,
) -> str:
    planned_hours = _float(appointment.get("planned_hours"))
    real_hours = _float(appointment.get("real_hours"))
    time_variance_hours = _float(appointment.get("time_variance_hours"))
    produced_qty = _float(appointment.get("produced_qty"))

    hints: list[str] = [
        f"{metric_label}: {_format_pct(efficiency_pct)}.",
    ]

    if (
        real_hours is not None
        and planned_hours is not None
        and real_hours > planned_hours
    ):
        hints.append(
            f"Tempo real ({_format_hours(real_hours)}) maior que o previsto "
            f"({_format_hours(planned_hours)})."
        )

    if time_variance_hours is not None and time_variance_hours < -0.01:
        hints.append(
            f"Variação de tempo negativa ({_format_hours(time_variance_hours)})."
        )

    if produced_qty is not None and produced_qty <= 0:
        hints.append("Quantidade apontada zerada ou ausente.")

    hints.append(
        "Verifique horários de início/fim, quantidade apontada, roteiro SG2/SHY010 "
        "e paradas não registradas no apontamento."
    )
    return " ".join(hints)
