#!/usr/bin/env python3
"""Gate: entityProfiles não duplica perfis substituíveis pelo OpenAPI (Fase 12)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)

configure_domain_infrastructure_ports()


def validate() -> dict:
    replaceable = ChatPresentationProfileService.node("openapiReplaceableProfileKeys") or []
    replaceable_set = {str(item).strip() for item in replaceable if str(item).strip()}
    entity_profiles = ChatPresentationProfileService.mapping("entityProfiles")
    violations = sorted(
        entity
        for entity, profile in entity_profiles.items()
        if str(profile).strip() in replaceable_set
    )
    catch_all_fragments = {"/supplies/", "/financial/", "/commercial/"}
    path_rules = ChatPresentationProfileService.node("pathRules") or []
    catch_all_rules = [
        rule
        for rule in path_rules
        if isinstance(rule, dict)
        and rule.get("contains") in catch_all_fragments
        and rule.get("profile") == "kpi_series"
    ]

    return {
        "ok": not violations and not catch_all_rules,
        "replaceableProfileKeys": sorted(replaceable_set),
        "entityProfileViolations": violations,
        "catchAllPathRuleViolations": catch_all_rules,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Exit 1 quando houver violações.")
    parser.add_argument("--json", action="store_true", help="Imprime relatório JSON.")
    args = parser.parse_args()

    report = validate()

    if args.json or not args.check:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.check and not report["ok"]:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
