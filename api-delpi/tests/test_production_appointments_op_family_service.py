from __future__ import annotations

import pytest

from app.domain.services.production.production_appointments_op_family_service import (
    ProductionAppointmentsOpFamilyService,
)


def test_family_prefix_strips_mother_suffix() -> None:
    assert (
        ProductionAppointmentsOpFamilyService.family_prefix("24656601001")
        == "24656601"
    )


def test_is_mother_op() -> None:
    assert ProductionAppointmentsOpFamilyService.is_mother_op("24656601001") is True
    assert ProductionAppointmentsOpFamilyService.is_mother_op("24656601002") is False
    assert ProductionAppointmentsOpFamilyService.is_mother_op("001") is False


def test_family_prefix_rejects_short_op() -> None:
    with pytest.raises(ValueError, match="OP inválida"):
        ProductionAppointmentsOpFamilyService.family_prefix("001")
