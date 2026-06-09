import pytest

from app.domain.services.chat_drawing_intent_service import ChatDrawingIntentService

_EXPLICIT_POSITIVE = [
    "Analise o desenho técnico 90260140",
    "Validar PDF do desenho 90264130",
    "Gerar relatório de conformidade DELPI 90260140",
    "Emitir relatório de conformidade do desenho 90260140",
    "Auditar desenho técnico 90260140",
    "Validar conformidade do desenho 90260140",
    "Comparar PDF com Protheus 90260140",
    "Liberar desenho para produção 90260140",
    "Reanalisar desenho 90260140",
    "Montar relatório técnico do desenho 90260140",
    "Conferir carimbo e tabela de materiais 90260140",
    "Validar roteiro do desenho 90260140",
]

_PDF_VOCABULARY_POSITIVE = [
    ("conferir bom do pdf anexado", ["att-1"]),
    ("validar carimbo do desenho em pdf", ["att-1"]),
    ("checklist de conformidade no arquivo anexado do desenho", ["att-1"]),
    ("conferir decapes deste pdf", ["att-1"]),
    ("validar folha técnica do pdf técnico", ["att-1"]),
]

_NEGATIVE = [
    "estoque do produto 10080047",
    "informações completas do produto 10080055",
    "qual a descrição do produto 10080047",
    "saldo disponível do item",
]

_REQUIRES_PDF = [
    "validar cotas do desenho",
    "gerar relatório de conformidade delpi",
    "checklist de conformidade do desenho",
    "conferir carimbo do desenho",
]


@pytest.mark.parametrize("message", _EXPLICIT_POSITIVE)
def test_explicit_drawing_triggers(message: str):
    assert ChatDrawingIntentService.is_drawing_analysis_request(message)


@pytest.mark.parametrize("message,attachment_ids", _PDF_VOCABULARY_POSITIVE)
def test_pdf_vocabulary_with_attachment(message: str, attachment_ids: list[str]):
    assert ChatDrawingIntentService.is_drawing_analysis_request(
        message,
        attachment_ids=attachment_ids,
    )


@pytest.mark.parametrize("message", _NEGATIVE)
def test_non_drawing_messages(message: str):
    assert not ChatDrawingIntentService.is_drawing_analysis_request(message)


@pytest.mark.parametrize("message", _REQUIRES_PDF)
def test_requires_pdf_without_attachment(message: str):
    assert ChatDrawingIntentService.requires_pdf_for_full_analysis(
        message,
        attachment_ids=None,
    )


def test_requires_pdf_satisfied_with_attachment():
    assert not ChatDrawingIntentService.requires_pdf_for_full_analysis(
        "validar cotas do desenho",
        attachment_ids=["att-1"],
    )
