"""Mocks universais de repositórios/serviços para smokes HTTP Nível A."""

from __future__ import annotations

import importlib
import tempfile
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import Any, Callable, Iterator
from unittest.mock import MagicMock, patch

_IDS = {
    "filial_id": "11111111-1111-1111-1111-111111111111",
    "setor_id": "22222222-2222-2222-2222-222222222222",
    "processo_id": "33333333-3333-3333-3333-333333333333",
    "instancia_id": "44444444-4444-4444-4444-444444444444",
    "revisao_id": "55555555-5555-5555-5555-555555555555",
    "recurso_id": "66666666-6666-6666-6666-666666666666",
    "recurso_custo_id": "77777777-7777-7777-7777-777777777777",
    "vinculo_id": "88888888-8888-8888-8888-888888888888",
    "investimento_id": "99999999-9999-9999-9999-999999999999",
    "arquivo_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "evidencia_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "medicao_id": "cccccccc-cccc-cccc-cccc-cccccccccccc",
}

_EMPTY_FLOW = {
    "format": "flowchart_v1",
    "format_version": 1,
    "nodes": [],
    "edges": [],
}
_EMPTY_TREE = {
    "format": "decomposition_tree_v1",
    "format_version": 1,
    "nodes": [],
}
_EMPTY_TREE_OVERLAY = {
    "format": "decomposition_overlay_v1",
    "format_version": 1,
    "node_overrides": {},
    "disabled_node_ids": [],
    "extra_nodes": [],
}
_EMPTY_FLOW_OVERLAY = {
    "format": "flowchart_overlay_v1",
    "format_version": 1,
    "modo": "full_scope",
    "node_overrides": {},
    "edge_overrides": {},
    "removed_node_ids": [],
    "removed_edge_ids": [],
    "extra_nodes": [],
    "extra_edges": [],
}

_SMOKE_FILE = Path(tempfile.gettempdir()) / "tm_route_smoke.bin"
if not _SMOKE_FILE.is_file():
    _SMOKE_FILE.write_bytes(b"smoke")

_ENTITY_ROW: dict[str, Any] = {
    "id": _IDS["processo_id"],
    "processo_id": _IDS["processo_id"],
    "instancia_id": _IDS["instancia_id"],
    "revisao_id": _IDS["revisao_id"],
    "medicao_id": _IDS["medicao_id"],
    "investimento_id": _IDS["investimento_id"],
    "recurso_id": _IDS["recurso_id"],
    "recurso_compartilhado_id": _IDS["recurso_id"],
    "recurso_custo_id": _IDS["recurso_custo_id"],
    "vinculo_id": _IDS["vinculo_id"],
    "arquivo_id": _IDS["arquivo_id"],
    "evidencia_id": _IDS["evidencia_id"],
    "filial_id": "01",
    "codigo_filial": "01",
    "setor_id": _IDS["setor_id"],
    "status_processo": "ativo",
    "status_filial": "ativo",
    "status_setor": "ativo",
    "status_recurso": "ativo",
    "nome": "Smoke",
    "nome_processo": "Smoke Processo",
    "titulo": "Smoke",
    "todas_filiais_ativas": False,
    "codigo_filial_list": ["01"],
    "conteudo": _EMPTY_FLOW,
    "mermaid_cached": "graph TD; A-->B;",
    "nome_armazenado": "smoke.bin",
    "nome_arquivo": "smoke.bin",
    "tipo_mime": "application/octet-stream",
    "tipo": "link",
    "url_externa": "https://example.com/smoke",
    "versao_revisao": "v1",
    "cenario_tipo": "baseline",
    "node_ids": [],
    "inherit_all": True,
    "include_descendants": True,
    "include_boundary_edges": False,
}

_SNAPSHOT = {"meta": {"source": "smoke"}, "total": 0, "items": []}
_MERGED_DIAGRAM = {
    "mermaid": "graph TD; A-->B;",
    "flowchart": _EMPTY_FLOW,
    "tree": _EMPTY_TREE,
    "conteudo": _EMPTY_FLOW,
    "nodes": [],
    "edges": [],
}
_DUPLICATE_PROCESSO = {
    "processo": dict(_ENTITY_ROW),
    "copiados": {"revisoes": 0},
}
_DUPLICATE_INSTANCIA = {
    "instancia": dict(_ENTITY_ROW),
    "processo_id": _IDS["processo_id"],
    "copiados": {"revisoes": 0},
}
_DUPLICATE_REVISAO = {
    "revisao": dict(_ENTITY_ROW),
    "processo_id": _IDS["processo_id"],
    "instancia_id": _IDS["instancia_id"],
    "copiados": {},
}


def smoke_ids() -> dict[str, str]:
    return dict(_IDS)


class SmokeDouble:
    """Double JSON-safe (evita MagicMock.assert_* e retorno não serializável)."""

    def __getattr__(self, name: str) -> Callable[..., Any]:
        def _method(*_args: Any, **_kwargs: Any) -> Any:
            if name.startswith("find_"):
                return None
            if name in {
                "list",
                "list_for_options",
                "list_by_processo",
                "list_by_revisao",
                "list_by_recurso",
                "list_vinculos",
                "list_custos",
                "list_processos_calculados",
                "query_ranking_processos",
                "query_resumo_por_familia",
                "build_rows",
            }:
                return []
            if name == "list_active_codigos":
                return {"01"}
            if name == "list_for_processo":
                return {"items": [], "total": 0, "page": 1, "page_size": 20}
            if name in {
                "get",
                "get_by_revisao",
                "create",
                "update",
                "upsert",
                "update_contexto",
                "soft_delete",
                "activate",
                "registrar_reajuste",
            }:
                return dict(_ENTITY_ROW)
            if name == "overlay_is_empty":
                return True
            if name == "assert_overlay_within_escopo":
                overlay = _kwargs.get("overlay")
                if isinstance(overlay, dict) and overlay:
                    return overlay
                return dict(_EMPTY_TREE_OVERLAY)
            if name == "fetch_one":
                return {"processos_table": "transformometro.processos"}
            if name in {
                "is_active_for_filial",
                "can_view_filial",
                "can_manage_filial",
                "can_view_consolidated",
            }:
                return True
            if name in {"delete", "delete_file", "log", "save_escopo", "notify", "publish"}:
                return True if name == "delete" else None
            if name == "save":
                return "smoke.bin"
            if name == "resolve_file":
                return str(_SMOKE_FILE)
            if name == "enrich_processos":
                return _args[0] if _args else []
            if name == "filter_filiais_options":
                return _args[0] if _args else []
            if name == "filter_rows_by_filial":
                return _args[0] if _args else []
            if name == "duplicate":
                return {
                    **_DUPLICATE_PROCESSO,
                    **_DUPLICATE_INSTANCIA,
                    **_DUPLICATE_REVISAO,
                }
            if name in {
                "export_csv",
                "export_excel",
                "export_package",
                "export_flat_csv",
                "render_csv",
                "build_csv",
            }:
                return b"a,b\n1,2\n"
            if name == "to_csv":
                return "a,b\n1,2\n"
            if name == "build_excel_html":
                return "<table><tr><td>smoke</td></tr></table>"
            if name == "export_xml":
                return "<definitions/>"
            if name in {"flowchart_to_mermaid", "to_mermaid"}:
                return "graph TD; A-->B;"
            if name == "import_xml":
                return dict(_EMPTY_FLOW)
            if name in {
                "merge",
                "build_revisao_view",
                "compose_for_processo",
                "compose_for_revisao",
            }:
                return dict(_MERGED_DIAGRAM)
            if name in {"processos", "instancias", "linhas", "resumo"}:
                return dict(_SNAPSHOT)
            if name == "meta":
                return {"latest_calculated_at": None, "row_count": 0, "source": "smoke"}
            if name in {"recalculate", "recalcular"}:
                return {"mode": "full", "ok": True}
            if name in {"preview", "preview_package"}:
                return {"valid": True, "ok": True, "diff": {}, "entities": {}}
            if name in {"apply", "apply_package"}:
                return {"ok": True, "entities": {}}
            if name == "export_bundle":
                return {"version": 1, "entities": {}}
            if name == "heartbeat":
                return {"ok": True, "user_id": "test-user"}
            if name == "acquire_lock":
                return {"acquired": True, "holder": {"user_name": "TM Test"}}
            if name == "release_lock":
                return {"ok": True}
            if name == "list_presence":
                return {"items": []}
            if name == "list_negative_savings_alerts":
                return {"items": []}
            if name == "resolve":
                scope = MagicMock(
                    is_unrestricted=True,
                    allowed_codigos=frozenset(),
                    can_view_consolidated=True,
                    scoped_manage=False,
                )
                scope.meta.return_value = {"mode": "unrestricted"}
                return scope
            if name.startswith("list_") or name.startswith("build_") or name.startswith("save_"):
                return {"items": [], "total": 0, "series": [], "ok": True}
            return {
                "ok": True,
                "items": [],
                "total": 0,
                "nodes": [],
                "edges": [],
                "series": [],
                "conteudo": _EMPTY_FLOW,
                "mermaid": "graph TD; A-->B;",
                "flowchart": _EMPTY_FLOW,
                "tree": _EMPTY_TREE,
                "copiados": {},
                "mode": "full",
            }

        return _method


def _make_instance() -> SmokeDouble:
    return SmokeDouble()


class _RepoFactory:
    """Substitui a classe: () -> instância; atributos de classe -> mesmos métodos do double."""

    def __call__(self, *_args: Any, **_kwargs: Any) -> SmokeDouble:
        return _make_instance()

    def __getattr__(self, name: str) -> Callable[..., Any]:
        return getattr(_make_instance(), name)


_ROUTE_MODULES = (
    "tm_app.interface.http.routes.crud_routes",
    "tm_app.interface.http.routes.dashboard_routes",
    "tm_app.interface.http.routes.integrations_routes",
    "tm_app.interface.http.routes.json_backup_routes",
    "tm_app.interface.http.routes.revisao_evidence_routes",
    "tm_app.interface.http.routes.processo_arquivo_routes",
    "tm_app.interface.http.routes.diagram_routes",
    "tm_app.interface.http.routes.decomposition_routes",
    "tm_app.interface.http.routes.collaboration_routes",
    "tm_app.interface.http.routes.transformometro_routes",
    "tm_app.interface.http.filial_access_http",
)

_NOTIFY_TARGETS = (
    "tm_app.interface.http.routes.collaboration_routes.notify_presence_updated",
    "tm_app.interface.http.routes.crud_routes.notify_entity_updated",
    "tm_app.interface.http.routes.json_backup_routes.notify_entity_updated",
    "tm_app.interface.http.routes.diagram_routes.notify_entity_updated",
    "tm_app.interface.http.routes.decomposition_routes.notify_entity_updated",
    "tm_app.interface.http.routes.revisao_evidence_routes.notify_entity_updated",
    "tm_app.interface.http.routes.processo_arquivo_routes.notify_entity_updated",
    "tm_app.interface.http.routes.dashboard_routes.notify_catalog_updated",
)


@contextmanager
def universal_route_mocks() -> Iterator[None]:
    """Patch classes *Repository/*Service e singletons nos módulos de rota."""
    with ExitStack() as stack:
        for target in _NOTIFY_TARGETS:
            try:
                stack.enter_context(patch(target, MagicMock(return_value=None)))
            except (AttributeError, ModuleNotFoundError):
                continue
        for mod_name in _ROUTE_MODULES:
            mod = importlib.import_module(mod_name)
            for name in dir(mod):
                if name.startswith("__"):
                    continue
                attr = getattr(mod, name)
                if isinstance(attr, type) and (
                    name.endswith("Repository")
                    or name.endswith("Service")
                    or name.endswith("Storage")
                ):
                    stack.enter_context(patch.object(mod, name, _RepoFactory()))
                elif name.startswith("_") and not isinstance(attr, type):
                    if callable(attr) and not hasattr(attr, "__self__"):
                        continue
                    if isinstance(
                        attr,
                        (frozenset, set, dict, list, tuple, str, bytes, int, float, bool),
                    ):
                        continue
                    if hasattr(attr, "pattern") and hasattr(attr, "search"):
                        continue
                    if name.endswith(("_FIELDS", "_PATTERN", "_CACHE", "_LOCK")):
                        continue
                    stack.enter_context(patch.object(mod, name, _make_instance()))
        yield
