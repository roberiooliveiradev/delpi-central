#!/usr/bin/env python3
"""Audita acoplamento template×LLM — gates canônicos e anti-padrões."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_APP = ROOT / "app"
MFE_SRC = ROOT.parent / "plugins" / "minha-delpi-chat" / "src"
PROSE_DELIVERY_JSON = API_APP / "content/pt-BR/assistant/presentation_prose_delivery.json"
HUMANIZED_JSON = API_APP / "content/pt-BR/assistant/humanized_data_response.json"
PROFILES_JSON = API_APP / "content/pt-BR/assistant/presentation_profiles.json"

CANONICAL_GATE = "ChatPresentationProseDeliveryService"
DECOUPLE_SERVICE = "ChatPresentationLlmProseDecouplingService"
NARRATIVE_GATE = "ChatOperationalNarrativeSynthesisService"

REQUIRED_CALLSITES = {
    API_APP / "application/services/chat_turn/chat_turn_preparation_post_tool_resolution_service.py": CANONICAL_GATE,
    API_APP / "application/use_cases/admin_agent_simulate_use_case.py": "apply_to_tool_context_result",
    API_APP / "domain/services/chat_response_mode_service.py": "ChatPresentationProseDeliveryService.resolve_mode",
}

ANTI_PATTERNS = [
    (
        "product_overview_template_fallback",
        re.compile(r"should_force_llm_synthesis[\s\S]{0,120}authorized_tool_answer"),
        set(),
    ),
]

ALLOWLIST_FILES = frozenset(
    {
        "chat_presentation_prose_delivery_service.py",
        "chat_presentation_data_only_prose_service.py",
        "chat_presentation_llm_prose_decoupling_service.py",
        "chat_operational_commentary_enrichment_service.py",
        "chat_tool_context_external_action_formatter.py",
        "chat_tool_context_presentation_service.py",
        "chat_tool_context_service.py",
        "chat_response_mode_synthesis_quality_service.py",
        "chat_turn_preparation_post_tool_resolution_service.py",
        "chat_rich_presentation_text_service.py",
        "chat_external_action_direct_answer_service.py",
        "chat_composite_direct_answer_service.py",
        "chat_product_query_intent_service.py",
        "chat_data_interpretation_answer_service.py",
        "text_presentation_presenter.py",
    }
)

DIRECT_LINHAS_PATTERN = re.compile(
    r'humanized(?:Summary)?\.get\(\s*["\']linhas(?:_detalhe)?["\']',
)

DIRECT_LINHAS_ALLOW_DIRS = frozenset(
    {
        "external_actions/presenters",
        "tests",
    }
)

MFE_DECOUPLE_MARKERS = [
    "isLlmProseDecoupledFromToolCalls",
    "isLlmProseDecoupledMetadata",
    "resolveLeadMarkdownSource",
]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def audit_required_callsites() -> list[str]:
    issues: list[str] = []

    for path, symbol in REQUIRED_CALLSITES.items():
        body = _read(path)

        if symbol not in body:
            issues.append(f"callsite ausente: {path.relative_to(ROOT)} não referencia {symbol}")

    return issues


def audit_canonical_modules_exist() -> list[str]:
    issues: list[str] = []
    modules = [
        API_APP / "domain/services/chat_presentation_prose_delivery_service.py",
        API_APP / "domain/services/chat_presentation_llm_prose_decoupling_service.py",
        API_APP / "content/pt-BR/assistant/presentation_prose_delivery.json",
    ]

    for path in modules:
        if not path.is_file():
            issues.append(f"módulo canônico ausente: {path.relative_to(ROOT)}")

    return issues


def audit_mfe_decouple_helpers() -> list[str]:
    issues: list[str] = []
    normalization = MFE_SRC / "ui/components/presentation/presentationMarkdownNormalization.ts"
    body = _read(normalization)

    for marker in MFE_DECOUPLE_MARKERS:
        if marker not in body:
            issues.append(f"MFE sem helper canônico `{marker}` em presentationMarkdownNormalization.ts")

    return issues


def audit_direct_humanized_linhas_reads() -> list[str]:
    """Consumidores pós-pipeline devem usar ChatPresentationProseDeliveryService helpers."""
    issues: list[str] = []

    for py_file in API_APP.rglob("*.py"):
        rel = py_file.relative_to(ROOT)
        rel_posix = rel.as_posix()

        if any(part in rel_posix for part in DIRECT_LINHAS_ALLOW_DIRS):
            continue

        if py_file.name in ALLOWLIST_FILES:
            continue

        body = _read(py_file)

        if not DIRECT_LINHAS_PATTERN.search(body):
            continue

        issues.append(
            f"leitura direta de humanized.linhas em {rel_posix} "
            f"(usar ChatPresentationProseDeliveryService.resolve_humanized_lines_*)"
        )

    return issues


def audit_anti_patterns() -> list[str]:
    issues: list[str] = []

    for py_file in API_APP.rglob("*.py"):
        body = _read(py_file)
        rel = str(py_file.relative_to(ROOT))

        for name, pattern, allowed in ANTI_PATTERNS:
            if not pattern.search(body):
                continue

            if py_file.name in ALLOWLIST_FILES:
                continue

            if any(token in rel or token in body for token in allowed):
                continue

            if name == "product_overview_template_fallback" and "post_tool" not in rel:
                continue

            issues.append(f"anti-padrão `{name}` em {rel}")

    return issues


def _load_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return payload if isinstance(payload, dict) else {}


def audit_tier_and_entity_set_config() -> list[str]:
    issues: list[str] = []
    prose = _load_json(PROSE_DELIVERY_JSON)
    profiles = _load_json(PROFILES_JSON)

    settings = prose.get("settings") if isinstance(prose.get("settings"), dict) else {}
    llm_everywhere = bool(settings.get("llmProseEverywhere"))

    by_tier = prose.get("proseDeliveryByTier")
    required_tiers = ("A", "B", "C") if llm_everywhere else ("A", "B")

    if not isinstance(by_tier, dict):
        issues.append("presentation_prose_delivery.json sem proseDeliveryByTier")
    else:
        for tier in required_tiers:
            mode = str(by_tier.get(tier) or "").strip().lower()

            if mode not in {"template", "llm"}:
                issues.append(
                    f"proseDeliveryByTier.{tier} ausente ou inválido (esperado template|llm)"
                )

        if llm_everywhere:
            for tier in required_tiers:
                if str(by_tier.get(tier) or "").lower() != "llm":
                    issues.append(
                        f"proseDeliveryByTier.{tier} deve ser llm (llmProseEverywhere ativo)"
                    )
        else:
            if str(by_tier.get("A") or "").lower() != "llm":
                issues.append("proseDeliveryByTier.A deve ser llm (narrativa tier A)")

            if str(by_tier.get("B") or "").lower() != "template":
                issues.append("proseDeliveryByTier.B deve ser template (KPI/listagem tier B)")

    if llm_everywhere and not settings.get("deprecateHumanizedLinhasAsProse"):
        issues.append(
            "llmProseEverywhere ativo exige deprecateHumanizedLinhasAsProse=true (playbook-19 P6)"
        )

    if llm_everywhere and settings.get("allowTemplateProseFallback"):
        issues.append(
            "llmProseEverywhere ativo exige allowTemplateProseFallback=false (playbook-19 P8.1)"
        )

    by_entity_set = profiles.get("proseDeliveryByEntitySet")

    if not isinstance(by_entity_set, dict):
        issues.append("presentation_profiles.json sem proseDeliveryByEntitySet")
    else:
        expected_entity_set_mode = "llm" if llm_everywhere else "template"

        for set_key in ("playbookOperational", "productListPresent"):
            mode = str(by_entity_set.get(set_key) or "").strip().lower()

            if mode != expected_entity_set_mode:
                issues.append(
                    f"proseDeliveryByEntitySet.{set_key} deve ser {expected_entity_set_mode}"
                    + (" (llmProseEverywhere ativo)" if llm_everywhere else " (listagem auditável)")
                )

    return issues


def audit_commentary_profiles_registry() -> list[str]:
    """W1b — todo commentaryProfileKey operacional deve existir em humanized_data_response."""
    issues: list[str] = []
    humanized = _load_json(HUMANIZED_JSON)
    profiles = _load_json(PROFILES_JSON)
    commentary_profiles = humanized.get("commentaryProfiles")

    if not isinstance(commentary_profiles, dict):
        issues.append("humanized_data_response.json sem commentaryProfiles")
        return issues

    registered_strategies = frozenset(
        {
            "none",
            "highlight_rules",
            "factory_status",
            "stock",
            "production_status",
            "shipping_status",
            "directives",
            "sale_pricing_insight",
            "analyser_divergence",
        }
    )

    for profile_key, config in commentary_profiles.items():
        if not isinstance(config, dict):
            issues.append(f"commentaryProfiles.{profile_key} deve ser objeto")
            continue

        strategy = str(config.get("builderStrategy") or "").strip()

        if strategy and strategy not in registered_strategies:
            issues.append(
                f"commentaryProfiles.{profile_key}.builderStrategy inválido: {strategy}"
            )

        content_section = str(config.get("contentSection") or "").strip()

        if strategy and strategy != "none" and not content_section:
            issues.append(
                f"commentaryProfiles.{profile_key} sem contentSection (builderStrategy={strategy})"
            )

    entity_profiles = profiles.get("entityProfiles")

    if isinstance(entity_profiles, dict):
        referenced: set[str] = set()

        for profile in entity_profiles.values():
            if not isinstance(profile, dict):
                continue

            key = str(profile.get("commentaryProfileKey") or "").strip()

            if key:
                referenced.add(key)

        operational_keys = {
            "factory_status",
            "stock",
            "production_status",
            "shipping_status",
            "directives",
            "structure_exclusivity",
            "sale_pricing",
            "analyser",
        }

        for key in sorted(referenced & operational_keys):
            if key not in commentary_profiles:
                issues.append(
                    f"commentaryProfileKey «{key}» em presentation_profiles sem entrada em commentaryProfiles"
                )

    exclusivity = commentary_profiles.get("structure_exclusivity")

    if not isinstance(exclusivity, dict):
        issues.append("commentaryProfiles.structure_exclusivity ausente (caso modelo W1)")
    elif exclusivity.get("templateProseCommentary") != "skip":
        issues.append(
            "commentaryProfiles.structure_exclusivity.templateProseCommentary deve ser skip (W1b)"
        )

    orchestration_path = (
        API_APP
        / "domain/services/chat_operational_data_commentary/chat_operational_data_commentary_orchestration_service.py"
    )
    orchestration_body = _read(orchestration_path)

    if 'builders = {' in orchestration_body:
        issues.append(
            "orchestration ainda usa mapa builders hardcoded por profile_key (usar registry JSON)"
        )

    return issues


def audit_presentation_profile_declarative_w2() -> list[str]:
    """W2 — frozensets e mapas de perfil devem viver em presentation_profiles.json."""
    issues: list[str] = []
    profiles = _load_json(PROFILES_JSON)
    entity_sets = profiles.get("entitySets") if isinstance(profiles.get("entitySets"), dict) else {}

    for set_key in ("textFirstProfiles", "tierAProfileKeys"):
        raw = entity_sets.get(set_key)

        if not isinstance(raw, list) or not raw:
            issues.append(f"entitySets.{set_key} ausente ou vazio em presentation_profiles.json")

    entity_table_profiles = profiles.get("entityTableProfiles")

    if not isinstance(entity_table_profiles, dict) or not entity_table_profiles:
        issues.append("entityTableProfiles ausente ou vazio em presentation_profiles.json")

    hardcoded_targets = {
        API_APP
        / "domain/services/chat_presentation_text_first_policy_service.py": "_TEXT_FIRST_PROFILES",
        API_APP
        / "domain/services/chat_presentation_visual_ui_hint_service.py": "_PROFILE_ROUTE_NAMESPACE",
        API_APP
        / "domain/services/chat_presentation_table_profile_inference_service.py": "_ENTITY_TABLE_PROFILES",
        API_APP
        / "domain/services/chat_presentation_coverage_service.py": "_RICH_PRODUCT_PATH_TOKENS",
        API_APP
        / "domain/services/chat_operational_refinement/chat_operational_refinement_vocabulary.py": "PAGINATED_PATH_FRAGMENTS = (",
    }

    for path, marker in hardcoded_targets.items():
        body = _read(path)

        if marker in body:
            issues.append(f"hardcoded W2 remanescente em {path.relative_to(ROOT)}: {marker}")

    profile_nodes = profiles.get("profiles") if isinstance(profiles.get("profiles"), dict) else {}
    visual_hint_profiles = {
        str(item).strip()
        for item in (entity_sets.get("visualHintProfileKeys") or [])
        if str(item).strip()
    }

    for profile_key in sorted(visual_hint_profiles):
        profile = profile_nodes.get(profile_key)

        if not isinstance(profile, dict):
            continue

        if not str(profile.get("routeNamespace") or "").strip():
            issues.append(
                f"profiles.{profile_key}.routeNamespace ausente (tier A exige namespace de hints)"
            )

    return issues


def build_prose_delivery_metrics_report() -> dict[str, object]:
    profiles = _load_json(PROFILES_JSON)
    prose = _load_json(PROSE_DELIVERY_JSON)

    by_entity = profiles.get("proseDeliveryByEntity") or {}
    by_profile = profiles.get("proseDeliveryByProfile") or {}
    by_entity_set = profiles.get("proseDeliveryByEntitySet") or {}
    by_tier = prose.get("proseDeliveryByTier") or {}

    entity_modes: dict[str, int] = {}
    for mode in by_entity.values():
        token = str(mode or "").strip().lower()
        entity_modes[token] = entity_modes.get(token, 0) + 1

    profile_modes: dict[str, int] = {}
    for mode in by_profile.values():
        token = str(mode or "").strip().lower()
        profile_modes[token] = profile_modes.get(token, 0) + 1

    return {
        "proseDeliveryByEntity": {"count": len(by_entity), "byMode": entity_modes},
        "proseDeliveryByProfile": {"count": len(by_profile), "byMode": profile_modes},
        "proseDeliveryByEntitySet": dict(by_entity_set),
        "proseDeliveryByTier": dict(by_tier),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 se houver issues")
    parser.add_argument(
        "--report-metrics",
        action="store_true",
        help="Imprime JSON com contagem template/llm por camada declarativa",
    )
    args = parser.parse_args()

    if args.report_metrics:
        print(json.dumps(build_prose_delivery_metrics_report(), ensure_ascii=False, indent=2))
        return 0

    issues = [
        *audit_canonical_modules_exist(),
        *audit_required_callsites(),
        *audit_mfe_decouple_helpers(),
        *audit_direct_humanized_linhas_reads(),
        *audit_anti_patterns(),
        *audit_tier_and_entity_set_config(),
        *audit_commentary_profiles_registry(),
        *audit_presentation_profile_declarative_w2(),
    ]

    if not issues:
        print("audit_presentation_prose_delivery: OK")
        return 0

    print("audit_presentation_prose_delivery: issues encontradas\n")

    for item in issues:
        print(f"  - {item}")

    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
