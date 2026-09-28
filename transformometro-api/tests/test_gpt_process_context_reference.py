"""Reference AS-IS semantics for get_process_context (BEHAVIORAL+ADDITIVE).

Canonical rule (V035 + write-side validation): the comparison reference of a
selected scenario is its `revisao_referencia_id` — never the original baseline
and never an implicit fallback. These tests lock baseline / reference / as_is /
scenario / to_be semantics and explicit-selection invariants.
"""

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

from tests.test_gpt_actions import _enter_process_context_patches

PID = "pppppppp-pppp-pppp-pppp-pppppppppppp"
IID = "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii"


def _enter_fixture(stack: ExitStack, iid: str, revisions):
    (
        _view,
        _proc_view,
        _inst_view,
        proc_cls,
        inst_cls,
        rev_cls,
        med_cls,
        inv_cls,
        vin_cls,
        diag_cls,
        decomp_cls,
        cmp_cls,
        _matrix,
        dcomp_cls,
        decomp_comp_cls,
    ) = _enter_process_context_patches(stack)
    stack.enter_context(
        patch(
            "tm_app.application.gpt_actions.process_context_service.filter_rows_for_access",
            side_effect=lambda _req, rows, **_kw: rows,
        )
    )
    proc_cls.return_value.get.return_value = {
        "processo_id": PID,
        "nome_processo": "P",
    }
    inst_cls.return_value.list_by_processo.return_value = [
        {
            "instancia_id": iid,
            "processo_id": PID,
            "codigo_filial": "01",
        }
    ]
    rev_cls.return_value.list_by_processo.return_value = revisions
    med_cls.return_value.get_by_revisao.side_effect = lambda rid: {
        "medicao_id": f"m-{str(rid)[:4]}",
        "revisao_id": rid,
    }
    inv_cls.return_value.list_by_revisao.return_value = []
    vin_cls.return_value.list_by_revisao.return_value = []
    diag_cls.return_value.get.return_value = None
    decomp_cls.return_value.get.return_value = None
    cmp_cls.return_value.compare.return_value = {
        "items": [{"revisao_id": r["revisao_id"]} for r in revisions],
        "total_revisoes": len(revisions),
    }
    dcomp_cls.return_value.compose_for_processo.return_value = {}
    decomp_comp_cls.return_value.compose_for_processo.return_value = {}


def _get_context(request, **kwargs):
    from tm_app.application.gpt_actions.process_context_service import (
        ProcessContextService,
    )

    return ProcessContextService().get_context(request, process_id=PID, **kwargs)


def test_reference_as_is_multi_generation_chain():
    request = MagicMock()
    r0 = "r0000000-0000-0000-0000-000000000000"
    r1 = "r1111111-1111-1111-1111-111111111111"
    r2 = "r2222222-2222-2222-2222-222222222222"
    revisions = [
        {
            "revisao_id": r0,
            "instancia_id": IID,
            "cenario_tipo": "baseline",
            "versao_revisao": "v1.0.0",
            "data_inicio_vigencia": "2026-01-01",
        },
        {
            "revisao_id": r1,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "versao_revisao": "v1.1.0",
            "data_inicio_vigencia": "2026-02-01",
            "revisao_referencia_id": r0,
        },
        {
            "revisao_id": r2,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "versao_revisao": "v2.0.0",
            "data_inicio_vigencia": "2026-03-01",
            "revisao_referencia_id": r1,
        },
    ]

    with ExitStack() as stack:
        _enter_fixture(stack, IID, revisions)
        result = _get_context(request, instance_id=IID, revision_id=r2)

    assert result["selection"]["baseline_revisao_id"] == r0
    assert result["selection"]["reference_revisao_id"] == r1
    assert result["selection"]["scenario_revisao_id"] == r2
    assert result["selection"]["resolved"] is True
    assert result["selection"]["requires_instance_selection"] is False
    assert result["baseline"]["revision"]["revisao_id"] == r0
    assert result["reference"]["revision"]["revisao_id"] == r1
    assert result["reference"]["epistemic_status"] == "OBSERVED"
    assert result["as_is"]["revision"]["revisao_id"] == r1
    assert result["as_is"]["revision"]["versao_revisao"] == "v1.1.0"
    assert result["as_is"]["epistemic_status"] == "OBSERVED"
    assert result["scenario"]["revision"]["revisao_id"] == r2
    assert result["to_be"]["revision"]["revisao_id"] == r2
    # AS-IS measurement belongs to the reference revision, not the baseline.
    assert result["as_is"]["measurement"]["revisao_id"] == r1
    assert result["baseline"]["measurement"]["revisao_id"] == r0
    assert "reference_revision" not in result["data_quality"]["missing"]


def test_reference_direct_baseline_case():
    request = MagicMock()
    r0 = "r0000000-0000-0000-0000-000000000000"
    r1 = "r1111111-1111-1111-1111-111111111111"
    revisions = [
        {
            "revisao_id": r0,
            "instancia_id": IID,
            "cenario_tipo": "baseline",
            "data_inicio_vigencia": "2026-01-01",
        },
        {
            "revisao_id": r1,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-02-01",
            "revisao_referencia_id": r0,
        },
    ]

    with ExitStack() as stack:
        _enter_fixture(stack, IID, revisions)
        result = _get_context(request, revision_id=r1)

    assert result["selection"]["baseline_revisao_id"] == r0
    assert result["selection"]["reference_revisao_id"] == r0
    assert result["selection"]["scenario_revisao_id"] == r1
    assert result["as_is"]["revision"]["revisao_id"] == r0
    assert result["to_be"]["revision"]["revisao_id"] == r1
    # baseline == reference here: measurement flagged once, no duplicate noise.
    assert "reference_measurement" not in result["data_quality"]["missing"]


def test_scenario_without_reference_has_no_baseline_fallback():
    request = MagicMock()
    r0 = "r0000000-0000-0000-0000-000000000000"
    r1 = "r1111111-1111-1111-1111-111111111111"
    revisions = [
        {
            "revisao_id": r0,
            "instancia_id": IID,
            "cenario_tipo": "baseline",
            "data_inicio_vigencia": "2026-01-01",
        },
        {
            "revisao_id": r1,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-02-01",
        },
    ]

    with ExitStack() as stack:
        _enter_fixture(stack, IID, revisions)
        result = _get_context(request, revision_id=r1)

    assert result["selection"]["baseline_revisao_id"] == r0
    assert result["selection"]["reference_revisao_id"] is None
    assert result["selection"]["scenario_revisao_id"] == r1
    assert "reference_revision" in result["data_quality"]["missing"]
    assert result["reference"]["revision"] is None
    assert result["as_is"]["revision"] is None
    assert result["as_is"]["epistemic_status"] == "UNKNOWN"
    # Baseline remains visible but is not promoted to AS-IS.
    assert result["baseline"]["revision"]["revisao_id"] == r0


def test_reference_out_of_scope_is_not_exposed():
    request = MagicMock()
    other_iid = "oooooooo-oooo-oooo-oooo-oooooooooooo"
    r0 = "r0000000-0000-0000-0000-000000000000"
    r1 = "r1111111-1111-1111-1111-111111111111"
    foreign = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    revisions = [
        {
            "revisao_id": r0,
            "instancia_id": IID,
            "cenario_tipo": "baseline",
            "data_inicio_vigencia": "2026-01-01",
        },
        {
            "revisao_id": r1,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-02-01",
            "revisao_referencia_id": foreign,
        },
        {
            "revisao_id": foreign,
            "instancia_id": other_iid,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-02-01",
        },
    ]

    with ExitStack() as stack:
        _enter_fixture(stack, IID, revisions)
        result = _get_context(request, instance_id=IID, revision_id=r1)

    assert result["selection"]["reference_revisao_id"] is None
    assert "reference_revision" in result["data_quality"]["missing"]
    assert (
        "reference_revision_out_of_scope" in result["data_quality"]["warnings"]
    )
    assert result["reference"]["revision"] is None
    assert result["as_is"]["revision"] is None
    assert result["as_is"]["epistemic_status"] == "UNKNOWN"
    exposed_revision_ids = {r["revisao_id"] for r in result["revisions"]} | {
        (result[key]["revision"] or {}).get("revisao_id")
        for key in ("baseline", "reference", "scenario", "as_is", "to_be")
        if result[key].get("revision")
    }
    assert foreign not in exposed_revision_ids


def test_explicit_baseline_not_substituted_by_scenario():
    request = MagicMock()
    r0 = "r0000000-0000-0000-0000-000000000000"
    r1 = "r1111111-1111-1111-1111-111111111111"
    revisions = [
        {
            "revisao_id": r0,
            "instancia_id": IID,
            "cenario_tipo": "baseline",
            "data_inicio_vigencia": "2026-01-01",
        },
        {
            "revisao_id": r1,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-02-01",
            "revisao_referencia_id": r0,
            "revisao_ativa": True,
        },
    ]

    with ExitStack() as stack:
        _enter_fixture(stack, IID, revisions)
        result = _get_context(request, instance_id=IID, revision_id=r0)

    # Explicit baseline selection is never silently swapped for a scenario.
    assert result["selection"]["revision_id"] == r0
    assert result["selection"]["baseline_revisao_id"] == r0
    assert result["selection"]["reference_revisao_id"] is None
    assert result["selection"]["scenario_revisao_id"] is None
    assert result["baseline"]["revision"]["revisao_id"] == r0
    assert result["as_is"]["revision"]["revisao_id"] == r0
    assert result["to_be"]["revision"] is None
    assert result["to_be"]["epistemic_status"] == "UNKNOWN"


def test_explicit_inactive_scenario_still_wins():
    request = MagicMock()
    r0 = "r0000000-0000-0000-0000-000000000000"
    r1 = "r1111111-1111-1111-1111-111111111111"
    r2 = "r2222222-2222-2222-2222-222222222222"
    revisions = [
        {
            "revisao_id": r0,
            "instancia_id": IID,
            "cenario_tipo": "baseline",
            "data_inicio_vigencia": "2026-01-01",
        },
        {
            "revisao_id": r1,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-02-01",
            "revisao_referencia_id": r0,
            "revisao_ativa": False,
        },
        {
            "revisao_id": r2,
            "instancia_id": IID,
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-03-01",
            "revisao_referencia_id": r1,
            "revisao_ativa": True,
        },
    ]

    with ExitStack() as stack:
        _enter_fixture(stack, IID, revisions)
        result = _get_context(request, instance_id=IID, revision_id=r1)

    assert result["selection"]["scenario_revisao_id"] == r1
    assert result["selection"]["reference_revisao_id"] == r0
    assert result["as_is"]["revision"]["revisao_id"] == r0
    assert result["to_be"]["revision"]["revisao_id"] == r1
