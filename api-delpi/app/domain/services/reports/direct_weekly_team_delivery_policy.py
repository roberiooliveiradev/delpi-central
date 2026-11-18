"""Fail-closed recipient binding for GLPI #887 nominal manager reports."""

from __future__ import annotations

from typing import Any, Mapping, Sequence
from uuid import UUID

from app.domain.services.reports.report_types import ReportDataset

DIRECT_WEEKLY_PROVIDER_KEY = "team_direct_app_opens_weekly"


def ensure_manager_is_sole_recipient(
    *,
    recipients: Sequence[Mapping[str, Any]],
    dataset: ReportDataset,
) -> None:
    """Prevent sending one manager's team data to arbitrary report recipients."""
    meta = dataset.meta
    if (
        dataset.provider_key != DIRECT_WEEKLY_PROVIDER_KEY
        or meta.get("directOnly") is not True
        or meta.get("managerRegistration") is None
    ):
        raise ValueError("Dados de equipe direta não atestados.")
    if len(recipients) != 1:
        raise ValueError("Relatório de equipe direta permite somente o gestor como destinatário.")

    manager_email = str(meta.get("managerEmail") or "").strip().casefold()
    manager_core_id = str(meta.get("managerCoreUserId") or "").strip()
    recipient_email = str(recipients[0].get("email") or "").strip().casefold()
    recipient_id = str(recipients[0].get("userId") or "").strip()
    try:
        manager_core_id = str(UUID(manager_core_id))
        recipient_id = str(UUID(recipient_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("Identidade do gestor destinatário não verificada.") from exc
    if (
        not manager_email
        or "@" not in manager_email
        or "***" in manager_email
        or recipient_email != manager_email
        or recipient_id != manager_core_id
    ):
        raise ValueError("Destinatário não corresponde à conta Core verificada do gestor.")
