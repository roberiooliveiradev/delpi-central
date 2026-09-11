"""J-R1 — evaluator R8 aplica thresholds canônicos (positive / sibling / negative)."""

from __future__ import annotations

import unittest

from app.domain.services.chat_r8_latency_threshold_service import (
    CANONICAL_TOTAL_LATENCY_MS_BY_MODE,
    ChatR8LatencyThresholdService,
)


class TestJR1R8LatencyThresholdEvaluator(unittest.TestCase):
    def test_canonical_thresholds_match_flow_families(self) -> None:
        self.assertEqual(CANONICAL_TOTAL_LATENCY_MS_BY_MODE["fast"], 3_000)
        self.assertEqual(CANONICAL_TOTAL_LATENCY_MS_BY_MODE["normal"], 5_000)
        self.assertEqual(CANONICAL_TOTAL_LATENCY_MS_BY_MODE["thinker"], 15_000)

    def test_positive_within_normal_threshold_passes(self) -> None:
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="normal",
            p50_ms=2_100,
            p95_ms=4_800,
            provider="openai_compatible",
            total_tokens=1_200,
            llm_calls=2,
            tool_calls=1,
            trials_ok=5,
        )
        self.assertEqual(result.decision, "PASS")
        self.assertEqual(result.threshold_ms, 5_000)
        self.assertIn("p50/p95 <= threshold", result.reason)

    def test_sibling_fast_and_thinker_thresholds(self) -> None:
        fast = ChatR8LatencyThresholdService.evaluate(
            response_mode="rapida",
            p50_ms=1_000,
            p95_ms=2_900,
            provider="openai_compatible",
            total_tokens=100,
            trials_ok=3,
        )
        thinker = ChatR8LatencyThresholdService.evaluate(
            response_mode="pensador",
            p50_ms=8_000,
            p95_ms=14_500,
            provider="openai_compatible",
            total_tokens=100,
            trials_ok=3,
        )
        self.assertEqual(fast.decision, "PASS")
        self.assertEqual(fast.threshold_ms, 3_000)
        self.assertEqual(thinker.decision, "PASS")
        self.assertEqual(thinker.threshold_ms, 15_000)

    def test_negative_above_normal_threshold_fails(self) -> None:
        # Valores do candidate histórico invalidado (A11-01).
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="normal",
            p50_ms=41_522,
            p95_ms=50_708,
            provider="openai_compatible",
            total_tokens=800,
            llm_calls=3,
            tool_calls=2,
            trials_ok=5,
        )
        self.assertEqual(result.decision, "FAIL")
        self.assertIn("acima do threshold", result.reason)
        self.assertEqual(result.threshold_ms, 5_000)

    def test_negative_p95_only_above_threshold_fails(self) -> None:
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="normal",
            p50_ms=4_000,
            p95_ms=5_001,
            provider="openai_compatible",
            total_tokens=50,
            trials_ok=3,
        )
        self.assertEqual(result.decision, "FAIL")

    def test_invalid_mode_never_passes(self) -> None:
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="turbo-ultra",
            p50_ms=10,
            p95_ms=20,
            provider="openai_compatible",
            total_tokens=10,
            trials_ok=5,
        )
        self.assertEqual(result.decision, "FAIL")
        self.assertIsNone(result.threshold_ms)
        self.assertIn("threshold ausente/inválido", result.reason)

    def test_missing_threshold_empty_mode_never_passes(self) -> None:
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="",
            p50_ms=10,
            p95_ms=20,
            provider="openai_compatible",
            total_tokens=10,
            trials_ok=5,
        )
        self.assertEqual(result.decision, "FAIL")
        self.assertNotEqual(result.decision, "PASS")

    def test_missing_p95_inconclusive_never_pass(self) -> None:
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="normal",
            p50_ms=100,
            p95_ms=None,
            provider="openai_compatible",
            total_tokens=10,
            trials_ok=5,
        )
        self.assertEqual(result.decision, "INCONCLUSIVE")
        self.assertNotEqual(result.decision, "PASS")

    def test_existence_of_p50_p95_alone_is_not_pass(self) -> None:
        """Regressão A11-01: métricas presentes sem comparação ao alvo ≠ PASS."""
        result = ChatR8LatencyThresholdService.evaluate(
            response_mode="normal",
            p50_ms=41_522,
            p95_ms=50_708,
            provider="openai_compatible",
            total_tokens=999,
            trials_ok=5,
        )
        self.assertNotEqual(result.decision, "PASS")
        self.assertEqual(result.decision, "FAIL")


if __name__ == "__main__":
    unittest.main()
