"""Unit — URL do portal para acompanhamentos no e-mail."""

from __future__ import annotations

from app.domain.services.reports.report_follow_up_portal_url import (
    build_follow_up_portal_url,
)


def test_build_follow_up_portal_url() -> None:
    assert (
        build_follow_up_portal_url(
            "https://portal.delpi.local/",
            "11111111-1111-1111-1111-111111111111",
        )
        == "https://portal.delpi.local/apps/reports/acompanhamentos/11111111-1111-1111-1111-111111111111"
    )


def test_build_follow_up_portal_url_missing_base() -> None:
    assert build_follow_up_portal_url(None, "def-1") is None
    assert build_follow_up_portal_url("  ", "def-1") is None


def test_build_follow_up_portal_url_missing_definition() -> None:
    assert build_follow_up_portal_url("https://portal", "") is None
