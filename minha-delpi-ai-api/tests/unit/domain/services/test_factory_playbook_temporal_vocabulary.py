"""Regressão: variações PT-BR de período no playbook fabril (F1–F5)."""

from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pytest

from app.application.services.external_actions.external_action_selection_service import (
    ExternalActionSelectionService,
)
from app.domain.services.chat_date_range_intent_service import ChatDateRangeIntentService
from app.domain.services.chat_operational_date_parameter_service import (
    ChatOperationalDateParameterService,
)
from app.domain.services.chat_operational_parameter_service import (
    ChatOperationalParameterService,
)
from app.domain.services.chat_temporal_intent_service import ChatTemporalIntentService
from tests.unit.application.services.test_external_action_selection_service import (
    FakeRepository,
)

_REFERENCE = date(2026, 6, 9)
_PRODUCT = "90269002"

_FACTORY_ACTION = {
    "actionId": "factory-status",
    "method": "GET",
    "path": "/products/{code}/factory-status",
    "operationId": "get_product_factory_status",
    "summary": "Status fabril",
    "parametersSchema": [
        {"name": "code"},
        {"name": "reference_date"},
        {"name": "date_start"},
        {"name": "date_end"},
    ],
}


def _factory_repo() -> ExternalActionSelectionService:
    return ExternalActionSelectionService(FakeRepository([_FACTORY_ACTION]))


@pytest.mark.parametrize(
    ("message", "reference_date", "date_start", "date_end"),
    [
        pytest.param(
            f"status fabril do produto {_PRODUCT} hoje",
            "09-06-2026",
            "09-06-2026",
            "09-06-2026",
            id="hoje",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} hj",
            "09-06-2026",
            "09-06-2026",
            "09-06-2026",
            id="hj",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} agora",
            "09-06-2026",
            "09-06-2026",
            "09-06-2026",
            id="agora",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} dia atual",
            "09-06-2026",
            "09-06-2026",
            "09-06-2026",
            id="dia-atual",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} ontem",
            "08-06-2026",
            "08-06-2026",
            "08-06-2026",
            id="ontem",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} essa semana",
            "08-06-2026",
            "08-06-2026",
            "14-06-2026",
            id="essa-semana",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} esta semana",
            "08-06-2026",
            "08-06-2026",
            "14-06-2026",
            id="esta-semana",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} nessa semana",
            "08-06-2026",
            "08-06-2026",
            "14-06-2026",
            id="nessa-semana",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} nesta semana",
            "08-06-2026",
            "08-06-2026",
            "14-06-2026",
            id="nesta-semana",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} semana passada",
            "01-06-2026",
            "01-06-2026",
            "07-06-2026",
            id="semana-passada",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} na semana passada",
            "01-06-2026",
            "01-06-2026",
            "07-06-2026",
            id="na-semana-passada",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} semana retrasada",
            "01-06-2026",
            "01-06-2026",
            "07-06-2026",
            id="semana-retrasada",
        ),
        pytest.param(
            f"status fabril do produto {_PRODUCT} em 01/06/2026",
            "01-06-2026",
            "01-06-2026",
            "01-06-2026",
            id="data-explicita",
        ),
        pytest.param(
            f"qual o status completo na fabrica do produto {_PRODUCT} hoje",
            "09-06-2026",
            "09-06-2026",
            "09-06-2026",
            id="frase-longa-hoje",
        ),
    ],
)
def test_factory_status_selects_action_with_period_variations(
    message: str,
    reference_date: str,
    date_start: str,
    date_end: str,
):
    service = _factory_repo()

    with patch("app.domain.services.chat_date_range_intent_service.date") as mock_date:
        mock_date.today.return_value = _REFERENCE

        selected = service.select_action_for_product(
            message,
            product_code=_PRODUCT,
            allowed_action_ids=["factory-status"],
            previous_messages=None,
        )

    assert selected is not None
    params = selected["arguments"]["parameters"]
    assert params["reference_date"] == reference_date
    assert params["date_start"] == date_start
    assert params["date_end"] == date_end


@pytest.mark.parametrize(
    "message",
    [
        pytest.param(f"status fabril do produto {_PRODUCT} hoje", id="hoje"),
        pytest.param(f"status fabril do produto {_PRODUCT} essa semana", id="essa-semana"),
        pytest.param(f"status fabril do produto {_PRODUCT} semana passada", id="semana-passada"),
        pytest.param(f"situacao de producao do {_PRODUCT} hoje", id="producao-hoje"),
        pytest.param(
            f"inspecao final expedicao produto {_PRODUCT} essa semana",
            id="expedicao-essa-semana",
        ),
        pytest.param(
            f"inspecao final expedicao produto {_PRODUCT} esse mes",
            id="expedicao-esse-mes",
        ),
    ],
)
def test_playbook_routes_do_not_request_missing_date_when_period_present(message: str):
    answer = ChatOperationalParameterService.resolve_missing_date_answer(message)

    assert answer is None


@pytest.mark.parametrize(
    "message",
    [
        pytest.param(f"status fabril do produto {_PRODUCT}", id="factory-sem-data"),
        pytest.param(
            f"qual o status completo na fabrica do produto {_PRODUCT}?",
            id="factory-frase-longa-sem-data",
        ),
        pytest.param(f"situacao de producao do {_PRODUCT}", id="producao-sem-data"),
    ],
)
def test_playbook_routes_still_request_date_when_period_absent(message: str):
    answer = ChatOperationalParameterService.resolve_missing_date_answer(message)

    assert answer is not None
    assert "data" in answer.lower() or "periodo" in answer.lower() or "período" in answer.lower()


@pytest.mark.parametrize(
    ("phrase", "start_date", "end_date"),
    [
        pytest.param("esse mes", "01-06-2026", "30-06-2026", id="esse-mes"),
        pytest.param("nesse mes", "01-06-2026", "30-06-2026", id="nesse-mes"),
        pytest.param("este mes", "01-06-2026", "30-06-2026", id="este-mes"),
        pytest.param("mes passado", "01-05-2026", "31-05-2026", id="mes-passado"),
        pytest.param("mes que vem", "01-07-2026", "31-07-2026", id="mes-que-vem"),
        pytest.param("esse ano", "01-01-2026", "31-12-2026", id="esse-ano"),
        pytest.param("nesse ano", "01-01-2026", "31-12-2026", id="nesse-ano"),
        pytest.param("ano passado", "01-01-2025", "31-12-2025", id="ano-passado"),
        pytest.param("esse trimestre", "01-04-2026", "30-06-2026", id="esse-trimestre"),
        pytest.param("trimestre passado", "01-01-2026", "31-03-2026", id="trimestre-passado"),
        pytest.param("na semana que vem", "15-06-2026", "21-06-2026", id="na-semana-que-vem"),
    ],
)
def test_temporal_phrase_variations_resolve_date_range(
    phrase: str,
    start_date: str,
    end_date: str,
):
    resolved = ChatDateRangeIntentService.resolve(
        f"cpv do {phrase}",
        today=_REFERENCE,
    )

    assert resolved is not None
    assert resolved.start_date == start_date
    assert resolved.end_date == end_date


@pytest.mark.parametrize(
    "phrase",
    [
        "essa semana",
        "esse mes",
        "nesse mes",
        "esse ano",
        "semana retrasada",
        "agora",
        "nessa data",
    ],
)
def test_has_temporal_reference_detects_vocabulary_variations(phrase: str):
    assert ChatTemporalIntentService.has_temporal_reference(f"status fabril {phrase}")
    assert ChatOperationalDateParameterService.has_temporal_reference(
        f"status fabril do produto {_PRODUCT} {phrase}"
    )
