from dataclasses import dataclass


@dataclass(frozen=True)
class SendChatMessageRequest:
    user_id: str
    session_id: str
    message: str
    context: str | None = None
    access_token: str | None = None
    attachment_ids: list[str] | None = None
    resend_from_message_id: str | None = None
    agent_id: str | None = None
    project_id: str | None = None
    # True quando o payload trouxe projectId (permite limpar projeto com null explícito).
    sync_project_binding: bool = False
    # common | agent — modo explícito do MFE (chat comum limpa agent_id legado na sessão).
    chat_mode: str | None = None
    # Modo de resposta: fast | normal | thinker (ver ChatResponseModeService).
    response_mode: str | None = None
    # Expor adminDebug na resposta/SSE (rotas definem via permissão). Persistência é sempre.
    admin_debug: bool = False
