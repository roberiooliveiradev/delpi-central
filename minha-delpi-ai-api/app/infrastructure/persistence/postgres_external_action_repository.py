import hashlib
import json
from datetime import datetime, timezone

import requests

from app.extensions.db import db
from app.infrastructure.db.models.external_action_model import ExternalActionModel
from app.infrastructure.db.models.external_action_provider_model import (
    ExternalActionProviderModel,
)
from app.infrastructure.db.models.external_action_schema_model import (
    ExternalActionSchemaModel,
)
from app.infrastructure.external_actions.openapi_action_importer import (
    OpenApiActionImporter,
)


class PostgresExternalActionRepository:
    def create_provider(self, payload: dict) -> dict:
        provider = ExternalActionProviderModel(
            provider_key=payload["providerKey"],
            name=payload["name"],
            provider_type=payload["type"],
            base_url=payload["baseUrl"].rstrip("/"),
            openapi_url=(payload.get("openApiUrl") or "").strip() or None,
            auth_mode=payload.get("authMode") or "none",
            auth_config=payload.get("authConfig"),
            enabled=bool(payload.get("enabled", True)),
        )

        db.session.add(provider)
        db.session.flush()

        return self._provider_to_dict(provider)

    def list_providers(self) -> list[dict]:
        providers = (
            ExternalActionProviderModel.query
            .order_by(ExternalActionProviderModel.created_at.desc())
            .all()
        )

        return [self._provider_to_dict(provider) for provider in providers]

    def get_provider_by_key(self, provider_key: str):
        return ExternalActionProviderModel.query.filter(
            ExternalActionProviderModel.provider_key == provider_key
        ).first()

    def import_schema_from_json(
        self,
        provider_key: str,
        schema_json: dict,
        source_type: str,
        source_url: str | None = None,
    ) -> dict:
        provider = self.get_provider_by_key(provider_key)

        if not provider:
            return {"found": False}

        schema_hash = self._hash_schema(schema_json)

        schema = ExternalActionSchemaModel(
            provider_id=provider.id,
            schema_json=schema_json,
            schema_hash=schema_hash,
            source_type=source_type,
            source_url=source_url,
            imported_at=datetime.now(timezone.utc),
        )

        db.session.add(schema)

        ExternalActionModel.query.filter(
            ExternalActionModel.provider_id == provider.id
        ).delete()

        importer = OpenApiActionImporter()
        actions = importer.import_actions(provider.provider_key, schema_json)

        for action in actions:
            db.session.add(
                ExternalActionModel(
                    provider_id=provider.id,
                    action_id=action["action_id"],
                    operation_id=action["operation_id"],
                    method=action["method"],
                    path=action["path"],
                    summary=action.get("summary"),
                    description=action.get("description"),
                    tags=action.get("tags"),
                    parameters_schema=action.get("parameters_schema"),
                    request_body_schema=action.get("request_body_schema"),
                    response_schema=action.get("response_schema"),
                    sensitivity=action.get("sensitivity") or "read",
                    enabled=bool(action.get("enabled", True)),
                    deprecated=bool(action.get("deprecated", False)),
                )
            )

        db.session.flush()

        return {
            "found": True,
            "provider": self._provider_to_dict(provider),
            "schemaHash": schema_hash,
            "actionsImported": len(actions),
        }

    def import_schema_from_url(self, provider_key: str, timeout: int = 20) -> dict:
        provider = self.get_provider_by_key(provider_key)

        if not provider:
            return {"found": False}

        if not provider.openapi_url:
            raise ValueError("openApiUrl is required")

        response = requests.get(provider.openapi_url, timeout=timeout)
        response.raise_for_status()

        schema_json = response.json()

        return self.import_schema_from_json(
            provider_key=provider_key,
            schema_json=schema_json,
            source_type="url",
            source_url=provider.openapi_url,
        )

    def list_actions(self, provider_key: str | None = None) -> list[dict]:
        query = ExternalActionModel.query.join(ExternalActionProviderModel)

        if provider_key:
            query = query.filter(ExternalActionProviderModel.provider_key == provider_key)

        actions = query.order_by(
            ExternalActionProviderModel.provider_key.asc(),
            ExternalActionModel.path.asc(),
            ExternalActionModel.method.asc(),
        ).all()

        return [self._action_to_dict(action) for action in actions]

    def _hash_schema(self, schema_json: dict) -> str:
        raw = json.dumps(schema_json, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _provider_to_dict(self, provider: ExternalActionProviderModel) -> dict:
        return {
            "id": str(provider.id),
            "providerKey": provider.provider_key,
            "name": provider.name,
            "type": provider.provider_type,
            "baseUrl": provider.base_url,
            "openApiUrl": provider.openapi_url,
            "authMode": provider.auth_mode,
            "enabled": provider.enabled,
            "createdAt": provider.created_at.isoformat(),
            "updatedAt": provider.updated_at.isoformat(),
        }

    def _action_to_dict(self, action: ExternalActionModel) -> dict:
        return {
            "id": str(action.id),
            "actionId": action.action_id,
            "operationId": action.operation_id,
            "method": action.method,
            "path": action.path,
            "summary": action.summary,
            "description": action.description,
            "tags": action.tags or [],
            "parametersSchema": action.parameters_schema or [],
            "requestBodySchema": action.request_body_schema,
            "responseSchema": action.response_schema,
            "sensitivity": action.sensitivity,
            "enabled": action.enabled,
            "deprecated": action.deprecated,
        }
