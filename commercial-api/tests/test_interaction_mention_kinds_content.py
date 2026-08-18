from commercial_app.domain.services.interaction_mention_kinds_content_service import (
    InteractionMentionKindsContentService,
)

_REQUIRED_P0_IDS = frozenset(
    {
        "user",
        "customer",
        "portfolio",
        "order",
        "opportunity",
        "proposal",
        "production_order",
        "otd_line",
        "invoice",
        "product",
        "kpi",
        "goal",
        "raw_material",
    }
)

_REQUIRED_FIELDS = (
    "id",
    "group",
    "label",
    "hrefStrategy",
    "suggestEnabled",
    "previewEnabled",
)


def setup_function() -> None:
    InteractionMentionKindsContentService.clear_cache()


def test_bundle_loads_object_with_kinds() -> None:
    bundle = InteractionMentionKindsContentService.bundle()
    assert isinstance(bundle, dict)
    kinds = InteractionMentionKindsContentService.kinds()
    assert kinds
    assert all(isinstance(item, dict) for item in kinds)


def test_required_p0_kind_ids_exist() -> None:
    ids = InteractionMentionKindsContentService.kind_ids()
    missing = _REQUIRED_P0_IDS - ids
    assert not missing, f"kinds P0 ausentes: {sorted(missing)}"


def test_each_kind_has_required_fields() -> None:
    for item in InteractionMentionKindsContentService.kinds():
        for field in _REQUIRED_FIELDS:
            assert field in item, f"{item.get('id')} sem {field}"
        assert str(item["id"]).strip()
        assert str(item["label"]).strip()
        assert str(item["hrefStrategy"]).strip()
        assert item["group"] in {"people", "objects"}
        assert isinstance(item["suggestEnabled"], bool)
        assert isinstance(item["previewEnabled"], bool)


def test_is_known_and_get() -> None:
    assert InteractionMentionKindsContentService.is_known("user")
    assert InteractionMentionKindsContentService.is_known("product")
    assert not InteractionMentionKindsContentService.is_known("unknown_kind")
    user = InteractionMentionKindsContentService.get("user")
    assert user is not None
    assert user["hrefStrategy"] == "user_profile"
    assert InteractionMentionKindsContentService.get("missing") is None


def test_suggest_enabled_excludes_raw_material() -> None:
    enabled = InteractionMentionKindsContentService.suggest_enabled_ids()
    assert "user" in enabled
    assert "customer" in enabled
    assert "raw_material" not in enabled


def test_group_labels_come_from_json() -> None:
    assert InteractionMentionKindsContentService.group_label("people") == "Pessoas"
    assert InteractionMentionKindsContentService.group_label("objects") == "Objetos"
