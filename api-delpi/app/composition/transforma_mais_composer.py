# app/composition/transforma_mais_composer.py

import os

from app.application.use_cases.transforma_mais.list_process_use_case import ListProcessUseCase
from app.application.use_cases.transforma_mais.get_process_summary_use_case import GetProcessSummaryUseCase
from app.domain.services.transforma_mais.process_summary_calculator import ProcessSummaryCalculator
from app.infrastructure.persistence.google_sheets.transforma_mais.process_repository import ProcessRepository
from app.infrastructure.persistence.google_sheets.transforma_mais.sheet_sources import (
    TransformaMaisSources,
)
from app.infrastructure.providers.google_sheets.google_sheets_client import GoogleSheetsClient


DEFAULT_TRANSFORMA_MAIS_SHEET_ID = "193G5ff5qmkhQPBwgDuW-DTGo_IBwluTBo4cNHfyzGgQ"
DEFAULT_GOOGLE_SHEETS_TIMEOUT = 10

DEFAULT_TRANSFORMA_MAIS_GID_PROCESSOS = "0"
DEFAULT_TRANSFORMA_MAIS_GID_REVISAO = "1384756454"
DEFAULT_TRANSFORMA_MAIS_GID_MEDICOES = "1495163132"
DEFAULT_TRANSFORMA_MAIS_GID_INVESTIMENTOS = "592789663"
DEFAULT_TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS = "1501701990"
DEFAULT_TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS = "1661621038"


def _build_sources() -> TransformaMaisSources:
    sheet_id = os.getenv("TRANSFORMA_MAIS_SHEET_ID", DEFAULT_TRANSFORMA_MAIS_SHEET_ID)

    return TransformaMaisSources(
        sheet_id=sheet_id,
        tabs={
            "processos": os.getenv(
                "TRANSFORMA_MAIS_GID_PROCESSOS",
                DEFAULT_TRANSFORMA_MAIS_GID_PROCESSOS,
            ),
            "revisao": os.getenv(
                "TRANSFORMA_MAIS_GID_REVISAO",
                DEFAULT_TRANSFORMA_MAIS_GID_REVISAO,
            ),
            "medicoes": os.getenv(
                "TRANSFORMA_MAIS_GID_MEDICOES",
                DEFAULT_TRANSFORMA_MAIS_GID_MEDICOES,
            ),
            "investimentos": os.getenv(
                "TRANSFORMA_MAIS_GID_INVESTIMENTOS",
                DEFAULT_TRANSFORMA_MAIS_GID_INVESTIMENTOS,
            ),
            "recursos_compartilhados": os.getenv(
                "TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS",
                DEFAULT_TRANSFORMA_MAIS_GID_RECURSOS_COMPARTILHADOS,
            ),
            "revisao_recursos_compartilhados": os.getenv(
                "TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS",
                DEFAULT_TRANSFORMA_MAIS_GID_REVISAO_RECURSOS_COMPARTILHADOS,
            ),
        },
    )


def _build_repository() -> ProcessRepository:
    timeout = int(os.getenv("GOOGLE_SHEETS_TIMEOUT", str(DEFAULT_GOOGLE_SHEETS_TIMEOUT)))

    client = GoogleSheetsClient(timeout=timeout)
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