"""Serialização de openInNewTab em /me/apps (rotas do manifesto)."""

from app.application.use_cases.list_user_apps_use_case import ListUserAppsUseCase
from app.domain.ports.app_query_port import AppDTO, RouteDTO


class FakeAppQuery:
    def __init__(self, apps):
        self._apps = apps

    def list_active_apps_with_routes(self):
        return self._apps


def test_list_user_apps_serializes_open_in_new_tab_from_route_dto():
    route_flagged = RouteDTO(
        path="/manutencao/checklist",
        label="Checklist",
        icon=None,
        permission_code="manutencao.view",
        show_in_menu=True,
        order=1,
        entry="https://script.google.com/macros/s/abc/exec",
        open_in_new_tab=True,
    )
    route_default = RouteDTO(
        path="/manutencao",
        label="Início",
        icon=None,
        permission_code="manutencao.view",
        show_in_menu=True,
        order=0,
        entry=None,
    )

    app = AppDTO(
        id="manutencao",
        name="Manutenção",
        base_path="/manutencao",
        icon="wrench",
        type="iframe",
        entry_url="https://example.local/manutencao",
        render_mode="embedded",
        routes=[route_default, route_flagged],
    )

    result = ListUserAppsUseCase(app_query=FakeAppQuery([app])).execute(
        permissions=["manutencao.view"],
        is_superadmin=False,
    )

    assert len(result) == 1
    by_path = {r["path"]: r for r in result[0]["routes"]}
    assert by_path["/manutencao"]["openInNewTab"] is False
    assert by_path["/manutencao/checklist"]["openInNewTab"] is True
    assert (
        by_path["/manutencao/checklist"]["entry"]
        == "https://script.google.com/macros/s/abc/exec"
    )
