"""Matriz R01–R15 — superfície honesta de evidências (B-δ, docs 93/104).

O que esta rota É: agregação derivada do snapshot da competência —
quantos itens do checklist referenciam cada R-ID e seu estado de
validação — somada ao catálogo canônico de fonte/owner do processo.

O que NÃO é: relatório oficial, export do ERP ou comprovação de
paridade. `OPERATIONAL_VIEW` marca as consultas auxiliares já
implementadas (R01/R02 baixas SE5, R03 estoque SB9/SB1, R05
movimentações, R08 material em processo) — auxiliares, não oficiais.
`official_parity` separa a implementação da homologação oficial:
toda consulta implementada permanece `PENDING` até validação contra
o relatório oficial do Protheus. R-IDs sem contrato/owner confirmado
permanecem `PENDING_CONTRACT` — captura manual de evidência pelo
fluxo P2.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query, Request

from controllership_finance_app.core.responses import fail, ok
from controllership_finance_app.domain.closing_checklist.errors import (
    ChecklistDomainError,
)
from controllership_finance_app.domain.closing_documents.resource_scope import (
    normalize_request_scope,
    scope_in_context,
)
from controllership_finance_app.infrastructure.persistence.closing_checklist_repository import (
    ClosingChecklistRepository,
)
from controllership_finance_app.interface.http.authz import authorized_user

router = APIRouter(
    prefix="/closing/competences", tags=["Closing Reports Matrix"]
)

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

# Catálogo canônico R01–R15 (doc 93): fonte real do processo e postura
# do Portal. `PENDING_CONTRACT` = owner/contrato não confirmados — não
# inventar automação; o fluxo manual autorizado é a evidência P2.
REPORT_CATALOG: tuple[dict, ...] = (
    {
        "report_id": "R01",
        "label": "Baixas a pagar (SE5)",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SE5",
        "operational_view": "financial-settlements",
        "official_parity": "PENDING",
        "note": "Consulta auxiliar operacional — não é relatório oficial.",
    },
    {
        "report_id": "R02",
        "label": "Baixas a receber (SE5)",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SE5",
        "operational_view": "financial-settlements",
        "official_parity": "PENDING",
        "note": "Consulta auxiliar operacional — não é relatório oficial.",
    },
    {
        "report_id": "R03",
        "label": "Posição de estoque (SB9/SB1)",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SB9",
        "operational_view": "stock-inventory",
        "official_parity": "PENDING",
        "note": "Snapshot operacional — não é o MATR460/P7 oficial.",
    },
    {
        "report_id": "R04",
        "label": "Consumo por OP",
        "source_kind": "PENDING_CONTRACT",
        "owner": None,
        "operational_view": None,
        "official_parity": None,
        "note": "Fonte/owner não confirmados — captura manual governada.",
    },
    {
        "report_id": "R05",
        "label": "Entradas/Saídas",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SD1-SD4",
        "operational_view": "stock-movements",
        "official_parity": "PENDING",
        "note": "Consulta operacional — não substitui o MATR320 oficial.",
    },
    {
        "report_id": "R06",
        "label": "CPV / Kardex",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SD1-SD2-SD3",
        "operational_view": "stock-kardex",
        "official_parity": "PENDING",
        "note": "Consulta operacional do motor MATR910 + CPV gerencial (SD2) — não substitui o MATR910 oficial.",
    },
    {
        "report_id": "R07",
        "label": "Inventários / Kardex99",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SD3-INVENT",
        "operational_view": "inventory-adjustments",
        "official_parity": "PENDING",
        "note": "Ajustes de inventário (D3_DOC='INVENT') do motor MATR910 — não substitui a emissão oficial.",
    },
    {
        "report_id": "R08",
        "label": "Posição H02",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SD3-SC2",
        "operational_view": "work-in-process",
        "official_parity": "PENDING",
        "note": "Consulta operacional — não substitui o MATR989 oficial. Alimenta a conciliação P3.",
    },
    {
        "report_id": "R09",
        "label": "Faturamento × MOD",
        "source_kind": "PENDING_CONTRACT",
        "owner": None,
        "operational_view": None,
        "official_parity": None,
        "note": "Fonte/owner não confirmados — captura manual governada.",
    },
    {
        "report_id": "R10",
        "label": "Despesas por centro de custo",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SD1-SB1-CTT",
        "operational_view": "cost-center-expenses",
        "official_parity": "PENDING",
        "note": "Consulta operacional da seleção histórica SD1/D1_DTDIGIT com universo investigativo separado — não substitui o relatório oficial. Achados são possíveis divergências, nunca erro confirmado.",
    },
    {
        "report_id": "R11",
        "label": "NF a desconsiderar",
        "source_kind": "OPERATIONAL_VIEW",
        "owner": "TOTVS/SD2-SF4-SB1",
        "operational_view": "billing-exclusion-roster",
        "official_parity": "PENDING",
        "note": "Lista investigativa da seleção histórica SD2/D2_EMISSAO (grupo 9035 ∩ TES 594 observado) — nenhuma nota é excluída automaticamente de CPV, faturamento ou DRE. Achados são possíveis divergências, nunca erro confirmado.",
    },
    {
        "report_id": "R12",
        "label": "Wizard de fechamento",
        "source_kind": "PENDING_CONTRACT",
        "owner": None,
        "operational_view": None,
        "official_parity": None,
        "note": "Fonte/owner não confirmados — captura manual governada.",
    },
    {
        "report_id": "R13",
        "label": "Extratos bancários e aplicações",
        "source_kind": "EXTERNAL",
        "owner": "Instituições financeiras",
        "operational_view": None,
        "official_parity": None,
        "note": "Origem externa — evidência anexada e validada (P2).",
    },
    {
        "report_id": "R14",
        "label": "Importações, câmbio e SWIFT/ACSI",
        "source_kind": "EXTERNAL",
        "owner": "Instituições financeiras",
        "operational_view": None,
        "official_parity": None,
        "note": "Origem externa — evidência anexada e validada (P2).",
    },
    {
        "report_id": "R15",
        "label": "Cutoff / SB9 final",
        "source_kind": "PENDING_CONTRACT",
        "owner": None,
        "operational_view": None,
        "official_parity": None,
        "note": "Vinculado ao cutoff P3 — owner do fechamento no ERP.",
    },
)

_ITEM_ACCEPTED_STATES = frozenset({"ACCEPTED", "NOT_APPLICABLE"})
_ITEM_TERMINAL_STATES = frozenset(
    {"ACCEPTED", "NOT_APPLICABLE", "CANCELLED"}
)


def _domain_fail(exc: ChecklistDomainError, operation_id: str):
    return fail(
        exc.message,
        exc.status,
        data={"error": {"code": exc.code}},
        operation_id=operation_id,
    )


@router.get(
    "/{period}/reports",
    operation_id="list_report_matrix",
)
def list_report_matrix(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    branch_scope: str | None = Query(
        default=None, pattern="^(MATRIX|BRANCH|BOTH)$"
    ),
):
    """Matriz R01–R15 derivada do snapshot da competência — nunca
    promove consulta auxiliar a relatório oficial."""
    authorized_user(request)
    try:
        ctx = normalize_request_scope(branch_scope)
        items = ClosingChecklistRepository().list_competence_items(
            period
        )
        items = [
            item
            for item in items
            if scope_in_context(
                request_scope=ctx,
                document_scope=item.get("branch_scope"),
            )
        ]
        by_report: dict[str, list[dict]] = {}
        for item in items:
            ref = item.get("totvs_report_ref")
            if ref:
                by_report.setdefault(ref, []).append(item)

        matrix = []
        for entry in REPORT_CATALOG:
            linked = by_report.get(entry["report_id"], [])
            total = len(linked)
            accepted = sum(
                1
                for i in linked
                if i["state"] in _ITEM_ACCEPTED_STATES
            )
            terminal = sum(
                1
                for i in linked
                if i["state"] in _ITEM_TERMINAL_STATES
            )
            pending = total - terminal
            matrix.append(
                {
                    **entry,
                    "checklist_items": total,
                    "items_validated": accepted,
                    "items_terminal": terminal,
                    "items_pending": pending,
                    "coverage": (
                        "validated"
                        if total and pending == 0
                        else "partial"
                        if accepted
                        else "pending"
                    ),
                }
            )
        return ok(
            {"period": period, "reports": matrix},
            operation_id="list_report_matrix",
        )
    except ChecklistDomainError as exc:
        return _domain_fail(exc, "list_report_matrix")
