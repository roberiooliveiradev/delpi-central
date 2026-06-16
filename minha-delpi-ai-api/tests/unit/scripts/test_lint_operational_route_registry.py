from pathlib import Path

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.operational_route_registry_lint_service import (
    OperationalRouteRegistryLintService,
)


def setup_module() -> None:
    configure_domain_infrastructure_ports()


def test_docie_registry_lint_passes() -> None:
    root = Path(__file__).resolve().parents[2]
    report = OperationalRouteRegistryLintService.run(package_root=root)

    assert report.ok, OperationalRouteRegistryLintService.format_report(report)


def test_playbook_none_of_rules_present() -> None:
    from app.domain.services.operational_route_registry_service import (
        OperationalRouteRegistryService,
    )

    generic = OperationalRouteRegistryService.route_by_id("productInvoicesGeneric")
    match_spec = generic.get("match") or {}
    none_of = match_spec.get("noneOf") or []
    predicates = {
        str(node.get("customPredicate") or "")
        for node in none_of
        if isinstance(node, dict)
    }

    assert "inboundInvoiceRoute" in predicates
    assert "outboundInvoiceRoute" in predicates
