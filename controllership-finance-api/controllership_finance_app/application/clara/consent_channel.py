"""CLARA consent channel policy (CF-UX-053).

Runtime default remains Portal step-up (V014 / R-CLARA-01). The
conversational TÉO-shaped contract (proposal presentation +
``confirmation=true`` on ACT) is implemented behind an explicit
channel setting and a separate security acknowledgement so production
cannot silently weaken the human-proof guarantee.
"""

from __future__ import annotations

from controllership_finance_app.config import settings

CHANNEL_PORTAL = "portal"
CHANNEL_CONVERSATIONAL = "conversational"
CHANNEL_DUAL = "dual"

# Must be set verbatim by Security/Platform after formal acceptance of
# TÉO-equivalent residual risk for CONFIRMATION_REQUIRED capabilities.
SECURITY_ACK_VALUE = "R-CLARA-01-TEO-EQUIVALENCE-ACCEPTED"

CONSENT_TYPE_MCP_CONFIRMATION = "mcp_tool_confirmation"


def consent_channel() -> str:
    raw = str(settings.CLARA_CONSENT_CHANNEL or CHANNEL_PORTAL).strip().lower()
    if raw in {CHANNEL_PORTAL, CHANNEL_CONVERSATIONAL, CHANNEL_DUAL}:
        return raw
    return CHANNEL_PORTAL


def conversational_security_ack_present() -> bool:
    return (
        str(settings.CLARA_CONVERSATIONAL_SECURITY_ACK or "").strip()
        == SECURITY_ACK_VALUE
    )


def conversational_act_enabled() -> bool:
    """True only when channel opts in AND security ack is present.

    Without the ack, conversational/dual never bypass Portal V014.
    """
    channel = consent_channel()
    if channel not in {CHANNEL_CONVERSATIONAL, CHANNEL_DUAL}:
        return False
    return conversational_security_ack_present()


def portal_consent_required() -> bool:
    """Portal V014 remains mandatory unless conversational ACT is armed."""
    if consent_channel() == CHANNEL_CONVERSATIONAL and conversational_act_enabled():
        return False
    return True


def prepare_status() -> str:
    return "proposal_pending_confirmation"


def confirmation_instruction_for_prepare() -> str:
    channel = consent_channel()
    conversational_ready = conversational_act_enabled()
    if channel == CHANNEL_CONVERSATIONAL and conversational_ready:
        return (
            "Apresente a operação exata ao usuário (quem, recurso, "
            "competência, versão, efeito, riscos, reversibilidade) e "
            "aguarde confirmação explícita e específica no ChatGPT. "
            "Somente então chame phase=commit com o proposal_handle "
            "(ou proposal_id) e confirmation=true. "
            "confirmation=true não substitui a autorização efetiva do "
            "Core — o backend revalida permissões, escopo, OCC, "
            "idempotência e read-back no ACT. "
            "Atenção: este canal conversacional está armado com "
            "acknowledgement de Segurança; a prova humana não é o "
            "step-up Portal V014."
        )
    if channel == CHANNEL_DUAL and conversational_ready:
        return (
            "Apresente a operação selada na conversa e peça confirmação "
            "explícita. Em seguida chame phase=commit com "
            "confirmation=true. Enquanto o dual permanecer com Portal "
            "obrigatório para prova V014, o usuário também deve "
            "aprovar em confirmation_url quando o canal conversacional "
            "não estiver autorizado a substituir o step-up."
        )
    # Default / portal / conversational without ack: V014 mandatory.
    return (
        "Apresente a operação exata ao usuário (quem, recurso, "
        "competência, versão, efeito, motivo, riscos) no ChatGPT. "
        "A confirmação textual sozinha NÃO autoriza a execução. "
        "Direcione o usuário à confirmation_url no Portal "
        "Controladoria & Finanças para consentimento verificável "
        "(step-up V014). Depois chame phase=commit com o "
        "proposal_handle exato. Opcionalmente envie confirmation=true "
        "na segunda chamada (padrão TÉO de contrato); sem consentimento "
        "Portal o ACT continua rejeitado. A confirmação não substitui "
        "a autorização efetiva — o backend revalida tudo no ACT."
    )


def phase_policy_for_capability(*, direct: bool) -> str:
    """Schema/catalog phase_policy aligned with the active consent channel.

    Hardcoding «Portal consent» while the contract is TÉO-shaped caused
    ChatGPT to keep instructing an external page even after the MCP
    tools already expose ``confirmation``. This helper keeps CURRENT
    and TARGET honest in ``get_context(topic=schema)``.
    """
    if direct:
        return (
            "phase=direct (default) executa já com AuthZ + "
            "idempotência; phase=prepare → phase=commit também é "
            "aceito"
        )
    if conversational_act_enabled() and not portal_consent_required():
        return (
            "phase=prepare → proposal_pending_confirmation (apresente "
            "a alteração selada) → após confirmação explícita do "
            "usuário phase=commit com proposal_handle + "
            "confirmation=true; AuthZ Core + OCC + read-back no ACT; "
            "sem página Portal obrigatória (canal conversacional "
            "armado)"
        )
    return (
        "phase=prepare → proposal_pending_confirmation (apresente a "
        "alteração selada) → confirmation_url Portal step-up V014 → "
        "phase=commit com proposal_handle (confirmation=true é sinal "
        "TÉO de contrato, não substitui V014 enquanto "
        "portal_consent_required=true); AuthZ Core + OCC + read-back"
    )


def batch_consent_instruction() -> str:
    if conversational_act_enabled() and not portal_consent_required():
        return (
            "Apresente UMA confirmação consolidada ao usuário listando "
            "ator, competência, objetos, operações, motivos, efeitos e "
            "dependências. Após confirmação explícita chame "
            "batch.phase=confirm (ou commit) com batch_handle, "
            "plan_hash e confirmation=true. confirmation=true não "
            "substitui AuthZ efetiva — o backend revalida por operação."
        )
    return (
        "Apresente UMA confirmação consolidada ao usuário listando "
        "ator, competência, objetos, operações, motivos, efeitos e "
        "dependências — nunca uma confirmação por operação. Direcione "
        "o usuário à confirmation_url no Portal Controladoria & "
        "Finanças para consentir o plano inteiro: responder 'sim' no "
        "chat NÃO autoriza a execução — o consentimento é gravado "
        "pela página do Portal com credencial fresca que esta "
        "conversa não consegue produzir. O plano selado não pode ser "
        "ampliado. confirmation=true no MCP é sinal TÉO e, sem canal "
        "conversacional armado, não substitui V014."
    )
