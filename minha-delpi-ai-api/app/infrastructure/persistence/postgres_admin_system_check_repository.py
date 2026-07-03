import requests

from sqlalchemy import text

from app.domain.ports.admin_system_check_repository_port import (
    AdminSystemCheckRepositoryPort,
)
from app.extensions.db import db
from app.infrastructure.config.embedding_config import (
    resolve_embedding_config,
    resolve_embedding_provider_name,
)
from app.infrastructure.config.llm_text_config import (
    resolve_llm_provider_name,
    resolve_llm_text_config,
)


REQUIRED_TABLES = [
    "ai_admin_runtime_settings",
    "ai_audit_logs",
    "ai_chat_message_feedback",
    "ai_chat_messages",
    "ai_chat_sessions",
    "ai_knowledge_chunks",
    "ai_knowledge_documents",
    "ai_response_evaluations",
]


class PostgresAdminSystemCheckRepository(AdminSystemCheckRepositoryPort):
    def check(self) -> dict:
        database = self._check_database()
        pgvector = self._check_pgvector()
        tables = self._check_tables()
        llm = self._check_text_llm()
        embedding = self._check_embedding()
        overall_status = self._overall_status(database, pgvector, tables, llm, embedding)

        return {
            "status": overall_status,
            "database": database,
            "pgvector": pgvector,
            "tables": tables,
            "llm": llm,
            "embedding": embedding,
        }

    def _check_database(self) -> dict:
        try:
            result = db.session.execute(text("select 1")).scalar()
            return {
                "status": "ok" if result == 1 else "error",
                "reachable": result == 1,
            }
        except Exception as exc:
            return {
                "status": "error",
                "reachable": False,
                "message": self._safe_error(exc),
            }

    def _check_pgvector(self) -> dict:
        try:
            row = db.session.execute(
                text(
                    "select extname, extversion "
                    "from pg_extension "
                    "where extname = 'vector'"
                )
            ).mappings().first()

            if not row:
                return {
                    "status": "error",
                    "installed": False,
                    "extension": "vector",
                }

            return {
                "status": "ok",
                "installed": True,
                "extension": row["extname"],
                "version": row["extversion"],
            }
        except Exception as exc:
            return {
                "status": "error",
                "installed": False,
                "extension": "vector",
                "message": self._safe_error(exc),
            }

    def _check_tables(self) -> dict:
        details = []

        try:
            for table in REQUIRED_TABLES:
                exists = db.session.execute(
                    text("select to_regclass(:table_name) is not null"),
                    {"table_name": f"public.{table}"},
                ).scalar()

                details.append(
                    {
                        "name": table,
                        "exists": bool(exists),
                        "status": "ok" if exists else "missing",
                    }
                )

            missing = [item["name"] for item in details if not item["exists"]]

            return {
                "status": "ok" if not missing else "error",
                "required": len(REQUIRED_TABLES),
                "missing": missing,
                "items": details,
            }
        except Exception as exc:
            return {
                "status": "error",
                "required": len(REQUIRED_TABLES),
                "missing": REQUIRED_TABLES,
                "items": details,
                "message": self._safe_error(exc),
            }

    def _check_text_llm(self) -> dict:
        provider = resolve_llm_provider_name()

        if provider == "ollama":
            return self._check_ollama_text_models()

        if provider == "openai_compatible":
            config = resolve_llm_text_config()
            return {
                "status": "ok",
                "provider": provider,
                "baseUrl": config.base_url,
                "chatModel": {
                    "name": config.model,
                    "available": True,
                },
                "message": "OpenAI-compatible text provider configured.",
            }

        return {
            "status": "error",
            "provider": provider,
            "message": "Unsupported LLM provider.",
        }

    def _check_embedding(self) -> dict:
        provider = resolve_embedding_provider_name()
        config = resolve_embedding_config()

        if provider == "ollama":
            return self._check_ollama_embedding_model(config)

        if provider == "openai_compatible":
            return {
                "status": "ok",
                "provider": provider,
                "baseUrl": config.base_url,
                "model": {
                    "name": config.model,
                    "available": True,
                },
                "message": "OpenAI-compatible embedding provider configured.",
            }

        return {
            "status": "error",
            "provider": provider,
            "message": "Unsupported embedding provider.",
        }

    def _check_ollama_text_models(self) -> dict:
        config = resolve_llm_text_config()

        try:
            response = requests.get(
                f"{config.base_url}/api/tags",
                timeout=min(float(config.timeout_seconds), 10),
            )
            response.raise_for_status()

            body = response.json()
            models = [item.get("name") for item in body.get("models", [])]
            chat_model_ok = self._model_available(config.model, models)
            status = "ok" if chat_model_ok else "warning"

            return {
                "status": status,
                "provider": "ollama",
                "baseUrl": config.base_url,
                "chatModel": {
                    "name": config.model,
                    "available": chat_model_ok,
                },
                "models": models,
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": "ollama",
                "baseUrl": config.base_url,
                "message": self._safe_error(exc),
            }

    def _check_ollama_embedding_model(self, config) -> dict:
        try:
            response = requests.get(
                f"{config.base_url}/api/tags",
                timeout=min(float(config.timeout_seconds), 10),
            )
            response.raise_for_status()

            body = response.json()
            models = [item.get("name") for item in body.get("models", [])]
            embedding_model_ok = self._model_available(config.model, models)
            status = "ok" if embedding_model_ok else "warning"

            return {
                "status": status,
                "provider": "ollama",
                "baseUrl": config.base_url,
                "model": {
                    "name": config.model,
                    "available": embedding_model_ok,
                },
                "models": models,
            }
        except Exception as exc:
            return {
                "status": "error",
                "provider": "ollama",
                "baseUrl": config.base_url,
                "message": self._safe_error(exc),
            }

    def _model_available(self, expected_model: str, available_models: list[str]) -> bool:
        if expected_model in available_models:
            return True

        if ":" not in expected_model and f"{expected_model}:latest" in available_models:
            return True

        return False

    def _overall_status(self, database: dict, pgvector: dict, tables: dict, llm: dict, embedding: dict) -> str:
        statuses = {
            database.get("status"),
            pgvector.get("status"),
            tables.get("status"),
            llm.get("status"),
            embedding.get("status"),
        }

        if "error" in statuses:
            return "error"

        if "warning" in statuses:
            return "warning"

        return "ok"

    def _safe_error(self, exc: Exception) -> str:
        return exc.__class__.__name__
