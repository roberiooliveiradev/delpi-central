"""Unit — enrich da Observação com acompanhamento humano."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.application.services.reports.shortage_item_note_observation_enrichment_service import (
    ShortageItemNoteObservationEnrichmentService,
)
from app.application.use_cases.reports.preview_report_provider_use_case import (
    PreviewReportProviderUseCase,
)
from app.application.use_cases.reports.run_report_definition_use_case import (
    RunReportDefinitionUseCase,
)
from app.domain.services.reports.report_types import EmailPayload, ReportDataset
from app.domain.services.reports.safety_stock_shortage_30d_rules import (
    build_follow_up_observation,
)
from app.infrastructure.reports.report_run_artifact_storage import (
    ReportRunArtifactStorage,
)


def test_build_follow_up_observation_without_date() -> None:
    assert (
        build_follow_up_observation("Maria Silva", "Chega na próxima semana")
        == "Acompanhamento (Maria Silva): Chega na próxima semana"
    )


def test_build_follow_up_observation_with_date() -> None:
    assert (
        build_follow_up_observation(
            "Maria Silva",
            "Confirmado com fornecedor",
            "2026-08-05",
        )
        == "Acompanhamento (Maria Silva): Previsão 05/08/2026 — Confirmado com fornecedor"
    )


def test_build_follow_up_observation_empty_text() -> None:
    assert build_follow_up_observation("Maria", "  ") == ""


def test_enrich_dataset_replaces_system_observation_with_follow_up() -> None:
    dataset = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code", "observation"),
        rows=(
            {
                "product_code": "10020113",
                "observation": "Material de terceiro - ACME",
            },
            {"product_code": "200", "observation": ""},
        ),
    )
    notes = {
        "10020113": {
            "noteText": "Chega semana que vem",
            "authorDisplayName": "Maria Silva",
            "expectedReceiptDate": "2026-08-05",
        }
    }
    enriched = ShortageItemNoteObservationEnrichmentService.enrich_dataset(
        dataset, notes
    )
    assert enriched.rows[0]["observation"] == (
        "Acompanhamento (Maria Silva): Previsão 05/08/2026 — Chega semana que vem"
    )
    assert "Material de terceiro" not in enriched.rows[0]["observation"]
    assert enriched.rows[1]["observation"] == ""
    assert enriched.meta["followUpNotesApplied"] == 1


def test_enrich_dataset_skips_other_provider() -> None:
    dataset = ReportDataset(
        provider_key="other",
        title="X",
        columns=("product_code",),
        rows=({"product_code": "1", "observation": ""},),
    )
    enriched = ShortageItemNoteObservationEnrichmentService.enrich_dataset(
        dataset,
        {"1": {"noteText": "n", "authorDisplayName": "A"}},
    )
    assert enriched is dataset


def test_preview_enriches_when_definition_id_present() -> None:
    provider = MagicMock()
    provider.collect.return_value = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code", "observation"),
        rows=({"product_code": "P1", "observation": ""},),
    )
    repo = MagicMock()
    repo.get_shortage_item_notes_by_product.return_value = {
        "P1": {
            "noteText": "ok",
            "authorDisplayName": "Ana",
            "expectedReceiptDate": None,
        }
    }
    result = PreviewReportProviderUseCase(provider, repository=repo).execute(
        {"branch": "01"},
        definition_id="def-1",
    )
    assert result["items"][0]["observation"] == "Acompanhamento (Ana): ok"
    repo.get_shortage_item_notes_by_product.assert_called_once_with(
        definition_id="def-1",
        branch="01",
    )


def test_run_report_enriches_observation_before_render(tmp_path) -> None:
    repo = MagicMock()
    repo.get_definition.return_value = {
        "id": "d1",
        "providerKey": "safety_stock_shortage_30d",
        "params": {"branch": "01"},
        "active": True,
    }
    repo.list_active_recipients.return_value = [{"email": "a@delpi.com.br"}]
    repo.create_run.return_value = {"id": "run-1", "status": "running"}
    repo.create_delivery.return_value = {"id": "del-1"}
    repo.finish_run.return_value = {"id": "run-1", "status": "succeeded"}
    repo.list_deliveries_for_run.return_value = []
    repo.get_shortage_item_notes_by_product.return_value = {
        "10020113": {
            "noteText": "Negociado",
            "authorDisplayName": "Maria Silva",
            "expectedReceiptDate": None,
        }
    }

    provider = MagicMock()
    provider.collect.return_value = ReportDataset(
        provider_key="safety_stock_shortage_30d",
        title="Rupturas",
        columns=("product_code", "observation"),
        rows=(
            {
                "product_code": "10020113",
                "observation": "AMOSTRA - 80123456",
            },
        ),
    )
    provider.render_email.return_value = EmailPayload(
        subject="Assunto",
        html_body="<p>ok</p>",
    )
    registry = MagicMock()
    registry.require.return_value = provider
    mail = MagicMock()

    use_case = RunReportDefinitionUseCase(
        repo,
        registry,
        mail,
        artifact_storage=ReportRunArtifactStorage(str(tmp_path)),
    )
    use_case.execute(definition_id="d1", trigger="manual")

    rendered = provider.render_email.call_args.args[0]
    assert (
        rendered.rows[0]["observation"]
        == "Acompanhamento (Maria Silva): Negociado"
    )
    repo.get_shortage_item_notes_by_product.assert_called_once_with(
        definition_id="d1",
        branch="01",
    )
