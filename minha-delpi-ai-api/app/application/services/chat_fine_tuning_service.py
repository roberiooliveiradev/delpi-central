"""Fine-tuning offline — curadoria, exportação e jobs (playbook Fase 7)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.domain.services.chat_fine_tuning_anonymization_service import (
    ChatFineTuningAnonymizationService,
)
from app.domain.ports.chat_message_feedback_repository_port import (
    ChatMessageFeedbackRepositoryPort,
)
from app.domain.ports.fine_tuning_repository_port import FineTuningRepositoryPort
from app.domain.services.chat_fine_tuning_export_service import ChatFineTuningExportService
from app.domain.services.chat_fine_tuning_modelfile_builder_service import (
    ChatFineTuningModelfileBuilderService,
)
from app.domain.services.chat_learning_safety_guard import ChatLearningSafetyGuard
from app.infrastructure.config.settings import Settings


def _default_fine_tuning_repository() -> FineTuningRepositoryPort:
    from app.composition.repository_composer import make_fine_tuning_repository

    return make_fine_tuning_repository()


def _default_feedback_repository() -> ChatMessageFeedbackRepositoryPort:
    from app.composition.repository_composer import make_chat_message_feedback_repository

    return make_chat_message_feedback_repository()

_MIN_SAMPLES_FOR_RUN = 3


class ChatFineTuningService:
    def __init__(
        self,
        repository: FineTuningRepositoryPort | None = None,
        feedback_repository: ChatMessageFeedbackRepositoryPort | None = None,
    ):
        self._repository = repository
        self._feedback_repository = feedback_repository

    def _repo(self) -> FineTuningRepositoryPort:
        if self._repository is None:
            self._repository = _default_fine_tuning_repository()

        return self._repository

    def _feedback_repo(self) -> ChatMessageFeedbackRepositoryPort:
        if self._feedback_repository is None:
            self._feedback_repository = _default_feedback_repository()

        return self._feedback_repository

    @staticmethod
    def _enabled() -> bool:
        from app.application.services.chat_platform_runtime_access import learning_flag

        return learning_flag("learningFineTuningEnabled")

    @staticmethod
    def _capture_positive_enabled() -> bool:
        from app.application.services.chat_platform_runtime_access import learning_flag

        return learning_flag("learningFineTuningCapturePositiveFeedback")

    def capture_from_positive_feedback(
        self,
        *,
        message_id: UUID,
        feedback_id: int | None = None,
        context_metadata: dict | None = None,
        created_by: str | None = None,
    ) -> dict | None:
        if not self._capture_positive_enabled():
            return None

        source_ref = f"feedback:{feedback_id}" if feedback_id else f"message:{message_id}"

        if self._repo().find_sample_by_source(source="feedback_positive", source_ref=source_ref):
            return {"skipped": True}

        user_text = self._feedback_repo().get_user_question_for_assistant(message_id)
        assistant = self._feedback_repo().get_assistant_message(message_id)

        assistant_content = (assistant or {}).get("content") if isinstance(assistant, dict) else None

        if not user_text or not assistant_content:
            return None

        raw_messages = [
            {"role": "user", "content": str(user_text)},
            {"role": "assistant", "content": str(assistant_content)},
        ]
        combined = " ".join(item["content"] for item in raw_messages)

        if not ChatLearningSafetyGuard.is_safe_to_learn(combined):
            return None

        anonymized_messages = ChatFineTuningAnonymizationService.anonymize_messages(raw_messages)
        risk = ChatFineTuningAnonymizationService.assess_risk(
            " ".join(m["content"] for m in anonymized_messages)
        )

        intent_label = self._intent_from_context(context_metadata)

        try:
            sample = self._repo().create_sample(
                messages_json=anonymized_messages,
                category=self._category_from_intent(intent_label),
                source="feedback_positive",
                source_ref=source_ref,
                intent_label=intent_label,
                quality_score=0.85,
                anonymized=True,
                risk_level=risk.get("riskLevel"),
                created_by=self._to_uuid(created_by),
            )
            return {"created": True, "sample": sample}
        except Exception:
            return None

    def create_sample_manual(self, *, payload: dict, created_by: str | None = None) -> dict:
        messages = payload.get("messages") or []

        if not isinstance(messages, list) or len(messages) < 2:
            raise ValueError("messages must include user and assistant turns")

        raw_text = " ".join(str(m.get("content") or "") for m in messages if isinstance(m, dict))

        if not ChatLearningSafetyGuard.is_safe_to_learn(raw_text):
            raise ValueError("blocked by safety guard")

        anonymized = ChatFineTuningAnonymizationService.anonymize_messages(messages)
        risk = ChatFineTuningAnonymizationService.assess_risk(
            " ".join(m["content"] for m in anonymized)
        )

        return self._repo().create_sample(
            messages_json=anonymized,
            category=str(payload.get("category") or "routing").strip() or "routing",
            source="admin",
            intent_label=payload.get("intentLabel") or payload.get("intent_label"),
            quality_score=payload.get("qualityScore"),
            anonymized=True,
            risk_level=risk.get("riskLevel"),
            dataset_id=payload.get("datasetId"),
            created_by=self._to_uuid(created_by),
        )

    def review_sample(
        self,
        sample_id: int,
        *,
        action: str,
        reviewer_id: str | None = None,
        dataset_id: int | None = None,
    ) -> dict:
        normalized = str(action or "").strip().lower()

        if normalized not in {"approve", "reject"}:
            raise ValueError("invalid review action")

        status = "approved" if normalized == "approve" else "rejected"
        updated = self._repo().update_sample_status(
            sample_id,
            status=status,
            reviewer_id=self._to_uuid(reviewer_id),
            dataset_id=dataset_id,
        )

        if not updated:
            raise ValueError("sample not found")

        return {"sample": updated}

    def create_dataset(self, *, payload: dict, created_by: str | None = None) -> dict:
        name = str(payload.get("name") or "").strip()

        if not name:
            raise ValueError("name is required")

        return self._repo().create_dataset(
            name=name,
            description=payload.get("description"),
            target_model=str(payload.get("targetModel") or "intent_classifier"),
            metadata=payload.get("metadata"),
            created_by=self._to_uuid(created_by),
        )

    def approve_dataset(self, dataset_id: int, *, approved_by: str | None = None) -> dict:
        dataset = self._repo().get_dataset(dataset_id)

        if not dataset:
            raise ValueError("dataset not found")

        approved_count = len(self._repo().list_approved_for_dataset(dataset_id))

        if approved_count < _MIN_SAMPLES_FOR_RUN:
            raise ValueError(
                f"dataset needs at least {_MIN_SAMPLES_FOR_RUN} approved samples "
                f"(has {approved_count})"
            )

        updated = self._repo().approve_dataset(
            dataset_id, approved_by=self._to_uuid(approved_by)
        )
        return {"dataset": updated}

    def assign_samples(self, *, dataset_id: int, sample_ids: list[int]) -> dict:
        count = self._repo().assign_samples_to_dataset(
            dataset_id=dataset_id,
            sample_ids=sample_ids,
        )
        return {"assigned": count}

    def export_dataset(self, dataset_id: int) -> dict:
        dataset = self._repo().get_dataset(dataset_id)

        if not dataset:
            raise ValueError("dataset not found")

        samples = self._repo().list_approved_for_dataset(dataset_id)
        jsonl = ChatFineTuningExportService.build_jsonl(samples)
        stats = ChatFineTuningExportService.export_stats(samples, jsonl=jsonl)

        return {"dataset": dataset, "jsonl": jsonl, "stats": stats}

    def start_run(self, *, dataset_id: int, created_by: str | None = None) -> dict:
        dataset = self._repo().get_dataset(dataset_id)

        if not dataset:
            raise ValueError("dataset not found")

        if dataset["status"] != "approved":
            raise ValueError("dataset must be approved before starting a run")

        return self._repo().create_run(
            dataset_id=dataset_id,
            target_model=dataset["targetModel"],
            created_by=self._to_uuid(created_by),
        )

    def execute_run_export(self, run_id: int) -> dict:
        run = self._repo().get_run(run_id)

        if not run:
            raise ValueError("run not found")

        export = self.export_dataset(int(run["datasetId"]))
        now = datetime.now(timezone.utc)

        updated = self._repo().update_run(
            run_id,
            status="exported",
            export_stats=export["stats"],
            started_at=now,
        )

        return {"run": updated, **export}

    def execute_run_training(self, run_id: int) -> dict:
        """Valida export e cria adaptador Ollama (Modelfile) quando habilitado."""
        run = self._repo().get_run(run_id)

        if not run:
            raise ValueError("run not found")

        if run["status"] not in {"exported", "pending"}:
            raise ValueError(f"cannot train from status {run['status']}")

        export = self.export_dataset(int(run["datasetId"]))
        line_count = int(export["stats"].get("lineCount", 0))

        if line_count < _MIN_SAMPLES_FOR_RUN:
            self._repo().update_run(
                run_id,
                status="failed",
                error_message=f"insufficient samples ({line_count})",
                completed_at=datetime.now(timezone.utc),
            )
            raise ValueError("insufficient approved samples for training")

        now = datetime.now(timezone.utc)
        dataset = export["dataset"]
        samples = self._repo().list_approved_for_dataset(int(run["datasetId"]))
        metrics: dict = {
            "sampleCount": line_count,
            "baseModel": Settings.CHAT_LEARNING_FINE_TUNING_BASE_MODEL,
        }

        ollama_model_name = ChatFineTuningModelfileBuilderService.build_model_name(
            dataset_id=int(run["datasetId"]),
            run_id=run_id,
        )

        from app.composition.fine_tuning_model_composer import make_fine_tuning_model_gateway
        from app.domain.services.chat_learning_content_service import ChatLearningContentService

        if Settings.CHAT_LEARNING_FINE_TUNING_OLLAMA_CREATE_ENABLED:
            gateway = make_fine_tuning_model_gateway()

            if gateway.supports_local_deploy():
                try:
                    modelfile = ChatFineTuningModelfileBuilderService.build_modelfile(
                        base_model=Settings.CHAT_LEARNING_FINE_TUNING_BASE_MODEL,
                        samples=samples,
                        target_model=str(dataset.get("targetModel") or run.get("targetModel") or "chat"),
                    )
                    create_result = gateway.create_from_modelfile(
                        name=ollama_model_name,
                        modelfile=modelfile,
                    )
                    metrics.update(
                        {
                            "mode": "ollama_modelfile",
                            "ollamaModelName": ollama_model_name,
                            "ollamaCreateStatus": create_result.get("status"),
                            "fineTuningProvider": gateway.provider_name(),
                        }
                    )
                except Exception as exc:
                    self._repo().update_run(
                        run_id,
                        status="failed",
                        error_message=str(exc)[:500],
                        completed_at=now,
                    )
                    raise ValueError(f"fine-tuning model create failed: {exc}") from exc
            else:
                metrics.update(
                    {
                        "mode": "export_only",
                        "note": ChatLearningContentService.get(
                            "fineTuning",
                            "exportOnlyNote",
                            default="Treino local indisponível; use export JSONL e webhook externo.",
                        ),
                        "fineTuningProvider": gateway.provider_name(),
                    }
                )
        else:
            metrics.update(
                {
                    "mode": "export_only",
                    "note": ChatLearningContentService.get(
                        "fineTuning",
                        "exportOnlyDisabled",
                        default="Criação Ollama desligada; use export JSONL e webhook externo se necessário.",
                    ),
                }
            )

        updated = self._repo().update_run(
            run_id,
            status="completed",
            export_stats=export["stats"],
            metrics=metrics,
            started_at=run.get("startedAt") and now or now,
            completed_at=now,
        )

        webhook_result = self._notify_train_webhook(
            run=updated,
            export_stats=export["stats"],
        )
        if webhook_result:
            metrics["webhook"] = webhook_result
            updated = self._repo().update_run(run_id, metrics=metrics) or updated

        return {"run": updated, "metrics": metrics, "ollamaModelName": metrics.get("ollamaModelName")}

    @staticmethod
    def _notify_train_webhook(*, run: dict, export_stats: dict) -> dict | None:
        url = Settings.CHAT_LEARNING_FINE_TUNING_TRAIN_WEBHOOK_URL

        if not url:
            return None

        try:
            import requests

            response = requests.post(
                url,
                json={
                    "runId": run.get("id"),
                    "datasetId": run.get("datasetId"),
                    "targetModel": run.get("targetModel"),
                    "exportStats": export_stats,
                },
                timeout=15,
            )
            return {"statusCode": response.status_code, "ok": response.ok}
        except Exception as exc:
            return {"ok": False, "error": str(exc)[:200]}

    def deploy_run(self, run_id: int) -> dict:
        run = self._repo().get_run(run_id)

        if not run:
            raise ValueError("run not found")

        if run["status"] != "completed":
            raise ValueError("only completed runs can be deployed")

        self._repo().deactivate_deploys(
            target_model=run["targetModel"],
            except_run_id=run_id,
        )
        updated = self._repo().update_run(
            run_id,
            status="deployed",
            active_deploy=True,
        )
        deployed_model = None

        if isinstance(run.get("metrics"), dict):
            deployed_model = run["metrics"].get("ollamaModelName")

        return {
            "run": updated,
            "deployedOllamaModel": deployed_model,
            "effectiveChatModel": deployed_model,
        }

    def rollback_run(self, run_id: int) -> dict:
        run = self._repo().get_run(run_id)

        if not run:
            raise ValueError("run not found")

        updated = self._repo().update_run(
            run_id,
            status="rolled_back",
            active_deploy=False,
            completed_at=datetime.now(timezone.utc),
        )
        return {"run": updated}

    def list_samples(self, **kwargs) -> dict:
        items, total = self._repo().list_samples(**kwargs)
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "hasNext": offset + limit < total,
                "hasPrevious": offset > 0,
            },
        }

    def list_datasets(self, **kwargs) -> dict:
        items, total = self._repo().list_datasets(**kwargs)
        limit = int(kwargs.get("limit", 50))
        offset = int(kwargs.get("offset", 0))
        return {
            "items": items,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total,
                "hasNext": offset + limit < total,
                "hasPrevious": offset > 0,
            },
        }

    @staticmethod
    def _intent_from_context(context_metadata: dict | None) -> str | None:
        if not isinstance(context_metadata, dict):
            return None

        intent = context_metadata.get("intent")
        sub = context_metadata.get("subIntent")

        if intent and sub:
            return f"{intent}.{sub}"

        return str(intent) if intent else None

    @staticmethod
    def _category_from_intent(intent_label: str | None) -> str:
        if not intent_label:
            return "routing"

        base = str(intent_label).split(".", 1)[0].lower()

        if base in {"small_talk", "utility", "assistant_identity", "capabilities"}:
            return "routing"

        if base == "clarification":
            return "fallback"

        return "routing"

    @staticmethod
    def _to_uuid(value) -> UUID | None:
        if not value:
            return None

        try:
            return UUID(str(value))
        except (TypeError, ValueError):
            return None
