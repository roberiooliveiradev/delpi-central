from app.domain.services.chat_presentation_operational_root_service import (
    ChatPresentationOperationalRootService,
)


def test_resolve_items_root_from_top_level_items():
    root = {"items": [{"branch": "01"}]}

    resolved = ChatPresentationOperationalRootService.resolve_items_root(root)

    assert resolved is root


def test_resolve_items_root_unwraps_stock_envelope():
    stock = {"items": [{"branch": "01"}]}
    root = {"stock": stock, "meta": {"page": 1}}

    resolved = ChatPresentationOperationalRootService.resolve_items_root(
        root,
        path="/products/10080022/stock",
    )

    assert resolved is stock


def test_resolve_bundle_root_falls_back_to_original_dict():
    root = {"rows": [{"id": 1}]}

    resolved = ChatPresentationOperationalRootService.resolve_bundle_root(root)

    assert resolved is root
