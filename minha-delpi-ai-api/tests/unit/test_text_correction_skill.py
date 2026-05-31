"""Regressão — correção de texto (playbook C1–C12, subset automatizado)."""

from app.domain.services.chat_email_intent_service import ChatEmailIntentService
from app.domain.services.chat_text_correction_intent_service import (
    ChatTextCorrectionIntentService,
)
from app.domain.services.chat_text_correction_quality_validator import (
    ChatTextCorrectionQualityValidator,
)
from app.domain.services.chat_text_task_intent_service import ChatTextTaskIntentService


def _assert_pure_correction(msg: str) -> None:
    assert ChatTextTaskIntentService.is_pure_text_task(msg) is True
    assert ChatEmailIntentService.is_email_writing(msg) is False
    assert ChatTextCorrectionIntentService.is_text_correction(msg) is True


def test_c1_spelling():
    _assert_pure_correction("corrija: o estoque esta baixo")
    assert (
        ChatTextCorrectionIntentService.classify_subtype(
            "corrija: o estoque esta baixo",
        )
        == "text_correct_basic"
    )


def test_c2_agreement_extract():
    ctx = ChatTextCorrectionIntentService.extract_context(
        "corrija: os item foi enviado ontem",
    )
    assert "item" in (ctx.get("sourceText") or "")


def test_c4_preserve_product_code():
    msg = "corrija: o produto 10080001 esta com divergencia na BOM"
    ctx = ChatTextCorrectionIntentService.extract_context(msg)
    assert "10080001" in (ctx.get("preservedCodes") or [])
    good = "Segue a versão corrigida:\n\nO produto 10080001 está com divergência na BOM."
    assert ChatTextCorrectionQualityValidator.validate(good, user_message=msg)["passed"]


def test_c6_final_only_preference():
    msg = "daqui para frente entregue só a versão final quando eu pedir correção"
    ctx = ChatTextCorrectionIntentService.extract_context(msg)
    assert ctx.get("deliverFinalOnly") is True


def test_c7_explain_subtype():
    assert (
        ChatTextCorrectionIntentService.classify_subtype(
            "corrija e explique: nos vai enviar o pedido amanhã",
        )
        == "text_correct_explain"
    )


def test_c8_compare_subtype():
    assert (
        ChatTextCorrectionIntentService.classify_subtype(
            "corrija e mostre antes e depois deste texto",
        )
        == "text_correct_compare"
    )


def test_c9_formal_subtype():
    assert (
        ChatTextCorrectionIntentService.classify_subtype(
            "corrija e deixe mais formal: preciso que envie isso",
        )
        == "text_correct_formal"
    )


def test_c10_preserve_style():
    assert (
        ChatTextCorrectionIntentService.classify_subtype(
            "corrija sem mudar meu estilo: Robério, segue os arquivo",
        )
        == "text_correct_preserve_style"
    )


def test_c11_technical_terms_flag():
    ctx = ChatTextCorrectionIntentService.extract_context(
        "corrija: divergencia na BOM do produto 10080001",
    )
    assert ctx.get("containsTechnicalTerms") is True


def test_c12_not_email_correction():
    msg = "corrija este e-mail: segue texto"
    assert ChatEmailIntentService.is_email_writing(msg) is True
    assert ChatTextCorrectionIntentService.is_text_correction(msg) is False


def test_metadata_type_correction():
    meta = ChatTextCorrectionIntentService.build_text_task_metadata(
        message="corrija: texto com erro",
    )
    assert meta is not None
    assert meta["textTask"]["type"] == "correction"


def test_validator_flags_missing_code():
    msg = "corrija: produto 10080001 com erro"
    bad = "Segue a versão corrigida:\n\nO produto 10080099 com erro."
    result = ChatTextCorrectionQualityValidator.validate(bad, user_message=msg)
    assert result["passed"] is False
    assert any(item["code"] == "code_altered" for item in result["checks"])
