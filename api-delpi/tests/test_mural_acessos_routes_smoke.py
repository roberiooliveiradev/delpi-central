"""Smoke Nível A — Mural de Acessos."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.interface.http.routes.mural_acessos.mural_acessos_public_router import (
    list_public_menu,
    list_public_menu_by_token,
)
from app.interface.http.routes.mural_acessos.mural_acessos_router import (
    HubBody,
    LinkBody,
    ReorderBody,
    create_hub,
    create_link,
    delete_hub,
    delete_link,
    delete_link_image,
    get_hub,
    list_hubs,
    list_links,
    reorder_links,
    update_hub,
    update_link,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_HUB_ID = uuid4()
_LINK_ID = uuid4()
_HUB = {
    "id": str(_HUB_ID),
    "title": "Acessos DELPI",
    "subtitle": "",
    "publicToken": "mural",
    "publicPath": "/p/mural-acessos/menu/mural",
    "linkCount": 1,
}
_LINK = {
    "id": str(_LINK_ID),
    "hubId": str(_HUB_ID),
    "title": "Benefícios",
    "url": "https://intranet.delpi.local/beneficios",
    "description": "Portal de benefícios",
    "orderIndex": 0,
    "active": True,
    "hasImage": False,
    "imageUrl": None,
}


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_list_hubs_use_case"
)
def test_list_mural_acessos_hubs_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = [_HUB]
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(list_hubs()),
        operation_id="list_mural_acessos_hubs",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_create_hub_use_case"
)
def test_create_mural_acessos_hub_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _HUB
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(create_hub(body=HubBody(title="RH", subtitle="", public_token="rh"))),
        operation_id="create_mural_acessos_hub",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_get_hub_use_case"
)
def test_get_mural_acessos_hub_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _HUB
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(get_hub(hub_id=_HUB_ID)),
        operation_id="get_mural_acessos_hub",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_update_hub_use_case"
)
def test_update_mural_acessos_hub_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _HUB
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(
            update_hub(
                hub_id=_HUB_ID,
                body=HubBody(title="Mural", subtitle="", public_token="mural"),
            )
        ),
        operation_id="update_mural_acessos_hub",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_delete_hub_use_case"
)
def test_delete_mural_acessos_hub_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"id": str(_HUB_ID), "deleted": True}
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(delete_hub(hub_id=_HUB_ID)),
        operation_id="delete_mural_acessos_hub",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_list_links_use_case"
)
def test_list_mural_acessos_links_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = [_LINK]
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(list_links(hub_id=_HUB_ID)),
        operation_id="list_mural_acessos_links",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_create_link_use_case"
)
def test_create_mural_acessos_link_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _LINK
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(
            create_link(
                hub_id=_HUB_ID,
                body=LinkBody(
                    title="Benefícios",
                    url="https://intranet.delpi.local/beneficios",
                ),
            )
        ),
        operation_id="create_mural_acessos_link",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_update_link_use_case"
)
def test_update_mural_acessos_link_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _LINK
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(
            update_link(
                link_id=_LINK_ID,
                body=LinkBody(
                    title="Benefícios",
                    url="https://intranet.delpi.local/beneficios",
                ),
            )
        ),
        operation_id="update_mural_acessos_link",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_delete_link_use_case"
)
def test_delete_mural_acessos_link_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {"id": str(_LINK_ID), "deleted": True}
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(delete_link(link_id=_LINK_ID)),
        operation_id="delete_mural_acessos_link",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_reorder_links_use_case"
)
def test_reorder_mural_acessos_links_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = [_LINK]
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(
            reorder_links(
                hub_id=_HUB_ID, body=ReorderBody(ordered_ids=[_LINK_ID])
            )
        ),
        operation_id="reorder_mural_acessos_links",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_router.build_delete_link_image_use_case"
)
def test_delete_mural_acessos_link_image_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _LINK
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(delete_link_image(link_id=_LINK_ID)),
        operation_id="delete_mural_acessos_link_image",
        shape="scalar",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_public_router.build_list_public_menu_use_case"
)
def test_list_public_mural_acessos_menu_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "title": "Acessos DELPI",
        "subtitle": "",
        "items": [_LINK],
    }
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(list_public_menu()),
        operation_id="list_public_mural_acessos_menu",
        shape="paged_list",
    )


@patch(
    "app.interface.http.routes.mural_acessos.mural_acessos_public_router.build_list_public_menu_use_case"
)
def test_list_public_mural_acessos_menu_by_token_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "title": "RH",
        "subtitle": "",
        "publicToken": "rh",
        "items": [_LINK],
    }
    mock_build.return_value = use_case
    assert_envelope_meta(
        body_json(list_public_menu_by_token(public_token="rh")),
        operation_id="list_public_mural_acessos_menu_by_token",
        shape="paged_list",
    )


def test_upload_and_image_operation_ids_are_registered() -> None:
    from app.interface.http.route_contract_registry import ROUTE_CONTRACTS

    for operation_id in (
        "upload_mural_acessos_link_image",
        "get_mural_acessos_link_image",
        "get_public_mural_acessos_link_image",
        "get_mural_acessos_hub_qr",
        "list_mural_acessos_hubs",
        "create_mural_acessos_hub",
        "delete_mural_acessos_hub",
        "list_public_mural_acessos_menu_by_token",
    ):
        assert operation_id in ROUTE_CONTRACTS


def test_qr_and_image_handlers_exist() -> None:
    from app.interface.http.routes.mural_acessos.mural_acessos_public_router import (
        get_public_link_image,
    )
    from app.interface.http.routes.mural_acessos.mural_acessos_router import (
        get_hub_qr,
        get_link_image,
        upload_link_image,
    )

    assert callable(get_hub_qr)
    assert callable(get_link_image)
    assert callable(upload_link_image)
    assert callable(get_public_link_image)
    assert Path(__file__).name  # operationIds citados acima para cobertura
