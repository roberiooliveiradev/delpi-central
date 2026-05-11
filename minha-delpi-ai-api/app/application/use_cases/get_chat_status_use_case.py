from app.domain.entities.authenticated_user import AuthenticatedUser


class GetChatStatusUseCase:
    def execute(self, user: AuthenticatedUser) -> dict:
        return {
            "status": "ok",
            "service": "minha-delpi-ai-api",
            "module": "minha-delpi-chat",
            "authenticated": True,
            "user": {
                "sub": user.sub,
                "email": user.email,
                "name": user.name,
            },
        }
