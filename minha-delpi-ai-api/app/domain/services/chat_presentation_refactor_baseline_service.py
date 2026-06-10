"""Inventário de débito técnico — apresentação declarativa (Playbook 12, fase R0)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.domain.services.chat_presentation_profile_service import (
    ChatPresentationProfileService,
)
from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)


@dataclass(frozen=True)
class PathConditionalHit:
    line: int
    kind: str
    text: str


@dataclass(frozen=True)
class FileAuditResult:
    relative_path: str
    line_count: int
    path_conditional_count: int
    path_conditional_hits: tuple[PathConditionalHit, ...]
    dedicated_enrich_methods: tuple[str, ...]
    profile_flag_variables: tuple[str, ...]


class ChatPresentationRefactorBaselineService:
    @classmethod
    def package_root(cls) -> Path:
        return Path(__file__).resolve().parents[3]

    @classmethod
    def default_stored_baseline_path(cls) -> Path:
        return cls.package_root() / "docs" / "architecture" / "presentation-refactor-baseline-jun2026.json"

    @classmethod
    def audit_file_paths(cls) -> tuple[Path, ...]:
        root = cls.package_root()
        return tuple(root / relative for relative in ChatPresentationVocabularyService.playbook12_audit_files())

    @classmethod
    def tier_a_profile_keys(cls) -> tuple[str, ...]:
        return ChatPresentationVocabularyService.playbook12_tier_a_profile_keys()

    @classmethod
    def scan_file(cls, file_path: Path) -> FileAuditResult:
        relative = str(file_path.relative_to(cls.package_root()))
        text = file_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        hits: list[PathConditionalHit] = []
        enrich_methods: list[str] = []
        profile_flags: list[str] = []

        path_literal_in = ChatPresentationVocabularyService.playbook12_scan_pattern("pathLiteralIn")
        route_policy_is = ChatPresentationVocabularyService.playbook12_scan_pattern("routePolicyIs")
        path_fragment_elif = ChatPresentationVocabularyService.playbook12_scan_pattern("pathFragmentElif")
        dedicated_enrich = ChatPresentationVocabularyService.playbook12_scan_pattern("dedicatedEnrich")
        profile_flag = ChatPresentationVocabularyService.playbook12_scan_pattern("profileFlag")

        for index, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if path_literal_in.search(line):
                hits.append(PathConditionalHit(index, "path_literal_in", stripped))
            elif route_policy_is.search(line):
                hits.append(PathConditionalHit(index, "route_policy_is", stripped))
            elif path_fragment_elif.search(line):
                hits.append(PathConditionalHit(index, "path_fragment_elif", stripped))

            enrich_match = dedicated_enrich.match(line)
            if enrich_match:
                enrich_methods.append(enrich_match.group(1))

            flag_match = profile_flag.match(line)
            if flag_match:
                profile_flags.append(flag_match.group(1))

        return FileAuditResult(
            relative_path=relative,
            line_count=len(lines),
            path_conditional_count=len(hits),
            path_conditional_hits=tuple(hits),
            dedicated_enrich_methods=tuple(enrich_methods),
            profile_flag_variables=tuple(profile_flags),
        )

    @classmethod
    def profile_declaration_gaps(cls) -> dict[str, list[str]]:
        profiles = ChatPresentationProfileService.node("profiles") or {}
        missing_visual: list[str] = []
        missing_assembly: list[str] = []
        missing_section_rules: list[str] = []

        for key in sorted(profiles):
            profile = profiles.get(key) or {}
            if not isinstance(profile, dict):
                continue

            if not profile.get("visualBuilders"):
                missing_visual.append(key)

            if not profile.get("tableAssembly"):
                missing_assembly.append(key)

            stack_key = str(profile.get("stackPlan") or "default").strip() or "default"
            stack_plan = ChatPresentationProfileService.node("stackPlans", stack_key) or {}
            stack_section_rules = (
                isinstance(stack_plan, dict)
                and isinstance(stack_plan.get("sectionRules"), dict)
                and stack_plan["sectionRules"].get("enabled")
            )

            if (
                not profile.get("sectionRules")
                and not profile.get("stackSectionRules")
                and not stack_section_rules
            ):
                missing_section_rules.append(key)

        tier_a = cls.tier_a_profile_keys()
        return {
            "missingVisualBuilders": missing_visual,
            "missingTableAssembly": missing_assembly,
            "missingSectionRules": missing_section_rules,
            "tierAMissingVisualBuilders": [key for key in tier_a if key in missing_visual],
            "tierAMissingTableAssembly": [key for key in tier_a if key in missing_assembly],
            "tierAMissingSectionRules": [key for key in tier_a if key in missing_section_rules],
        }

    @classmethod
    def build_report(cls) -> dict[str, Any]:
        file_results = [cls.scan_file(path) for path in cls.audit_file_paths()]
        profile_gaps = cls.profile_declaration_gaps()
        table_assembly_fragments = ChatPresentationVocabularyService.playbook12_table_assembly_path_fragments()
        tier_a_keys = cls.tier_a_profile_keys()

        total_path_conditionals = sum(item.path_conditional_count for item in file_results)
        dedicated_enrich = sorted(
            {
                method
                for item in file_results
                for method in item.dedicated_enrich_methods
            }
        )
        profile_flags = sorted(
            {
                flag
                for item in file_results
                for flag in item.profile_flag_variables
            }
        )

        use_case = next(
            (item for item in file_results if item.relative_path.endswith("execute_external_action_use_case.py")),
            None,
        )
        section_availability = next(
            (
                item
                for item in file_results
                if item.relative_path.endswith("chat_presentation_section_availability_service.py")
            ),
            None,
        )
        visual_bundle = next(
            (
                item
                for item in file_results
                if item.relative_path.endswith("chat_presentation_visual_bundle_service.py")
            ),
            None,
        )

        use_case_table_assembly = 0
        if use_case is not None:
            use_case_table_assembly = sum(
                1
                for hit in use_case.path_conditional_hits
                if hit.kind == "path_literal_in"
                and any(fragment in hit.text for fragment in table_assembly_fragments)
            )

        section_route_handlers = 0
        if section_availability is not None:
            section_route_handlers = sum(
                1
                for hit in section_availability.path_conditional_hits
                if hit.kind == "route_policy_is"
            )

        return {
            "generatedAt": datetime.now(tz=UTC).isoformat(),
            "playbook": "12-R0",
            "summary": {
                "auditFileCount": len(file_results),
                "totalPathConditionals": total_path_conditionals,
                "dedicatedEnrichMethodCount": len(dedicated_enrich),
                "profileFlagVariableCount": len(profile_flags),
                "useCaseTableAssemblyPathConditionalCount": use_case_table_assembly,
                "sectionAvailabilityRouteHandlerCount": section_route_handlers,
                "sectionAvailabilityLineCount": section_availability.line_count if section_availability else 0,
                "visualBundleDedicatedEnrichCount": len(visual_bundle.dedicated_enrich_methods)
                if visual_bundle
                else 0,
                "tierAProfileCount": len(tier_a_keys),
                "tierAMissingVisualBuildersCount": len(profile_gaps["tierAMissingVisualBuilders"]),
                "tierAMissingTableAssemblyCount": len(profile_gaps["tierAMissingTableAssembly"]),
            },
            "targets": ChatPresentationVocabularyService.playbook12_targets(),
            "profileGaps": profile_gaps,
            "dedicatedEnrichMethods": dedicated_enrich,
            "profileFlagVariables": profile_flags,
            "files": [
                {
                    "relativePath": item.relative_path,
                    "lineCount": item.line_count,
                    "pathConditionalCount": item.path_conditional_count,
                    "pathConditionalHits": [asdict(hit) for hit in item.path_conditional_hits],
                    "dedicatedEnrichMethods": list(item.dedicated_enrich_methods),
                    "profileFlagVariables": list(item.profile_flag_variables),
                }
                for item in file_results
            ],
        }

    @classmethod
    def write_baseline(cls, target: Path | None = None) -> Path:
        destination = target or cls.default_stored_baseline_path()
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(cls.build_report(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return destination

    @classmethod
    def load_stored_baseline(cls, path: Path | None = None) -> dict[str, Any]:
        target = path or cls.default_stored_baseline_path()
        return json.loads(target.read_text(encoding="utf-8"))

    @classmethod
    def compare_to_stored(cls, stored: dict[str, Any] | None = None) -> dict[str, Any]:
        current = cls.build_report()
        baseline = stored or cls.load_stored_baseline()
        drift: list[dict[str, Any]] = []

        current_summary = current.get("summary") or {}
        baseline_summary = baseline.get("summary") or {}

        for key, baseline_value in baseline_summary.items():
            current_value = current_summary.get(key)
            if current_value != baseline_value:
                drift.append(
                    {
                        "field": f"summary.{key}",
                        "baseline": baseline_value,
                        "current": current_value,
                    }
                )

        baseline_files = {
            item["relativePath"]: item
            for item in baseline.get("files") or []
            if isinstance(item, dict)
        }
        for file_item in current.get("files") or []:
            if not isinstance(file_item, dict):
                continue
            relative = file_item.get("relativePath")
            baseline_item = baseline_files.get(relative)
            if baseline_item is None:
                drift.append(
                    {
                        "field": f"files.{relative}",
                        "baseline": None,
                        "current": file_item.get("pathConditionalCount"),
                    }
                )
                continue

            if file_item.get("pathConditionalCount") != baseline_item.get("pathConditionalCount"):
                drift.append(
                    {
                        "field": f"files.{relative}.pathConditionalCount",
                        "baseline": baseline_item.get("pathConditionalCount"),
                        "current": file_item.get("pathConditionalCount"),
                    }
                )

        return {
            "ok": not drift,
            "drift": drift,
            "currentSummary": current_summary,
            "baselineSummary": baseline_summary,
        }
