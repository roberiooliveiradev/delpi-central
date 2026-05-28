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
    agent_key: str | None = None
    # Expor adminDebug na resposta/SSE (rotas definem via permissão). Persistência é sempre.
    admin_debug: bool = False
