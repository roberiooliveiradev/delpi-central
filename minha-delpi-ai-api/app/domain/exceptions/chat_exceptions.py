class ChatSessionNotFoundError(Exception):
    code = "chat.session_not_found"
    message = "Chat session not found"


class ChatSessionAccessDeniedError(Exception):
    code = "chat.session_access_denied"
    message = "Chat session access denied"


class ChatMessageNotFoundError(Exception):
    code = "chat.message_not_found"

    def __init__(self, message: str = "Mensagem não encontrada."):
        self.message = message
        super().__init__(message)


class InvalidChatSessionInputError(Exception):
    code = "chat.invalid_session_input"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
