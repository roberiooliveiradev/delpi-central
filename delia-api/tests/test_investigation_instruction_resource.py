"""INT-1 investigation instruction resource — load, fingerprint, rollback."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.infrastructure.config.cri_instruction_resource import (
    CriInstructionResourceError,
    default_investigation_instructions_path,
    load_investigation_instructions,
    resolve_investigation_instruction_version,
)
from app.infrastructure.orchestration import pydantic_ai_investigation as pai


_BASELINE = "generalist-semantic-v2"
_DEFAULT = "generalist-semantic-v2-1-object-continuity"
_CANDIDATE = "generalist-semantic-v3-objective-progress"
_BASELINE_FP = "7dbc94c5035b0f19"
_DEFAULT_FP = "4ebd5260b6cf9ba9"


def test_shipped_resource_loads_and_selects_baseline() -> None:
    bundle = load_investigation_instructions(
        default_investigation_instructions_path()
    )
    assert bundle.default_instruction_version == _DEFAULT
    assert _BASELINE in bundle.instructions
    assert _DEFAULT in bundle.instructions
    assert _CANDIDATE in bundle.instructions
    selected = bundle.select(None)
    assert selected.instruction_version == _DEFAULT
    assert selected.text_fingerprint == _DEFAULT_FP
    assert (
        hashlib.sha256(selected.text.encode()).hexdigest()[:16]
        == _DEFAULT_FP
    )


def test_baseline_text_matches_historical_fingerprint() -> None:
    """Extraction must not alter generalist-semantic-v2 content."""
    selected = pai.load_selected_investigation_instructions(
        instruction_version=_BASELINE
    )
    assert selected.text_fingerprint == _BASELINE_FP
    # Module compatibility exports expose the *default* at import.
    assert pai._INVESTIGATION_INSTRUCTION_VERSION == _DEFAULT
    assert (
        hashlib.sha256(
            pai._INVESTIGATION_INSTRUCTIONS.encode()
        ).hexdigest()[:16]
        == _DEFAULT_FP
    )


def test_candidate_select_via_env(monkeypatch) -> None:
    bundle = load_investigation_instructions(
        default_investigation_instructions_path()
    )
    monkeypatch.setenv(
        "DELIA_INVESTIGATION_INSTRUCTION_VERSION", _CANDIDATE
    )
    assert resolve_investigation_instruction_version() == _CANDIDATE
    selected = bundle.select(resolve_investigation_instruction_version())
    assert selected.instruction_version == _CANDIDATE
    assert selected.text_fingerprint == "658d3da51783e23d"
    assert selected.text_fingerprint != _BASELINE_FP


def test_rollback_to_baseline_via_explicit_version() -> None:
    selected = pai.load_selected_investigation_instructions(
        instruction_version=_BASELINE
    )
    assert selected.instruction_version == _BASELINE
    assert selected.text_fingerprint == _BASELINE_FP


def test_unknown_version_fail_closed() -> None:
    with pytest.raises(CriInstructionResourceError) as exc:
        pai.load_selected_investigation_instructions(
            instruction_version="does-not-exist"
        )
    assert exc.value.code == "investigation_instruction_version_unknown"


def test_resource_reject_missing_default(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(
        json.dumps(
            {
                "resource_id": "delia.investigation.instructions",
                "kind": "investigation_instructions",
                "version": "1",
                "owner": "DELPI",
                "default_instruction_version": "missing-key",
                "instructions": {"other": "text " * 20},
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(CriInstructionResourceError):
        load_investigation_instructions(path)


def test_candidate_is_provider_agnostic() -> None:
    text = load_investigation_instructions(
        default_investigation_instructions_path()
    ).instructions[_CANDIDATE]
    lowered = text.casefold()
    for token in ("davi.", "teo.", "vista.", " for davi", " for teo"):
        assert token not in lowered


def test_ablation_variants_load_distinct_fingerprints() -> None:
    bundle = load_investigation_instructions(
        default_investigation_instructions_path()
    )
    names = (
        "generalist-semantic-ablation-obj-v1",
        "generalist-semantic-ablation-prog-v1",
        "generalist-semantic-ablation-disc-v1",
    )
    fps = {n: bundle.select(n).text_fingerprint for n in names}
    assert fps["generalist-semantic-ablation-obj-v1"] == "d455ef41408ccdea"
    assert fps["generalist-semantic-ablation-prog-v1"] == "7d38c1237ea79909"
    assert fps["generalist-semantic-ablation-disc-v1"] == "30d80637559e6ec8"
    assert len(set(fps.values())) == 3
    assert bundle.default_instruction_version == _DEFAULT


def test_inline_instruction_constant_removed_from_source() -> None:
    """After isolation, the long prose must not live as a Python literal."""
    module_path = Path(pai.__file__).resolve()
    source = module_path.read_text(encoding="utf-8")
    assert "You are DÉLIA's generalist semantic investigation agent" not in source
    assert "load_selected_investigation_instructions" in source
    assert "investigation_instructions.delpi.json" in source
