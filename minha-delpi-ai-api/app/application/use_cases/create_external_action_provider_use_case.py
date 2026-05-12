from app.domain.services.external_actions.external_provider_url_policy import (
    ExternalProviderUrlPolicy,
)


class CreateExternalActionProviderUseCase:
    def __init__(self, repository, url_policy: ExternalProviderUrlPolicy):
        self.repository = repository
        self.url_policy = url_policy

    def execute(self, payload: dict) -> dict:
        provider_key = str(payload.get("providerKey") or "").strip()
        name = str(payload.get("name") or "").strip()
        provider_type = str(payload.get("type") or "").strip()
        base_url = str(payload.get("baseUrl") or "").strip()
        openapi_url = str(payload.get("openApiUrl") or "").strip()

        if not provider_key:
            raise ValueError("providerKey is required")

        if not name:
            raise ValueError("name is required")

        if provider_type not in {"internal", "external"}:
            raise ValueError("type must be internal or external")

        if not base_url:
            raise ValueError("baseUrl is required")

        self.url_policy.validate(base_url, provider_type)

        if openapi_url:
            self.url_policy.validate(openapi_url, provider_type)

        payload = {
            **payload,
            "providerKey": provider_key,
            "name": name,
            "type": provider_type,
            "baseUrl": base_url,
            "openApiUrl": openapi_url or None,
        }

        return self.repository.create_provider(payload)
