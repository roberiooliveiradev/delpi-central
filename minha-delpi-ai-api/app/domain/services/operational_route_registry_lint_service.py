"""Lint DOCIE — operational_route_registry e vocabulário centralizado."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from app.domain.services.external_actions.external_action_response_content_service import (
    ExternalActionResponseContentService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)
from app.domain.services.operational_route_registry_service import (
    OperationalRouteRegistryService,
)


_API_DELPI_PATH_PATTERN = re.compile(
    r"""["'](?:/products/\{code\}|factory-status|production-status|shipping-status|last-purchase|raw-material-price-intelligence|cost-impact-simulation)["']""",
    re.IGNORECASE,
)

_SCANNED_PYTHON_RELATIVE = (
    "app/application/services/external_actions/external_action_selection_dispatch_service.py",
    "app/application/services/external_actions/external_action_selection_preflight_service.py",
    "app/application/services/external_actions/external_action_session_refinement_phase_service.py",
    "app/application/services/external_actions/external_action_candidate_prioritization_service.py",
    "app/application/services/external_actions/external_action_route_selection_service.py",
    "app/application/services/external_actions/external_action_product_route_catalog_service.py",
    "app/application/services/external_actions/external_action_generic_route_selection_service.py",
)

_INLINE_TERM_TUPLE_PATTERN = re.compile(
    r"""for\s+term\s+in\s+\(\s*["'][^"']{3,}["']""",
)

_ALLOWED_RESOLVERS = frozenset(
    {
        "production_query",
        "inventory_query",
        "generic_auto_execute",
    }
)

_KNOWN_DISPATCH_PHASES = frozenset(
    {
        "sessionRefinement",
        "operationalRoutes",
        "domainRoutes",
        "intentBoundRoutes",
        "sqlFallback",
        "semanticFallback",
    }
)

_PLAYBOOK_NONE_OF_RULES: dict[str, list[str]] = {
    "productInvoicesGeneric": ["inboundInvoiceRoute", "outboundInvoiceRoute"],
    "productPurchases": [
        "lastPurchase",
        "purchasePriceHistory",
        "purchaseBudgetHistory",
        "rawMaterialPriceIntelligence",
    ],
    "productFactoryStatus": ["productionStatus"],
    "productLastPurchase": ["directives"],
    "productGenericPricing": ["salePricingRoute"],
}

_LEGACY_SYMBOLS = (
    "ExternalActionProductRouteRankingService",
    "_rank_product_actions",
    "productRouteRanking",
    "vocabularyFastPaths",
    "ExternalActionProductRouteSelectionService",
    "ExternalActionKpiRouteSelectionService",
)


@dataclass
class OperationalRouteRegistryLintReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)


class OperationalRouteRegistryLintService:
    @classmethod
    def run(cls, *, package_root: Path | None = None) -> OperationalRouteRegistryLintReport:
        root = package_root or Path(__file__).resolve().parents[2]
        report = OperationalRouteRegistryLintReport()

        cls._lint_dispatch_order(report)
        cls._lint_fallback_policies(report)
        cls._lint_routes(report)
        cls._lint_parameter_strategies(report)
        cls._lint_actionable_predicates(report)
        cls._lint_playbook_product_predicates(report)
        cls._lint_playbook_none_of_rules(report)
        cls._lint_python_route_selection_files(root, report)
        cls._lint_legacy_symbols(root, report)

        return report

    @classmethod
    def _lint_dispatch_order(cls, report: OperationalRouteRegistryLintReport) -> None:
        order = OperationalRouteRegistryService.dispatch_order()

        if not order:
            report.add_error("operational_route_registry.dispatchOrder está vazio")
            return

        unknown = [phase for phase in order if phase not in _KNOWN_DISPATCH_PHASES]

        for phase in unknown:
            report.add_error(f"dispatchOrder contém fase desconhecida: {phase}")

    @classmethod
    def _lint_fallback_policies(cls, report: OperationalRouteRegistryLintReport) -> None:
        for policy in OperationalRouteRegistryService.fallback_policies():
            policy_id = str(policy.get("id") or "").strip() or "<sem-id>"
            resolver = str(policy.get("resolver") or "").strip()

            if resolver and resolver not in _ALLOWED_RESOLVERS:
                report.add_error(
                    f"fallbackPolicies.{policy_id}: resolver desconhecido {resolver!r}"
                )

            reason_key = str(policy.get("reasonKey") or "").strip()

            if reason_key and not cls._selection_reason_exists(reason_key):
                report.add_error(
                    f"fallbackPolicies.{policy_id}: selectionReasons.{reason_key} ausente"
                )

            phase = str(policy.get("phase") or "").strip()

            if phase and phase not in _KNOWN_DISPATCH_PHASES:
                report.add_error(
                    f"fallbackPolicies.{policy_id}: phase desconhecida {phase!r}"
                )

        refinement = OperationalRouteRegistryService.sql_refinement_policy()
        reason_key = str(refinement.get("reasonKey") or "").strip()

        if reason_key and not cls._selection_reason_exists(reason_key):
            report.add_error(f"sqlRefinementPolicy.reasonKey ausente: {reason_key!r}")

    @classmethod
    def _lint_routes(cls, report: OperationalRouteRegistryLintReport) -> None:
        seen_ids: set[str] = set()

        for route in OperationalRouteRegistryService.routes():
            route_id = str(route.get("id") or "").strip()

            if not route_id:
                report.add_error("rota registry sem id")
                continue

            if route_id in seen_ids:
                report.add_error(f"rota registry duplicada: {route_id}")
            seen_ids.add(route_id)

            cls._lint_match_spec(route_id, route.get("match"), report)
            cls._lint_presentation(route_id, route.get("presentation") or {}, report)
            cls._lint_route_parameter_strategy(route_id, route, report)

            fallback = route.get("fallbackPolicy")

            if isinstance(fallback, dict):
                reason_key = str(fallback.get("reasonKey") or "").strip()

                if reason_key and not cls._selection_reason_exists(reason_key):
                    report.add_error(
                        f"routes.{route_id}.fallbackPolicy.reasonKey ausente: {reason_key!r}"
                    )

                resolver = str(fallback.get("resolver") or "").strip()

                if resolver and resolver not in _ALLOWED_RESOLVERS:
                    report.add_error(
                        f"routes.{route_id}.fallbackPolicy.resolver inválido: {resolver!r}"
                    )

    @classmethod
    def _lint_match_spec(
        cls,
        route_id: str,
        match_spec: Any,
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        if not isinstance(match_spec, dict):
            return

        cls._lint_terms_references(route_id, match_spec, report)

        for key in ("allOf", "noneOf"):
            nodes = match_spec.get(key)

            if not isinstance(nodes, list):
                continue

            for index, node in enumerate(nodes):
                if not isinstance(node, dict):
                    report.add_error(f"routes.{route_id}.match.{key}[{index}] inválido")
                    continue

                cls._lint_terms_references(
                    f"{route_id}.match.{key}[{index}]",
                    node,
                    report,
                )
                cls._lint_custom_predicate(f"{route_id}.match.{key}[{index}]", node, report)

        cls._lint_custom_predicate(route_id, match_spec, report)

    @classmethod
    def _lint_terms_references(
        cls,
        context: str,
        spec: dict[str, Any],
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        for key in ("termsFrom", "excludeTermsFrom"):
            reference = str(spec.get(key) or "").strip()

            if not reference:
                continue

            terms = OperationalRouteMatcherService._resolve_terms(reference)

            if not terms:
                report.add_error(
                    f"routes.{context}.{key} não resolve termos: {reference!r}"
                )

    @classmethod
    def _lint_custom_predicate(
        cls,
        context: str,
        spec: dict[str, Any],
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        predicate = str(spec.get("customPredicate") or "").strip()

        if not predicate:
            return

        if predicate not in cls._allowed_custom_predicates():
            report.add_error(
                f"routes.{context}.customPredicate {predicate!r} fora da allowlist"
            )

    @classmethod
    def _allowed_custom_predicates(cls) -> frozenset[str]:
        from app.domain.services.chat_product_route_predicate_service import (
            ChatProductRoutePredicateService,
        )

        return frozenset(ChatProductRoutePredicateService.registered_predicates())

    @classmethod
    def _lint_presentation(
        cls,
        route_id: str,
        presentation: dict[str, Any],
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        reason_key = str(presentation.get("reasonKey") or "").strip()

        if reason_key and not cls._selection_reason_exists(reason_key):
            report.add_error(
                f"routes.{route_id}.presentation.reasonKey ausente: {reason_key!r}"
            )

        format_key = str(presentation.get("reasonFormatKey") or "").strip()

        if format_key and not cls._selection_reason_exists(format_key):
            report.add_error(
                f"routes.{route_id}.presentation.reasonFormatKey ausente: {format_key!r}"
            )

    @classmethod
    def _lint_parameter_strategies(cls, report: OperationalRouteRegistryLintReport) -> None:
        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )

        allowed = ChatOperationalApiDomainService.parameter_strategy_ids()

        for domain_id, config in ChatOperationalApiDomainService.domains().items():
            if not isinstance(config, dict):
                continue

            strategy = str(config.get("parameterStrategy") or "").strip()

            if strategy and strategy not in allowed:
                report.add_error(
                    f"api_route_domains.domains.{domain_id}.parameterStrategy "
                    f"desconhecida: {strategy!r}"
                )

    @classmethod
    def _lint_route_parameter_strategy(
        cls,
        route_id: str,
        route: dict[str, Any],
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        from app.domain.services.chat_operational_api_domain_service import (
            ChatOperationalApiDomainService,
        )

        parameters_spec = route.get("parameters") or {}

        if not isinstance(parameters_spec, dict):
            return

        strategy = str(parameters_spec.get("strategy") or "").strip()

        if not strategy:
            return

        allowed = ChatOperationalApiDomainService.parameter_strategy_ids()

        if strategy not in allowed:
            report.add_error(
                f"routes.{route_id}.parameters.strategy desconhecida: {strategy!r}"
            )

    @classmethod
    def _lint_actionable_predicates(cls, report: OperationalRouteRegistryLintReport) -> None:
        for predicate in OperationalRouteRegistryService.actionable_product_predicates():
            if predicate not in cls._allowed_custom_predicates():
                report.add_error(
                    f"actionableProductPredicates.{predicate!r} fora da allowlist"
                )

    @classmethod
    def _lint_playbook_product_predicates(
        cls,
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        for predicate in OperationalRouteRegistryService.playbook_product_predicates():
            if predicate not in cls._allowed_custom_predicates():
                report.add_error(
                    f"playbookProductPredicates.{predicate!r} fora da allowlist"
                )

    @classmethod
    def _lint_playbook_none_of_rules(cls, report: OperationalRouteRegistryLintReport) -> None:
        for route_id, required_predicates in _PLAYBOOK_NONE_OF_RULES.items():
            route = OperationalRouteRegistryService.route_by_id(route_id)

            if not route:
                report.add_error(
                    f"playbookConflictRules: rota {route_id!r} ausente do registry"
                )
                continue

            match_spec = route.get("match")

            if not isinstance(match_spec, dict):
                report.add_error(f"routes.{route_id}.match ausente para conflito playbook")
                continue

            present = cls._collect_none_of_predicates(match_spec)

            for predicate in required_predicates:
                if predicate not in present:
                    report.add_error(
                        f"routes.{route_id} deve declarar noneOf customPredicate={predicate!r}"
                    )

    @classmethod
    def _collect_none_of_predicates(cls, match_spec: dict[str, Any]) -> set[str]:
        predicates: set[str] = set()
        none_of = match_spec.get("noneOf")

        if not isinstance(none_of, list):
            return predicates

        for node in none_of:
            if not isinstance(node, dict):
                continue

            predicate = str(node.get("customPredicate") or "").strip()

            if predicate:
                predicates.add(predicate)

        return predicates

    @classmethod
    def _lint_python_route_selection_files(
        cls,
        root: Path,
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        for relative in _SCANNED_PYTHON_RELATIVE:
            path = root / relative

            if not path.is_file():
                report.add_warning(f"arquivo de lint não encontrado: {relative}")
                continue

            source = path.read_text(encoding="utf-8")
            cls._lint_python_source(relative, source, report)

            if _API_DELPI_PATH_PATTERN.search(source):
                report.add_error(
                    f"{relative}: path api-delpi hardcoded — use operational_route_registry.json"
                )

    @classmethod
    def _lint_python_source(
        cls,
        relative_path: str,
        source: str,
        report: OperationalRouteRegistryLintReport,
    ) -> None:
        if _INLINE_TERM_TUPLE_PATTERN.search(source):
            report.add_error(
                f"{relative_path}: tupla inline de termos — use JSON (product_query_intent / registry)"
            )

    @classmethod
    def _lint_legacy_symbols(cls, root: Path, report: OperationalRouteRegistryLintReport) -> None:
        services_dir = root / "app/application/services/external_actions"

        if not services_dir.is_dir():
            return

        for path in sorted(services_dir.glob("*.py")):
            source = path.read_text(encoding="utf-8")

            for symbol in _LEGACY_SYMBOLS:
                if symbol in source:
                    report.add_error(
                        f"{path.relative_to(root)}: símbolo legado DOCIE {symbol!r}"
                    )

    @staticmethod
    def _selection_reason_exists(key: str) -> bool:
        value = ExternalActionResponseContentService.get("selectionReasons", key)
        return bool(str(value or "").strip())

    @classmethod
    def format_report(cls, report: OperationalRouteRegistryLintReport) -> str:
        lines: list[str] = []

        if report.errors:
            lines.append(f"ERROS ({len(report.errors)}):")

            for item in report.errors:
                lines.append(f"  - {item}")

        if report.warnings:
            lines.append(f"AVISOS ({len(report.warnings)}):")

            for item in report.warnings:
                lines.append(f"  - {item}")

        if report.ok and not report.warnings:
            lines.append("DOCIE lint OK — registry e vocabulário centralizado.")

        return "\n".join(lines)
