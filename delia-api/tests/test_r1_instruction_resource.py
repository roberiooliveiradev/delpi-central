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
        "fd53f920b00b1b4721dcff4039d44279b8a756ca3ec5a7a3f5188f3c0597c86b",
        4590,
    ),
    "delia.capability_orchestration.select_capability": (
        "3d6bc40ec5f07697b99f89cbd62b48937f8c4bb0ecf8ecd8bb071229a59870be",
        2838,
    ),
    "delia.capability_orchestration.select_capability#with_goal": (
        "1b4c0a376870c6d4262604e8d3499901082d800b027959a53e38b697b634d9c2",
        3414,
    ),
    "delia.capability_orchestration.index_probe": (
        "5acfbc5f0843e2fa2810f456554caad27f3a5f56df49069371fbeb7731d9539a",
        1195,
    ),
    "delia.capability_orchestration.index_select": (
        "60180b058aac1a5e8edb2adeb68fc440663b6cc73b7224321dfa1e4a72b174ed",
        989,
    ),
    "delia.capability_orchestration.arguments": (
        "aa5d338f2a2464d7133097739797a0f83231727e506402282fbde71fad3b3e85",
        5176,
    ),
    "delia.capability_orchestration.select_resolver": (
        "2864d08fccfd4f87b52041c1fe572abfe1768d01489a81b8aa6e8d216bcf9b57",
        927,
    ),
    "delia.capability_orchestration.analysis_continuation": (
        "7e0c74e4b19450b8bab0ef45dd5b49612641475785cafeca973a533554f02be8",
        954,
    ),
    "delia.capability_orchestration.clarification_wording": (
        "c4658693e0adf352d3ad4c32e04f6e71a4fe2576aba23ab6368ad3fd7cf0e347",
        891,
    ),
    "delia.capability_orchestration.grounded_synthesis": (
        "78186ca4040fe0cff0e1c7379fcc0586c06dc13aecc1ff9190fffb8d148642a9",
        3851,
    ),
    "delia.capability_orchestration.native_assessment": (
        "c86f7fc613906321d391ca84bc2c066ce5d9ab3a1f08239d0e7d04f35fa6c72c",
        1029,
    ),
    "delia.capability_orchestration.foreign_selection": (
        "afb1a67d48f58010c42409f28f3a5015874e426f2b2a389eda06144057bc52e0",
        757,
    ),
    "delia.capability_orchestration.turn_goal": (
        "d3d698d22cc7d6fd8d48e6290b6bd169c272f54027a86c5cc56d40d569999497",
        3216,
    ),
    "delia.capability_orchestration.comparison": (
        "ff44ae46838b8febac48388eee73efbec1f64637df8a6a44197b4db4bb8aa315",
        1067,
    ),
    "delia.capability_orchestration.candidate_arguments": (
        "9e9e827c57eab1d07747286d5fc0235edc0fbe3c8229ca443df2af213106dd23",
        758,
    ),
    "delia.capability_orchestration.select_candidate": (
        "97eb592d4d0b9a733bf6d3a5f243704c42885e48a6870495354cb71cec2ca8d7",
        558,
    ),
    "delia.capability_orchestration.interaction_admission": (
        "1e4594d1ca7b4ebda39350a27623ca4af9fbc1d34e4190843958f79ff4f58174",
        4176,
    ),
    "delia.capability_orchestration.goal_evidence_relevance": (
        "cd753bdd55ef6b1bf8fdfb7dc78781c6690d46806de9810709e9aaf4ca8fecb7",
        1171,
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
    assert res.version == "5"
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
