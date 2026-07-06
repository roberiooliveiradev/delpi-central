from __future__ import annotations

import pytest

from tm_app.infrastructure.persistence.repositories.revisao_repository import RevisaoRepository


class _FakeConnection:
    def commit(self) -> None:
        return None


def test_validate_referencia_baseline_cannot_have_reference():
    repo = RevisaoRepository(connection=_FakeConnection())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="baseline"):
        repo._validate_referencia_payload(
            {"cenario_tipo": "baseline", "revisao_referencia_id": "abc"},
            instancia_id="inst-1",
        )


def test_validate_referencia_non_baseline_requires_reference():
    repo = RevisaoRepository(connection=_FakeConnection())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="referência"):
        repo._validate_referencia_payload(
            {"cenario_tipo": "melhoria"},
            instancia_id="inst-1",
        )
