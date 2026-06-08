from app.domain.ports.admin_system_check_repository_port import AdminSystemCheckRepositoryPort
from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.infrastructure.config.settings import Settings
from app.infrastructure.gateways.core_api_http_gateway import CoreApiHttpGateway


class GetAdminToolsHealthUseCase:
    def __init__(
        self,
        system_check_repository: AdminSystemCheckRepositoryPort,
        external_action_repository: ExternalActionRepositoryPort,
    ):
        self.system_check_repository = system_check_repository
        self.external_action_repository = external_action_repository

    def execute(self, *, access_token: str | None = None) -> dict:
        system = self.system_check_repository.check()
        items: list[dict] = []

        items.append(
            {
                "id": "database",
                "label": "Banco de dados",
                "status": self._map_status(system.get("database", {}).get("status")),
                "description": "Conectividade PostgreSQL do serviço.",
            }
        )
        items.append(
            {
                "id": "pgvector",
                "label": "Extensão pgvector",
                "status": self._map_status(system.get("pgvector", {}).get("status")),
                "description": "Extensão necessária para embeddings e RAG.",
            }
        )

        tables = system.get("tables") or {}
        missing = tables.get("missing") or []

        items.append(
            {
                "id": "schema-tables",
                "label": "Tabelas obrigatórias",
                "status": self._map_status(tables.get("status")),
                "description": (
                    "Todas as tabelas presentes."
                    if not missing
                    else f"Tabelas ausentes: {', '.join(missing)}"
                ),
            }
        )

        llm = system.get("llm") or {}
        items.append(
            {
                "id": "llm-provider",
                "label": f"LLM ({llm.get('provider', Settings.LLM_PROVIDER)})",
                "status": self._map_status(llm.get("status")),
                "description": llm.get("message")
                or (
                    f"Modelo de chat: {((llm.get('chatModel') or {}).get('name'))}"
                )
                or "Provedor configurado.",
            }
        )

        items.append(self._core_api_item(access_token))

        providers = self.external_action_repository.list_providers()
        actions = self.external_action_repository.list_actions()

        items.append(
            {
                "id": "external-actions-catalog",
                "label": "Catálogo de actions externas",
                "status": "ok" if actions else "warning",
                "description": (
                    f"{len(providers)} provider(s), {len(actions)} action(s) cadastrada(s)."
                ),
            }
        )

        for provider in providers[:12]:
            key = str(provider.get("key") or provider.get("providerKey") or "provider")
            enabled = provider.get("enabled", True)

            items.append(
                {
                    "id": f"provider-{key}",
                    "label": f"Provider {key}",
                    "status": "ok" if enabled else "warning",
                    "description": (
                        "Provider habilitado."
                        if enabled
                        else "Provider desabilitado no catálogo."
                    ),
                }
            )

        overall = "ok"
        statuses = {item["status"] for item in items}

        if "error" in statuses:
            overall = "error"
        elif "warning" in statuses:
            overall = "warning"

        return {
            "status": overall,
            "systemCheck": system,
            "items": items,
        }

    def _core_api_item(self, access_token: str | None) -> dict:
        if not access_token:
            return {
                "id": "core-api",
                "label": "Core API",
                "status": "unknown",
                "description": "Token ausente para validar integração com o core.",
            }

        try:
            CoreApiHttpGateway().get_me(access_token)
            return {
                "id": "core-api",
                "label": "Core API",
                "status": "ok",
                "description": "Autenticação e /me respondendo corretamente.",
            }
        except Exception as exc:
            return {
                "id": "core-api",
                "label": "Core API",
                "status": "error",
                "description": f"Falha ao consultar core: {exc.__class__.__name__}",
            }

    def _map_status(self, value: str | None) -> str:
        normalized = str(value or "unknown").lower()

        if normalized in {"ok", "warning", "error"}:
            return normalized

        return "unknown"
