"""T7 — Writer único NC: legado congelado por LMP_NC_WRITE_MODE + guard
de permissão endurecido (api-delpi.access não concede mais NC WRITE)."""

from __future__ import annotations

import os
from unittest.mock import patch
from uuid import UUID

from app.application.security.api_delpi_permissions import (
    API_DELPI_ACCESS,
    DASHBOARD_LMPS_NC_WRITE,
    ENGINEERING_LMP_NC_WRITE,
)
from app.interface.http.routes.engineering.lmp_nonconformity_router import (
    ImportLmpNonconformitiesBody,
    LmpNonconformityBody,
    create_lmp_nonconformity,
    delete_lmp_nonconformity,
    import_lmp_nonconformities,
    update_lmp_nonconformity,
)

_NC_ID = UUID("22222222-2222-2222-2222-222222222222")


def test_nc_write_requires_dedicated_permission_not_api_delpi_access() -> None:
    """Hardening T7-E: a permissão genérica da API DELPI não pode mais
    habilitar sozinha CREATE/UPDATE/DELETE/IMPORT de NC."""
    assert ENGINEERING_LMP_NC_WRITE == [DASHBOARD_LMPS_NC_WRITE]
    assert API_DELPI_ACCESS not in ENGINEERING_LMP_NC_WRITE


def _env_frozen():
    return patch.dict(os.environ, {"LMP_NC_WRITE_MODE": "frozen"}, clear=False)


def _assert_blocked(result) -> None:
    assert result.status_code == 409
    assert "Engineering API" in result.body.decode()


def test_create_frozen_blocks_mutation() -> None:
    with _env_frozen():
        result = create_lmp_nonconformity(
            LmpNonconformityBody(
                status="open",
                occurrence_date="2026-01-01",
                products=[],
                problem_tags=[],
            )
        )
    _assert_blocked(result)


def test_update_frozen_blocks_mutation() -> None:
    with _env_frozen():
        result = update_lmp_nonconformity(
            _NC_ID,
            LmpNonconformityBody(
                status="open",
                occurrence_date="2026-01-01",
                products=[],
                problem_tags=[],
            ),
        )
    _assert_blocked(result)


def test_delete_frozen_blocks_mutation() -> None:
    with _env_frozen():
        result = delete_lmp_nonconformity(_NC_ID)
    _assert_blocked(result)


def test_import_frozen_blocks_mutation() -> None:
    with _env_frozen():
        result = import_lmp_nonconformities(
            ImportLmpNonconformitiesBody(items=[{"status": "open"}])
        )
    _assert_blocked(result)


def test_create_unfrozen_reaches_use_case() -> None:
    """Modo normal preservado: sem a flag, o endpoint segue para o use case."""
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("LMP_NC_WRITE_MODE", None)
        with patch(
            "app.interface.http.routes.engineering."
            "lmp_nonconformity_router.build_create_lmp_nonconformity_use_case"
        ) as mock_build:
            mock_build.return_value.execute.return_value = {"id": str(_NC_ID)}
            result = create_lmp_nonconformity(
                LmpNonconformityBody(
                    status="open",
                    occurrence_date="2026-01-01",
                    products=[],
                    problem_tags=[],
                )
            )
    assert result.status_code == 200
    mock_build.return_value.execute.assert_called_once()
