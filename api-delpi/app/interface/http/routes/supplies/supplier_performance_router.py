from fastapi import APIRouter, Query
from pydantic import ValidationError
from delpi_auth.authorization import require_auth

from app.composition.supplier_performance_composer import (
    build_supplier_performance_use_case,
)
from app.composition.supplier_performance_export_composer import (
    build_supplier_performance_export_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.query_param_enums import BRANCH_CODES_QUERY
from app.interface.http.schemas.supplier_performance_schema import (
    SupplierPerformancePayload,
    SupplierPerformanceResponse,
    SupplierPerformanceExportPayload,
    SupplierPerformanceExportResponse,
)
from app.interface.http.supplies_bff_service_access import is_trusted_supplies_bff_call
from app.utils.logger import log_error

router = APIRouter(prefix="/supplies", tags=["Supplies — supplier performance"])


@router.get(
    "/supplier-performance",
    operation_id="get_supplies_supplier_performance",
    response_model=SupplierPerformanceResponse,
)
@require_auth()
def get_supplies_supplier_performance(
    branch: list[str] = BRANCH_CODES_QUERY(),
    date_from: str = Query(...),
    date_to: str = Query(...),
):
    """IDF 70/30; private to the trusted supplies BFF, which enforces user access."""
    if not is_trusted_supplies_bff_call():
        return error_response("Acesso negado.", status_code=403)
    try:
        result = build_supplier_performance_use_case().execute(
            branches=branch or [],
            date_from=date_from,
            date_to=date_to,
        )
        # Validate before JSONResponse (FastAPI cannot validate an already-built Response).
        result = SupplierPerformancePayload.model_validate(result).model_dump(
            by_alias=True
        )
        return api_delpi_success(
            result, operation_id="get_supplies_supplier_performance"
        )
    except ValidationError:
        log_error("IDF: contrato da fonte inválido.")
        return error_response(
            "Não foi possível validar a base do IDF.", status_code=502
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError:
        log_error("IDF: base TOTVS indisponível.")
        return error_response("Base TOTVS indisponível.", status_code=503)
    except Exception:
        log_error("IDF: falha ao consultar o indicador.")
        return error_response("Não foi possível consultar o IDF.", status_code=500)


@router.get(
    "/supplier-performance/evidence-export",
    operation_id="export_supplies_supplier_performance_evidence",
    response_model=SupplierPerformanceExportResponse,
)
@require_auth()
def export_supplies_supplier_performance_evidence(
    branch: list[str] = BRANCH_CODES_QUERY(),
    date_from: str = Query(...),
    date_to: str = Query(...),
    supplier_code: str | None = Query(default=None, max_length=12),
    supplier_store: str | None = Query(default=None, max_length=4),
):
    """Bounded evidence for XLSX; BFF-only, read-only, never raw SQL to clients."""
    if not is_trusted_supplies_bff_call():
        return error_response("Acesso negado.", status_code=403)
    try:
        result = build_supplier_performance_export_use_case().execute(
            branches=branch or [],
            date_from=date_from, date_to=date_to,
            supplier_code=supplier_code, supplier_store=supplier_store,
        )
        result = SupplierPerformanceExportPayload.model_validate(result).model_dump(
            by_alias=True
        )
        return api_delpi_success(
            result, operation_id="export_supplies_supplier_performance_evidence"
        )
    except ValidationError:
        log_error("IDF export: contrato da fonte inválido.")
        return error_response("Não foi possível validar a base da exportação.", status_code=502)
    except ValueError as exc:
        return error_response(str(exc), status_code=422)
    except DatabaseConnectionError:
        log_error("IDF export: base TOTVS indisponível.")
        return error_response("Base TOTVS indisponível.", status_code=503)
    except Exception:
        log_error("IDF export: falha ao consultar evidências.")
        return error_response("Não foi possível gerar a exportação do IDF.", status_code=500)
