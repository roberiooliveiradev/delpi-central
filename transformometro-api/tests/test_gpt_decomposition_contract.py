"""Decomposition contract discovery — TÉO must be able to learn the
canonical ``decomposition_tree_v1`` write contract without guessing
enums, and PREPARE must surface structural errors before an auto_act
proposal is advertised as executable.

Regression: the MCP/Actions catalog could exceed the response budget
(``catalog_budget_trimmed``), and ``entity_schemas`` carried the level
enum only inside prose notes — so the agent produced ``level`` values
(``None``/``0``/``1``/``"processo"``) that the domain validator correctly
rejected at COMMIT. The targeted ``entity`` catalog parameter and the
machine-readable ``enums`` entries make the contract retrievable; the
PREPARE document validation marks bad payloads ``ready=false`` early.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.application.gpt_actions.governed_actions_facade import (
    GovernedActionsFacade,
)
from tm_app.application.gpt_actions.openapi_builder import (
    build_gpt_actions_openapi,
)
from tm_app.application.gpt_actions.registration_guide import (
    build_registration_guide,
)
from tm_app.domain.decomposition.decomposition_tree_v1 import (
    HIGHLIGHTS,
    NODE_LEVELS,
)


@pytest.fixture(autouse=True)
def _reset_proposals():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _user(uid="u1"):
    return SimpleNamespace(
        id=uid,
        email=f"{uid}@example.com",
        name="User",
        permissions=["transformometro.access", "transformometro.manage"],
        roles=[],
        groups=[],
        is_superadmin=False,
    )


def _request(uid="u1"):
    req = MagicMock()
    req.state.user = _user(uid)
    return req


def _tree(**overrides):
    doc = {
        "format": "decomposition_tree_v1",
        "format_version": 1,
        "nodes": [
            {"id": "pk_1", "level": "processo_chave", "ordem": 1, "label": "Preparação"},
            {
                "id": "t_1",
                "level": "tarefa",
                "ordem": 1,
                "label": "Registrar produto",
                "parent_id": "pk_1",
            },
            {
                "id": "st_1",
                "level": "sub_tarefa",
                "ordem": 1,
                "label": "Conferir ficha",
                "parent_id": "t_1",
            },
        ],
    }
    doc.update(overrides)
    return doc


from contextlib import contextmanager


@contextmanager
def _catalog_repos():
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.FilialRepository"
        ) as filial_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
        ) as setor_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
        ) as proc_cls,
    ):
        filial_cls.return_value.list_for_options.return_value = []
        setor_cls.return_value.list_for_options.return_value = []
        proc_cls.return_value.list_distinct_tag_values.return_value = []
        yield


def test_entity_schemas_expose_level_enum_machine_readably():
    guide = build_registration_guide()
    schema = guide["entity_schemas"]["decomposition_tree"]
    levels = schema["enums"]["conteudo.nodes[].level"]
    assert set(levels) == set(NODE_LEVELS)
    assert levels == sorted(levels)
    assert schema["enums"]["conteudo.format"] == ["decomposition_tree_v1"]

    overlay = guide["entity_schemas"]["revision_decomposition_overlay"]
    assert set(overlay["enums"]["conteudo.node_overrides[].highlight"]) == set(
        HIGHLIGHTS
    )
    assert overlay["enums"]["conteudo.format"] == ["decomposition_overlay_v1"]


def test_catalog_entity_param_returns_targeted_schema(tm_client):
    with _catalog_repos():
        response = tm_client.get(
            "/transformometro/gpt-actions/v1/catalog?entity=decomposition_tree"
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["entity"] == "decomposition_tree"
    schema = data["entity_schema"]
    assert set(schema["enums"]["conteudo.nodes[].level"]) == set(NODE_LEVELS)
    assert "conteudo" in schema["required"]
    assert data["concept"]
    assert data["write_contract_rules"]["entity_write_flow"]
    # Targeted mode is intentionally small — no full-catalog bulk keys.
    assert "diagram_catalog" not in data
    assert "familias_processo" not in data


def test_catalog_entity_param_unknown_entity_typed_error(tm_client):
    with _catalog_repos():
        response = tm_client.get(
            "/transformometro/gpt-actions/v1/catalog?entity=mapeamento"
        )
    assert response.status_code == 400
    payload = response.json()
    blob = str(payload).lower()
    assert "decomposition_tree" in blob or "valid_entities" in blob


def test_catalog_entity_param_in_openapi():
    doc = build_gpt_actions_openapi()
    params = doc["paths"]["/transformometro/gpt-actions/v1/catalog"]["get"]["parameters"]
    entity_param = next(p for p in params if p["name"] == "entity")
    assert entity_param["in"] == "query"
    assert entity_param["required"] is False


def test_full_catalog_still_complete_without_entity_param(tm_client):
    with _catalog_repos():
        response = tm_client.get("/transformometro/gpt-actions/v1/catalog")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "registration_guide" in data
    assert "decomposition_tree" in data["registration_guide"]["entity_schemas"]


def test_prepare_rejects_invalid_tree_level_early():
    """The exact failure TÉO hit: level=1 must surface at PREPARE as
    ready=false/act_allowed=false — never as an auto_act proposal that
    COMMIT then refuses."""
    facade = GovernedActionsFacade()
    bad = _tree()
    bad["nodes"][0]["level"] = 1
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
            return_value=None,
        ),
    ):
        prepared = facade.prepare_record_change(
            _request(),
            entity="decomposition_tree",
            operation="create",
            changes={"processo_id": "proc-1", "conteudo": bad},
        )
    assert prepared["proposal"]["ready"] is False
    assert prepared["proposal"]["act_allowed"] is False
    assert "level" in str(prepared["validation_result"])


def test_prepare_rejects_textual_processo_level():
    facade = GovernedActionsFacade()
    bad = _tree()
    bad["nodes"][0]["level"] = "processo"
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
            return_value=None,
        ),
    ):
        prepared = facade.prepare_record_change(
            _request(),
            entity="decomposition_tree",
            operation="create",
            changes={"processo_id": "proc-1", "conteudo": bad},
        )
    assert prepared["proposal"]["ready"] is False
    assert "level" in str(prepared["validation_result"])


def test_prepare_accepts_valid_multilevel_tree():
    facade = GovernedActionsFacade()
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
            return_value=None,
        ),
    ):
        prepared = facade.prepare_record_change(
            _request(),
            entity="decomposition_tree",
            operation="create",
            changes={"processo_id": "proc-1", "conteudo": _tree()},
        )
    assert prepared["proposal"]["ready"] is True
    assert prepared["proposal"]["act_allowed"] is True


def test_prepare_rejects_structural_errors():
    """Duplicate ids, missing parents and parent/level mismatches are
    caught at PREPARE too — same domain validator as COMMIT."""
    facade = GovernedActionsFacade()
    cases = [
        # duplicate id
        {**_tree(), "nodes": _tree()["nodes"] + [dict(_tree()["nodes"][0])]},
        # parent_id missing for tarefa
        {**_tree(), "nodes": [n for n in _tree()["nodes"] if n["id"] != "pk_1"]},
        # duplicate sibling ordem
        {
            **_tree(),
            "nodes": _tree()["nodes"]
            + [
                {
                    "id": "pk_2",
                    "level": "processo_chave",
                    "ordem": 1,
                    "label": "Outra",
                }
            ],
        },
    ]
    for bad in cases:
        with (
            patch.object(facade._dispatch, "_require_capability"),
            patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ),
        ):
            prepared = facade.prepare_record_change(
                _request(),
                entity="decomposition_tree",
                operation="create",
                changes={"processo_id": "proc-1", "conteudo": bad},
            )
        assert prepared["proposal"]["ready"] is False, bad


def test_prepare_update_validates_overlay():
    facade = GovernedActionsFacade()
    bad = {
        "format": "decomposition_overlay_v1",
        "format_version": 1,
        "node_overrides": {"n1": {"highlight": "invalid"}},
    }
    with (
        patch.object(facade._dispatch, "_require_capability"),
        patch(
            "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
            return_value=None,
        ),
        patch.object(
            facade._dispatch, "get_record", return_value={"id": "rev-1"}
        ),
    ):
        prepared = facade.prepare_record_change(
            _request(),
            entity="revision_decomposition_overlay",
            operation="update",
            record_id="rev-1",
            changes={"conteudo": bad},
        )
    assert prepared["proposal"]["ready"] is False
    assert "highlight" in str(prepared["validation_result"])
