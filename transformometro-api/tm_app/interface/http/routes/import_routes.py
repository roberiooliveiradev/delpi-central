from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from tm_app.application.services.sheet_import_service import SheetImportService
from tm_app.core.responses import fail, ok

router = APIRouter(prefix="/transformometro", tags=["Transformômetro Import"])


class ImportApplyBody(BaseModel):
    replace_existing: bool = False
    recalc_dashboard: bool = True
    csv_dir: str | None = Field(
        default=None,
        description="Caminho absoluto no servidor com CSVs exportados (opcional).",
    )


@router.get("/import/preview")
def import_preview(csv_dir: str | None = Query(default=None)):
    try:
        data = SheetImportService().preview(
            csv_dir=Path(csv_dir) if csv_dir else None,
        )
        return ok(data, "Pré-visualização da importação.")
    except Exception as exc:
        return fail(str(exc), 400)


@router.post("/import/apply")
def import_apply(body: ImportApplyBody):
    try:
        data = SheetImportService().apply(
            csv_dir=Path(body.csv_dir) if body.csv_dir else None,
            replace_existing=body.replace_existing,
            recalc_dashboard=body.recalc_dashboard,
        )
        return ok(data, "Importação concluída.")
    except ValueError as exc:
        return fail(str(exc), 400)
    except Exception as exc:
        return fail(str(exc), 500)
