"""E9.S2 — baseline offline no corpus v1 (mesmo datasetHash do E9.S1)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS = _ROOT / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json"
_EVIDENCE = (
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/e9-s2-baseline-offline-v1/manifest.json"
)

_DATASET_HASH = "371f0cfa802188c805f986ff15452e152a5f98e636132fa81145fad7cfcf26b8"


def test_e9_s2_baseline_manifest_matches_corpus_hash():
    raw = _CORPUS.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _DATASET_HASH

    manifest = json.loads(_EVIDENCE.read_text(encoding="utf-8"))
    assert manifest.get("datasetHash") == _DATASET_HASH
    assert manifest.get("datasetVersion") == "intelligence_baseline/r1_r11_corpus_v1"
    assert manifest.get("role") == "BASELINE"
    assert manifest.get("liveLlm") is False
    assert int((manifest.get("summary") or {}).get("exitCode", 1)) == 0
    assert int((manifest.get("summary") or {}).get("failed", 1)) == 0
