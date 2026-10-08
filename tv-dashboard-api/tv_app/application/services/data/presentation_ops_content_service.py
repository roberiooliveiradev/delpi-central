"""Catálogo canônico de ops tipadas da PresentationMutation (PT + schemas)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pathlib import Path

CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "presentation_ops_content.json"

_RISK_RANK = {"additive": 1, "mutation": 2, "destructive": 3}

_REF_PREFIX = "#/definitions/"

# Ops that mutate the slide nativeConfig document — single canonical
# source shared by the patch engine (mutation semantics) and the HTTP
# command planner (CRUD projection). Both consumers must stay in lockstep;
# a divergent copy silently rejects catalog-declared ops at runtime.
NATIVE_CONFIG_OPS = frozenset(
    {
        "upsert_data_source",
        "patch_data_source_params",
        "set_data_transform",
        "upsert_block",
        "set_display_format",
        "delete_block",
        "bind_visual",
        "patch_native_config",
        "ensure_brand_logo_on_slide",
        "apply_published_slide_template",
        # Mutates slide nativeConfig / dataFilters; must preload like other
        # native ops or preview raises misleading missingTarget.
        "re_layer_playlist_filters",
        # PRESENTATION-001 — geometry / identity ops on nativeConfig.
        "create_block",
        "align_blocks",
        "reorder_block_z",
        "duplicate_blocks",
        "transform_text_case",
        "bump_font_size",
        # DM1 — DataModel is a logical document in nativeConfig.dataModels.
        "upsert_data_model",
        "patch_data_model",
        "delete_data_model",
        # DM4 — legacy→DataModel migration also acts on nativeConfig.
        "migrate_data_sources_to_model",
        # Owner quality loop — marker op expanding to deterministic
        # safe corrections on the slide nativeConfig (safe_auto_fix).
        "apply_safe_layout_fixes",
    }
)


def _expand_definitions_refs(node: Any, definitions: dict[str, Any], seen: frozenset[str]) -> Any:
    """Expande ``$ref: #/definitions/*`` inline na carga do catálogo.

    Consumers (nested contract, OpenAPI builder, capability surface) recebem o
    schema já resolvido — ``definitions`` é a única fonte de fragments tipados
    (TransformPlan/TransformStep/ExpressionSpec) e refs são não-recursivas.
    """
    if isinstance(node, list):
        return [_expand_definitions_refs(item, definitions, seen) for item in node]
    if not isinstance(node, dict):
        return node
    ref = node.get("$ref")
    if isinstance(ref, str) and ref.startswith(_REF_PREFIX):
        name = ref[len(_REF_PREFIX) :]
        target = definitions.get(name)
        if not isinstance(target, dict):
            raise ValueError(f"presentation_ops_content: $ref não resolvido {ref!r}")
        if name in seen:
            raise ValueError(f"presentation_ops_content: $ref cíclico {ref!r}")
        merged = _expand_definitions_refs(target, definitions, seen | {name})
        siblings = {k: v for k, v in node.items() if k != "$ref"}
        if siblings:
            merged = {
                **merged,
                **{
                    k: _expand_definitions_refs(v, definitions, seen)
                    for k, v in siblings.items()
                },
            }
        return merged
    if ref is not None:
        raise ValueError(f"presentation_ops_content: $ref externo não suportado {ref!r}")
    return {
        key: _expand_definitions_refs(value, definitions, seen)
        for key, value in node.items()
    }


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    content = json.loads(CONTENT_PATH.read_text(encoding="utf-8"))
    definitions = content.get("definitions")
    if isinstance(definitions, dict) and definitions:
        operations = content.get("operations")
        if isinstance(operations, dict):
            content["operations"] = _expand_definitions_refs(
                operations, definitions, frozenset()
            )
    return content


def clear_presentation_ops_content_cache() -> None:
    """Invalida o cache do JSON (testes / hot-reload)."""
    _load.cache_clear()


class PresentationOpsContentService:
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
    def setting_float(cls, key: str, default: float) -> float:
        settings = _load().get("settings") or {}
        try:
            return float(settings.get(key, default))
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
    def destructive_action_terms(cls) -> list[str]:
        """Verbos que indicam remoção (apagar, excluir, …) — vocabulário do catálogo."""
        raw = _load().get("destructiveActionTerms")
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
        if key == "destructive":
            return cls.destructive_action_terms()
        if key == "any":
            seen: set[str] = set()
            out: list[str] = []
            for term in [
                *cls.mutation_action_terms(),
                *cls.create_action_terms(),
                *cls.destructive_action_terms(),
            ]:
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
    def display_format_hints(cls) -> list[dict[str, Any]]:
        raw = _load().get("displayFormatHints")
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
            name = cls.resolve_op_name(str(raw.get("op") or ""))
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
    def operation_produces(cls, op: str) -> list[str]:
        spec = cls.operation_spec(op) or {}
        raw = spec.get("produces")
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    @classmethod
    def operation_consumes(cls, op: str) -> list[str]:
        spec = cls.operation_spec(op) or {}
        raw = spec.get("consumes")
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    @classmethod
    def plan_resource_requirements(
        cls,
        ops: list[dict[str, Any]],
        target: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """External resource needs after walking ops in the given (ordered) sequence.

        Resources produced earlier in the plan satisfy later consumes. Target
        playlistId/slideId seed the available set.
        """
        target_obj = target if isinstance(target, dict) else {}
        available: set[str] = set()
        if str(target_obj.get("playlistId") or "").strip():
            available.add("playlist")
        if str(target_obj.get("slideId") or "").strip():
            available.add("slide")
        if str(target_obj.get("sectionId") or "").strip():
            available.add("section")

        external_playlist = False
        external_slide = False
        external_section = False
        unsatisfied: list[dict[str, str]] = []

        for raw in ops:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("op") or "").strip()
            if not name:
                continue
            for resource in cls.operation_consumes(name):
                if resource in available:
                    continue
                unsatisfied.append({"op": name, "resource": resource})
                if resource == "playlist":
                    external_playlist = True
                elif resource == "slide":
                    external_slide = True
                elif resource == "section":
                    external_section = True
            for resource in cls.operation_produces(name):
                available.add(resource)

        return {
            "requiresPlaylist": external_playlist,
            "requiresSlide": external_slide,
            "requiresSection": external_section,
            "available": sorted(available),
            "unsatisfied": unsatisfied,
            "satisfiable": len(unsatisfied) == 0,
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
    def op_aliases(cls) -> dict[str, str]:
        """Legacy/synonym op names → canonical catalog op (temporary compatibility)."""
        raw = _load().get("opAliases")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for alias, target in raw.items():
            key = str(alias or "").strip()
            if not key:
                continue
            if isinstance(target, str):
                canonical = target.strip()
            elif isinstance(target, dict):
                canonical = str(target.get("canonical") or "").strip()
            else:
                continue
            if canonical:
                out[key] = canonical
        return out

    @classmethod
    def native_config_ops(cls) -> frozenset[str]:
        """Canonical set of ops that mutate the slide nativeConfig document."""
        return NATIVE_CONFIG_OPS

    @classmethod
    def resolve_op_name(cls, name: str | None) -> str:
        """Map deprecated synonyms to the catalog op; unknown names stay as-is."""
        token = str(name or "").strip()
        if not token:
            return ""
        return cls.op_aliases().get(token, token)

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
    def capability_catalog_document(
        cls, *, include_field_vocabulary: bool = False
    ) -> dict[str, Any]:
        """Catalog projected on ``gpt_get_catalog`` (GPT Actions response budget).

        Operations are a **compact index** (risk / requires / hints) — full JSON
        Schemas live in the Custom GPT Action ``requestBody`` oneOf and in the
        server-side ``presentation_ops_content.json`` validator. Duplicating
        schemas here was the main ResponseTooLargeError driver.

        ``include_field_vocabulary`` projects canonical enum/discriminator
        vocabularies per op — used by the orchestrator-facing MCP surface,
        which has no attached OpenAPI schemas to discover values from.
        """
        return {
            "catalogVersion": cls.catalog_version(),
            "targetShape": {
                "fields": ["playlistId", "slideId"],
                "description": (
                    "Envelope target: playlistId quando a operação "
                    "requiresPlaylist; slideId quando requiresSlide."
                ),
            },
            "capabilities": cls._capabilities_for_actions(),
            "operations": cls._operations_for_actions(
                include_field_vocabulary=include_field_vocabulary
            ),
            "operationSchemas": "openapi_requestBody_oneOf",
            "allowedOps": sorted(cls.allowed_ops()),
            "sideEffectHintCatalog": cls.side_effect_hint_catalog(),
        }

    @classmethod
    def _strip_schema_examples(cls, node: Any) -> Any:
        if isinstance(node, dict):
            return {
                key: cls._strip_schema_examples(value)
                for key, value in node.items()
                if key != "example"
            }
        if isinstance(node, list):
            return [cls._strip_schema_examples(item) for item in node]
        return node

    @classmethod
    def _operations_for_actions(
        cls, *, include_field_vocabulary: bool = False
    ) -> dict[str, Any]:
        """Index-only projection — no inputSchema trees (OpenAPI owns those).

        ``fieldVocabulary`` is emitted only on the orchestrator-facing
        transport (MCP ``get_catalog``): the Actions surface already
        carries full JSON Schemas via OpenAPI, so duplicating enum
        vocabularies here would breach the Actions response budget
        without adding information to that consumer."""
        out: dict[str, Any] = {}
        for name, spec in cls.operations().items():
            if not isinstance(spec, dict):
                continue
            schema = spec.get("inputSchema") if isinstance(spec.get("inputSchema"), dict) else {}
            required = schema.get("required") if isinstance(schema.get("required"), list) else []
            row: dict[str, Any] = {
                "risk": spec.get("risk"),
                "confirmationPolicy": spec.get("confirmationPolicy"),
                "requiresPlaylist": bool(spec.get("requiresPlaylist")),
                "requiresSlide": bool(spec.get("requiresSlide")),
                "produces": list(spec.get("produces") or [])
                if isinstance(spec.get("produces"), list)
                else [],
                "consumes": list(spec.get("consumes") or [])
                if isinstance(spec.get("consumes"), list)
                else [],
                "sideEffectHints": list(spec.get("sideEffectHints") or [])
                if isinstance(spec.get("sideEffectHints"), list)
                else [],
            }
            req = [str(item).strip() for item in required if str(item).strip() and str(item) != "op"]
            if req:
                row["requiredFields"] = req
            properties = schema.get("properties")
            if isinstance(properties, dict):
                fields = sorted(
                    str(k).strip()
                    for k in properties
                    if str(k).strip() and str(k) != "op"
                )
                if fields:
                    row["fields"] = fields
                if include_field_vocabulary:
                    vocab = cls._field_vocabulary(schema)
                    # The canonical block-type vocabulary fills a declared
                    # discriminator field that carries no enum — never
                    # injected for fields the schema does not declare.
                    declares_type = "type" in properties
                    declares_block_type = (
                        isinstance(properties.get("block"), dict)
                        and "type"
                        in (properties["block"].get("properties") or {})
                    )
                    if (
                        declares_type
                        and "type" not in vocab
                        or declares_block_type
                        and "block.type" not in vocab
                    ):
                        block_types = cls.block_type_vocabulary()
                        if block_types:
                            key = "block.type" if declares_block_type else "type"
                            vocab[key] = block_types
                    if vocab:
                        row["fieldVocabulary"] = vocab
            when = spec.get("whenToUse")
            if isinstance(when, list) and when:
                row["whenToUse"] = [str(item).strip() for item in when[:3] if str(item).strip()]
            out[str(name)] = row
        return out

    @classmethod
    def block_type_vocabulary(cls) -> list[str]:
        """Canonical block-type vocabulary — projected from
        ``blockDefaults`` keys plus every enum value declared under a
        ``type``/``block.type`` field in the operation schemas. A new
        block type added to the canonical sources becomes visible to
        consumers automatically; nothing is duplicated."""
        vocab = {
            str(key).strip()
            for key in (_load().get("blockDefaults") or {})
            if str(key).strip() and str(key).strip() != "default"
        }
        for spec in cls.operations().values():
            schema = (
                spec.get("inputSchema")
                if isinstance(spec.get("inputSchema"), dict)
                else {}
            )
            props = schema.get("properties") or {}
            for field, fprop in props.items():
                if not isinstance(fprop, dict):
                    continue
                if field == "type" and isinstance(fprop.get("enum"), list):
                    vocab.update(str(v) for v in fprop["enum"])
                if field != "block":
                    continue
                sub = fprop.get("properties")
                if isinstance(sub, dict) and isinstance(sub.get("type"), dict):
                    enum = sub["type"].get("enum")
                    if isinstance(enum, list):
                        vocab.update(str(v) for v in enum)
        return sorted(vocab)

    @classmethod
    def _field_vocabulary(cls, schema: dict[str, Any]) -> dict[str, list[str]]:
        """Bounded enum/const vocabulary declared by an op schema —
        the discriminator values a consumer needs to build valid ops.
        Projected from the canonical schema, never duplicated."""
        properties = schema.get("properties")
        if not isinstance(properties, dict):
            return {}
        vocab: dict[str, list[str]] = {}
        for field, fprop in list(properties.items())[:32]:
            if not isinstance(fprop, dict) or field == "op":
                continue
            enum = fprop.get("enum")
            if isinstance(enum, list) and enum:
                vocab[str(field)] = [str(v) for v in enum[:32]]
            const = fprop.get("const")
            if const is not None:
                vocab.setdefault(str(field), [str(const)])
            sub = fprop.get("properties")
            if isinstance(sub, dict):
                for subfield, subprop in list(sub.items())[:32]:
                    if isinstance(subprop, dict) and isinstance(
                        subprop.get("enum"), list
                    ):
                        vocab[f"{field}.{subfield}"] = [
                            str(v) for v in subprop["enum"][:32]
                        ]
        return vocab

    @classmethod
    def _capabilities_for_actions(cls) -> list[dict[str, Any]]:
        compact: list[dict[str, Any]] = []
        drop = {
            "payloadTemplate",
            "payloadTemplates",
            "contentMarkers",
            "excludeMarkers",
            "actionTermSet",
            "clarificationMessageKey",
            "requiresFilledPlaceholders",
        }
        for item in cls.capabilities():
            if not isinstance(item, dict):
                continue
            row = {k: v for k, v in item.items() if k not in drop}
            compact.append(row)
        return compact

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
