"""J-R3 — evidence reproducibility (runner ↔ manifest)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.domain.services.chat_evidence_reproducibility_service import (
    ChatEvidenceReproducibilityService,
)

_ROOT = Path(__file__).resolve().parents[4]
_OFFLINE_MANIFEST = (
    _ROOT
    / "docs/roadmap/llm-json-decoupling/evidence/e11-s9-final-candidate-offline-v1/manifest.json"
)


class TestJR3EvidenceReproducibility(unittest.TestCase):
    def test_negative_true_with_reason_fails(self) -> None:
        manifest = {
            "role": "FINAL_CANDIDATE_OFFLINE",
            "liveLlm": False,
            "globalReleasePass": True,
            "reasonGlobalReleasePassFalse": "live deferred",
            "liveDeferred": {"R8_live_latency_p50_p95": "DEFERRED_LIVE"},
        }
        finding = ChatEvidenceReproducibilityService.validate_manifest(manifest)
        self.assertFalse(finding.ok)
        self.assertFalse(finding.expected_global_release_pass)

    def test_positive_aligned_false_passes(self) -> None:
        manifest = {
            "role": "FINAL_CANDIDATE_OFFLINE",
            "liveLlm": False,
            "globalReleasePass": False,
            "reasonGlobalReleasePassFalse": "live deferred",
            "liveDeferred": {"R8_live_latency_p50_p95": "DEFERRED_LIVE"},
        }
        finding = ChatEvidenceReproducibilityService.validate_manifest(manifest)
        self.assertTrue(finding.ok)
        self.assertFalse(finding.expected_global_release_pass)

    def test_sibling_align_rewrites_contradiction(self) -> None:
        manifest = {
            "role": "FINAL_CANDIDATE_OFFLINE",
            "liveLlm": False,
            "globalReleasePass": True,
            "reasonGlobalReleasePassFalse": "cannot close offline",
            "liveDeferred": {"R7": "DEFERRED_LIVE"},
        }
        aligned = ChatEvidenceReproducibilityService.align_global_release_pass(manifest)
        self.assertFalse(aligned["globalReleasePass"])
        finding = ChatEvidenceReproducibilityService.validate_manifest(aligned)
        self.assertTrue(finding.ok)

    def test_offline_manifest_on_disk_is_consistent_after_j_r3(self) -> None:
        data = json.loads(_OFFLINE_MANIFEST.read_text(encoding="utf-8"))
        finding = ChatEvidenceReproducibilityService.validate_manifest(
            data, path=str(_OFFLINE_MANIFEST)
        )
        self.assertTrue(
            finding.ok,
            f"manifest inconsistente: {finding.errors}; "
            "rode scripts/align_evidence_release_pass.py",
        )
        self.assertIs(data.get("globalReleasePass"), False)

    def test_provenance_builder_includes_required_keys(self) -> None:
        runner = _ROOT / "scripts/run_e11_s9_final_candidate_offline.py"
        prov = ChatEvidenceReproducibilityService.build_provenance(
            git_sha="abc",
            dataset_version="intelligence_baseline/r1_r11_corpus_v2",
            dataset_hash="1147e05d",
            runner_path=runner,
            config_material={
                "datasetVersion": "intelligence_baseline/r1_r11_corpus_v2",
                "datasetHash": "1147e05d",
                "liveLlm": False,
                "role": "FINAL_CANDIDATE_OFFLINE",
            },
            provider="openai_compatible",
            model="kimi",
        )
        for key in (
            "finalCandidateGitSha",
            "datasetVersion",
            "datasetHash",
            "timestamp",
            "runnerSha256",
            "configHash",
        ):
            self.assertTrue(str(prov.get(key) or "").strip(), key)


if __name__ == "__main__":
    unittest.main()
