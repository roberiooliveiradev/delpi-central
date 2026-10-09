"""Structured design intelligence projected to VISTA (catalog authority)."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, Sequence

from tv_app.application.services.data.slide_layout_quality_service import (
    SlideLayoutQualityService,
)

_CONTENT = Path(__file__).resolve().parents[3] / "content" / "design_intelligence.json"

_LABEL_KEYS = frozenset({"label", "bucket", "periodo", "date", "name", "categoria", "category"})
_TEMPORAL_KEYS = frozenset({"date", "bucket", "periodo", "competencia", "granularity"})
_GOAL_HINTS = ("target", "goal", "meta", "objetivo")
_PERCENT_HINTS = ("pct", "percent", "rate", "taxa", "conversion")
_CURRENCY_HINTS = ("revenue", "receita", "valor", "amount", "brl")


@lru_cache(maxsize=1)
def _document() -> dict[str, Any]:
    raw = json.loads(_CONTENT.read_text(encoding="utf-8"))
    return raw if isinstance(raw, dict) else {}


class DesignIntelligenceService:
    @classmethod
    def catalog_projection(cls) -> dict[str, Any]:
        doc = _document()
        specs_in = doc.get("componentSpecs") if isinstance(doc.get("componentSpecs"), dict) else {}
        specs_out: dict[str, Any] = {}
        for name, spec in specs_in.items():
            if not isinstance(spec, dict):
                continue
            row: dict[str, Any] = {
                "componentType": spec.get("componentType") or name,
                "purpose": spec.get("purpose") or [],
                "avoidFor": spec.get("avoidFor") or [],
            }
            if isinstance(spec.get("variants"), dict):
                row["variants"] = {
                    variant: {
                        "purpose": (meta.get("purpose") if isinstance(meta, dict) else None) or [],
                        "avoidFor": (meta.get("avoidFor") if isinstance(meta, dict) else None) or [],
                    }
                    for variant, meta in spec["variants"].items()
                }
            specs_out[str(name)] = row
        return {
            "version": doc.get("version"),
            "componentSpecs": specs_out,
            "authority": "design_intelligence.json",
            "fields": [
                "semanticDigest",
                "visualRecommendation",
                "designAudit",
                "storyDigest",
                "candidatePreview",
                "visualVerification",
                "designMethodology",
            ],
            "designMethodology": cls._methodology_catalog_projection(),
        }

    @classmethod
    def _methodology_contract(cls) -> dict[str, Any]:
        doc = _document()
        contract = doc.get("designMethodology")
        return contract if isinstance(contract, dict) else {}

    @classmethod
    def _methodology_catalog_projection(cls) -> dict[str, Any]:
        """Compact contract projection — vocabulary + rules, no prose blobs."""
        contract = cls._methodology_contract()
        return {
            "version": contract.get("version"),
            "intents": contract.get("intents") or [],
            "readinessStates": contract.get("readinessStates") or [],
            "epistemicStates": contract.get("epistemicStates") or [],
            "sufficiencyOutcomes": contract.get("sufficiencyOutcomes") or [],
            "evidenceLevels": contract.get("evidenceLevels") or [],
            "factRequirements": contract.get("factRequirements") or {},
            "readBeforeAsk": contract.get("readBeforeAsk") or {},
            "forbiddenClaims": contract.get("forbiddenClaims") or [],
            "confidencePolicy": contract.get("confidencePolicy"),
        }

    # -- PHASE 5 methodology evaluator --------------------------------------
    # Deterministic readiness/sufficiency evaluation over facts the caller
    # already assembled (digests, P4 grounding, audits). No I/O here — dispatch
    # owns reads; the evaluator only classifies known/unknown/readable.

    _FACTS_DERIVED_FROM_DIGEST = ("primary_metric", "time_series", "category_count")

    # Bounded sub-intent detector for high-level design requests. This is the
    # methodology's own vocabulary — Knowledge Orchestration remains the outer
    # router; direct typed commands must return None so ops flow ungated.
    _DESIGN_INTENT_PATTERNS = (
        ("CHOOSE_VISUAL", ("qual grafico", "que grafico", "qual visual", "grafico devo", "qual tipo de grafico")),
        ("FIX_LAYOUT", ("sobrepo", "sobrepost", "fora do slide", "apertad", "organiz", "layout quebrad")),
        ("REVIEW_SLIDE", ("esta bom", "ta bom", "revise", "avalie", "como esta", "bonit")),
        ("COMPOSE_SLIDE", ("executiv", "monte", "componha", "crie um slide", "novo slide")),
        ("IMPROVE_EXISTING", ("melhore", "melhorar", "destaque", "destacar", "deixe melhor", "polir")),
    )

    @classmethod
    def design_intent_for_message(cls, message: str | None) -> str | None:
        import unicodedata

        text = " ".join(str(message or "").lower().split())
        text = "".join(
            c for c in unicodedata.normalize("NFD", text)
            if unicodedata.category(c) != "Mn"
        )
        if not text:
            return None
        for intent, markers in cls._DESIGN_INTENT_PATTERNS:
            if any(marker in text for marker in markers):
                return intent
        return None

    @classmethod
    def evaluate_methodology(
        cls,
        *,
        intent: str,
        digest: Mapping[str, Any] | None = None,
        design_audit: Mapping[str, Any] | None = None,
        selected_objects: Sequence[Mapping[str, Any]] | None = None,
        missing_ids: Sequence[str] | None = None,
        selection_state: str | None = None,
        canonical_pixels: Any = None,
        has_data_source: bool = False,
        explicit_user_choice: str | None = None,
        dominant_family: str | None = None,
        preview_error: Any = None,
        slide_known: bool = True,
        extra_missing_readable: Sequence[str] | None = None,
        extra_missing_user: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        contract = cls._methodology_contract()
        intents = contract.get("intents") or []
        if intent not in intents:
            intent = intents[0] if intents else "REVIEW_SLIDE"
        requirements = (contract.get("factRequirements") or {}).get(intent) or {}
        fact_sources = contract.get("factSources") or {}

        facts: dict[str, Any] = {}
        missing: list[dict[str, Any]] = []

        def _known(name: str, value: Any, epistemic: str) -> None:
            facts[name] = {"value": value, "epistemic": epistemic}

        def _miss(name: str, *, reason: str | None = None) -> None:
            source = fact_sources.get(name) or {}
            entry: dict[str, Any] = {"fact": name, "epistemic": "UNKNOWN"}
            if reason:
                entry["reason"] = reason
            if isinstance(source.get("read"), str) or isinstance(source.get("derived"), str):
                entry["readableVia"] = source.get("read") or source.get("derived")
                entry["userRequired"] = False
            else:
                entry["userRequired"] = True
            missing.append(entry)

        # --- assemble facts from current materials --------------------------
        if isinstance(digest, Mapping):
            rows = int(digest.get("rowCount") or 0)
            if rows > 0:
                _known("data_shape", {
                    "rowCount": rows,
                    "fields": [f.get("name") for f in digest.get("fields") or []],
                }, "FACT")
                metrics = [
                    f.get("name") for f in digest.get("fields") or []
                    if isinstance(f, Mapping) and f.get("role") == "metric"
                ]
                if metrics:
                    _known("primary_metric", metrics[0], "INFERRED")
                temporal = digest.get("temporal") if isinstance(digest.get("temporal"), Mapping) else {}
                _known("time_series", bool(temporal.get("detected")), "FACT")
                cardinality = digest.get("categoryCardinality") if isinstance(digest.get("categoryCardinality"), Mapping) else {}
                if cardinality:
                    _known("category_count", max(cardinality.values()), "FACT")
                if metrics and cardinality:
                    _known("comparison_goal", "category_comparison", "INFERRED")

        objects = [o for o in (selected_objects or []) if isinstance(o, Mapping)]
        if selection_state == "AMBIGUOUS" or len(objects) > 1:
            facts["target_object"] = {
                "value": None,
                "epistemic": "UNKNOWN",
                "note": "AMBIGUOUS_SELECTION",
            }
            missing.append(
                {"fact": "target_object", "epistemic": "UNKNOWN",
                 "reason": "ambiguous_selection", "userRequired": True}
            )
        elif len(objects) == 1:
            _known("target_object", objects[0].get("id"), "FACT")
            block_type = objects[0].get("type")
            if block_type:
                _known("existing_visual_type", str(block_type), "FACT")
        if missing_ids:
            _known("unresolved_selection", list(missing_ids), "FACT")

        if isinstance(design_audit, Mapping):
            issues = [i for i in design_audit.get("issues") or [] if isinstance(i, dict)]
            _known("layout_audit", {"issueCount": len(issues), "issues": [i.get("id") for i in issues]}, "FACT")
            _known("layout_density", "issues" if issues else "clean", "INFERRED")
        if dominant_family:
            _known("dominant_family", str(dominant_family), "FACT")
        if slide_known:
            _known("target_scope", "focused_slide", "FACT")
        if canonical_pixels:
            _known("visual_evidence_available", "canonical_stage", "FACT")

        for name in extra_missing_readable or ():
            _miss(str(name))
        for name in extra_missing_user or ():
            entry = {"fact": str(name), "epistemic": "UNKNOWN", "userRequired": True}
            if all(m.get("fact") != name for m in missing):
                missing.append(entry)

        for name in requirements.get("required") or []:
            if name not in facts and all(m.get("fact") != name for m in missing):
                if name == "data_shape" and digest is None and not has_data_source:
                    _miss(name)
                else:
                    _miss(name)
            elif name in facts and facts[name].get("epistemic") == "UNKNOWN":
                pass

        # --- readiness -------------------------------------------------------
        missing_required = [
            m for m in missing
            if m.get("fact") in (requirements.get("required") or [])
        ]
        missing_optional_known = [
            m for m in missing
            if m.get("fact") in (requirements.get("optional") or [])
        ]
        if preview_error:
            readiness = "BLOCKED"
        elif missing_ids and not objects and intent in {"IMPROVE_EXISTING", "FIX_LAYOUT"}:
            readiness = "MISSING_INFORMATION"
        elif missing_required:
            readiness = "MISSING_INFORMATION"
        elif missing_optional_known or missing:
            readiness = "PARTIAL"
        else:
            readiness = "READY"

        # --- sufficiency -----------------------------------------------------
        readable_missing = [m for m in missing if not m.get("userRequired")]
        if readiness == "BLOCKED":
            sufficiency = "NO_SAFE_RECOMMENDATION"
        elif any(m in missing_required for m in readable_missing):
            sufficiency = "READ_MORE_STATE"
        elif any(m.get("userRequired") for m in missing_required):
            sufficiency = "ASK_USER"
        elif readable_missing:
            sufficiency = "READ_MORE_STATE"
        elif any(m.get("userRequired") for m in missing):
            sufficiency = "ASK_USER"
        else:
            sufficiency = "RECOMMEND_NOW"

        # --- evidence ---------------------------------------------------------
        if canonical_pixels:
            level = "CANONICAL_PIXELS"
        elif isinstance(design_audit, Mapping):
            level = "STRUCTURAL"
        elif facts:
            level = "DOMAIN_STATE"
        else:
            level = "NONE"
        evidence = {
            "level": level,
            "sources": [
                s for s, ok in (
                    ("semanticDigest", isinstance(digest, Mapping)),
                    ("designAudit", isinstance(design_audit, Mapping)),
                    ("editorFocus", bool(objects) or bool(missing_ids)),
                    ("canonical_stage", bool(canonical_pixels)),
                ) if ok
            ],
        }

        # --- strategy / recommendations --------------------------------------
        strategy: dict[str, Any] | None = None
        recommendations: list[dict[str, Any]] = []
        fabricated = False
        if intent == "CHOOSE_VISUAL" and readiness in {"READY", "PARTIAL"}:
            if isinstance(digest, Mapping) and int(digest.get("rowCount") or 0) > 0:
                rec = cls._recommend(digest)
                reasons = [f"{key}={facts[key]['value']}" for key in (
                    "time_series", "category_count", "primary_metric", "comparison_goal"
                ) if key in facts]
                strategy = {
                    "visualFamily": rec.get("recommendedType"),
                    "epistemic": "RECOMMENDED",
                    "reasons": reasons or list(rec.get("reasons") or []),
                    "alternatives": [
                        {**{k: v for k, v in alt.items() if k != "confidence"},
                         "epistemic": "RECOMMENDED"}
                        for alt in rec.get("alternatives") or []
                        if isinstance(alt, dict)
                    ],
                    "rejected": rec.get("rejected") or [],
                }
                if explicit_user_choice:
                    strategy["explicitUserChoice"] = {
                        "visualFamily": str(explicit_user_choice),
                        "respected": True,
                        "epistemic": "FACT",
                        "note": "user intent preserved; recommendation is advisory",
                    }
            else:
                fabricated = strategy is not None
        if isinstance(design_audit, Mapping):
            for issue in design_audit.get("issues") or []:
                if isinstance(issue, dict) and issue.get("recommendation"):
                    recommendations.append(
                        {
                            "id": issue.get("id"),
                            "category": issue.get("category"),
                            "recommendation": issue.get("recommendation"),
                            "safeAutoFix": bool(issue.get("safeAutoFix")),
                            "epistemic": "RECOMMENDED",
                        }
                    )

        # Aesthetic/pixel claims are gated by the evidence ladder — structural
        # or domain evidence never authorizes a beauty verdict.
        aesthetic_gate = None
        if intent == "REVIEW_SLIDE":
            aesthetic_gate = (
                "PIXELS_AVAILABLE"
                if canonical_pixels
                else "PIXELS_REQUIRED_FOR_AESTHETIC_CLAIMS"
            )

        next_action = None
        next_question = None
        if sufficiency == "READ_MORE_STATE" and readable_missing:
            first = readable_missing[0]
            next_action = {
                "kind": "READ",
                "capability": first.get("readableVia") or "get_playlist_context",
                "fact": first.get("fact"),
            }
        elif sufficiency == "ASK_USER":
            target = next(
                (m for m in missing if m.get("userRequired")), None
            )
            if target:
                next_question = {
                    "fact": target.get("fact"),
                    "prompt": _next_question_prompt(str(target.get("fact"))),
                }
                next_action = {"kind": "ASK_USER", "fact": target.get("fact")}
        elif sufficiency == "NO_SAFE_RECOMMENDATION":
            next_action = {"kind": "STOP", "reason": "evidence_or_read_failure"}

        return {
            "version": contract.get("version"),
            "designIntent": intent,
            "readiness": readiness,
            "sufficiency": sufficiency,
            "facts": facts,
            "missingFacts": missing,
            "strategy": strategy,
            "recommendations": recommendations,
            "evidence": evidence,
            "nextAction": next_action,
            "nextQuestion": next_question,
            "aestheticGate": aesthetic_gate,
            "_fabricated": fabricated,
        }

    @classmethod
    def semantic_digest(
        cls,
        rows: list[Mapping[str, Any]] | None,
        *,
        columns: list[str] | None = None,
    ) -> dict[str, Any]:
        typed = [row for row in (rows or []) if isinstance(row, Mapping)]
        names = list(columns or [])
        if not names and typed:
            names = [str(key) for key in typed[0].keys()]
        fields: list[dict[str, Any]] = []
        temporal = {"detected": False}
        category_cardinality: dict[str, int] = {}
        ranking: list[str] = []
        goals: list[str] = []
        composition: list[str] = []
        trends: list[str] = []
        for name in names:
            sample = next((row.get(name) for row in typed if name in row), None)
            role = _role_for(name, sample)
            unit = _unit_for(name, sample)
            cardinality = None
            if role in {"category", "dimension"} and typed:
                cardinality = len({str(row.get(name)) for row in typed if row.get(name) is not None})
                category_cardinality[name] = cardinality
                if cardinality and cardinality > 4:
                    ranking.append(name)
                if cardinality and cardinality <= 5:
                    composition.append(name)
            if role == "temporal":
                temporal = {"detected": True, "field": name}
                trends.append(name)
            if role == "goal":
                goals.append(name)
            if role == "metric" and temporal.get("detected"):
                trends.append(name)
            fields.append(
                {
                    "name": name,
                    "role": role,
                    "dataType": _data_type(sample),
                    "unit": unit,
                    "cardinality": cardinality,
                }
            )
        return {
            "fields": fields,
            "rowCount": len(typed),
            "temporal": temporal,
            "categoryCardinality": category_cardinality,
            "rankingCandidates": ranking,
            "goalCandidates": goals,
            "compositionCandidates": composition,
            "trendCandidates": trends,
        }

    @classmethod
    def _recommend(cls, digest: Mapping[str, Any]) -> dict[str, Any]:
        temporal = digest.get("temporal") if isinstance(digest.get("temporal"), dict) else {}
        ranking = digest.get("rankingCandidates") if isinstance(digest.get("rankingCandidates"), list) else []
        goals = digest.get("goalCandidates") if isinstance(digest.get("goalCandidates"), list) else []
        composition = (
            digest.get("compositionCandidates")
            if isinstance(digest.get("compositionCandidates"), list)
            else []
        )
        rejected: list[dict[str, str]] = []
        alternatives: list[dict[str, str]] = []
        metrics = [
            field
            for field in digest.get("fields") or []
            if isinstance(field, dict) and field.get("role") == "metric"
        ]
        if temporal.get("detected") and metrics:
            rejected.append({"type": "pie", "reason": "temporal series is not a composition"})
            rejected.append({"type": "doughnut", "reason": "temporal series is not a composition"})
            return {
                "recommendedType": "line",
                "confidence": 0.86,
                "reasons": ["temporal dimension plus metric"],
                "alternatives": [{"type": "area", "reason": "same trend, filled"}],
                "rejected": rejected,
            }
        if goals and metrics:
            return {
                "recommendedType": "gauge",
                "confidence": 0.8,
                "reasons": ["metric and goal present"],
                "alternatives": [{"type": "kpi_view", "reason": "hero KPI with progress"}],
                "rejected": [{"type": "pie", "reason": "goal progress is not a composition"}],
            }
        if ranking and metrics:
            return {
                "recommendedType": "horizontal_bar",
                "confidence": 0.82,
                "reasons": ["category cardinality above 4"],
                "alternatives": [{"type": "table_view", "reason": "exact values"}],
                "rejected": [{"type": "pie", "reason": "too many categories"}],
            }
        if composition and metrics:
            return {
                "recommendedType": "doughnut",
                "confidence": 0.7,
                "reasons": ["low-cardinality composition candidate"],
                "alternatives": [{"type": "bar", "reason": "safer comparison"}],
                "rejected": [],
            }
        if metrics and not ranking and not composition:
            return {
                "recommendedType": "kpi_view",
                "confidence": 0.6,
                "reasons": ["single metric snapshot"],
                "alternatives": [{"type": "bar", "reason": "if a category emerges"}],
                "rejected": [],
            }
        # No metric evidence: an exact listing is the honest family — never a
        # fabricated categorical chart on shapeless string data.
        return {
            "recommendedType": "table_view",
            "confidence": 0.4,
            "reasons": ["no metric detected — exact listing is safe"],
            "alternatives": [{"type": "kpi_view", "reason": "if a metric is bound"}],
            "rejected": [],
        }

    @classmethod
    def design_audit(cls, native_config: Mapping[str, Any] | None) -> dict[str, Any]:
        raw_issues = SlideLayoutQualityService.collect_native_layout_issues(native_config)
        issues = [_enrich_issue(code) for code in raw_issues]
        return {
            "issues": issues,
            "signals": {"issueCount": len(issues)},
            "layout": {"issueCodes": raw_issues},
        }

    @classmethod
    def visual_recommendation(
        cls,
        digest: Mapping[str, Any],
        *,
        dominant_visual_family: str | None = None,
    ) -> dict[str, Any]:
        rec = cls._recommend(digest)
        # Legacy heuristic score kept for wire compat; methodology decisions
        # never depend on it (PHASE 5 — evidence/readiness are the contract).
        rec["confidenceStatus"] = "LEGACY_UNCALIBRATED"
        family = str(dominant_visual_family or "").strip()
        if not family:
            return rec
        rejected = {
            str(item.get("type") or "")
            for item in rec.get("rejected") or []
            if isinstance(item, dict)
        }
        alternatives = [
            item
            for item in rec.get("alternatives") or []
            if isinstance(item, dict)
            and str(item.get("type") or "") not in rejected
            and str(item.get("type") or "") != family
        ]
        reasons = list(rec.get("reasons") or [])
        recommended = str(rec.get("recommendedType") or "")
        if recommended == family and alternatives:
            recommended = str(alternatives[0].get("type") or recommended)
            reasons.append("dominant visual family is repetitive")
        elif recommended == family:
            reasons.append("no compatible alternative for the repetitive family")
        return {
            **rec,
            "recommendedType": recommended,
            "reasons": reasons,
            "alternatives": alternatives,
        }


_QUESTION_PROMPTS: dict[str, str] = {
    "comparison_goal": "Você quer comparar as categorias entre si ou mostrar a evolução ao longo do tempo?",
    "slide_purpose": "Qual é o objetivo principal deste slide para o público da TV?",
    "display_context": "Este slide será exibido em modo kiosk (TV) ou usado em detalhe?",
    "target_object": "Qual bloco você quer que eu altere? Selecione no editor ou indique o alvo.",
}


def _next_question_prompt(fact: str) -> str:
    return _QUESTION_PROMPTS.get(fact) or f"Falta um fato para decidir: {fact}."


_ISSUE_PROFILES: dict[str, dict[str, Any]] = {
    "kpi_density_exceeded": {
        "category": "density",
        "message": "Há indicadores demais para um único slide.",
        "recommendation": "Distribua os KPIs em outra tela ou use a grade de quatro.",
        "recommendedRecipe": "TV_KPI_GRID_4",
        "safeAutoFix": False,
    },
    "block_overlap": {
        "category": "layout",
        "message": "Blocos se sobrepõem acima do limite do layout.",
        "recommendation": "Reposicione os blocos nos slots da recipe.",
        "safeAutoFix": True,
    },
    "block_frame_overflow": {
        "category": "layout",
        "message": "O frame do bloco sai da área do slide.",
        "recommendation": "Traga o frame para dentro da safe area.",
        "safeAutoFix": True,
    },
    "block_frame_non_positive": {
        "category": "layout",
        "message": "O frame do bloco tem largura ou altura inválida.",
        "recommendation": "Defina um frame positivo dentro da safe area.",
        "safeAutoFix": True,
    },
    "safe_area_violation": {
        "category": "layout",
        "message": "O frame invade a margem segura do slide.",
        "recommendation": "Afaste o bloco da borda usando safeMargin.",
        "safeAutoFix": True,
    },
    "widescreen_single_data_visual": {
        "category": "layout",
        "message": "Um único visual de dado ocupa a tela inteira.",
        "recommendation": "Adicione hierarquia (título ou KPI) se o pedido pedir composição.",
        "safeAutoFix": False,
    },
    "low_contrast": {
        "category": "typography",
        "message": "O contraste do texto está abaixo do mínimo da TV.",
        "recommendation": "Use a cor de texto dos design tokens.",
        "safeAutoFix": True,
    },
    "part_font_below_min": {
        "category": "typography",
        "message": "A tipografia da parte está abaixo do mínimo do token.",
        "recommendation": "Eleve fontSize até o mínimo de partChrome.",
        "safeAutoFix": True,
    },
    "hierarchy_inverted": {
        "category": "typography",
        "message": "A hierarquia tipográfica da parte está invertida.",
        "recommendation": "O valor numérico precisa ficar maior que o título.",
        "safeAutoFix": True,
    },
}


def _enrich_issue(code: str) -> dict[str, Any]:
    prefix = code.split(":", 1)[0]
    profile = _ISSUE_PROFILES.get(prefix) or {
        "category": "layout",
        "message": code,
        "recommendation": "Revise o layout no módulo de qualidade do slide.",
        "safeAutoFix": False,
    }
    issue: dict[str, Any] = {
        "id": code,
        "severity": "warning",
        "category": profile["category"],
        "message": profile["message"],
        "blockIds": _block_ids_from_code(code),
        "recommendation": profile["recommendation"],
        "safeAutoFix": bool(profile["safeAutoFix"]),
        "evidence": {"code": code},
    }
    recipe = profile.get("recommendedRecipe")
    if recipe:
        issue["recommendedRecipe"] = recipe
    return issue


def _block_ids_from_code(code: str) -> list[str]:
    parts = code.split(":")
    if len(parts) < 2:
        return []
    prefix = parts[0]
    if prefix == "block_overlap":
        return [item for item in parts[1].split("~") if item]
    if prefix in {
        "block_frame_overflow",
        "block_frame_non_positive",
        "safe_area_violation",
        "low_contrast",
        "part_font_below_min",
        "hierarchy_inverted",
    }:
        return [parts[1]] if parts[1] else []
    return []


def _role_for(name: str, sample: Any) -> str:
    key = name.lower()
    if key in _TEMPORAL_KEYS or key.endswith("_date"):
        return "temporal"
    if any(hint in key for hint in _GOAL_HINTS):
        return "goal"
    if isinstance(sample, (int, float)) and not isinstance(sample, bool):
        return "metric"
    if key in _LABEL_KEYS:
        return "temporal" if key in _TEMPORAL_KEYS else "category"
    return "dimension"


def _unit_for(name: str, sample: Any) -> str | None:
    key = name.lower()
    if any(hint in key for hint in _PERCENT_HINTS):
        return "percent"
    if any(hint in key for hint in _CURRENCY_HINTS):
        return "currency"
    if isinstance(sample, int) and not isinstance(sample, bool):
        return "integer"
    if isinstance(sample, float):
        return "number"
    return None


def _data_type(sample: Any) -> str:
    if isinstance(sample, bool):
        return "boolean"
    if isinstance(sample, int):
        return "integer"
    if isinstance(sample, float):
        return "number"
    return "string"
