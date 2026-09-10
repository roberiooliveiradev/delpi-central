from app.domain.services.registry_selection_shadow_observability_service import (
    RegistrySelectionShadowObservabilityService,
)


def test_extract_shadows_from_selected_external_action():
    shadows = RegistrySelectionShadowObservabilityService.extract_shadows(
        assistant_metadata={
            "selectedExternalAction": {
                "actionId": "acme.products.stock",
                "registrySelectionShadow": {
                    "kind": "registry_route_id",
                    "routeId": "product.stock",
                    "agree": True,
                },
            }
        }
    )
    assert len(shadows) == 1
    assert shadows[0]["routeId"] == "product.stock"


def test_extract_shadows_from_tool_call_metadata():
    tool_calls = [
        {
            "name": "execute_external_action",
            "metadata": {
                "registrySelectionShadow": {
                    "kind": "registry_route_id",
                    "routeId": "product.stock",
                    "legacyActionId": "acme.products.stock",
                    "agree": True,
                    "candidateTopIds": ["acme.products.stock"],
                }
            },
        }
    ]
    shadows = RegistrySelectionShadowObservabilityService.extract_shadows(
        tool_calls=tool_calls
    )
    assert len(shadows) == 1
    assert shadows[0]["agree"] is True


def test_enrich_audit_metadata_persists_compact_list():
    audit: dict = {}
    RegistrySelectionShadowObservabilityService.enrich_audit_metadata(
        audit,
        tool_calls=[
            {
                "metadata": {
                    "productSelectionShadow": {
                        "kind": "product_intent_segment",
                        "routeId": "product.intent:stock|segment:stock",
                        "legacyActionId": "acme.products.stock",
                        "agree": False,
                        "error": None,
                        "intent": "stock",
                        "routeSegment": "stock",
                        "candidateTopIds": ["other"],
                    }
                }
            }
        ],
    )
    assert "registrySelectionShadows" in audit
    assert audit["registrySelectionShadows"][0]["kind"] == "product_intent_segment"
    assert audit["registrySelectionShadows"][0]["agree"] is False
    assert "candidateTopIds" not in audit["registrySelectionShadows"][0]


def test_aggregate_snapshots_computes_agree_rate():
    entries = [
        {
            "loggedAt": "2026-09-10T12:00:00Z",
            "action": "chat.message.sent",
            "snapshot": [
                {
                    "kind": "registry_route_id",
                    "routeId": "a",
                    "legacyActionId": "x",
                    "agree": True,
                },
                {
                    "kind": "product_intent_segment",
                    "routeId": "b",
                    "legacyActionId": "y",
                    "agree": False,
                },
            ],
        },
        {
            "loggedAt": "2026-09-10T11:00:00Z",
            "action": "chat.message.streamed",
            "snapshot": [
                {
                    "kind": "registry_route_id",
                    "routeId": "c",
                    "legacyActionId": "z",
                    "agree": True,
                }
            ],
        },
    ]
    result = RegistrySelectionShadowObservabilityService.aggregate_snapshots(
        entries,
        hours=24,
        since_iso="2026-09-09T12:00:00Z",
    )
    assert result["samplesCount"] == 3
    assert result["agreeCount"] == 2
    assert result["divergeCount"] == 1
    assert result["agreeRate"] == round(2 / 3, 4)
    assert result["byKind"]["registry_route_id"]["agreeCount"] == 2
    assert result["byKind"]["product_intent_segment"]["agreeCount"] == 0
    assert len(result["divergeRecent"]) == 1
    assert result["cutoverReadyHint"] == "not_ready"


def test_aggregate_empty_is_safe():
    result = RegistrySelectionShadowObservabilityService.aggregate_snapshots(
        [],
        hours=168,
        since_iso="2026-09-01T00:00:00Z",
    )
    assert result["samplesCount"] == 0
    assert result["agreeRate"] is None
    assert result["cutoverReadyHint"] == "not_ready"
