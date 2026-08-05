"""Conteúdo PT do copiloto TV (patches tipados)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pathlib import Path

CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "tv_copilot_content.json"

_RISK_RANK = {"additive": 1, "mutation": 2, "destructive": 3}


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_tv_copilot_content_cache() -> None:
    """Invalida o cache do JSON (testes / hot-reload)."""
    _load.cache_clear()


class TvCopilotContentService:
    @classmethod
    def message(cls, key: str, default: str = "", **format_kwargs: Any) -> str:
        messages = _load().get("messages") or {}
        text = str(messages.get(key) or default or key)
        if format_kwargs:
            try:
                return text.format_map(format_kwargs)
            except (KeyError, ValueError):
                return text
        return text

    @classmethod
    def setting_int(cls, key: str, default: int) -> int:
        settings = _load().get("settings") or {}
        try:
            return int(settings.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def setting_str(cls, key: str, default: str = "") -> str:
        settings = _load().get("settings") or {}
        value = settings.get(key, default)
        if value is None:
            return default
        return str(value)

    @classmethod
    def catalog_version(cls) -> str:
        return str(_load().get("catalogVersion") or "").strip()

    @classmethod
    def block_defaults(cls, block_type: str) -> dict[str, Any]:
        """frame/style padrão do bloco — espelha o editor para o bloco aparecer no slide."""
        defaults = _load().get("blockDefaults") or {}
        entry = defaults.get(str(block_type or "").strip()) or defaults.get("default") or {}
        return entry if isinstance(entry, dict) else {}

    @classmethod
    def mutation_action_terms(cls) -> list[str]:
        raw = _load().get("mutationActionTerms")
        if not isinstance(raw, list):
            return []
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def create_action_terms(cls) -> list[str]:
        raw = _load().get("createActionTerms")
        if not isinstance(raw, list):
            return []
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def action_terms_for_set(cls, term_set: str) -> list[str]:
        key = str(term_set or "").strip().lower()
        if key == "create":
            return cls.create_action_terms()
        if key == "mutation":
            return cls.mutation_action_terms()
        if key == "any":
            seen: set[str] = set()
            out: list[str] = []
            for term in [*cls.mutation_action_terms(), *cls.create_action_terms()]:
                if term in seen:
                    continue
                seen.add(term)
                out.append(term)
            return out
        return []

    @classmethod
    def _recognition(cls) -> dict[str, Any]:
        raw = _load().get("recognition")
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def recognition_float(cls, key: str, default: float) -> float:
        try:
            return float(cls._recognition().get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def recognition_int(cls, key: str, default: int) -> int:
        try:
            return int(cls._recognition().get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def editor_nouns(cls) -> list[str]:
        raw = cls._recognition().get("editorNouns")
        if not isinstance(raw, list):
            return []
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def recognition_extra_action_terms(cls) -> list[str]:
        raw = cls._recognition().get("extraActionTerms")
        if not isinstance(raw, list):
            return []
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def recognition_action_term_sets(cls) -> list[str]:
        raw = cls._recognition().get("actionTermSets")
        if not isinstance(raw, list) or not raw:
            return ["any"]
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def placeholder_clarifications(cls) -> dict[str, str]:
        raw = _load().get("placeholderClarifications")
        if not isinstance(raw, dict):
            return {}
        return {
            str(key).strip(): str(value).strip()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def op_field_clarifications(cls) -> dict[str, str]:
        raw = _load().get("opFieldClarifications")
        if not isinstance(raw, dict):
            return {}
        return {
            str(key).strip(): str(value).strip()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def color_vocabulary(cls) -> dict[str, str]:
        raw = _load().get("colorVocabulary")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for key, value in raw.items():
            name = str(key or "").strip().lower()
            hex_value = str(value or "").strip()
            if name and hex_value:
                out[name] = hex_value
        return out

    @classmethod
    def nl_route_hints(cls) -> dict[str, str]:
        raw = _load().get("nlRouteHints")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for key, value in raw.items():
            alias = str(key or "").strip().lower()
            operation_id = str(value or "").strip()
            if alias and operation_id:
                out[alias] = operation_id
        return out

    @classmethod
    def param_hints(cls) -> dict[str, Any]:
        raw = _load().get("paramHints")
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def transform_step_hints(cls) -> list[dict[str, Any]]:
        raw = _load().get("transformStepHints")
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    @classmethod
    def capabilities(cls) -> list[dict[str, Any]]:
        raw = _load().get("capabilities")
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    @classmethod
    def operations(cls) -> dict[str, dict[str, Any]]:
        raw = _load().get("operations")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, dict[str, Any]] = {}
        for key, value in raw.items():
            op_name = str(key or "").strip()
            if not op_name or not isinstance(value, dict):
                continue
            out[op_name] = value
        return out

    @classmethod
    def operation_spec(cls, op: str) -> dict[str, Any] | None:
        op_key = str(op or "").strip()
        if not op_key:
            return None
        return cls.operations().get(op_key)

    @classmethod
    def aggregate_ops_policy(cls, ops: list[dict[str, Any]]) -> dict[str, Any]:
        """Agrega risco/confirmação/target mínimo de uma lista de ops tipadas."""
        requires_playlist = False
        requires_slide = False
        risk = "additive"
        confirmation = "direct"
        hints: list[str] = []
        seen_hints: set[str] = set()
        op_names: list[str] = []

        for raw in ops:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("op") or "").strip()
            if not name:
                continue
            op_names.append(name)
            spec = cls.operation_spec(name) or {}
            if bool(spec.get("requiresPlaylist")):
                requires_playlist = True
            if bool(spec.get("requiresSlide")):
                requires_slide = True
            risk_value = str(spec.get("risk") or "mutation").strip().lower()
            if _RISK_RANK.get(risk_value, 2) > _RISK_RANK.get(risk, 1):
                risk = risk_value
            policy = str(spec.get("confirmationPolicy") or "direct").strip().lower()
            if policy == "confirm":
                confirmation = "confirm"
            for hint in spec.get("sideEffectHints") or []:
                token = str(hint or "").strip()
                if token and token not in seen_hints:
                    seen_hints.add(token)
                    hints.append(token)

        return {
            "requiresPlaylist": requires_playlist,
            "requiresSlide": requires_slide,
            "risk": risk,
            "confirmationPolicy": confirmation,
            "sideEffectHints": hints,
            "opNames": op_names,
        }

    @classmethod
    def side_effect_hint_catalog(cls) -> list[str]:
        raw = _load().get("sideEffectHintCatalog")
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    @classmethod
    def capability_by_op(cls, op: str) -> dict[str, Any] | None:
        op_key = str(op or "").strip()
        if not op_key:
            return None
        fallback: dict[str, Any] | None = None
        for item in cls.capabilities():
            if str(item.get("op") or "").strip() != op_key:
                continue
            if bool(item.get("isComposite")):
                fallback = fallback or item
                continue
            return item
        return fallback

    @classmethod
    def allowed_ops(cls) -> frozenset[str]:
        from_ops = set(cls.operations().keys())
        if from_ops:
            return frozenset(from_ops)
        caps = cls.capabilities()
        if caps:
            from_caps = {
                str(item.get("op") or "").strip()
                for item in caps
                if str(item.get("op") or "").strip() and not bool(item.get("isComposite"))
            }
            for item in caps:
                templates = item.get("payloadTemplates")
                if not isinstance(templates, list):
                    continue
                for template in templates:
                    if not isinstance(template, dict):
                        continue
                    op_name = str(template.get("op") or "").strip()
                    if op_name:
                        from_caps.add(op_name)
            if from_caps:
                return frozenset(from_caps)
        raw = _load().get("allowedOps") or []
        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def capability_catalog_document(cls) -> dict[str, Any]:
        return {
            "catalogVersion": cls.catalog_version(),
            "capabilities": cls.capabilities(),
            "operations": cls.operations(),
            "allowedOps": sorted(cls.allowed_ops()),
            "sideEffectHintCatalog": cls.side_effect_hint_catalog(),
        }

    @classmethod
    def side_effect_hints_for_op(cls, op: str) -> list[str]:
        spec = cls.operation_spec(op)
        if isinstance(spec, dict):
            raw = spec.get("sideEffectHints")
            if isinstance(raw, list) and raw:
                return [str(item).strip() for item in raw if str(item).strip()]
        cap = cls.capability_by_op(op)
        if not cap:
            return []
        raw = cap.get("sideEffectHints")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()]
        return []
