from __future__ import annotations

from fastapi import APIRouter, Query

from tm_app.application.integrations.engineering_transforma_mais import (
    EngineeringProcessFilters,
    EngineeringTransformaMaisService,
)
from tm_app.core.responses import ok

router = APIRouter(
    prefix="/transformometro/integrations/engineering/transforma-mais",
    tags=["Transformômetro Integrações"],
)


@router.get("/processes",
    operation_id="integration_list_processes")
def integration_list_processes(
    id: str | None = Query(default=None),
    name_process: str | None = Query(default=None),
    filial_id: str | None = Query(default=None),
    sector_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
):
    data = EngineeringTransformaMaisService().list_processes(
        EngineeringProcessFilters(
            id=id,
            name_process=name_process,
            filial_id=filial_id,
            sector_name=sector_name,
            status=status,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
    )
    return ok(data, "Processos (contrato engenharia).")


@router.get("/processes/summary",
    operation_id="integration_process_summary")
def integration_process_summary(
    filial_id: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    data = EngineeringTransformaMaisService().get_summary(
        filial_id=filial_id,
        start_date=start_date,
        end_date=end_date,
    )
    return ok(data, "Resumo (contrato engenharia).")
