"""R1 (plan 125 / M01): orchestration instructions are a governed
versioned resource, not Python string constants.

Contract under test:
- the resource loads fail-closed through the existing governed
  instruction loader;
- every migrated instruction preserves (instruction key, version,
  sha256 content) exactly — the snapshot below pins the pre-R1
  lineage so silent text drift fails closed;
- the orchestrator consumes the injected mapping and produces the
  same InstructionLineage hash the inline constants produced;
- absent/corrupt/oversized resources never load partially.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.infrastructure.config.cri_instruction_resource import (
    CriInstructionResourceError,
    load_orchestration_instructions,
)
from app.application.capability_provision.orchestration import (
    ARGUMENTS_INSTRUCTION_ID,
    CAPABILITY_GOAL_INSTRUCTION_KEY,
    GOAL_INSTRUCTION_ID,
    ORCHESTRATION_INSTRUCTION_KEYS,
    SELECTION_INSTRUCTION_VERSION,
    OperationalCapabilityOrchestrator,
)

_RESOURCE_PATH = (
    Path(__file__).resolve().parents[1]
    / "config"
    / "orchestration_instructions.delpi.json"
)

# Frozen pre-R1 snapshot: instruction key -> (version, sha256 of the
# exact pre-migration text, byte length). Keys are the typed
# instruction ids; the fused capability+goal variant shares the
# selection id and is keyed distinctly. Any intentional text change
# must bump the resource version and update this map — that is the
# governed-evolution gate, not a bug.
_SNAPSHOT = {
    "delia.capability_orchestration.select_group": (
        "8eb95ebdafe8b33865725f246578d584dcf46e73c660646e35a63452b9196865",
        6776,
    ),
    "delia.capability_orchestration.select_capability": (
        "902a4dc2d4a6984d5349596d83b2630df27c7c310a3be516c5878417d2d56470",
        3808,
    ),
    "delia.capability_orchestration.select_capability#with_goal": (
        "4ab9e249b69913b0254ad339e4b710f36a8065ef12c62a04066878ef81569040",
        4104,
    ),
    "delia.capability_orchestration.index_probe": (
        "5acfbc5f0843e2fa2810f456554caad27f3a5f56df49069371fbeb7731d9539a",
        1195,
    ),
    "delia.capability_orchestration.index_select": (
        "92dad685cd94c4a73ba8ba605d1e9a0a49b8419f75e177f268145a4005bd1c9a",
        1225,
    ),
    "delia.capability_orchestration.arguments": (
        "5f2b656d0fe361e235eee2a09921af39e25a94439fd06e7878c1d6671a5d1d75",
        8186,
    ),
    "delia.capability_orchestration.select_resolver": (
        "d030eb7a0b71d60a7a62c3f0a718e42207c7b0857f6a27e9689498fc63667c4e",
        1181,
    ),
    "delia.capability_orchestration.analysis_continuation": (
        "635fa2810b4b66d1c61ee44f003503ee462a3910b422eb47ccfc426d8d6988f8",
        1208,
    ),
    "delia.capability_orchestration.clarification_wording": (
        "64d2a27f5ab135a3a9e2ea955381ce0bad41343b46e501d21219a07bccd1a4b4",
        1117,
    ),
    "delia.capability_orchestration.grounded_synthesis": (
        "f24b17ddf298766503528e9358c49045a0c8607edd616ecaaf06d356b8d5c859",
        4163,
    ),
    "delia.capability_orchestration.native_assessment": (
        "fcdbd185527595b9083a6c83e97b70ca66adc3728b9b722fc2cb3366ed5ee35f",
        2863,
    ),
    "delia.capability_orchestration.foreign_selection": (
        "6b6dab2fe474723ceb3f5d99b7244ef10472988443102801f325c01bbd4a54d3",
        1850,
    ),
    "delia.capability_orchestration.turn_goal": (
        "44f882de5c3d6fc29951bc72c38ba86083bd706410b9c7fa1a0cfb7f681ddc14",
        3344,
    ),
    "delia.capability_orchestration.comparison": (
        "9a26c820deb88cd2f48b102d7ad8826f993be937ec2d1d6ab77980228149b3bf",
        1346,
    ),
    "delia.capability_orchestration.candidate_arguments": (
        "98b63e1de917d2fb44e534fc271516b56e852f8518d5bf3c84a11733add97dc5",
        2167,
    ),
    "delia.capability_orchestration.select_candidate": (
        "c00fc6d9e76e5aa0620ee4b060165fddb799d9ed50edeb91453417fbe47d7101",
        1211,
    ),
    "delia.capability_orchestration.interaction_admission": (
        "793be681b2dee203626989ddf80e11c64fb835afa21b2914e1c90c71de484f7c",
        4484,
    ),
    "delia.capability_orchestration.goal_evidence_relevance": (
        "14effd87356774e92ba7b6bd77cd825369114d2a52ff091bfb12ae5aa2ba4755",
        2388,
    ),
}


def _load():
    return load_orchestration_instructions(
        _RESOURCE_PATH, required_names=ORCHESTRATION_INSTRUCTION_KEYS
    )


def test_instruction_resource_snapshot_parity():
    """Every migrated instruction keeps (version, sha256) — the
    pre-R1 lineage is byte-for-byte preserved, so the content_hash in
    InstructionLineage cannot drift silently."""
    res = _load()
    assert res.resource_id == "delia.capability_orchestration.instructions"
    assert res.version == "23"
    assert set(res.instructions) == set(_SNAPSHOT)
    for key, (sha, nbytes) in _SNAPSHOT.items():
        text = res.instructions[key]
        assert hashlib.sha256(text.encode("utf-8")).hexdigest() == sha
        assert len(text.encode("utf-8")) == nbytes


def test_instruction_keys_single_sourced():
    """The required key set is declared once in the orchestration
    module — the loader takes it as input, never a second copy."""
    assert set(ORCHESTRATION_INSTRUCTION_KEYS) == set(_SNAPSHOT)
    assert ARGUMENTS_INSTRUCTION_ID == (
        "delia.capability_orchestration.arguments"
    )
    assert CAPABILITY_GOAL_INSTRUCTION_KEY.endswith("#with_goal")


def test_orchestrator_consumes_injected_instructions():
    """Wiring parity: the injected mapping produces the same
    instruction text and lineage the inline constants produced, and
    the governed CRI clause still appends to the goal baselines."""
    res = _load()
    orch = OperationalCapabilityOrchestrator(
        [], orchestration_instructions=res.instructions
    )
    assert orch._goal_instruction == res.instructions[GOAL_INSTRUCTION_ID]
    assert orch._capability_goal_instruction == res.instructions[
        CAPABILITY_GOAL_INSTRUCTION_KEY
    ]

    orch_cri = OperationalCapabilityOrchestrator(
        [],
        orchestration_instructions=res.instructions,
        response_intelligence_enabled=True,
        cri_instruction_clause="GOVERNED_CLAUSE",
        cri_instruction_version=SELECTION_INSTRUCTION_VERSION,
    )
    base = res.instructions[GOAL_INSTRUCTION_ID]
    assert orch_cri._goal_instruction == base + "GOVERNED_CLAUSE"
    assert orch_cri._capability_goal_instruction == (
        res.instructions[CAPABILITY_GOAL_INSTRUCTION_KEY]
        + "GOVERNED_CLAUSE"
    )


@pytest.mark.parametrize(
    "mutator",
    [
        lambda d: d.update(resource_id="delia.bogus.id"),
        lambda d: d.update(kind="bogus"),
        lambda d: d.update(version="99"),
        lambda d: d.update(extra_field=True),
        lambda d: d.pop("owner"),
        lambda d: d["instructions"].pop(
            "delia.capability_orchestration.turn_goal"
        ),
        lambda d: d["instructions"].update(bogus_key="x"),
        lambda d: d["instructions"].update(
            {"delia.capability_orchestration.turn_goal": "  "}
        ),
        lambda d: d["instructions"].update(
            {"delia.capability_orchestration.select_group": "x" * 9000}
        ),
        lambda d: d.update(instructions="not-a-mapping"),
    ],
)
def test_instruction_resource_fail_closed(tmp_path, mutator):
    """Adversarial negatives: identity/kind/version/extra/missing/
    oversized/empty entries never load partially."""
    data = json.loads(_RESOURCE_PATH.read_text(encoding="utf-8"))
    mutator(data)
    target = tmp_path / "bad.delpi.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CriInstructionResourceError):
        load_orchestration_instructions(
            target, required_names=ORCHESTRATION_INSTRUCTION_KEYS
        )


def test_instruction_resource_missing_file_fails_closed(tmp_path):
    with pytest.raises(CriInstructionResourceError):
        load_orchestration_instructions(
            tmp_path / "absent.delpi.json",
            required_names=ORCHESTRATION_INSTRUCTION_KEYS,
        )


def test_instruction_resource_malformed_json_fails_closed(tmp_path):
    target = tmp_path / "corrupt.delpi.json"
    target.write_text("{not json", encoding="utf-8")
    with pytest.raises(CriInstructionResourceError):
        load_orchestration_instructions(
            target, required_names=ORCHESTRATION_INSTRUCTION_KEYS
        )


# ---------------------------------------------------------------------------
# R1 → R2 entry gate: production composition path, never the test
# constructor seam. With at least one provider wired, a missing or
# corrupt instruction resource must suppress governed orchestration on
# the real handler — no partial activation.
# ---------------------------------------------------------------------------


def _composed_handler(monkeypatch, tmp_path, *, resource_content):
    from app.application.model_invocation.invoke_model import InvokeModel
    from app.composition import root_composer
    from app.infrastructure.config.settings import Settings
    from app.infrastructure.interoperability.config import (
        SpecialistConnectionProfile,
    )
    from tests.test_specialist_capability_orchestration import (
        TEST_MODEL_REF,
        FakeProposalModel,
    )

    if resource_content is None:
        target = tmp_path / "absent.delpi.json"  # never created
    else:
        target = tmp_path / "orch.delpi.json"
        target.write_text(resource_content, encoding="utf-8")
    monkeypatch.setattr(
        root_composer, "_ORCHESTRATION_INSTRUCTIONS_PATH", target
    )
    connections = {
        "davi": SpecialistConnectionProfile(
            endpoint="http://davi.example/mcp",
            enabled=True,
            timeout_seconds=1.0,
            exchange_audience="aud-x",
            resource_audience="aud-r",
        )
    }
    return root_composer._compose_turn_handler(
        InvokeModel(FakeProposalModel({})),
        TEST_MODEL_REF,
        None,
        Settings.for_testing(),
        connections,
    )


def test_composer_valid_resource_enables_orchestration(
    monkeypatch, tmp_path
):
    handler = _composed_handler(
        monkeypatch, tmp_path,
        resource_content=_RESOURCE_PATH.read_text(encoding="utf-8"),
    )
    assert handler._capability_orchestration is not None


def test_composer_missing_resource_disables_orchestration(
    monkeypatch, tmp_path, caplog
):
    handler = _composed_handler(
        monkeypatch, tmp_path, resource_content=None
    )
    assert handler._capability_orchestration is None


def test_composer_corrupt_resource_disables_orchestration(
    monkeypatch, tmp_path, caplog
):
    handler = _composed_handler(
        monkeypatch, tmp_path, resource_content="{not json"
    )
    assert handler._capability_orchestration is None


def test_admission_instruction_scopes_conversational_exemption():
    """R7 admission defect regression pin: v18 taught that "N exemplos
    de X" without registration markers (cadastrados/reais/DELPI)
    defaults to conversational/hypothetical — a rule that silently
    contradicted the ambiguous-preference clause and collapsed real
    catalog lookups at admission. The contract may exempt only
    explicitly fictional/invented requests and item types with no
    registered form; record-seeking requests stay on the owner path
    regardless of markers."""
    text = _load().instructions[
        "delia.capability_orchestration.interaction_admission"
    ]
    assert "explicitly fictional or invented examples" in text
    assert "could be a DELPI-registered entity" in text
    assert "ambiguous over hypothetical" in text
