"""E9.S1 — cobertura do corpus R1–R11 ampliado (índice imutável, sem live LLM)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS = _ROOT / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json"
_ONDA_A = (
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/onda-a-baseline/manifest.json"
)

_REQUIRED_CLASSES = set(range(1, 21))


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def test_e9_s1_corpus_covers_all_twenty_classes():
    corpus = json.loads(_CORPUS.read_text(encoding="utf-8"))
    assert corpus.get("datasetVersion") == "intelligence_baseline/r1_r11_corpus_v1"
    cases = corpus.get("cases") or []
    assert len(cases) == 20

    class_ids = {int(case["classId"]) for case in cases}
    assert class_ids == _REQUIRED_CLASSES

    ids = [str(case["id"]) for case in cases]
    assert len(ids) == len(set(ids))


def test_e9_s1_harness_refs_resolve():
    corpus = json.loads(_CORPUS.read_text(encoding="utf-8"))
    missing: list[str] = []
    for case in corpus.get("cases") or []:
        ref = str(case.get("harnessRef") or "").strip()
        path = _ROOT / ref
        if not path.is_file():
            missing.append(f"{case.get('id')}: {ref}")
    assert missing == [], missing


def test_e9_s1_onda_a_baseline_untouched():
    """Negative: freeze Onda A permanece imutável e com corpus estreito."""

    manifest = json.loads(_ONDA_A.read_text(encoding="utf-8"))
    assert manifest.get("immutable") is True
    assert manifest.get("runId") == "0249db78-d6fd-45b3-84bf-d11abcd17a6a"
    assert "routing_cases.json@v1" in str(manifest.get("datasetVersion") or "")


def test_e9_s1_dataset_hash_stable_for_freeze():
    raw = _CORPUS.read_bytes()
    digest = _sha256_bytes(raw)
    # Freeze E9.S1 — alterar corpus exige novo datasetVersion + evidência.
    assert digest == (
        "371f0cfa802188c805f986ff15452e152a5f98e636132fa81145fad7cfcf26b8"
    )