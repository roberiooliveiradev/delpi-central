import hashlib
import json
from datetime import datetime, timezone

import requests

from app.domain.ports.external_action_repository_port import ExternalActionRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.external_action_model import ExternalActionModel
from app.infrastructure.db.models.external_action_provider_model import (
    ExternalActionProviderModel,
)
from app.infrastructure.db.models.external_action_schema_model import (
    ExternalActionSchemaModel,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.external_actions.openapi_action_importer import (
    OpenApiActionImporter,
)


class PostgresExternalActionRepository(ExternalActionRepositoryPort):
    def __init__(self, embedding_service=None):
        self.embedding_service = embedding_service
    def create_provider(self, payload: dict) -> dict:
        provider = ExternalActionProviderModel(
            provider_key=payload["providerKey"],
            name=payload["name"],
            provider_type=payload["type"],
            base_url=payload["baseUrl"].rstrip("/"),
            openapi_url=(payload.get("openApiUrl") or "").strip() or None,
            privacy_policy_url=(payload.get("privacyPolicyUrl") or "").strip() or None,
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

    def update_provider(self, provider_key: str, payload: dict) -> dict | None:
        provider = self.get_provider_by_key(provider_key)

        if not provider:
            return None

        if "name" in payload and payload.get("name"):
            provider.name = str(payload.get("name")).strip()

        if "baseUrl" in payload and payload.get("baseUrl"):
            provider.base_url = str(payload.get("baseUrl")).strip().rstrip("/")

        if "openApiUrl" in payload:
            value = str(payload.get("openApiUrl") or "").strip()
            provider.openapi_url = value or None

        if "privacyPolicyUrl" in payload:
            value = str(payload.get("privacyPolicyUrl") or "").strip()
            provider.privacy_policy_url = value or None

        if "authMode" in payload:
            provider.auth_mode = str(payload.get("authMode") or "none").strip() or "none"

        if "authConfig" in payload:
            provider.auth_config = payload.get("authConfig") or {}

        if "enabled" in payload and payload.get("enabled") is not None:
            provider.enabled = bool(payload.get("enabled"))

        db.session.flush()

        return self._provider_to_dict(provider)

    def get_provider_details(self, provider_key: str) -> dict | None:
        provider = self.get_provider_by_key(provider_key)

        if not provider:
            return None

        latest_schema = (
            ExternalActionSchemaModel.query
            .filter(ExternalActionSchemaModel.provider_id == provider.id)
            .order_by(ExternalActionSchemaModel.imported_at.desc())
            .first()
        )

        data = self._provider_to_dict(provider)
        data["authConfig"] = provider.auth_config or {}
        data["latestSchema"] = latest_schema.schema_json if latest_schema else None
        data["latestSchemaHash"] = latest_schema.schema_hash if latest_schema else None
        data["latestSchemaImportedAt"] = (
            latest_schema.imported_at.isoformat() if latest_schema else None
        )

        return data

    def import_schema_from_json(
        self,
        provider_key: str,
        schema_json: dict,
        source_type: str,
        source_url: str | None = None,
        *,
        embed_on_import: bool | None = None,
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

        from app.infrastructure.config.chat_intelligence_runtime_reader import (
            read_resolved_chat_intelligence,
        )
        from app.infrastructure.persistence.postgres_admin_runtime_settings_repository import (
            PostgresAdminRuntimeSettingsRepository,
        )

        if embed_on_import is None:
            intelligence = read_resolved_chat_intelligence(
                PostgresAdminRuntimeSettingsRepository()
            )
            embed_on_import = intelligence.external_action_embedding_on_import

        for action in actions:
            embedding = None

            if self.embedding_service and embed_on_import:
                embedding = self.embedding_service.embed_action(
                    {
                        "actionId": action["action_id"],
                        "method": action["method"],
                        "path": action["path"],
                        "summary": action.get("summary"),
                        "description": action.get("description"),
                        "operationId": action.get("operation_id"),
                        "tags": action.get("tags"),
                    }
                )

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
                    embedding=embedding,
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

    def import_schema_from_url(
        self,
        provider_key: str,
        timeout: int = 20,
        *,
        embed_on_import: bool | None = None,
    ) -> dict:
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
            embed_on_import=embed_on_import,
        )



    def find_candidate_actions(
        self,
        query: str,
        limit: int = 8,
        *,
        allowed_action_ids: list[str] | None = None,
    ) -> list[dict]:
        normalized = str(query or "").lower()
        allowed_ids = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        db_query = ExternalActionModel.query.join(ExternalActionProviderModel).filter(
            ExternalActionModel.enabled.is_(True),
            ExternalActionProviderModel.enabled.is_(True),
        )

        if allowed_ids:
            db_query = db_query.filter(ExternalActionModel.action_id.in_(allowed_ids))

        is_supplies_kpi = any(
            term in normalized
            for term in ["giro de estoque", "giro do estoque", "valor de estoque", "valor total de estoque", "idd"]
        )

        if is_supplies_kpi:
            db_query = db_query.filter(
                db.or_(
                    ExternalActionModel.path.ilike("%supplies%"),
                    ExternalActionModel.summary.ilike("%supri%"),
                    ExternalActionModel.operation_id.ilike("%supplies%"),
                    ExternalActionModel.operation_id.ilike("%inventory%"),
                )
            )
        elif any(
            term in normalized
            for term in [
                "produto",
                "product",
                "item",
                "código",
                "codigo",
                "estoque",
                "stock",
                "venda",
                "vendas",
                "descrição",
                "descricao",
                "busque",
                "buscar",
                "pesquise",
                "procure",
                "traga",
                "search",
                "exemplos",
                "estrutura",
                "composição",
                "composicao",
                "componentes",
                "bom",
                "roteiro",
                "pai do",
                "pais do",
                "onde é usado",
                "onde e usado",
                "where used",
                "fornecedor",
                "compra",
                "preço",
                "preco",
                "quanto custa",
                "custo",
                "movimentação",
                "movimentacao",
                "inspeção",
                "inspecao",
                "nota de entrada",
                "nota de saída",
                "notas de entrada",
                "notas de saída",
                "diretiva",
                "diretivas",
                "directive",
                "directives",
            ]
        ):
            db_query = db_query.filter(
                db.or_(
                    ExternalActionModel.path.ilike("%products%"),
                    ExternalActionModel.path.ilike("%produto%"),
                    ExternalActionModel.summary.ilike("%product%"),
                    ExternalActionModel.summary.ilike("%produto%"),
                    ExternalActionModel.description.ilike("%product%"),
                    ExternalActionModel.description.ilike("%produto%"),
                )
            )
        elif any(
            term in normalized
            for term in ["lmp", "lmps", "amostra", " ov ", "ordens de venda", "pedidos de venda"]
        ):
            db_query = db_query.filter(
                db.or_(
                    ExternalActionModel.path.ilike("%lmp%"),
                    ExternalActionModel.summary.ilike("%lmp%"),
                    ExternalActionModel.description.ilike("%lmp%"),
                    ExternalActionModel.path.ilike("%sales%"),
                    ExternalActionModel.summary.ilike("%venda%"),
                    ExternalActionModel.operation_id.ilike("%sale_order%"),
                )
            )
        elif any(
            term in normalized
            for term in [
                "cpv", "otd", "giro", "suprimento", "supplies",
                "valor de estoque", "valor total", "inventory",
            ]
        ):
            db_query = db_query.filter(
                db.or_(
                    ExternalActionModel.path.ilike("%supplies%"),
                    ExternalActionModel.summary.ilike("%supri%"),
                    ExternalActionModel.operation_id.ilike("%supplies%"),
                    ExternalActionModel.operation_id.ilike("%inventory%"),
                )
            )
        elif any(
            term in normalized
            for term in ["ordens de venda", "pedidos de venda", "listar ov", "vendas do período"]
        ):
            db_query = db_query.filter(
                db.or_(
                    ExternalActionModel.path.ilike("%/sales%"),
                    ExternalActionModel.operation_id.ilike("%sale_orders%"),
                )
            )
        elif any(term in normalized for term in ["sql", "data", "dados", "query", "select "]):
            db_query = db_query.filter(
                db.or_(
                    ExternalActionModel.path.ilike("%sql%"),
                    ExternalActionModel.path.ilike("%data%"),
                    ExternalActionModel.summary.ilike("%sql%"),
                    ExternalActionModel.summary.ilike("%data%"),
                    ExternalActionModel.description.ilike("%sql%"),
                    ExternalActionModel.description.ilike("%data%"),
                    ExternalActionModel.operation_id.ilike("%sql%"),
                    ExternalActionModel.operation_id.ilike("%data%"),
                )
            )
        elif not allowed_ids:
            return []

        actions = db_query.order_by(
            ExternalActionModel.method.asc(),
            ExternalActionModel.path.asc(),
        ).limit(limit).all()

        return [self._action_to_dict(action) for action in actions]

    def search_similar_actions(
        self,
        embedding: list[float],
        *,
        allowed_action_ids: list[str] | None = None,
        limit: int = 20,
    ) -> list[dict]:
        allowed_ids = [str(item).strip() for item in (allowed_action_ids or []) if str(item).strip()]

        query = (
            db.session.query(
                ExternalActionModel,
                ExternalActionModel.embedding.cosine_distance(embedding).label("distance"),
            )
            .join(ExternalActionProviderModel)
            .filter(
                ExternalActionModel.enabled.is_(True),
                ExternalActionProviderModel.enabled.is_(True),
                ExternalActionModel.embedding.isnot(None),
            )
        )

        if allowed_ids:
            query = query.filter(ExternalActionModel.action_id.in_(allowed_ids))

        rows = (
            query.order_by(ExternalActionModel.embedding.cosine_distance(embedding))
            .limit(max(1, limit))
            .all()
        )

        result: list[dict] = []

        for action, distance in rows:
            item = self._action_to_dict(action)
            item["selectionScore"] = round(float(1 - distance), 4) if distance is not None else None
            result.append(item)

        return result

    def backfill_action_embeddings(
        self,
        *,
        provider_key: str | None = None,
        on_progress=None,
        commit_batch_size: int = 0,
    ) -> dict:
        if not self.embedding_service:
            return {"updated": 0, "skipped": 0, "total": 0}

        query = ExternalActionModel.query.join(ExternalActionProviderModel).filter(
            ExternalActionModel.enabled.is_(True),
            ExternalActionProviderModel.enabled.is_(True),
            ExternalActionModel.embedding.is_(None),
        )

        if provider_key:
            query = query.filter(ExternalActionProviderModel.provider_key == provider_key)

        actions = query.all()
        updated = 0
        skipped = 0
        total = len(actions)
        batch_size = max(0, int(commit_batch_size or 0))

        for index, action in enumerate(actions, start=1):
            embedding = self.embedding_service.embed_action(self._action_to_dict(action))

            if embedding:
                action.embedding = embedding
                updated += 1
            else:
                skipped += 1

            if on_progress:
                on_progress(index, total)

            if batch_size and index % batch_size == 0:
                db.session.flush()

        db.session.flush()

        return {
            "updated": updated,
            "skipped": skipped,
            "total": total,
        }

    def get_action_for_execution(self, action_id: str) -> dict | None:
        action = ExternalActionModel.query.filter(
            ExternalActionModel.action_id == action_id
        ).first()

        if not action:
            return None

        provider = ExternalActionProviderModel.query.filter(
            ExternalActionProviderModel.id == action.provider_id
        ).first()

        if not provider:
            return None

        return {
            "provider": self._provider_to_dict_with_auth(provider),
            "action": self._action_to_dict(action),
        }

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


    def _provider_to_dict_with_auth(self, provider: ExternalActionProviderModel) -> dict:
        data = self._provider_to_dict(provider)
        data["authConfig"] = provider.auth_config or {}
        data["timeoutSeconds"] = 30
        return data

    def _safe_isoformat(self, value) -> str | None:
        return value.isoformat() if value else None

    def _provider_to_dict(self, provider: ExternalActionProviderModel) -> dict:
        return {
            "id": str(provider.id),
            "providerKey": provider.provider_key,
            "name": provider.name,
            "type": provider.provider_type,
            "baseUrl": provider.base_url,
            "openApiUrl": provider.openapi_url,
            "privacyPolicyUrl": provider.privacy_policy_url,
            "authMode": provider.auth_mode,
            "enabled": provider.enabled,
            "createdAt": self._safe_isoformat(provider.created_at),
            "updatedAt": self._safe_isoformat(provider.updated_at),
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
