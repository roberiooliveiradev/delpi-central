"""DAVI-PRODUCT-DRAWING-CAPABILITY-001 — JSON catalog/metadata foundation."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from app.application.external_capabilities.dynamic_information.action_index import (
    reset_action_index_for_tests,
    set_actions_for_tests,
)
from app.application.external_capabilities.dynamic_information.argument_validator import (
    ArgumentValidationError,
    build_argument_json_schema,
    validate_arguments,
)
from app.application.external_capabilities.dynamic_information.candidate_token import (
    mint_candidate_token,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.discover_service import (
    discover_delpi_information,
)
from app.application.external_capabilities.dynamic_information.execute_service import (
    execute_delpi_information,
)
from app.application.external_capabilities.dynamic_information.projection import (
    apply_approved_field_projection,
)
from app.application.external_capabilities.dynamic_information.read_only_intent_guard import (
    clear_read_only_intent_guard_cache,
)
from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
)
from app.domain.ports.davi_catalog_action_executor_port import CatalogActionExecutionResult

_API_ROOT = Path(__file__).resolve().parents[1]
_DRAWING = ("list_product_drawings", "get_product_drawing")
_PRIOR_FIFTEEN = (
    "search_products",
    "get_product_stock",
    "get_product_suppliers",
    "get_product_customers",
    "get_product_purchases",
    "get_product_structure",
    "get_product_production_status",
    "get_product_factory_status",
    "get_product_structure_exclusivity",
    "get_product_shipping_status",
    "get_product_pricing",
    "get_product_purchase_price_history",
    "get_product_last_purchase",
    "get_product_guide",
    "get_product_parents",
)
_UNKNOWN_ARGS = (
    "sql",
    "url",
    "path",
    "method",
    "operationId",
    "legacy",
    "debug",
    "filename",
    "sort",
    "direction",
    "library_dir",
)


@pytest.fixture(autouse=True)
def _reset_index():
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()
    yield
    reset_action_index_for_tests()
    load_external_read_allowlist.cache_clear()
    load_dynamic_read_budgets.cache_clear()
    clear_read_only_intent_guard_cache()


def _actions() -> list[TechnicalAction]:
    baseline = json.loads(
        (_API_ROOT / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )
    return build_technical_actions_from_baseline(
        baseline, allowlist=load_external_read_allowlist()
    )


def _action(oid: str) -> TechnicalAction:
    return next(a for a in _actions() if a.operation_id == oid)


def _allowlist_entry(oid: str) -> dict[str, Any]:
    allow = load_external_read_allowlist()
    return next(
        op
        for op in allow["operations"]
        if isinstance(op, dict) and op.get("operationId") == oid
    )


def _dumped(payload: Any) -> str:
    return json.dumps(payload, default=str, ensure_ascii=False)


class _PayloadExecutor:
    def __init__(self, payload: Any):
        self.payload = payload
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, *, action_id: str, validated_arguments: dict[str, Any]):
        self.calls.append((action_id, dict(validated_arguments)))
        return CatalogActionExecutionResult(outcome="ok", payload=self.payload)


def test_drawing_eligible_count_exactly_seventeen():
    eligible = sorted(a.operation_id for a in _actions() if a.executable)
    assert len(eligible) == 17
    assert set(eligible) == set(_PRIOR_FIFTEEN) | set(_DRAWING)
    allow = load_external_read_allowlist()
    assert allow.get("version") == 9
    assert allow.get("coverageDecision", {}).get("taskId") == (
        "DAVI-PRODUCT-DRAWING-CAPABILITY-001"
    )
    blocked = {
        item.get("operationId")
        for item in allow.get("explicitlyNotApproved") or []
        if isinstance(item, dict)
    }
    assert "get_product_drawing_pdf" in blocked
    assert "get_product_analyser" in blocked
    assert "get_product_inspection" in blocked
    assert "list_product_drawings" not in blocked
    assert "get_product_drawing" not in blocked


def test_drawing_mcp_tools_remain_three():
    import asyncio
    from app.interface.mcp.server import create_mcp_server

    tools = asyncio.run(create_mcp_server().list_tools())
    assert [t.name for t in tools] == [
        "search_products",
        "discover_delpi_information",
        "execute_delpi_information",
    ]


@pytest.mark.parametrize(
    "query,expected",
    [
        ("desenho do produto 90261805", "list_product_drawings"),
        ("desenho técnico do produto", "list_product_drawings"),
        ("PDF do desenho", "list_product_drawings"),
        ("listar desenhos do produto", "list_product_drawings"),
        ("product drawing", "list_product_drawings"),
        ("technical drawing", "list_product_drawings"),
        ("drawing PDF", "list_product_drawings"),
        ("metadados do desenho", "get_product_drawing"),
        ("drawing metadata", "get_product_drawing"),
        ("server-resolved drawing", "get_product_drawing"),
    ],
)
def test_drawing_discovery_aliases(query: str, expected: str, monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    set_actions_for_tests(_actions())
    discovered = discover_delpi_information(query=query, actor_id="user-1")
    assert discovered["eligible_action_count"] == 17, query
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert expected in ids


@pytest.mark.parametrize(
    "query,winner,loser",
    [
        ("desenho do produto", "list_product_drawings", "get_product_structure"),
        ("desenho técnico", "list_product_drawings", "get_product_guide"),
        ("estrutura do produto", "get_product_structure", "list_product_drawings"),
        ("roteiro do produto", "get_product_guide", "list_product_drawings"),
    ],
)
def test_drawing_retrieval_collision_regressions(
    query: str, winner: str, loser: str, monkeypatch
):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    set_actions_for_tests(_actions())
    discovered = discover_delpi_information(query=query, actor_id="user-1")
    ids = [c["action_id"] for c in discovered["candidates"]]
    assert winner in ids
    if loser in ids:
        assert ids.index(winner) < ids.index(loser)


@pytest.mark.parametrize(
    "query",
    [
        "substitua o desenho do produto",
        "publique o desenho",
        "aprove o desenho",
        "libere o desenho",
        "exclua o PDF do desenho",
        "renomeie o desenho",
        "atualize o arquivo no servidor",
        "grave esta revisão do desenho",
    ],
)
def test_drawing_write_guard_blocks_mutation_intents(query: str, monkeypatch):
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.discover_service.candidate_token_secret",
        lambda: "sec",
    )
    set_actions_for_tests(_actions())
    discovered = discover_delpi_information(query=query, top_k=5, actor_id="user-1")
    assert discovered["candidate_count"] == 0, (query, discovered["candidates"])


def test_catalog_require_code_and_reject_unknown_args():
    action = _action("list_product_drawings")
    schema = build_argument_json_schema(action)
    assert "code" in schema["required"]
    assert set(schema["properties"]) == {
        "code",
        "code_exact",
        "revision",
        "file_kind",
        "has_variant",
        "has_revision",
        "page",
        "page_size",
    }
    with pytest.raises(ArgumentValidationError, match="Missing required argument: code"):
        validate_arguments(action, {})
    with pytest.raises(ArgumentValidationError, match="Unknown argument"):
        validate_arguments(action, {"code": "10000001", "filename": "x.pdf"})
    for bad in _UNKNOWN_ARGS:
        with pytest.raises(ArgumentValidationError):
            validate_arguments(action, {"code": "10000001", bad: "x"})
    cleaned = validate_arguments(action, {"code": "10000001"})
    assert cleaned["code"] == "10000001"
    assert cleaned["page"] == 1
    assert cleaned["page_size"] == 50


def test_metadata_requires_code_only():
    action = _action("get_product_drawing")
    schema = build_argument_json_schema(action)
    assert schema["required"] == ["code"]
    assert set(schema["properties"]) == {"code"}
    with pytest.raises(ArgumentValidationError, match="Missing required argument: code"):
        validate_arguments(action, {})
    assert validate_arguments(action, {"code": "10000001"}) == {"code": "10000001"}


def test_catalog_projection_drops_library_dir_and_route_paths():
    entry = _allowlist_entry("list_product_drawings")
    fields = tuple(entry["approvedResponseFields"])
    raw = {
        "items": [
            {
                "product_code": "10000001",
                "filename": "10000001.pdf",
                "file_kind": "exact",
                "revision": None,
                "variant_suffix": None,
                "size_bytes": 12,
                "modified_at": "2026-01-01T00:00:00+00:00",
                "media_type": "application/pdf",
                "drawing_metadata_path": "/products/10000001/drawing",
                "drawing_pdf_path": "/products/10000001/drawing/pdf",
                "absolute_path": "/srv/drawings/10000001.pdf",
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "summary": {
            "library_available": True,
            "library_dir": "/secret/drawing-pdfs",
            "scanned_files": 10,
            "matched_files": 1,
            "filters_applied": {"code": "10000001"},
        },
        "internal_debug": True,
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["items"][0]["product_code"] == "10000001"
    assert projected["items"][0]["filename"] == "10000001.pdf"
    assert projected["summary"]["library_available"] is True
    assert projected["summary"]["scanned_files"] == 10
    assert "library_dir" not in dumped
    assert "drawing_metadata_path" not in dumped
    assert "drawing_pdf_path" not in dumped
    assert "absolute_path" not in dumped
    assert "/secret/" not in dumped
    assert "filters_applied" not in dumped
    assert "internal_debug" not in dumped


def test_metadata_projection_no_path_leak():
    entry = _allowlist_entry("get_product_drawing")
    fields = tuple(entry["approvedResponseFields"])
    raw = {
        "found": True,
        "product_code": "10000001",
        "filename": "10000001_R02.pdf",
        "revision": "2",
        "variant_suffix": None,
        "size_bytes": 99,
        "modified_at": "2026-01-01T00:00:00+00:00",
        "media_type": "application/pdf",
        "path": "/secret/10000001_R02.pdf",
        "absolute_path": "/secret/10000001_R02.pdf",
        "message": "ok",
    }
    projected = apply_approved_field_projection(raw, approved_fields=fields)
    dumped = _dumped(projected)
    assert projected["found"] is True
    assert projected["filename"] == "10000001_R02.pdf"
    assert "path" not in dumped
    assert "absolute_path" not in dumped
    assert "message" not in dumped
    assert "/secret/" not in dumped


def test_execute_catalog_and_metadata_generic_path(monkeypatch: pytest.MonkeyPatch):
    set_actions_for_tests(_actions())
    secret = "drawing-test-secret"
    monkeypatch.setattr(
        "app.application.external_capabilities.dynamic_information.execute_service.candidate_token_secret",
        lambda: secret,
    )
    catalog_payload = {
        "items": [
            {
                "product_code": "10000001",
                "filename": "10000001.pdf",
                "file_kind": "exact",
                "revision": None,
                "variant_suffix": None,
                "size_bytes": 12,
                "modified_at": "2026-01-01T00:00:00+00:00",
                "media_type": "application/pdf",
                "drawing_metadata_path": "/products/10000001/drawing",
                "drawing_pdf_path": "/products/10000001/drawing/pdf",
            }
        ],
        "page": 1,
        "page_size": 50,
        "total": 1,
        "total_pages": 1,
        "summary": {
            "library_available": True,
            "library_dir": "/secret",
            "scanned_files": 1,
            "matched_files": 1,
        },
    }
    meta_payload = {
        "found": True,
        "product_code": "10000001",
        "filename": "10000001.pdf",
        "revision": None,
        "variant_suffix": None,
        "size_bytes": 12,
        "modified_at": "2026-01-01T00:00:00+00:00",
        "media_type": "application/pdf",
        "path": "/secret/10000001.pdf",
    }

    for oid, payload in (
        ("list_product_drawings", catalog_payload),
        ("get_product_drawing", meta_payload),
    ):
        token = mint_candidate_token(
            action_id=oid,
            actor_id="actor-1",
            secret=secret,
            ttl_seconds=60,
        )
        result = execute_delpi_information(
            candidate_token=token,
            arguments={"code": "10000001"},
            actor_id="actor-1",
            catalog_action_executor=_PayloadExecutor(
                {"success": True, "data": payload}
            ),
        )
        assert result["status"] == "ok"
        dumped = _dumped(result.get("data") or {})
        assert "library_dir" not in dumped
        assert "drawing_metadata_path" not in dumped
        assert "drawing_pdf_path" not in dumped
        assert "/secret" not in dumped
        assert "pdf_base64" not in dumped


def test_pdf_not_eligible_and_no_operation_specific_executor_branch():
    eligible = {a.operation_id for a in _actions() if a.executable}
    assert "get_product_drawing_pdf" not in eligible
    assert "get_product_analyser" not in eligible
    execute_src = (
        _API_ROOT
        / "app/application/external_capabilities/dynamic_information/execute_service.py"
    ).read_text(encoding="utf-8")
    tree = ast.parse(execute_src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and comparator.value in {
                    "list_product_drawings",
                    "get_product_drawing",
                    "get_product_drawing_pdf",
                }:
                    pytest.fail("operationId-specific branch in execute_service")


def test_resolver_synthetic_filenames_not_labeled_official(tmp_path: Path):
    library = tmp_path / "drawings"
    library.mkdir()
    (library / "10000001.pdf").write_bytes(b"%PDF-1.4 exact")
    (library / "10000001_R01.pdf").write_bytes(b"%PDF-1.4 r01")
    (library / "10000001_R02.pdf").write_bytes(b"%PDF-1.4 r02")
    (library / "10000001-1.pdf").write_bytes(b"%PDF-1.4 variant")
    storage = DrawingPdfLibraryStorage(library)

    exact = storage.find_drawing("10000001")
    assert exact is not None
    assert exact.filename == "10000001.pdf"

    only_revs = tmp_path / "revs"
    only_revs.mkdir()
    (only_revs / "10000002_R01.pdf").write_bytes(b"%PDF-1.4 r01")
    (only_revs / "10000002_R02.pdf").write_bytes(b"%PDF-1.4 r02")
    rev = DrawingPdfLibraryStorage(only_revs).find_drawing("10000002")
    assert rev is not None
    assert rev.filename == "10000002_R02.pdf"
    assert rev.revision == "2"

    variant = storage.find_drawing("10000001-1")
    assert variant is not None
    assert variant.filename == "10000001-1.pdf"
    # Resolution is file-server selection, not proven engineering approval.
    assert getattr(exact, "official", None) is None
    assert getattr(exact, "approved", None) is None
