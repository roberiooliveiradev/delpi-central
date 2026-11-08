"""Projeção pura MyWEG → linhas internas de Demanda (somente leitura).

Reusa ``resolve_product_identity`` do motor de comparação. Não consulta Protheus,
não altera snapshots e não alimenta ``GET /demand``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Mapping, Sequence

from production_control_app.domain.myweg_demand_source_contract import (
    DEMAND_SOURCE_BRANCH,
    DISPLAY_ORDER_MYWEG,
    LINE_ID_PREFIX,
    PROVISIONAL_SAMPLE_MATCHED_BY,
    SOURCE_MYWEG,
    WEG_LINHARES_CUSTOMER_CODE,
    WEG_LINHARES_CUSTOMER_NAME,
    WEG_LINHARES_CUSTOMER_STORE,
)
from production_control_app.domain.myweg_needs_contract import decimal_to_canonical_str
from production_control_app.domain.services.myweg_needs_comparison import (
    resolve_product_identity,
)

ZERO = Decimal("0")


def _dec(value: Any) -> Decimal:
    if value is None:
        return ZERO
    if isinstance(value, Decimal):
        return value
    text = str(value).strip()
    if not text:
        return ZERO
    return Decimal(text)


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _iso_dt(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text = str(value).strip()
    return text or None


def is_provisional_sample_resolution(sb1: Mapping[str, Any] | None) -> bool:
    """Vínculo provisório de amostra (8…) — rastreável, fora da cobertura produtiva."""
    if not isinstance(sb1, Mapping):
        return False
    matched_by = str(sb1.get("matched_by") or "").strip()
    return matched_by in PROVISIONAL_SAMPLE_MATCHED_BY


def is_coverage_eligible(
    *,
    identity_kind: str,
    resolution_status: str,
    matched_by: str | None,
    verified_product_code: str | None,
) -> bool:
    """Somente identidade SB1 confirmada e não provisória de amostra."""
    if identity_kind != "verified_code":
        return False
    if str(resolution_status or "").strip().lower() != "confirmed":
        return False
    if not (verified_product_code or "").strip():
        return False
    if (matched_by or "").strip() in PROVISIONAL_SAMPLE_MATCHED_BY:
        return False
    return True


@dataclass(frozen=True, slots=True)
class MyWegDemandProjectionLine:
    """Linha interna pronta para a Etapa 2 — não é o DTO público de Demanda."""

    id: str
    source: str
    branch: str
    customer_code: str
    customer_store: str
    customer_name: str
    display_order: str
    product_code: str | None
    due_date: date
    open_quantity: Decimal
    quantity_mi: Decimal
    batch_id: str
    record_id: str
    collected_at: str | None
    resolution_status: str
    identity_kind: str
    matched_by: str | None
    coverage_eligible: bool
    material_weg_tratado: str | None
    codigo_referencia_weg: str | None
    line_no: int | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "branch": self.branch,
            "customer_code": self.customer_code,
            "customer_store": self.customer_store,
            "customer_name": self.customer_name,
            "display_order": self.display_order,
            "product_code": self.product_code,
            "due_date": self.due_date.isoformat(),
            "open_quantity": decimal_to_canonical_str(self.open_quantity),
            "quantity_mi": decimal_to_canonical_str(self.quantity_mi),
            "batch_id": self.batch_id,
            "record_id": self.record_id,
            "collected_at": self.collected_at,
            "resolution_status": self.resolution_status,
            "identity_kind": self.identity_kind,
            "matched_by": self.matched_by,
            "coverage_eligible": self.coverage_eligible,
            "material_weg_tratado": self.material_weg_tratado,
            "codigo_referencia_weg": self.codigo_referencia_weg,
            "line_no": self.line_no,
        }


def build_line_id(*, batch_id: str, record_id: str) -> str:
    """Identificador interno estável — nunca usa o texto «MyWEG» como chave."""
    return f"{LINE_ID_PREFIX}:{batch_id}:{record_id}"


def project_myweg_demand_lines(
    rows: Sequence[Mapping[str, Any]],
    *,
    batch_id: str,
    collected_at: Any = None,
    branch: str = DEMAND_SOURCE_BRANCH,
) -> list[MyWegDemandProjectionLine]:
    """Projeta registros de uma coleta aceita em linhas internas de Demanda.

    - Uma linha por ``record_id`` (rastreabilidade).
    - Quantidade canônica = ``quantidade_original_un`` (não ``quantidade_mi``).
    - Datas de remessa preservadas; linhas sem remessa são omitidas.
    - Registros sem identidade confiável permanecem com ``coverage_eligible=False``.
    """
    collected = _iso_dt(collected_at)
    branch_code = str(branch or DEMAND_SOURCE_BRANCH).strip() or DEMAND_SOURCE_BRANCH
    lines: list[MyWegDemandProjectionLine] = []

    for row in rows:
        remessa = _parse_date(row.get("data_remessa"))
        if remessa is None:
            continue
        record_id = str(row.get("id") or "").strip()
        if not record_id:
            continue

        sb1 = row.get("sb1_resolution") if isinstance(row.get("sb1_resolution"), Mapping) else {}
        product_key, identity_kind, verified = resolve_product_identity(row)
        _ = product_key  # identidade reutilizada; chave de linha é o record_id
        status = str((sb1 or {}).get("status") or row.get("sb1_status") or "pending").strip()
        matched_by_raw = (sb1 or {}).get("matched_by")
        matched_by = str(matched_by_raw).strip() if matched_by_raw is not None else None
        if matched_by == "":
            matched_by = None

        eligible = is_coverage_eligible(
            identity_kind=identity_kind,
            resolution_status=status,
            matched_by=matched_by,
            verified_product_code=verified,
        )
        # Elegível ou vínculo provisório de amostra: expõe o código verificado.
        # Pendente/ambíguo/divergente: sem product_code cobrável.
        if verified and (eligible or identity_kind == "verified_code"):
            product_code = verified
        else:
            product_code = None

        line_no_raw = row.get("line_no")
        try:
            line_no = int(line_no_raw) if line_no_raw is not None else None
        except (TypeError, ValueError):
            line_no = None

        lines.append(
            MyWegDemandProjectionLine(
                id=build_line_id(batch_id=batch_id, record_id=record_id),
                source=SOURCE_MYWEG,
                branch=branch_code,
                customer_code=WEG_LINHARES_CUSTOMER_CODE,
                customer_store=WEG_LINHARES_CUSTOMER_STORE,
                customer_name=WEG_LINHARES_CUSTOMER_NAME,
                display_order=DISPLAY_ORDER_MYWEG,
                product_code=product_code,
                due_date=remessa,
                open_quantity=_dec(row.get("quantidade_original_un")),
                quantity_mi=_dec(row.get("quantidade_mi")),
                batch_id=batch_id,
                record_id=record_id,
                collected_at=collected,
                resolution_status=status.lower() or "pending",
                identity_kind=identity_kind,
                matched_by=matched_by,
                coverage_eligible=eligible,
                material_weg_tratado=str(row.get("material_weg_tratado") or "").strip() or None,
                codigo_referencia_weg=str(row.get("codigo_referencia_weg") or "").strip() or None,
                line_no=line_no,
            )
        )

    lines.sort(
        key=lambda item: (
            item.due_date,
            item.product_code or "",
            item.line_no if item.line_no is not None else 10**9,
            item.record_id,
        )
    )
    return lines


def summarize_projection(lines: Sequence[MyWegDemandProjectionLine]) -> dict[str, Any]:
    """Contagens para diagnóstico da Etapa 1 / gate da Etapa 2."""
    eligible = [line for line in lines if line.coverage_eligible]
    provisional = [
        line
        for line in lines
        if (line.matched_by or "") in PROVISIONAL_SAMPLE_MATCHED_BY
    ]
    unresolved = [line for line in lines if line.identity_kind == "unresolved"]
    by_ref = [line for line in lines if line.identity_kind == "customer_reference"]
    return {
        "line_count": len(lines),
        "coverage_eligible_count": len(eligible),
        "provisional_sample_count": len(provisional),
        "unresolved_identity_count": len(unresolved),
        "customer_reference_count": len(by_ref),
        "open_quantity_un": decimal_to_canonical_str(
            sum((line.open_quantity for line in lines), ZERO)
        ),
        "coverage_open_quantity_un": decimal_to_canonical_str(
            sum((line.open_quantity for line in eligible), ZERO)
        ),
        "product_count_eligible": len(
            {line.product_code for line in eligible if line.product_code}
        ),
    }
