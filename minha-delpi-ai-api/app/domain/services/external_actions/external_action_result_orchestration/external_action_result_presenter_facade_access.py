"""Acesso lazy à fachada — ExternalActionResultPresenter."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


def result_presenter_type() -> type[ExternalActionResultPresenter]:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )

    return ExternalActionResultPresenter
