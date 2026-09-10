"""Telemetria E1.S4 — shadow markers/intent vs retrieval (sem alterar seleção)."""

from __future__ import annotations

import logging
from collections import Counter
from typing import Any

logger = logging.getLogger(__name__)

_SHADOW_KEYS = ("registrySelectionShadow", "productSelectionShadow")


class RegistrySelectionShadowObservabilityService:
    """Emite métricas estruturadas e agrega taxa agree/diverge do selection shadow."""

    @classmethod
    def record(cls, shadow: dict[str, Any] | None) -> None:
        if not isinstance(shadow, dict):
            return
        logger.info(
            "registry_selection_shadow",
            extra={
                "metric": "registry_selection_shadow",
                "kind": str(shadow.get("kind") or "registry_route_id"),
                "routeId": str(shadow.get("routeId") or ""),
                "legacyActionId": str(shadow.get("legacyActionId") or ""),
                "agree": bool(shadow.get("agree")),
                "candidateTopCount": len(shadow.get("candidateTopIds") or []),
                "error": str(shadow.get("error") or "") or None,
            },
        )

    @classmethod
    def compact_snapshot(cls, shadow: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": str(shadow.get("kind") or "registry_route_id"),
            "routeId": str(shadow.get("routeId") or ""),
            "legacyActionId": str(shadow.get("legacyActionId") or ""),
            "agree": bool(shadow.get("agree")),
            "error": str(shadow.get("error") or "") or None,
            "intent": str(shadow.get("intent") or "") or None,
            "routeSegment": str(shadow.get("routeSegment") or "") or None,
        }

    @classmethod
    def extract_shadows(
        cls,
        *,
        tool_calls: list | None = None,
        assistant_metadata: dict | None = None,
    ) -> list[dict[str, Any]]:
        found: list[dict[str, Any]] = []

        def _collect(container: Any) -> None:
            if not isinstance(container, dict):
                return
            for key in _SHADOW_KEYS:
                shadow = container.get(key)
                if isinstance(shadow, dict):
                    found.append(shadow)
            nested = container.get("metadata")
            if isinstance(nested, dict):
                for key in _SHADOW_KEYS:
                    shadow = nested.get(key)
                    if isinstance(shadow, dict):
                        found.append(shadow)
            selected = container.get("selectedExternalAction")
            if isinstance(selected, dict) and selected is not container:
                _collect(selected)

        _collect(assistant_metadata)
        for tool_call in tool_calls or []:
            _collect(tool_call)

        return found

    @classmethod
    def enrich_audit_metadata(
        cls,
        audit_metadata: dict,
        *,
        tool_calls: list | None = None,
        assistant_metadata: dict | None = None,
    ) -> dict:
        shadows = [
            cls.compact_snapshot(shadow)
            for shadow in cls.extract_shadows(
                tool_calls=tool_calls,
                assistant_metadata=assistant_metadata,
            )
        ]
        if shadows:
            audit_metadata["registrySelectionShadows"] = shadows
        return audit_metadata

    @classmethod
    def aggregate_snapshots(
        cls,
        entries: list[dict[str, Any]],
        *,
        hours: int,
        since_iso: str,
    ) -> dict[str, Any]:
        samples: list[dict[str, Any]] = []
        for entry in entries:
            snapshot = entry.get("snapshot")
            logged_at = entry.get("loggedAt")
            action = entry.get("action")
            if isinstance(snapshot, list):
                for item in snapshot:
                    if isinstance(item, dict):
                        samples.append(
                            {
                                **item,
                                "loggedAt": logged_at,
                                "action": action,
                            }
                        )
            elif isinstance(snapshot, dict):
                samples.append(
                    {
                        **snapshot,
                        "loggedAt": logged_at,
                        "action": action,
                    }
                )

        by_kind_total: Counter[str] = Counter()
        by_kind_agree: Counter[str] = Counter()
        agree_count = 0
        diverge_count = 0
        error_count = 0
        diverge_recent: list[dict[str, Any]] = []
        recent: list[dict[str, Any]] = []

        for sample in samples:
            kind = str(sample.get("kind") or "registry_route_id")
            by_kind_total[kind] += 1
            agreed = bool(sample.get("agree"))
            if agreed:
                agree_count += 1
                by_kind_agree[kind] += 1
            else:
                diverge_count += 1
            if sample.get("error"):
                error_count += 1

        for sample in samples:
            if len(recent) >= 12:
                break
            recent.append(
                {
                    "loggedAt": sample.get("loggedAt"),
                    "action": sample.get("action"),
                    "kind": sample.get("kind"),
                    "routeId": sample.get("routeId"),
                    "legacyActionId": sample.get("legacyActionId"),
                    "agree": bool(sample.get("agree")),
                }
            )

        for sample in samples:
            if bool(sample.get("agree")):
                continue
            if len(diverge_recent) >= 12:
                break
            diverge_recent.append(
                {
                    "loggedAt": sample.get("loggedAt"),
                    "kind": sample.get("kind"),
                    "routeId": sample.get("routeId"),
                    "legacyActionId": sample.get("legacyActionId"),
                    "error": sample.get("error"),
                }
            )

        samples_count = len(samples)
        agree_rate = (
            round(agree_count / samples_count, 4) if samples_count else None
        )
        by_kind: dict[str, Any] = {}
        for kind, total in by_kind_total.items():
            agreed = by_kind_agree.get(kind, 0)
            by_kind[kind] = {
                "samplesCount": total,
                "agreeCount": agreed,
                "agreeRate": round(agreed / total, 4) if total else None,
            }

        return {
            "windowHours": hours,
            "since": since_iso,
            "samplesCount": samples_count,
            "agreeCount": agree_count,
            "divergeCount": diverge_count,
            "errorCount": error_count,
            "agreeRate": agree_rate,
            "byKind": by_kind,
            "divergeRecent": diverge_recent,
            "recent": recent,
            "cutoverReadyHint": (
                "not_ready"
                if samples_count < 20
                else ("candidate" if (agree_rate or 0) >= 0.95 else "investigate_divergences")
            ),
        }
