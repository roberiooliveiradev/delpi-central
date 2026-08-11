from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest

from app.application.security import api_delpi_permissions as perms
from app.application.services.mural_acessos.mural_acessos_image_storage import (
    MuralAcessosImageStorage,
    MuralAcessosStorageError,
)
from app.application.use_cases.mural_acessos.mural_acessos_use_cases import (
    ActorContext,
    CreateHubUseCase,
    CreateLinkUseCase,
    ListPublicMenuUseCase,
    ReorderLinksUseCase,
)
from app.domain.services.mural_acessos.exceptions import (
    MuralAcessosNotFoundError,
    MuralAcessosValidationError,
)
from app.domain.services.mural_acessos.link_url import (
    normalize_link_url,
    normalize_public_token,
    normalize_title,
)


class ProbeRepo:
    def __init__(self) -> None:
        self.hubs: list[dict[str, Any]] = []
        self.created: list[dict[str, Any]] = []
        self.links: list[dict[str, Any]] = []

    def get_hub(self, hub_id: str) -> dict[str, Any] | None:
        return next((row for row in self.hubs if row["id"] == hub_id), None)

    def get_hub_by_token(self, public_token: str) -> dict[str, Any] | None:
        return next(
            (row for row in self.hubs if row["publicToken"] == public_token), None
        )

    def create_hub(self, **kwargs: Any) -> dict[str, Any]:
        row = {
            "id": str(uuid4()),
            "title": kwargs["title"],
            "subtitle": kwargs["subtitle"],
            "publicToken": kwargs["public_token"],
            "linkCount": 0,
        }
        self.hubs.append(row)
        return row

    def create_link(self, **kwargs: Any) -> dict[str, Any]:
        row = {
            "id": str(uuid4()),
            "hubId": kwargs["hub_id"],
            "title": kwargs["title"],
            "url": kwargs["url"],
            "description": kwargs["description"],
            "orderIndex": 0,
            "active": kwargs["active"],
            "hasImage": False,
            "imageStoredName": None,
            "createdAt": None,
            "updatedAt": None,
            "createdByName": kwargs["actor_name"],
            "updatedByName": kwargs["actor_name"],
        }
        self.created.append(row)
        self.links.append(row)
        return row

    def list_links(
        self, *, hub_id: str, active_only: bool = False
    ) -> list[dict[str, Any]]:
        rows = [row for row in self.links if row["hubId"] == hub_id]
        if active_only:
            rows = [row for row in rows if row["active"]]
        return list(rows)

    def reorder_links(
        self, *, hub_id: str, ordered_ids: list[str]
    ) -> list[dict[str, Any]]:
        scoped = [row for row in self.links if row["hubId"] == hub_id]
        by_id = {row["id"]: row for row in scoped}
        reordered = [by_id[item_id] for item_id in ordered_ids]
        for index, row in enumerate(reordered):
            row["orderIndex"] = index
        others = [row for row in self.links if row["hubId"] != hub_id]
        self.links = others + reordered
        return list(reordered)


def test_mural_acessos_permission_constants() -> None:
    assert perms.MURAL_ACESSOS_ACCESS == "mural-acessos.access"
    assert perms.MURAL_ACESSOS_MANAGE == "mural-acessos.manage"
    assert perms.MURAL_ACESSOS_ACCESS in perms.MURAL_ACESSOS_READ_PERMISSIONS
    assert perms.MURAL_ACESSOS_MANAGE in perms.MURAL_ACESSOS_WRITE_PERMISSIONS
    assert perms.MURAL_ACESSOS_ACCESS not in perms.MURAL_ACESSOS_WRITE_PERMISSIONS


def test_normalize_link_url_rejects_javascript() -> None:
    with pytest.raises(MuralAcessosValidationError, match="http"):
        normalize_link_url("javascript:alert(1)")


def test_normalize_link_url_accepts_https() -> None:
    assert normalize_link_url("https://intranet.delpi.local/rh") == (
        "https://intranet.delpi.local/rh"
    )


def test_normalize_title_rejects_blank() -> None:
    with pytest.raises(MuralAcessosValidationError, match="título"):
        normalize_title("   ")


def test_normalize_public_token_slugifies() -> None:
    assert normalize_public_token(" RH Qualidade ") == "rh-qualidade"


def test_normalize_public_token_rejects_short() -> None:
    with pytest.raises(MuralAcessosValidationError, match="identificador"):
        normalize_public_token("a")


def test_create_hub_derives_token_from_title() -> None:
    repo = ProbeRepo()
    created = CreateHubUseCase(repo).execute(  # type: ignore[arg-type]
        {"title": "RH - Indique", "subtitle": "Equipe"}
    )
    assert created["publicToken"] == "rh-indique"
    assert created["title"] == "RH - Indique"
    assert created["publicPath"] == "/p/mural-acessos/menu/rh-indique"


def test_create_link_use_case_normalizes_payload() -> None:
    repo = ProbeRepo()
    hub = repo.create_hub(title="Mural", subtitle="", public_token="mural")
    created = CreateLinkUseCase(repo).execute(  # type: ignore[arg-type]
        hub["id"],
        {
            "title": "  Benefícios  ",
            "url": "https://exemplo.delpi.local/beneficios",
            "description": "  Portal  ",
            "active": True,
        },
        ActorContext("u1", "Ana"),
    )
    assert created["title"] == "Benefícios"
    assert created["description"] == "Portal"
    assert created["url"].startswith("https://")
    assert created["hubId"] == hub["id"]


def test_reorder_rejects_unknown_and_incomplete_set() -> None:
    repo = ProbeRepo()
    hub = repo.create_hub(title="Mural", subtitle="", public_token="mural")
    first = repo.create_link(
        hub_id=hub["id"],
        title="A",
        url="https://a.example",
        description="",
        active=True,
        actor_id=None,
        actor_name=None,
    )
    second = repo.create_link(
        hub_id=hub["id"],
        title="B",
        url="https://b.example",
        description="",
        active=True,
        actor_id=None,
        actor_name=None,
    )
    with pytest.raises(MuralAcessosValidationError, match="inexistente"):
        ReorderLinksUseCase(repo).execute(hub["id"], [first["id"], str(uuid4())])  # type: ignore[arg-type]
    with pytest.raises(MuralAcessosValidationError, match="todos os acessos"):
        ReorderLinksUseCase(repo).execute(hub["id"], [first["id"]])  # type: ignore[arg-type]
    assert {first["id"], second["id"]} == {
        row["id"] for row in repo.list_links(hub_id=hub["id"])
    }


def test_public_menu_scopes_links_to_token() -> None:
    repo = ProbeRepo()
    mural = repo.create_hub(title="Geral", subtitle="", public_token="mural")
    rh = repo.create_hub(title="RH", subtitle="", public_token="rh")
    repo.create_link(
        hub_id=mural["id"],
        title="Geral A",
        url="https://a.example",
        description="",
        active=True,
        actor_id=None,
        actor_name=None,
    )
    repo.create_link(
        hub_id=rh["id"],
        title="Indique",
        url="https://rh.example",
        description="",
        active=True,
        actor_id=None,
        actor_name=None,
    )
    menu = ListPublicMenuUseCase(repo).execute("rh")  # type: ignore[arg-type]
    assert menu["title"] == "RH"
    assert [item["title"] for item in menu["items"]] == ["Indique"]


def test_public_menu_unknown_token_is_not_found() -> None:
    repo = ProbeRepo()
    with pytest.raises(MuralAcessosNotFoundError):
        ListPublicMenuUseCase(repo).execute("inexistente")  # type: ignore[arg-type]


def test_image_storage_rejects_path_traversal(tmp_path) -> None:
    storage = MuralAcessosImageStorage(base_dir=str(tmp_path))
    with pytest.raises(MuralAcessosStorageError):
        storage.resolve_file(link_id="abc", stored_name="../secret.png")
