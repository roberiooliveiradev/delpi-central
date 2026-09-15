from pathlib import Path


DOC = Path(__file__).resolve().parents[1] / "docs" / "gpt-actions" / "specialist-instructions.md"
BUILDER_HARD_LIMIT = 8000
PROJECT_TARGET_LIMIT = 7000


def _builder_instructions_block() -> str:
    text = DOC.read_text(encoding="utf-8")
    heading = "## Instructions (colar no GPT Builder)"
    start = text.index("```text\n", text.index(heading)) + len("```text\n")
    end = text.index("\n```", start)
    return text[start:end]


def test_teo_builder_instructions_fit_character_budget():
    block = _builder_instructions_block()
    assert len(block) <= PROJECT_TARGET_LIMIT
    assert len(block) < BUILDER_HARD_LIMIT


def test_teo_builder_core_keeps_required_invariants():
    block = _builder_instructions_block()
    required = [
        "INFERRED != FACT",
        "Search miss != proof of absence",
        "AS_IS != CURRENT_COMPOSED != TO_BE",
        "TÉO capability <= authenticated user capability",
        "PREPARE EXACT CHANGE",
        "EXPLICIT CONFIRMATION",
        "AUTHORITATIVE READ-BACK",
        "surface_supports = suporte, não autorização",
        "OUTCOME_VERIFICATION_FAILED",
        "teo-method-playbooks.md",
    ]
    for marker in required:
        assert marker in block


def test_teo_builder_user_facing_language_is_portuguese_first():
    block = _builder_instructions_block()
    required = [
        "## Linguagem com o usuário",
        "na conversa use português claro",
        "OBSERVED/INFORMED → Informado/Observado",
        "INFERRED → Hipótese",
        "PROPOSED → Proposto",
        "UNKNOWN → Ainda não sabemos",
        "AS-IS → processo atual",
        "TO-BE → processo futuro proposto",
        "E2E → processo ponta a ponta",
        "Evite AuthZ, surface_supports, write, read-back, runtime, instance_id",
        "explique em português na primeira ocorrência",
        "Não altere nomes técnicos ao chamar Actions",
    ]
    for marker in required:
        assert marker in block


def test_teo_persistence_outcome_states_are_distinct():
    """CASO 1–3/6: validated/confirmed/attempted/persisted/verified are not equivalent."""
    block = _builder_instructions_block()
    for marker in [
        "VALIDATED",
        "CONFIRMED",
        "COMMIT_ATTEMPTED",
        "COMMIT_CONFIRMED",
        "PERSISTED",
        "VERIFIED",
        "ready=true != saved",
        "confirmation != authorization",
        "commit attempted != persisted",
        "2xx != verified",
        "VALIDATE != WRITE",
    ]:
        assert marker in block


def test_teo_validate_ready_does_not_authorize_saved_claims():
    """CASO 1: ready=true may say validated/ready — never saved/gravado/cadastrado/ativo."""
    block = _builder_instructions_block()
    assert "gpt_validate_improvement_package" in block
    assert "ready=true != saved/gravado/cadastrado/ativo" in block or (
        "ready=true != saved" in block and "gravado" in block and "cadastrado" in block
    )


def test_teo_confirmation_is_not_authorization():
    """CASO 2: user 'sim' is confirmation, not AuthZ; backend remains authority."""
    block = _builder_instructions_block()
    assert "Confirmação conversacional != AuthZ" in block
    assert "backend continua autoridade" in block
    assert "confirmation != authorization" in block


def test_teo_inconclusive_commit_must_remain_unknown():
    """CASO 3: consequential Action unavailable → UNKNOWN, never claim saved."""
    block = _builder_instructions_block()
    assert "COMMIT_ATTEMPTED" in block
    assert "UNKNOWN" in block
    assert "unavailable" in block or "disabled" in block
    assert "não afirme salvo" in block.lower()
    # Must not teach that attempt alone is success.
    assert "cadastro concluído" not in block.lower()


def test_teo_no_dangerous_fallback_after_commit_failure():
    """CASO 4: no curl/HTTP bypass/silent CRUD substitute/retry loop."""
    block = _builder_instructions_block()
    assert "Sem curl" in block or "sem curl" in block.lower()
    assert "create/update_record" in block
    assert "bypass" in block.lower()
    assert (
        "retry em loop" in block.lower()
        or "retry-loop" in block.lower()
        or "no retry" in block.lower()
    )
    assert "gpt_call_any_route" in block


def test_teo_retry_same_package_requires_read_and_invalidates_on_change():
    """CASO 5: identical package may keep confirmation; change invalidates; read before retry."""
    block = _builder_instructions_block()
    assert "Antes de retry" in block or "antes de retry" in block.lower()
    assert "estado atual" in block.lower()
    assert "duplicidade" in block.lower() or "duplicate" in block.lower()
    assert (
        "confirmação anterior invalidada" in block.lower()
        or "confirmação anterior inválida" in block.lower()
    )


def test_teo_commit_2xx_still_requires_read_back_verify():
    """CASO 6–7: 2xx alone is not success; diverge → OUTCOME_VERIFICATION_FAILED."""
    block = _builder_instructions_block()
    assert "AUTHORITATIVE READ-BACK" in block
    assert "PERSISTED+VERIFIED" in block or ("PERSISTED" in block and "VERIFIED" in block)
    assert "2xx != verified" in block
    assert "OUTCOME_VERIFICATION_FAILED" in block


def test_teo_auth_errors_must_not_bypass_security():
    """CASO 8: 401 AuthN / 403 AuthZ — never reinterpret confirmation as permission."""
    block = _builder_instructions_block()
    assert "401=AuthN" in block
    assert "403=AuthZ" in block
    assert "confirmation != authorization" in block


def test_teo_entity_canonical_contract_precedes_generic_action():
    """Entity schema from catalog beats generic Action envelope guessing."""
    block = _builder_instructions_block()
    for marker in [
        "Contrato canônico da entidade",
        "entity_schemas",
        "Schema canônico da entidade > assinatura genérica",
        "Entidade específica > tool genérica",
        "shared_resource",
        "data.conteudo",
        "nome_recurso",
        "tipo_custo",
        "recorrencia",
        "Erro de validação",
        "não persistiu parcial",
        "Contrato incerto",
    ]:
        assert marker in block, marker


def test_teo_playbook_documents_canonical_write_contract():
    playbook = (
        Path(__file__).resolve().parents[1]
        / "docs"
        / "gpt-actions"
        / "teo-method-playbooks.md"
    ).read_text(encoding="utf-8")
    assert "Canonical entity contract before any write" in playbook
    assert "shared_resource" in playbook
    assert "data.conteudo" in playbook
    assert "resource_link" in playbook


def test_teo_must_read_action_error_message_not_only_http_code():
    block = _builder_instructions_block()
    assert "message" in block and "data.errors" in block
    assert "error_kind" in block
    assert "código HTTP" in block or "HTTP" in block
    assert "Nunca informe só o código HTTP" in block or "nunca informe só" in block.lower()
