"""Valida e normaliza o contrato canônico de Turn Refinement (E3.S3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.domain.entities.turn_refinement import (
    FORBIDDEN_SEMANTIC_KEYS,
    SUPPORTED_REFINEMENT_KINDS,
    SUPPORTED_TARGET_KINDS,
    TURN_REFINEMENT_CONTRACT_VERSION,
    TurnRefinement,
    TurnRefinementClarification,
    TurnRefinementConflict,
    TurnRefinementTarget,
    _clean_argument_delta,
    _strip_forbidden,
)


@dataclass
class TurnRefinementValidationResult:
    ok: bool
    contract: TurnRefinement | None = None
    errors: list[str] = field(default_factory=list)
    used_fallback: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "errors": list(self.errors),
            "usedFallback": self.used_fallback,
            "contract": self.contract.as_dict() if self.contract else None,
        }


class TurnRefinementValidatorService:
    @classmethod
    def validate(
        cls,
        raw: TurnRefinement | dict[str, Any] | None,
        *,
        inherited_arguments: dict[str, Any] | None = None,
        fallback_reason: str | None = None,
    ) -> TurnRefinementValidationResult:
        errors: list[str] = []
        raw_kind: str | None = None
        if isinstance(raw, dict):
            raw_kind = str(raw.get("kind") or "").strip().lower() or None
            if raw_kind and raw_kind not in SUPPORTED_REFINEMENT_KINDS:
                errors.append(f"invalid_kind:{raw_kind}")

        if isinstance(raw, TurnRefinement):
            contract = raw
        else:
            contract = TurnRefinement.from_dict(raw if isinstance(raw, dict) else None)

        if contract is None:
            reason = str(fallback_reason or "").strip() or "malformed_or_missing_contract"
            return TurnRefinementValidationResult(
                ok=False,
                contract=TurnRefinement.fallback_clarify(reason),
                errors=errors + ["malformed_or_missing_contract"],
                used_fallback=True,
            )

        kind = contract.kind if contract.kind in SUPPORTED_REFINEMENT_KINDS else "unknown"
        if contract.kind not in SUPPORTED_REFINEMENT_KINDS and not any(
            item.startswith("invalid_kind:") for item in errors
        ):
            errors.append(f"invalid_kind:{contract.kind}")

        target = contract.target
        if target is not None and target.kind not in SUPPORTED_TARGET_KINDS:
            errors.append(f"invalid_target_kind:{target.kind}")
            target = TurnRefinementTarget(
                kind="unknown",
                action_id=target.action_id,
                result_set_id=target.result_set_id,
                topic_id=target.topic_id,
                ordinal=target.ordinal,
            )

        # Detect forbidden keys in raw dict surface when available.
        if isinstance(raw, dict):
            for key in FORBIDDEN_SEMANTIC_KEYS:
                if key in (raw.get("argumentDelta") or {}) or key in (
                    raw.get("argument_delta") or {}
                ):
                    errors.append(f"forbidden_argument:{key}")
                if isinstance(raw.get("target"), dict) and key in raw["target"]:
                    errors.append(f"forbidden_target_field:{key}")
                if key in raw and key not in {
                    # top-level unknown fields are ignored, but flagged when semantic
                }:
                    # only flag if they look like decision keys at top level
                    if key in {
                        "path",
                        "operationId",
                        "routeSegment",
                        "pathContains",
                        "preferredRouteId",
                    }:
                        errors.append(f"forbidden_top_level:{key}")

        argument_delta = _clean_argument_delta(contract.argument_delta)
        presentation = (
            _strip_forbidden(contract.presentation_delta)
            if contract.presentation_delta
            else None
        )
        if presentation == {}:
            presentation = None

        cleared = tuple(
            name
            for name in contract.cleared_arguments
            if name and name not in FORBIDDEN_SEMANTIC_KEYS
        )

        conflicts = list(contract.conflicts)
        inherited = _clean_argument_delta(inherited_arguments or {})
        for key, proposed in argument_delta.items():
            if key in inherited and inherited[key] != proposed:
                already = {item.argument for item in conflicts}
                if key not in already:
                    conflicts.append(
                        TurnRefinementConflict(
                            argument=key,
                            inherited_value=inherited[key],
                            proposed_value=proposed,
                            resolution="explicit_wins",
                        )
                    )
                    errors.append(f"conflicting_inherited_arg:{key}")

        confidence = float(contract.confidence)
        if confidence < 0 or confidence > 1:
            errors.append("confidence_out_of_range")
            confidence = max(0.0, min(1.0, confidence))

        clarification = contract.clarification
        if kind == "clarify" and clarification is None:
            clarification = TurnRefinementClarification(
                reason=str(contract.reason or "needs_clarification").strip()
                or "needs_clarification"
            )
            errors.append("clarify_missing_payload")

        if kind == "argument_delta" and not argument_delta and not cleared:
            errors.append("argument_delta_empty")

        normalized = TurnRefinement(
            kind=kind,
            confidence=confidence,
            target=target,
            argument_delta=argument_delta,
            cleared_arguments=cleared,
            presentation_delta=presentation,
            clarification=clarification,
            conflicts=tuple(conflicts),
            reason=str(contract.reason or "").strip(),
            source=str(contract.source or "heuristic").strip() or "heuristic",
            contract_version=max(1, int(contract.contract_version or TURN_REFINEMENT_CONTRACT_VERSION)),
        )

        ok = not any(
            error.startswith("malformed")
            or error.startswith("invalid_kind")
            or error == "argument_delta_empty"
            for error in errors
        )
        # Forbidden/conflict are soft errors: contract still usable after strip.
        soft_only = errors and all(
            error.startswith("forbidden_")
            or error.startswith("conflicting_inherited_arg")
            or error == "confidence_out_of_range"
            or error == "clarify_missing_payload"
            or error.startswith("invalid_target_kind")
            for error in errors
        )
        if soft_only:
            ok = True

        return TurnRefinementValidationResult(
            ok=ok,
            contract=normalized,
            errors=errors,
            used_fallback=False,
        )

    @classmethod
    def ensure(
        cls,
        raw: TurnRefinement | dict[str, Any] | None,
        *,
        inherited_arguments: dict[str, Any] | None = None,
        fallback_reason: str | None = None,
    ) -> TurnRefinement:
        result = cls.validate(
            raw,
            inherited_arguments=inherited_arguments,
            fallback_reason=fallback_reason,
        )
        assert result.contract is not None
        return result.contract
