from app.config import settings

from app.application.use_cases.transforma_mais.list_process_use_case import (
    ListProcessUseCase,
)
from app.application.use_cases.transforma_mais.get_process_summary_use_case import (
    GetProcessSummaryUseCase,
)
from app.domain.services.transforma_mais.process_summary_calculator import (
    ProcessSummaryCalculator,
)
from app.infrastructure.persistence.google_sheets.transforma_mais.process_repository import (
    ProcessRepository,
)
from app.infrastructure.persistence.google_sheets.transforma_mais.sheet_sources import (
    TransformaMaisSources,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import (
    GoogleSheetsClient,
)


def _build_sources() -> TransformaMaisSources:
    return TransformaMaisSources(
        sheet_id=settings.TRANSFORMA_MAIS_SHEET_ID,
        tabs={
            "processos": settings.TRANSFORMA_MAIS_GID_PROCESSOS,
            "revisao": settings.TRANSFORMA_MAIS_GID_REVISAO,
            "medicoes": settings.TRANSFORMA_MAIS_GID_MEDICOES,
            "investimentos": settings.TRANSFORMA_MAIS_GID_INVESTIMENTOS,
            "recursos_compartilhados": settings.TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS,
            "revisao_recursos_compartilhados": settings.TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS,
        },
    )


def _build_repository() -> ProcessRepository:
    client = GoogleSheetsClient(timeout=int(settings.GOOGLE_SHEETS_TIMEOUT))
    sources = _build_sources()

    return ProcessRepository(
        client=client,
        sources=sources,
    )


def _build_calculator() -> ProcessSummaryCalculator:
    return ProcessSummaryCalculator()


def transforma_mais_list_process_composer() -> ListProcessUseCase:
    return ListProcessUseCase(
        repository=_build_repository(),
        calculator=_build_calculator(),
    )


def transforma_mais_get_process_summary_composer() -> GetProcessSummaryUseCase:
    return GetProcessSummaryUseCase(
        repository=_build_repository(),
        calculator=_build_calculator(),
    )