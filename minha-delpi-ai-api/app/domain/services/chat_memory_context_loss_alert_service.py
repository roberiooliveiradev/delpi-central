"""Alertas por turno de risco de perda de contexto — Playbook memória Fase 9."""

from __future__ import annotations

from typing import Any


class ChatMemoryContextLossAlertService:
    @classmethod
    def build_turn_alerts(
        cls,
        *,
        assertiveness: dict[str, Any] | None,
        snapshot: dict[str, Any] | None = None,
    ) -> list[dict[str, str]]:
        if not isinstance(assertiveness, dict):
            return []

        alerts: list[dict[str, str]] = []
        score = assertiveness.get("score")
        flags = (
            assertiveness.get("flags")
            if isinstance(assertiveness.get("flags"), list)
            else []
        )
        flag_set = {str(item) for item in flags if item}

        if "follow_up_without_entity_reuse" in flag_set:
            alerts.append(
                {
                    "code": "follow_up_without_entity_reuse",
                    "message": (
                        "Follow-up detectado, mas a resposta não reutilizou "
                        "produto/período da memória."
                    ),
                }
            )

        if "unnecessary_code_request" in flag_set:
            alerts.append(
                {
                    "code": "unnecessary_code_request",
                    "message": "Pediu código novamente apesar de já estar na memória.",
                }
            )

        if "stale_product_context" in flag_set:
            alerts.append(
                {
                    "code": "stale_product_context",
                    "message": "Possível produto obsoleto na memória de sessão.",
                }
            )

        if isinstance(score, (int, float)) and float(score) < 60:
            alerts.append(
                {
                    "code": "low_assertiveness",
                    "message": f"Assertividade contextual baixa ({float(score):.0f}/100).",
                }
            )

        snap = snapshot if isinstance(snapshot, dict) else {}
        ambiguity = snap.get("memoryAmbiguity")

        if isinstance(ambiguity, dict) and ambiguity.get("candidates"):
            alerts.append(
                {
                    "code": "memory_ambiguity",
                    "message": "Referência ambígua — memória não resolveu sozinha.",
                }
            )

        return alerts[:5]

    @classmethod
    def attach_to_metadata(
        cls,
        metadata: dict[str, Any],
        *,
        assertiveness: dict[str, Any] | None,
        snapshot: dict[str, Any] | None = None,
    ) -> None:
        alerts = cls.build_turn_alerts(assertiveness=assertiveness, snapshot=snapshot)

        if alerts:
            metadata["memoryContextAlerts"] = alerts
