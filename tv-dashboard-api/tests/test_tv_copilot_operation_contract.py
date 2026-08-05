"""Integridade do contrato executável do catálogo do Copiloto TV."""

from tv_app.application.services.data.tv_copilot_content_service import (
    TvCopilotContentService,
)
from tv_app.application.services.data.tv_copilot_catalog_audit_service import (
    TvCopilotCatalogAuditService,
)


def _template_ops(capability: dict) -> set[str]:
    names: set[str] = set()
    payload = capability.get("payloadTemplate")
    if isinstance(payload, dict) and payload.get("op"):
        names.add(str(payload["op"]))
    payloads = capability.get("payloadTemplates")
    if isinstance(payloads, list):
        for item in payloads:
            if isinstance(item, dict) and item.get("op"):
                names.add(str(item["op"]))
    if capability.get("op"):
        names.add(str(capability["op"]))
    return names


def test_all_capability_ops_have_complete_operation_specs():
    TvCopilotCatalogAuditService.assert_valid()
    operations = TvCopilotContentService.operations()
    referenced = {
        op
        for capability in TvCopilotContentService.capabilities()
        for op in _template_ops(capability)
    }

    assert referenced
    assert referenced <= set(operations)
    for op_name in sorted(referenced):
        spec = operations[op_name]
        assert isinstance(spec.get("requiresPlaylist"), bool), op_name
        assert isinstance(spec.get("requiresSlide"), bool), op_name
        assert spec.get("risk") in {"additive", "mutation", "destructive"}, op_name
        assert spec.get("confirmationPolicy") in {"direct", "confirm"}, op_name
        assert isinstance(spec.get("inputSchema"), dict), op_name
        assert isinstance(spec.get("sideEffectHints"), list), op_name


def test_only_destructive_operations_require_confirmation():
    operations = TvCopilotContentService.operations()

    confirmed = {
        name
        for name, spec in operations.items()
        if spec.get("confirmationPolicy") == "confirm"
    }
    assert confirmed == {"delete_block", "delete_slide", "delete_section"}
    assert all(operations[name]["risk"] == "destructive" for name in confirmed)
