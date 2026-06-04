from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard


def test_blocks_secret():
    verdict = ChatLearningSafetyGuard.inspect("minha senha é 12345", candidate_type="term_definition")
    assert verdict["allowed"] is False
    assert verdict["reason"] == "secret_detected"


def test_blocks_token_like():
    verdict = ChatLearningSafetyGuard.inspect("o token é sk-abcdef0123456789", candidate_type="vocabulary")
    assert verdict["allowed"] is False


def test_blocks_pii_cpf():
    verdict = ChatLearningSafetyGuard.inspect("cliente 123.456.789-09", candidate_type="term_definition")
    assert verdict["allowed"] is False
    assert verdict["reason"] in {"pii_detected", "operational_sensitive"}


def test_blocks_operational_code_for_vocabulary():
    verdict = ChatLearningSafetyGuard.inspect("estoque do 10080001", candidate_type="normalization_rule")
    assert verdict["allowed"] is False
    assert verdict["reason"] == "operational_code"


def test_blocks_price():
    verdict = ChatLearningSafetyGuard.inspect("o preço do item", candidate_type="term_definition")
    assert verdict["allowed"] is False
    assert verdict["reason"] == "operational_sensitive"


def test_allows_safe_term():
    verdict = ChatLearningSafetyGuard.inspect("modulo de engenharia", candidate_type="term_definition")
    assert verdict["allowed"] is True
    assert verdict["riskLevel"] == "low"


def test_allows_safe_typo():
    assert ChatLearningSafetyGuard.is_safe_to_learn("como vc s chama", candidate_type="normalization_rule")
