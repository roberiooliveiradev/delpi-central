from __future__ import annotations

from typing import Any, Mapping

import pytest

from app.application.security import api_delpi_permissions as perms
from app.domain.services.reports.report_provider_registry import ReportProviderRegistry
from app.domain.services.reports.report_types import EmailPayload, ReportDataset


class _StubProvider:
    def __init__(self, key: str) -> None:
        self._key = key

    @property
    def key(self) -> str:
        return self._key

    def describe_params(self) -> Mapping[str, Any]:
        return {"type": "object", "properties": {}}

    def collect(
        self,
        params: Mapping[str, Any],
        context: Mapping[str, Any] | None = None,
    ) -> ReportDataset:
        return ReportDataset(
            provider_key=self._key,
            title="stub",
            columns=("a",),
            rows=({"a": 1},),
        )

    def render_email(self, dataset: ReportDataset) -> EmailPayload:
        return EmailPayload(subject="s", html_body="<p>ok</p>")


def test_reports_permission_constants() -> None:
    assert perms.REPORTS_VIEW == "reports.view"
    assert perms.REPORTS_MANAGE == "reports.manage"
    assert perms.REPORTS_VIEW_FILIAL_SC == "reports.view.filial-sc"
    assert perms.REPORTS_VIEW_FILIAL_ES == "reports.view.filial-es"
    assert perms.REPORTS_BRANCH_VIEW_PERMS == {
        "01": perms.REPORTS_VIEW_FILIAL_SC,
        "02": perms.REPORTS_VIEW_FILIAL_ES,
    }
    assert perms.REPORTS_VIEW in perms.REPORTS_READ_PERMISSIONS
    assert perms.REPORTS_MANAGE in perms.REPORTS_WRITE_PERMISSIONS


def test_report_provider_registry_empty_then_register() -> None:
    registry = ReportProviderRegistry()
    assert registry.list_keys() == []
    assert registry.get("missing") is None

    registry.register(_StubProvider("safety_stock_shortage_30d"))
    assert registry.list_keys() == ["safety_stock_shortage_30d"]
    provider = registry.require("safety_stock_shortage_30d")
    assert provider.key == "safety_stock_shortage_30d"
    dataset = provider.collect({})
    assert dataset.row_count == 1
    email = provider.render_email(dataset)
    assert email.subject == "s"


def test_report_provider_registry_rejects_duplicate_and_blank() -> None:
    registry = ReportProviderRegistry()
    with pytest.raises(ValueError, match="obrigatório"):
        registry.register(_StubProvider("  "))
    registry.register(_StubProvider("a"))
    with pytest.raises(ValueError, match="já registrado"):
        registry.register(_StubProvider("a"))
    with pytest.raises(KeyError, match="não encontrado"):
        registry.require("b")
