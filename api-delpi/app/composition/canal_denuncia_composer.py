from __future__ import annotations

from app.application.use_cases.canal_denuncia.create_anonymous_denuncia_use_case import (
    CreateAnonymousDenunciaUseCase,
)
from app.config import settings
from app.infrastructure.persistence.plugins.repositories.canal_denuncia.postgres_canal_denuncia_repository import (
    PostgresCanalDenunciaRepository,
)
from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    MicrosoftGraphMailClient,
)


def build_canal_denuncia_repository() -> PostgresCanalDenunciaRepository:
    return PostgresCanalDenunciaRepository()


def build_microsoft_graph_mail_client() -> MicrosoftGraphMailClient:
    return MicrosoftGraphMailClient(
        tenant_id=settings.GRAPH_TENANT_ID,
        client_id=settings.GRAPH_CLIENT_ID,
        client_secret=settings.GRAPH_CLIENT_SECRET,
        sender=settings.GRAPH_MAIL_SENDER,
        recipient=settings.GRAPH_MAIL_RECIPIENT,
        timeout_seconds=float(settings.GRAPH_HTTP_TIMEOUT_SECONDS or "15"),
    )


def build_create_anonymous_denuncia_use_case() -> CreateAnonymousDenunciaUseCase:
    return CreateAnonymousDenunciaUseCase(
        build_canal_denuncia_repository(),
        build_microsoft_graph_mail_client(),
    )
