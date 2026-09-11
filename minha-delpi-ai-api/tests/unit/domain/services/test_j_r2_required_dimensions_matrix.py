"""J-R2 — requiredDimensions do corpus ≥ matriz canônica §4."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from app.domain.services.chat_required_dimensions_matrix_service import (
    CANONICAL_REQUIRED_DIMENSIONS,
    ChatRequiredDimensionsMatrixService,
)

_ROOT = Path(__file__).resolve().parents[4]
_CORPUS_V1 = _ROOT / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v1.json"
_CORPUS_V2 = _ROOT / "tests/fixtures/intelligence_baseline/r1_r11_corpus_v2.json"
_V2_HASH = "1147e05d6beae96dcf2322a08195f0bcc7a3727206418cd056692d570ce9523f"


class TestJR2RequiredDimensionsMatrix(unittest.TestCase):
    def test_canonical_action_read_includes_r3_r8_r9_r10(self) -> None:
        dims = CANONICAL_REQUIRED_DIMENSIONS["action_openapi_read"]
        for required in ("R1", "R2", "R3", "R4", "R8", "R9", "R10", "R11"):
            self.assertIn(required, dims)

    def test_canonical_security_includes_r10(self) -> None:
        dims = CANONICAL_REQUIRED_DIMENSIONS["security_adversarial"]
        self.assertIn("R10", dims)
        self.assertIn("R11", dims)

    def test_canonical_compound_includes_full_minimum(self) -> None:
        dims = CANONICAL_REQUIRED_DIMENSIONS["compound"]
        for required in ("R1", "R2", "R3", "R4", "R6", "R8", "R9", "R10", "R11"):
            self.assertIn(required, dims)

    def test_positive_corpus_v2_passes_matrix_gate(self) -> None:
        corpus = json.loads(_CORPUS_V2.read_text(encoding="utf-8"))
        report = ChatRequiredDimensionsMatrixService.validate_corpus(corpus)
        self.assertTrue(report.ok, report.as_dict())
        self.assertEqual(corpus.get("datasetVersion"), "intelligence_baseline/r1_r11_corpus_v2")
        self.assertEqual(len(report.findings), 20)

    def test_sibling_args_and_unknown_classes_cover_r3_r9(self) -> None:
        corpus = json.loads(_CORPUS_V2.read_text(encoding="utf-8"))
        by_id = {c["id"]: c for c in corpus["cases"]}
        for case_id in (
            "e9.c05.required_present",
            "e9.c06.required_missing_clarify",
            "e9.c07.enum_type_invalid",
            "e9.c11.unknown_external_openapi",
        ):
            dims = set(by_id[case_id]["requiredDimensions"])
            self.assertIn("R3", dims, case_id)
            self.assertTrue({"R8", "R9", "R11"} <= dims, case_id)

    def test_negative_corpus_v1_fails_matrix_gate(self) -> None:
        """A11-02: corpus histórico incompleto não pode passar o gate."""
        corpus = json.loads(_CORPUS_V1.read_text(encoding="utf-8"))
        report = ChatRequiredDimensionsMatrixService.validate_corpus(corpus)
        self.assertFalse(report.ok)
        self.assertEqual(len(report.failing), 20)
        unauthorized = next(f for f in report.failing if f.case_id == "e9.c13.unauthorized")
        self.assertIn("R10", unauthorized.missing)

    def test_negative_synthetic_incomplete_case_detected(self) -> None:
        case = {
            "id": "synth.incomplete",
            "classId": 14,
            "matrixClass": "action_write_admin_destructive",
            "requiredDimensions": ["R11"],
        }
        finding = ChatRequiredDimensionsMatrixService.validate_case(case)
        self.assertFalse(finding.ok)
        self.assertIn("R10", finding.missing)
        self.assertIn("R3", finding.missing)

    def test_corpus_v2_hash_frozen(self) -> None:
        import hashlib

        digest = hashlib.sha256(_CORPUS_V2.read_bytes()).hexdigest()
        self.assertEqual(digest, _V2_HASH)


if __name__ == "__main__":
    unittest.main()
