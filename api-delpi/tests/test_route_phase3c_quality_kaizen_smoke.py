"""Smoke — Kaizen records (rotas restantes phase 3c)."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_KZ = "app.interface.http.routes.quality.kaizen_records_router"

import importlib

for _mod in (_KZ,):
    importlib.import_module(_mod)

_REC = "rec-smoke-1"
_REV = 1
_EVID = "ev-smoke-1"


@pytest.fixture(autouse=True)
def _allow_kaizen_branch():
    """Gate de unidade usa JWT real; smokes não carregam permissões de filial."""
    with patch(f"{_KZ}.branch_access_error", return_value=None):
        yield


def _user_patch():
    return patch(
        f"{_KZ}.get_current_user",
        return_value=MagicMock(id="u1", name="User"),
    )


def _kaizen_repo(**methods: object) -> MagicMock:
    repo = MagicMock()
    repo.get_record.return_value = {"id": _REC, "branch_code": "01"}
    for name, value in methods.items():
        if callable(value):
            repo.configure_mock(**{name: value})
        else:
            getattr(repo, name).return_value = value
    return repo


@_user_patch()
@patch(f"{_KZ}.build_kaizen_repository")
def test_delete_kaizen_record_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import delete_kaizen_record

    mock_build.return_value = _kaizen_repo(delete_record=True)
    response = delete_kaizen_record(_REC)
    assert_envelope_meta(body_json(response), operation_id="delete_kaizen_record")


@_user_patch()
@patch(f"{_KZ}.build_kaizen_repository")
def test_update_kaizen_record_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        UpdateKaizenRecordBody,
        update_kaizen_record,
    )

    mock_build.return_value = _kaizen_repo(update_record={"id": _REC, "title": "Novo"})
    response = update_kaizen_record(_REC, body=UpdateKaizenRecordBody(title="Novo título"))
    assert_envelope_meta(body_json(response), operation_id="update_kaizen_record")


@patch(f"{_KZ}.build_kaizen_repository")
def test_get_kaizen_at_date_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import get_kaizen_at_date

    mock_build.return_value = _kaizen_repo(
        get_revision_at={"record_id": _REC, "revision_number": _REV}
    )
    response = get_kaizen_at_date(_REC, date="2026-01-15")
    assert_envelope_meta(body_json(response), operation_id="get_kaizen_at_date")


@patch(f"{_KZ}.build_kaizen_repository")
def test_list_kaizen_audit_log_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import list_kaizen_audit_log

    mock_build.return_value = _kaizen_repo(list_audit_log=[{"event": "created"}])
    response = list_kaizen_audit_log(_REC)
    assert_envelope_meta(body_json(response), operation_id="list_kaizen_audit_log")


@patch(f"{_KZ}.build_kaizen_evidence_repository")
@patch(f"{_KZ}.build_kaizen_repository")
def test_list_kaizen_evidences_returns_meta(mock_record, mock_ev) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import list_kaizen_evidences

    mock_record.return_value = _kaizen_repo()
    mock_ev.return_value = MagicMock(list_evidences=MagicMock(return_value=[]))
    response = list_kaizen_evidences(_REC)
    assert_envelope_meta(body_json(response), operation_id="list_kaizen_evidences")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_KZ}.build_kaizen_evidence_storage")
@patch(f"{_KZ}.build_kaizen_evidence_repository")
@patch(f"{_KZ}.build_kaizen_repository")
async def test_attach_kaizen_evidence_link_returns_meta(
    mock_record_repo, mock_ev_repo, mock_storage, _user
) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import attach_kaizen_evidence

    mock_record_repo.return_value = _kaizen_repo()
    mock_ev_repo.return_value = MagicMock(
        create_evidence=MagicMock(return_value={"id": _EVID, "type": "link"})
    )
    response = await attach_kaizen_evidence(
        _REC,
        evidence_type="link",
        external_url="https://example.com/evidence",
    )
    assert_envelope_meta(body_json(response), operation_id="attach_kaizen_evidence")


@patch(f"{_KZ}.build_kaizen_evidence_storage")
@patch(f"{_KZ}.build_kaizen_evidence_repository")
@patch(f"{_KZ}.build_kaizen_repository")
def test_delete_kaizen_evidence_returns_meta(mock_record, mock_ev_repo, mock_storage) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import delete_kaizen_evidence

    mock_record.return_value = _kaizen_repo()
    mock_ev_repo.return_value = MagicMock(
        delete_evidence=MagicMock(return_value={"stored_name": "file.bin"})
    )
    mock_storage.return_value = MagicMock(delete_file=MagicMock())
    response = delete_kaizen_evidence(_REC, _EVID)
    assert_envelope_meta(body_json(response), operation_id="delete_kaizen_evidence")


@patch(f"{_KZ}.build_kaizen_evidence_repository")
@patch(f"{_KZ}.build_kaizen_repository")
def test_update_kaizen_evidence_returns_meta(mock_record, mock_ev) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        UpdateKaizenEvidenceBody,
        update_kaizen_evidence,
    )

    mock_record.return_value = _kaizen_repo()
    mock_ev.return_value = MagicMock(
        update_evidence=MagicMock(return_value={"id": _EVID, "stage": "antes"})
    )
    response = update_kaizen_evidence(
        _REC, _EVID, body=UpdateKaizenEvidenceBody(stage="antes")
    )
    assert_envelope_meta(body_json(response), operation_id="update_kaizen_evidence")


@pytest.mark.asyncio
@_user_patch()
@patch(f"{_KZ}.build_kaizen_evidence_storage")
@patch(f"{_KZ}.build_kaizen_evidence_repository")
@patch(f"{_KZ}.build_kaizen_repository")
async def test_replace_kaizen_evidence_file_returns_meta(
    mock_record, mock_ev_repo, mock_storage, _user
) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        replace_kaizen_evidence_file,
    )

    mock_record.return_value = _kaizen_repo()
    mock_ev_repo.return_value = MagicMock(
        get_evidence=MagicMock(
            return_value={"id": _EVID, "type": "photo", "stored_name": "old.bin"}
        ),
        update_evidence=MagicMock(
            return_value={"id": _EVID, "stored_name": "new.bin", "type": "photo"}
        ),
    )
    mock_storage.return_value = MagicMock(
        save=MagicMock(return_value="new.bin"),
        delete_file=MagicMock(),
    )
    upload = MagicMock()
    upload.filename = "foto.jpg"
    upload.content_type = "image/jpeg"
    upload.read = AsyncMock(return_value=b"fake-image-bytes")

    response = await replace_kaizen_evidence_file(_REC, _EVID, file=upload)
    assert_envelope_meta(body_json(response), operation_id="replace_kaizen_evidence_file")
    mock_storage.return_value.delete_file.assert_called_once()


@patch(f"{_KZ}.FileResponse")
@patch(f"{_KZ}.build_kaizen_evidence_storage")
@patch(f"{_KZ}.build_kaizen_evidence_repository")
@patch(f"{_KZ}.build_kaizen_repository")
def test_download_kaizen_evidence_returns_file(
    mock_record, mock_ev_repo, mock_storage, mock_fr
) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import download_kaizen_evidence

    mock_record.return_value = _kaizen_repo()
    mock_ev_repo.return_value = MagicMock(
        get_evidence=MagicMock(return_value={"stored_name": "x.bin", "file_name": "x.bin"})
    )
    mock_storage.return_value = MagicMock(resolve_file=MagicMock(return_value="/tmp/x.bin"))
    mock_fr.return_value = MagicMock(status_code=200)
    response = download_kaizen_evidence(_REC, _EVID)
    assert response is not None
    mock_fr.assert_called_once()


@patch(f"{_KZ}.build_kaizen_repository")
def test_list_kaizen_history_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import list_kaizen_history

    mock_build.return_value = _kaizen_repo(list_history=[{"change": "title"}])
    response = list_kaizen_history(_REC)
    assert_envelope_meta(body_json(response), operation_id="list_kaizen_history")


@patch(f"{_KZ}.build_kaizen_repository")
def test_list_kaizen_revisions_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import list_kaizen_revisions

    mock_build.return_value = _kaizen_repo(list_revisions=[{"revision_number": 1}])
    response = list_kaizen_revisions(_REC)
    assert_envelope_meta(body_json(response), operation_id="list_kaizen_revisions")


@patch(f"{_KZ}.build_kaizen_repository")
def test_get_kaizen_revision_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import get_kaizen_revision

    mock_build.return_value = _kaizen_repo(
        get_revision={"record_id": _REC, "revision_number": _REV}
    )
    response = get_kaizen_revision(_REC, _REV)
    assert_envelope_meta(body_json(response), operation_id="get_kaizen_revision")


@patch(f"{_KZ}.build_kaizen_repository")
def test_get_kaizen_savings_timeline_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        get_kaizen_savings_timeline,
    )

    mock_build.return_value = _kaizen_repo(savings_timeline={"points": []})
    response = get_kaizen_savings_timeline(_REC)
    assert_envelope_meta(body_json(response), operation_id="get_kaizen_savings_timeline")


@_user_patch()
@patch(f"{_KZ}.build_kaizen_repository")
def test_create_kaizen_version_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        KaizenRecordBody,
        create_kaizen_version,
    )

    mock_build.return_value = _kaizen_repo(
        create_version={"id": _REC, "revision_number": 2}
    )
    response = create_kaizen_version(
        _REC,
        body=KaizenRecordBody(branch_code="01", title="Kaizen smoke"),
    )
    assert_envelope_meta(body_json(response), operation_id="create_kaizen_version")


@_user_patch()
@patch(f"{_KZ}.build_kaizen_repository")
def test_delete_kaizen_version_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import delete_kaizen_version

    mock_build.return_value = _kaizen_repo(delete_version=True)
    response = delete_kaizen_version(_REC, _REV)
    assert_envelope_meta(body_json(response), operation_id="delete_kaizen_version")


@_user_patch()
@patch(f"{_KZ}.build_kaizen_repository")
def test_update_kaizen_version_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        UpdateKaizenRecordBody,
        update_kaizen_version,
    )

    mock_build.return_value = _kaizen_repo(
        update_version={"id": _REC, "revision_number": _REV}
    )
    response = update_kaizen_version(
        _REC, _REV, body=UpdateKaizenRecordBody(title="Versão atualizada")
    )
    assert_envelope_meta(body_json(response), operation_id="update_kaizen_version")


@_user_patch()
@patch(f"{_KZ}.build_kaizen_repository")
def test_implement_kaizen_version_returns_meta(mock_build, _user) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import (
        ImplementKaizenVersionBody,
        implement_kaizen_version,
    )

    mock_build.return_value = _kaizen_repo(
        implement_version={"id": _REC, "status": "implantado"}
    )
    response = implement_kaizen_version(
        _REC, _REV, body=ImplementKaizenVersionBody()
    )
    assert_envelope_meta(body_json(response), operation_id="implement_kaizen_version")


@_user_patch()
@patch(f"{_KZ}.branch_access_error", return_value=None)
@patch(f"{_KZ}.build_kaizen_repository")
def test_create_kaizen_record_maps_repository_error(mock_build, _branch, _user) -> None:
    from app.infrastructure.persistence.plugins.plugin_base_repository import (
        PluginsRepositoryError,
    )
    from app.interface.http.routes.quality.kaizen_records_router import (
        KaizenRecordBody,
        create_kaizen_record,
    )

    mock_build.return_value = _kaizen_repo(
        create_record=MagicMock(
            side_effect=PluginsRepositoryError(
                "Falha ao executar comando com retorno no banco de plugins."
            )
        )
    )
    response = create_kaizen_record(
        body=KaizenRecordBody(branch_code="01", title="Kaizen teste"),
    )
    body = body_json(response)
    assert response.status_code == 500
    assert body.get("success") is False
    assert "banco de plugins" in (body.get("message") or "")


@_user_patch()
@patch(f"{_KZ}.branch_access_error", return_value=None)
@patch(f"{_KZ}.build_kaizen_repository")
def test_create_kaizen_record_maps_status_date_error(mock_build, _branch, _user) -> None:
    from app.domain.services.kaizen.kaizen_status_date_rules import KaizenStatusDateError
    from app.interface.http.routes.quality.kaizen_records_router import (
        KaizenRecordBody,
        create_kaizen_record,
    )

    mock_build.return_value = _kaizen_repo(
        create_record=MagicMock(
            side_effect=KaizenStatusDateError(
                "Informe a data de implantação para o status Implantado."
            )
        )
    )
    response = create_kaizen_record(
        body=KaizenRecordBody(
            branch_code="01",
            title="Kaizen implantado",
            status="implantado",
        ),
    )
    body = body_json(response)
    assert response.status_code == 400
    assert body.get("success") is False


@_user_patch()
@patch(f"{_KZ}.branch_access_error", return_value=None)
@patch(f"{_KZ}.build_kaizen_repository")
def test_create_kaizen_version_maps_repository_error(mock_build, _branch, _user) -> None:
    from app.infrastructure.persistence.plugins.plugin_base_repository import (
        PluginsRepositoryError,
    )
    from app.interface.http.routes.quality.kaizen_records_router import (
        KaizenRecordBody,
        create_kaizen_version,
    )

    mock_build.return_value = _kaizen_repo(
        create_version=MagicMock(
            side_effect=PluginsRepositoryError("Versão criada mas não encontrada.")
        )
    )
    response = create_kaizen_version(
        _REC,
        body=KaizenRecordBody(branch_code="01", title="Kaizen smoke"),
    )
    body = body_json(response)
    assert response.status_code == 500
    assert body.get("success") is False
    assert "Versão criada" in (body.get("message") or "")


def test_kaizen_summary_series_registered_before_path_param() -> None:
    from app.interface.http.routes.quality.quality_router import router

    paths = [getattr(route, "path", "") for route in router.routes]
    series_idx = next(
        i for i, path in enumerate(paths) if path.endswith("/kaizens/summary/series")
    )
    by_id_idx = next(i for i, path in enumerate(paths) if "{kaizen_id" in path)
    assert series_idx < by_id_idx


@patch(f"{_KZ}.build_kaizen_repository")
def test_get_kaizen_record_returns_meta(mock_build) -> None:
    from app.interface.http.routes.quality.kaizen_records_router import get_kaizen_record

    mock_build.return_value = _kaizen_repo()
    response = get_kaizen_record(_REC)
    assert_envelope_meta(body_json(response), operation_id="get_kaizen_record")


def test_kaizen_records_static_paths_registered_before_record_id() -> None:
    from app.interface.http.routes.quality.kaizen_records_router import router

    paths = [getattr(route, "path", "") for route in router.routes]
    record_id_idx = next(i for i, path in enumerate(paths) if path.endswith("/{record_id}"))
    for suffix in ("/export", "/import", "/summary", "/savings-investment/series"):
        static_idx = next(i for i, path in enumerate(paths) if path.endswith(suffix))
        assert static_idx < record_id_idx, suffix
