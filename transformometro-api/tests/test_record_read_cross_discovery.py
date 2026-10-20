"""Cross-Entity Discovery V1 — record_read search extensions.

Additive filters for instance/revision/measurement/process discovery
through the single canonical `record_read` surface (same use cases for
GPT Actions and MCP — tested at the transport-neutral dispatch layer).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)

_DISPATCH = "tm_app.application.gpt_actions.dispatch_service"


def _user(permissions: list[str] | None = None):
    return SimpleNamespace(
        id="user-1",
        permissions=(
            ["transformometro.access"] if permissions is None else permissions
        ),
    )


def _request(permissions: list[str] | None = None):
    req = MagicMock()
    req.state.user = _user(permissions)
    return req


def _svc() -> GptActionsDispatchService:
    return GptActionsDispatchService()


# --- instance discovery ---------------------------------------------------


def test_instance_cross_process_search_uses_list_filtered():
    svc = _svc()
    rows = [{"instancia_id": "i1", "fase_melhoria": "piloto"}]
    with patch(
        f"{_DISPATCH}.ProcessoInstanciaRepository"
    ) as repo_cls:
        repo_cls.return_value.list_filtered.return_value = rows
        out = svc.search_records(
            _request(), "instance", fase_melhoria="piloto"
        )
    repo_cls.return_value.list_filtered.assert_called_once()
    call = repo_cls.return_value.list_filtered.call_args.kwargs
    assert call["fase_melhoria"] == "piloto"
    assert call["processo_id"] is None
    assert out["total"] == 1
    assert out["items"][0]["instancia_id"] == "i1"


def test_instance_parent_scoped_search_preserved():
    svc = _svc()
    with patch(
        f"{_DISPATCH}.ProcessoInstanciaRepository"
    ) as repo_cls:
        repo_cls.return_value.list_filtered.return_value = []
        svc.search_records(_request(), "instance", parent_id="proc-uuid")
    assert (
        repo_cls.return_value.list_filtered.call_args.kwargs["processo_id"]
        == "proc-uuid"
    )


def test_instance_search_combines_org_and_phase_filters():
    svc = _svc()
    with (
        patch(f"{_DISPATCH}.ProcessoInstanciaRepository") as repo_cls,
        patch(f"{_DISPATCH}.SetorRepository") as setor_cls,
        patch(
            f"{_DISPATCH}.check_view_filial_access", return_value=None
        ),
    ):
        setor_cls.return_value.get.return_value = {"codigo_setor": "COM"}
        repo_cls.return_value.list_filtered.return_value = []
        svc.search_records(
            _request(),
            "instance",
            filial_id="filial-uuid",
            setor_id="setor-uuid",
            fase_melhoria="implantado",
            status_instancia="ativo",
            q="setup",
            date_field="data_alvo_go_live",
            date_from="2026-10-01",
            date_to="2026-10-31",
        )
    call = repo_cls.return_value.list_filtered.call_args.kwargs
    assert call["filial_ref"] == "filial-uuid"
    assert call["setor_ref"] == "COM"
    assert call["fase_melhoria"] == "implantado"
    assert call["status_instancia"] == "ativo"
    assert call["q"] == "setup"
    assert call["date_field"] == "data_alvo_go_live"
    assert call["date_from"] == "2026-10-01"
    assert call["date_to"] == "2026-10-31"


def test_instance_search_rejects_bad_phase_enum():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(_request(), "instance", fase_melhoria="bogus")
    assert exc.value.status_code == 400


def test_instance_search_rejects_disallowed_filter():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(
            _request(), "instance", action="search", unit_code="01"
        )
    assert exc.value.status_code == 400
    assert exc.value.data["error_code"] == "INVALID_FIELD"


# --- revision discovery ---------------------------------------------------


def test_revision_cross_process_search_by_cenario_and_active():
    svc = _svc()
    rows = [{"revisao_id": "r1", "cenario_tipo": "automacao"}]
    with patch(f"{_DISPATCH}.RevisaoRepository") as repo_cls:
        repo_cls.return_value.list_filtered.return_value = rows
        out = svc.search_records(
            _request(),
            "revision",
            cenario_tipo="automacao",
            revisao_ativa="true",
            date_field="data_inicio_vigencia",
            date_from="2026-10-01",
        )
    call = repo_cls.return_value.list_filtered.call_args.kwargs
    assert call["cenario_tipo"] == "automacao"
    assert call["revisao_ativa"] is True
    assert call["date_field"] == "data_inicio_vigencia"
    assert call["date_from"] == "2026-10-01"
    assert out["total"] == 1


def test_revision_instance_scoped_search_preserved():
    svc = _svc()
    with patch(f"{_DISPATCH}.RevisaoRepository") as repo_cls:
        repo_cls.return_value.list_filtered.return_value = []
        svc.search_records(_request(), "revision", instance_id="inst-1")
    assert (
        repo_cls.return_value.list_filtered.call_args.kwargs["instancia_id"]
        == "inst-1"
    )


def test_revision_parent_scoped_search_preserved():
    svc = _svc()
    with patch(f"{_DISPATCH}.RevisaoRepository") as repo_cls:
        repo_cls.return_value.list_filtered.return_value = []
        svc.search_records(_request(), "revision", parent_id="proc-1")
    assert (
        repo_cls.return_value.list_filtered.call_args.kwargs["processo_id"]
        == "proc-1"
    )


def test_revision_rejects_unlisted_date_field():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(
            _request(),
            "revision",
            date_field="deletado",
            date_from="2026-01-01",
        )
    assert exc.value.status_code == 400


def test_revision_rejects_date_range_without_field():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(_request(), "revision", date_from="2026-01-01")
    assert exc.value.status_code == 400


def test_revision_rejects_inverted_date_range():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(
            _request(),
            "revision",
            date_field="created_at",
            date_from="2026-12-01",
            date_to="2026-01-01",
        )
    assert exc.value.status_code == 400


# --- measurement discovery ------------------------------------------------


def test_measurement_parent_scoped_search_preserved():
    svc = _svc()
    with patch(f"{_DISPATCH}.MedicaoRepository") as repo_cls:
        repo_cls.return_value.get_by_revisao.return_value = {
            "medicao_id": "m1"
        }
        out = svc.search_records(_request(), "measurement", parent_id="rev-1")
    repo_cls.return_value.get_by_revisao.assert_called_once_with("rev-1")
    assert out["total"] == 1


def test_measurement_cross_search_with_date_range():
    svc = _svc()
    rows = [{"medicao_id": "m1"}, {"medicao_id": "m2"}]
    with patch(f"{_DISPATCH}.MedicaoRepository") as repo_cls:
        repo_cls.return_value.list_filtered.return_value = rows
        out = svc.search_records(
            _request(),
            "measurement",
            date_field="created_at",
            date_from="2026-10-01",
            date_to="2026-10-31",
        )
    call = repo_cls.return_value.list_filtered.call_args.kwargs
    assert call["date_field"] == "created_at"
    assert out["total"] == 2


def test_measurement_search_denied_without_view_permission():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(
            _request(permissions=[]), "measurement", parent_id="rev-1"
        )
    assert exc.value.status_code == 403


def test_measurement_rejects_parent_only_filters():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.record_read(
            _request(), "measurement", action="search", q="texto"
        )
    assert exc.value.status_code == 400


# --- process has_improvement ----------------------------------------------


def test_process_has_improvement_pushes_to_repository():
    svc = _svc()
    with (
        patch(f"{_DISPATCH}.ProcessoRepository") as repo_cls,
        patch(
            f"{_DISPATCH}.ProcessoSetupStatsService"
        ) as stats_cls,
    ):
        repo_cls.return_value.list.return_value = []
        stats_cls.return_value.enrich_processos.side_effect = (
            lambda rows: rows
        )
        svc.search_records(
            _request(), "process", has_improvement="true"
        )
    assert (
        repo_cls.return_value.list.call_args.kwargs["has_improvement"]
        is True
    )


# --- pagination ------------------------------------------------------------


def test_pagination_adds_typed_block_and_slices():
    svc = _svc()
    rows = [{"instancia_id": f"i{n}"} for n in range(5)]
    with patch(f"{_DISPATCH}.ProcessoInstanciaRepository") as repo_cls:
        repo_cls.return_value.list_filtered.return_value = rows
        out = svc.search_records(
            _request(), "instance", page="2", page_size="2"
        )
    assert out["total"] == 5
    assert [i["instancia_id"] for i in out["items"]] == ["i2", "i3"]
    assert out["pagination"] == {
        "page": 2,
        "page_size": 2,
        "has_more": True,
    }


def test_unpaginated_search_keeps_legacy_shape():
    svc = _svc()
    with patch(f"{_DISPATCH}.ProcessoInstanciaRepository") as repo_cls:
        repo_cls.return_value.list_filtered.return_value = []
        out = svc.search_records(_request(), "instance")
    assert "pagination" not in out
    assert out["total"] == 0


def test_page_size_above_max_rejected():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(
            _request(), "instance", page="1", page_size="41"
        )
    assert exc.value.status_code == 400


def test_page_rejects_non_integer():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(_request(), "instance", page="abc")
    assert exc.value.status_code == 400


# --- authz -----------------------------------------------------------------


def test_cross_process_search_denied_without_view_permission():
    svc = _svc()
    with pytest.raises(GptActionsError) as exc:
        svc.search_records(_request(permissions=[]), "instance")
    assert exc.value.status_code == 403
