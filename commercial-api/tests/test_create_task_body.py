"""Contrato CreateTaskBody — campos de vínculo com a sala de interação."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from commercial_app.interface.http.schemas.worklist_schemas import CreateTaskBody


def test_create_task_body_accepts_related_entity_and_source_message() -> None:
    message_id = uuid4()
    body = CreateTaskBody(
        title="Confirmar produto",
        related_entity_type="order",
        related_entity_id="01|102942",
        source_interaction_message_id=message_id,
    )
    assert body.related_entity_type == "order"
    assert body.related_entity_id == "01|102942"
    assert body.source_interaction_message_id == message_id


def test_create_task_body_related_entity_fields_optional() -> None:
    body = CreateTaskBody(title="Sem vínculo")
    assert body.related_entity_type is None
    assert body.related_entity_id is None
    assert body.source_interaction_message_id is None


def test_create_task_body_rejects_partial_related_entity() -> None:
    with pytest.raises(ValidationError):
        CreateTaskBody(title="x", related_entity_type="order")
    with pytest.raises(ValidationError):
        CreateTaskBody(title="x", related_entity_id="01|1")
