from __future__ import annotations

from app.application.services.supplies.safety_stock_shortage_30d_aggregation_service import (
    SafetyStockShortage30dAggregationService,
)
from app.config import settings
from app.domain.services.reports.providers.safety_stock_shortage_30d_provider import (
    SafetyStockShortage30dProvider,
)
from app.domain.services.reports.report_provider_registry import ReportProviderRegistry
from app.infrastructure.persistence.plugins.repositories.reports.postgres_reports_repository import (
    PostgresReportsRepository,
)
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_query_repository import (
    SafetyStockQueryRepository,
)
from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    MicrosoftGraphMailClient,
)
from app.infrastructure.reports.report_email_logo_attachment import (
    build_delpi_logo_report_attachment,
)


def build_reports_repository() -> PostgresReportsRepository:
    return PostgresReportsRepository()


def build_report_provider_registry() -> ReportProviderRegistry:
    """Composition root — providers registrados."""
    registry = ReportProviderRegistry()
    aggregation = SafetyStockShortage30dAggregationService(
        SafetyStockQueryRepository()
    )
    registry.register(
        SafetyStockShortage30dProvider(
            aggregation,
            logo_attachment=build_delpi_logo_report_attachment(),
        )
    )
    return registry


def build_reports_graph_mail_client() -> MicrosoftGraphMailClient:
    """Graph exclusivo do Reports — não reutiliza GRAPH_MAIL_* do canal-denúncia."""
    return MicrosoftGraphMailClient(
        tenant_id=settings.GRAPH_REPORTS_TENANT_ID,
        client_id=settings.GRAPH_REPORTS_CLIENT_ID,
        client_secret=settings.GRAPH_REPORTS_CLIENT_SECRET,
        sender=settings.GRAPH_REPORTS_MAIL_SENDER,
        recipient=None,
        timeout_seconds=float(settings.GRAPH_HTTP_TIMEOUT_SECONDS or "15"),
    )


def build_preview_safety_stock_shortage_30d_use_case():
    from app.application.use_cases.reports.preview_report_provider_use_case import (
        PreviewReportProviderUseCase,
    )

    provider = build_report_provider_registry().require("safety_stock_shortage_30d")
    return PreviewReportProviderUseCase(provider)


def build_list_report_definitions_use_case():
    from app.application.use_cases.reports.list_report_definitions_use_case import (
        ListReportDefinitionsUseCase,
    )

    return ListReportDefinitionsUseCase(build_reports_repository())


def build_get_report_definition_use_case():
    from app.application.use_cases.reports.get_report_definition_use_case import (
        GetReportDefinitionUseCase,
    )

    return GetReportDefinitionUseCase(build_reports_repository())


def build_create_report_definition_use_case():
    from app.application.use_cases.reports.create_report_definition_use_case import (
        CreateReportDefinitionUseCase,
    )

    return CreateReportDefinitionUseCase(build_reports_repository())


def build_update_report_definition_use_case():
    from app.application.use_cases.reports.update_report_definition_use_case import (
        UpdateReportDefinitionUseCase,
    )

    return UpdateReportDefinitionUseCase(build_reports_repository())


def build_list_report_runs_use_case():
    from app.application.use_cases.reports.list_report_runs_use_case import (
        ListReportRunsUseCase,
    )

    return ListReportRunsUseCase(build_reports_repository())


def build_list_report_providers_use_case():
    from app.application.use_cases.reports.list_report_providers_use_case import (
        ListReportProvidersUseCase,
    )

    return ListReportProvidersUseCase(build_report_provider_registry())


def build_list_report_recipients_use_case():
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        ListReportRecipientsUseCase,
    )

    return ListReportRecipientsUseCase(build_reports_repository())


def build_replace_report_recipients_use_case():
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        ReplaceReportRecipientsUseCase,
    )

    return ReplaceReportRecipientsUseCase(build_reports_repository())


def build_get_report_schedule_use_case():
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        GetReportScheduleUseCase,
    )

    return GetReportScheduleUseCase(build_reports_repository())


def build_upsert_report_schedule_use_case():
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        UpsertReportScheduleUseCase,
    )

    return UpsertReportScheduleUseCase(build_reports_repository())


def build_delete_report_schedule_use_case():
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        DeleteReportScheduleUseCase,
    )

    return DeleteReportScheduleUseCase(build_reports_repository())


def build_get_report_run_use_case():
    from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
        GetReportRunUseCase,
    )

    return GetReportRunUseCase(build_reports_repository())


def build_run_report_definition_use_case():
    from app.application.use_cases.reports.run_report_definition_use_case import (
        RunReportDefinitionUseCase,
    )

    return RunReportDefinitionUseCase(
        build_reports_repository(),
        build_report_provider_registry(),
        build_reports_graph_mail_client(),
    )


def build_process_due_report_schedules_use_case():
    from app.application.use_cases.reports.process_due_report_schedules_use_case import (
        ProcessDueReportSchedulesUseCase,
    )

    return ProcessDueReportSchedulesUseCase(
        build_reports_repository(),
        build_run_report_definition_use_case(),
    )
