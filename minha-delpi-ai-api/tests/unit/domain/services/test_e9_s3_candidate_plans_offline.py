"""E9.S3 — mapa candidate por plano + manifesto no mesmo datasetHash."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]
_MAP = _ROOT / "tests/fixtures/intelligence_baseline/e9_s3_plan_candidate_map.json"
_CORPUS = _ROOT / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json"
_MANIFEST = (
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/e9-s3-candidate-plans-offline-v1/manifest.json"
)
_DATASET_HASH = "371f0cfa802188c805f986ff15452e152a5f98e636132fa81145fad7cfcf26b8"


def test_e9_s3_map_covers_plans_01_to_08():
    mapping = json.loads(_MAP.read_text(encoding="utf-8"))
    assert mapping["datasetHash"] == _DATASET_HASH
    assert hashlib.sha256(_CORPUS.read_bytes()).hexdigest() == _DATASET_HASH
    plan_ids = [str(plan["planId"]) for plan in mapping["plans"]]
    assert plan_ids == [f"{i:02d}" for i in range(1, 9)]
    for plan in mapping["plans"]:
        assert plan.get("harnessRefs")
        for ref in plan["harnessRefs"]:
            assert (_ROOT / ref).is_file(), ref


def test_e9_s3_candidate_manifest_no_global_pass_with_deferred_dims():
    manifest = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    assert manifest["datasetHash"] == _DATASET_HASH
    assert manifest["role"] == "CANDIDATE"
    assert manifest["globalPass"] is False
    assert manifest["globalPassForbiddenWithDeferredDims"] is True
    assert manifest["aggregateStatus"] == "PASS_OFFLINE_WITH_INCONCLUSIVE_DIMS"
    assert len(manifest["plans"]) == 8
    assert all(plan.get("decision") == "NO_REGRESSION_OFFLINE" for plan in manifest["plans"])
    assert all(plan.get("pytest", {}).get("failed", 1) == 0 for plan in manifest["plans"])
