"""Executa uma definição de relatório: collect → render → Graph → persist."""

from __future__ import annotations

import logging
from typing import Any, Mapping, Protocol, Sequence

from app.config import settings
from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    sanitize_graph_error,
)
from app.infrastructure.reports.report_run_artifact_storage import (
    ReportRunArtifactStorage,
)

logger = logging.getLogger(__name__)

_VALID_TRIGGERS = frozenset({"manual", "schedule", "event"})


class _ReportsRepo(Protocol):
    def get_definition(self, definition_id: str) -> dict[str, Any] | None: ...
    def list_active_recipients(self, definition_id: str) -> list[dict[str, Any]]: ...
    def create_run(self, **kwargs: Any) -> dict[str, Any]: ...
    def finish_run(self, **kwargs: Any) -> dict[str, Any] | None: ...
    def create_delivery(self, **kwargs: Any) -> dict[str, Any]: ...
    def finish_delivery(self, **kwargs: Any) -> dict[str, Any] | None: ...
    def list_deliveries_for_run(self, run_id: str) -> list[dict[str, Any]]: ...


class _ProviderRegistry(Protocol):
    def require(self, provider_key: str) -> Any: ...


class _MailClient(Protocol):
    def send_mail_to(
        self,
        *,
        subject: str,
        html_body: str,
        to_addresses: list[str],
        attachments: Any = None,
    ) -> None: ...


def _chunked(items: Sequence[str], size: int) -> list[list[str]]:
    step = max(1, int(size))
    return [list(items[i : i + step]) for i in range(0, len(items), step)]


class RunReportDefinitionUseCase:
    def __init__(
        self,
        repository: _ReportsRepo,
        registry: _ProviderRegistry,
        mail_client: _MailClient,
        *,
        artifact_storage: ReportRunArtifactStorage | None = None,
        mail_batch_size: int | None = None,
    ) -> None:
        self._repository = repository
        self._registry = registry
        self._mail = mail_client
        self._artifacts = artifact_storage or ReportRunArtifactStorage(
            settings.REPORTS_RUN_ARTIFACTS_DIR
        )
        self._batch_size = (
            mail_batch_size
            if mail_batch_size is not None
            else int(settings.REPORTS_MAIL_BATCH_SIZE or 40)
        )

    def execute(
        self,
        *,
        definition_id: str,
        trigger: str = "manual",
    ) -> dict[str, Any]:
        normalized_trigger = str(trigger or "manual").strip().lower() or "manual"
        if normalized_trigger not in _VALID_TRIGGERS:
            raise ValueError("trigger deve ser manual, schedule ou event.")

        definition = self._repository.get_definition(definition_id)
        if definition is None:
            raise LookupError("Definição de relatório não encontrada.")
        if not definition.get("active"):
            raise ValueError("Definição de relatório está inativa.")

        recipients = self._repository.list_active_recipients(definition_id)
        emails = [
            str(item.get("email") or "").strip()
            for item in recipients
            if str(item.get("email") or "").strip()
        ]
        if not emails:
            raise ValueError("Nenhum destinatário ativo com e-mail para esta definição.")

        provider_key = str(definition.get("providerKey") or "").strip()
        params: Mapping[str, Any] = definition.get("params") or {}
        provider = self._registry.require(provider_key)

        run = self._repository.create_run(
            definition_id=definition_id,
            trigger=normalized_trigger,
            status="running",
            summary={"providerKey": provider_key},
        )
        run_id = run["id"]
        logger.info(
            "report_run_started runId=%s definitionId=%s trigger=%s "
            "recipientCount=%s",
            run_id,
            definition_id,
            normalized_trigger,
            len(emails),
        )

        artifact_path: str | None = None
        try:
            dataset = provider.collect(params)
            email_payload = provider.render_email(dataset)
            artifact_path = self._artifacts.save_html(
                run_id=run_id,
                html_body=email_payload.html_body,
            )
            attachments = [
                {
                    "name": att.name,
                    "content_type": att.content_type,
                    "content_base64": att.content_base64,
                    "is_inline": att.is_inline,
                    "content_id": att.content_id or "",
                }
                for att in (email_payload.attachments or ())
            ]
            batches = _chunked(emails, self._batch_size)
            sent_count = 0
            failed_count = 0
            last_error: str | None = None

            for batch_index, batch in enumerate(batches, start=1):
                delivery_ids: list[str] = []
                for email in batch:
                    delivery = self._repository.create_delivery(
                        run_id=run_id,
                        recipient_email=email,
                        status="pending",
                    )
                    delivery_ids.append(delivery["id"])
                try:
                    self._mail.send_mail_to(
                        subject=email_payload.subject,
                        html_body=email_payload.html_body,
                        to_addresses=batch,
                        attachments=attachments or None,
                    )
                except GraphMailError as exc:
                    message = sanitize_graph_error(str(exc))
                    last_error = message
                    failed_count += len(batch)
                    for delivery_id in delivery_ids:
                        self._repository.finish_delivery(
                            delivery_id=delivery_id,
                            status="failed",
                            error=message,
                        )
                    logger.warning(
                        "report_mail_batch_failed runId=%s batch=%s size=%s error=%s",
                        run_id,
                        batch_index,
                        len(batch),
                        message,
                    )
                    continue

                sent_count += len(batch)
                for delivery_id in delivery_ids:
                    self._repository.finish_delivery(
                        delivery_id=delivery_id,
                        status="sent",
                    )
                logger.info(
                    "report_mail_batch_sent runId=%s batch=%s size=%s",
                    run_id,
                    batch_index,
                    len(batch),
                )

            row_count = int(getattr(dataset, "row_count", 0) or 0)
            summary: dict[str, Any] = {
                "providerKey": provider_key,
                "recipientCount": len(emails),
                "rowCount": row_count,
                "title": getattr(dataset, "title", None),
                "batchCount": len(batches),
                "sentCount": sent_count,
                "failedCount": failed_count,
            }
            if artifact_path:
                summary["artifactHtmlPath"] = artifact_path

            if failed_count and sent_count == 0:
                finished = self._repository.finish_run(
                    run_id=run_id,
                    status="failed",
                    summary=summary,
                    error=last_error or "Falha ao enviar e-mail via Microsoft Graph.",
                )
            elif failed_count:
                summary["partialFailure"] = True
                finished = self._repository.finish_run(
                    run_id=run_id,
                    status="succeeded",
                    summary=summary,
                    error=last_error,
                )
            else:
                finished = self._repository.finish_run(
                    run_id=run_id,
                    status="succeeded",
                    summary=summary,
                    error=None,
                )

            result = self._with_deliveries(finished or run)
            logger.info(
                "report_run_finished runId=%s definitionId=%s trigger=%s "
                "status=%s rowCount=%s recipientCount=%s sentCount=%s failedCount=%s",
                run_id,
                definition_id,
                normalized_trigger,
                result.get("status"),
                row_count,
                len(emails),
                sent_count,
                failed_count,
            )
            return result

        except GraphMailError as exc:
            message = sanitize_graph_error(str(exc))
            for email in emails:
                delivery = self._repository.create_delivery(
                    run_id=run_id,
                    recipient_email=email,
                    status="pending",
                )
                self._repository.finish_delivery(
                    delivery_id=delivery["id"],
                    status="failed",
                    error=message,
                )
            summary = {
                "providerKey": provider_key,
                "recipientCount": len(emails),
                "rowCount": 0,
                "sentCount": 0,
                "failedCount": len(emails),
            }
            if artifact_path:
                summary["artifactHtmlPath"] = artifact_path
            finished = self._repository.finish_run(
                run_id=run_id,
                status="failed",
                summary=summary,
                error=message,
            )
            logger.warning(
                "report_run_finished runId=%s status=failed error=%s",
                run_id,
                message,
            )
            return self._with_deliveries(finished or run)

        except Exception as exc:
            message = sanitize_graph_error(str(exc))
            summary = {"providerKey": provider_key}
            if artifact_path:
                summary["artifactHtmlPath"] = artifact_path
            finished = self._repository.finish_run(
                run_id=run_id,
                status="failed",
                summary=summary,
                error=message,
            )
            logger.warning(
                "report_run_finished runId=%s status=failed error=%s",
                run_id,
                message,
            )
            return self._with_deliveries(finished or run)

    def _with_deliveries(self, run: dict[str, Any]) -> dict[str, Any]:
        payload = dict(run)
        payload["deliveries"] = self._repository.list_deliveries_for_run(run["id"])
        return payload
