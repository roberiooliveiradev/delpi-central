"""Central de Fechamento — governed cross-report comparison (doc 126).

``POST /closing/analysis/report-comparison`` — owner approved by D-03:
this BFF orchestrates the governed producer contracts (api-delpi)
through the same S2S + delegated-Bearer chain as the Portal report
routes. The BFF adds the ``controllership-finance.access`` gate and the
typed contract; authorization stays per-subject fail-closed at the
producer — a denied subject never contributes a value or an existence
signal to the comparison.

No SQL lives here; no financial formula is recomputed. The engine only
applies the comparative operations authorized by doc 126 §D4
(aggregation already owned by the producers, absolute delta, percentage
delta over a non-zero baseline).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field

from controllership_finance_app.application.report_comparison.compare_use_case import (
    ComparisonValidationError,
    ReportComparisonUseCase,
)
from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.interface.http.routes.closing_routes import (
    _authorized_user,
    _user_bearer,
)

logger = logging.getLogger("controllership-finance-api.analysis")

OPERATION_ID = "post_closing_analysis_report_comparison"

router = APIRouter(prefix="/closing", tags=["Closing"])


class ComparisonSubjectRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    report_id: str = Field(alias="reportId", min_length=1, max_length=16)
    period: str | None = Field(
        default=None,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
    )
    branch: str | None = Field(
        default=None, pattern="^(all|01|02)$"
    )
    filters: dict[str, Any] = Field(default_factory=dict)


class ReportComparisonRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    comparison_kind: str = Field(alias="comparisonKind")
    subjects: list[ComparisonSubjectRequest] = Field(
        min_length=2, max_length=6
    )
    measure: str | None = None
    grain: str | None = Field(default="total", max_length=32)
    baseline_index: int | None = Field(
        default=None, alias="baselineIndex", ge=0, le=5
    )
    diff_page: int | None = Field(
        default=None, alias="diffPage", ge=1
    )
    diff_page_size: int | None = Field(
        default=None, alias="diffPageSize", ge=1, le=500
    )


@router.post(
    "/analysis/report-comparison",
    operation_id=OPERATION_ID,
)
def post_closing_analysis_report_comparison(
    request: Request, body: ReportComparisonRequest
):
    """Comparação transversal governada de relatórios da Central de
    Fechamento.

    Compara apenas relatórios com contrato efetivamente implementado,
    classifica a compatibilidade semântica por par (COMPARABLE /
    RELATED_REQUIRES_EXPLANATION / NOT_COMPARABLE /
    INSUFFICIENT_EVIDENCE), aplica somente as normalizações autorizadas
    e retorna parciais honestos — um sujeito negado ou indisponível
    nunca vira zero implícito nem vaza existência.
    """
    _authorized_user(request)
    access_token = _user_bearer(request)

    payload = body.model_dump(by_alias=True)

    try:
        result = ReportComparisonUseCase().execute(
            payload, access_token=access_token
        )
    except ComparisonValidationError as exc:
        return fail(
            str(exc),
            400,
            data={"error": {"code": exc.code}},
            operation_id=OPERATION_ID,
        )
    return ok(
        result,
        message="Comparação executada.",
        operation_id=OPERATION_ID,
    )
