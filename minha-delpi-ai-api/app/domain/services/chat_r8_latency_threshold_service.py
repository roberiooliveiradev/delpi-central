"""R8 latency gate — thresholds canônicos por responseMode.

Authority: ``docs/testing/chat-ai-flow-families.md`` §12 (Latência — R8).

Não aumentar estes limites para acomodar candidate. P50 e P95 devem ser
comparados ao alvo total do modo; existência de métricas sem comparação
nunca produz PASS.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

# chat-ai-flow-families.md §12 — Alvos atuais por modo (total).
CANONICAL_TOTAL_LATENCY_MS_BY_MODE: dict[str, int] = {
    "fast": 3_000,  # Rápida ≤ 3 s
    "normal": 5_000,  # Normal ≤ 5 s
    "thinker": 15_000,  # Pensador ≤ 15 s
}

_STATIC_ALIASES: dict[str, str] = {
    "fast": "fast",
    "rapida": "fast",
    "rápida": "fast",
    "quick": "fast",
    "normal": "normal",
    "thinker": "thinker",
    "pensador": "thinker",
    "think": "thinker",
}


@dataclass(frozen=True)
class ChatR8LatencyGateResult:
    decision: str
    reason: str
    response_mode_raw: str | None
    response_mode: str | None
    threshold_ms: int | None
    p50_ms: float | None
    p95_ms: float | None
    provider: str | None = None
    total_tokens: float | None = None
    llm_calls: int | None = None
    tool_calls: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChatR8LatencyThresholdService:
    """Resolve threshold canônico e decide R8 sem self-attestation."""

    SOURCE_DOC = "docs/testing/chat-ai-flow-families.md#12-latencia--r8"

    @classmethod
    def resolve_mode(cls, response_mode: str | None) -> str | None:
        raw = str(response_mode or "").strip().lower()
        if not raw:
            return None

        aliases = dict(_STATIC_ALIASES)
        try:
            from app.domain.services.chat_response_mode_content_service import (
                ChatResponseModeContentService,
            )

            for key, value in ChatResponseModeContentService.alias_map().items():
                aliases[str(key).strip().lower()] = str(value).strip().lower()
        except Exception:  # noqa: BLE001 — evaluator must stay usable offline
            pass

        resolved = aliases.get(raw, raw)
        if resolved not in CANONICAL_TOTAL_LATENCY_MS_BY_MODE:
            return None
        return resolved

    @classmethod
    def threshold_ms_for_mode(cls, response_mode: str | None) -> int | None:
        mode = cls.resolve_mode(response_mode)
        if mode is None:
            return None
        return int(CANONICAL_TOTAL_LATENCY_MS_BY_MODE[mode])

    @classmethod
    def evaluate(
        cls,
        *,
        response_mode: str | None,
        p50_ms: float | None,
        p95_ms: float | None,
        provider: str | None = None,
        total_tokens: float | None = None,
        llm_calls: int | None = None,
        tool_calls: int | None = None,
        trials_ok: int | None = None,
        min_trials_ok: int = 3,
        require_tokens: bool = True,
    ) -> ChatR8LatencyGateResult:
        mode = cls.resolve_mode(response_mode)
        threshold = cls.threshold_ms_for_mode(response_mode)

        base = dict(
            response_mode_raw=str(response_mode).strip() if response_mode is not None else None,
            response_mode=mode,
            threshold_ms=threshold,
            p50_ms=float(p50_ms) if isinstance(p50_ms, (int, float)) else None,
            p95_ms=float(p95_ms) if isinstance(p95_ms, (int, float)) else None,
            provider=str(provider).strip() if provider else None,
            total_tokens=float(total_tokens) if isinstance(total_tokens, (int, float)) else None,
            llm_calls=int(llm_calls) if isinstance(llm_calls, (int, float)) else None,
            tool_calls=int(tool_calls) if isinstance(tool_calls, (int, float)) else None,
        )

        if threshold is None or mode is None:
            return ChatR8LatencyGateResult(
                decision="FAIL",
                reason=(
                    "threshold ausente/inválido para responseMode="
                    f"{response_mode!r} (authority={cls.SOURCE_DOC})"
                ),
                **base,
            )

        if trials_ok is not None and trials_ok < min_trials_ok:
            return ChatR8LatencyGateResult(
                decision="INCONCLUSIVE",
                reason=f"menos de {min_trials_ok} trials OK (ok={trials_ok})",
                **base,
            )

        provider_l = str(provider or "").strip().lower()
        if provider_l and "ollama" in provider_l:
            return ChatR8LatencyGateResult(
                decision="FAIL",
                reason="provider ollama observado (fallback proibido para R8 release)",
                **base,
            )

        if base["p50_ms"] is None or base["p95_ms"] is None:
            return ChatR8LatencyGateResult(
                decision="INCONCLUSIVE",
                reason="p50/p95 ausente — sem métrica não há PASS",
                **base,
            )

        if require_tokens and base["total_tokens"] is None:
            return ChatR8LatencyGateResult(
                decision="INCONCLUSIVE",
                reason="tokens metadata ausente (totalTokens)",
                **base,
            )

        # Required: ambos os percentis ≤ alvo total do modo.
        if base["p50_ms"] > threshold or base["p95_ms"] > threshold:
            return ChatR8LatencyGateResult(
                decision="FAIL",
                reason=(
                    f"latência acima do threshold canônico mode={mode} "
                    f"thresholdMs={threshold} p50Ms={base['p50_ms']} "
                    f"p95Ms={base['p95_ms']} (authority={cls.SOURCE_DOC})"
                ),
                **base,
            )

        return ChatR8LatencyGateResult(
            decision="PASS",
            reason=(
                f"p50/p95 <= threshold canônico mode={mode} "
                f"thresholdMs={threshold} p50Ms={base['p50_ms']} "
                f"p95Ms={base['p95_ms']}"
            ),
            **base,
        )
