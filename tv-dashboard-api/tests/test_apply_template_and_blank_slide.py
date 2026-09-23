"""apply_published_slide_template + add_blank_slide props."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from tv_app.application.services.data.presentation_mutation.patch_service import (
    PresentationPatchService,
)


def test_apply_published_slide_template_replaces_native():
    svc = PresentationPatchService(repo=MagicMock(), catalog=MagicMock())
    native = {"version": 5, "blocks": [{"id": "old", "type": "text"}]}
    template_native = {
        "version": 5,
        "brandThemeKey": "delpi-dark",
        "blocks": [{"id": "new", "type": "heading"}],
    }
    with patch(
        "tv_app.infrastructure.persistence.repositories.slide_template_repository.SlideTemplateRepository.get_by_key",
        return_value={
            "id": str(uuid4()),
            "status": "published",
            "nativeConfig": template_native,
        },
    ):
        svc._op_apply_published_slide_template(
            native,
            {"op": "apply_published_slide_template", "templateKey": "system-oee-overview"},
        )
    assert native["brandThemeKey"] == "delpi-dark"
    assert native["blocks"][0]["id"] == "new"


def test_add_blank_slide_preview_background_and_duration():
    svc = PresentationPatchService(repo=MagicMock())
    out = svc._op_add_blank_slide(
        str(uuid4()),
        {
            "op": "add_blank_slide",
            "title": "Verde",
            "durationSec": 45,
            "background": {"type": "color", "value": "#16a34a"},
        },
        persist=False,
        actor_user_id=None,
    )
    assert out["durationSec"] == 45
    assert out["nativeConfig"]["background"]["value"] == "#16a34a"
