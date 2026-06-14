from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.infrastructure.persistence.plugins.repositories.cultura_delpi.postgres_cultura_delpi_repository import (
    PostgresCulturaDelpiRepository,
)
from app.interface.http.routes.cultura_delpi.cultura_delpi_router import (
    CulturaDelpiContentBody,
)


def test_cultura_delpi_content_body_trims_text_and_values() -> None:
    body = CulturaDelpiContentBody(
        proposito="  Propósito  ",
        missao=" Missão ",
        visao="Visão",
        valores=["  Valor 1 ", "Valor 2"],
    )
    assert body.proposito == "Propósito"
    assert body.missao == "Missão"
    assert body.valores == ["Valor 1", "Valor 2"]


def test_cultura_delpi_content_body_rejects_non_string_valores_item() -> None:
    with pytest.raises(ValidationError):
        CulturaDelpiContentBody(
            proposito="",
            missao="",
            visao="",
            valores=["ok", 123],
        )


def test_cultura_delpi_content_body_rejects_non_list_valores() -> None:
    with pytest.raises(ValidationError):
        CulturaDelpiContentBody(
            proposito="",
            missao="",
            visao="",
            valores="invalid",
        )


def test_row_to_payload_maps_camel_case_fields() -> None:
    payload = PostgresCulturaDelpiRepository.row_to_payload(
        {
            "proposito": "P",
            "missao": "M",
            "visao": "V",
            "valores": ["A", "B"],
            "updated_at": None,
            "updated_by_user_id": "user-1",
            "updated_by_name": "Admin",
        }
    )
    assert payload == {
        "proposito": "P",
        "missao": "M",
        "visao": "V",
        "valores": ["A", "B"],
        "updatedAt": None,
        "updatedByUserId": "user-1",
        "updatedByName": "Admin",
    }
