"""Evidence-only DAVI capability expansion inventory (no runtime authority).

TASK: DAVI-CAPABILITY-EXPANSION-INVENTORY-001

Does not mutate allowlist, eligibility, projection, retrieval, execute, MCP, or Agent.
"""

from __future__ import annotations

import ast
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.application.external_capabilities.constants import (
    MCP_TOOL_DISCOVER_DELPI_INFORMATION,
    MCP_TOOL_EXECUTE_DELPI_INFORMATION,
)
from app.application.external_capabilities.dynamic_information.catalog_builder import (
    TechnicalAction,
    build_technical_actions_from_baseline,
)
from app.application.external_capabilities.dynamic_information.content_loader import (
    load_dynamic_read_budgets,
    load_external_read_allowlist,
)
from app.application.external_capabilities.dynamic_information.eligibility import (
    is_dynamically_executable,
)

TASK_ID = "DAVI-CAPABILITY-EXPANSION-INVENTORY-001"
ARTIFACT_STEM = "davi-capability-expansion-inventory-001"
FREEZE_STEM = "davi-capability-wave-001-freeze"

EXCLUSION_STATUSES = frozenset(
    {
        "ADMIN_OUT_OF_SCOPE",
        "DESTRUCTIVE_OUT_OF_SCOPE",
        "GENERIC_SQL_FORBIDDEN",
        "STREAM_BINARY_OUT_OF_SCOPE",
        "WRITE_OUT_OF_SCOPE",
        "LEGACY_UNSAFE",
        "NOT_RELEVANT",
        "EXPLICIT_PROCESSING_PROHIBITION",
    }
)

# Path-prefix → bounded context. First match wins.
_DOMAIN_PREFIXES: tuple[tuple[str, str], ...] = (
    ("/products", "product"),
    ("/supplies", "supplies"),
    ("/purchases", "supplies"),
    ("/production", "production"),
    ("/commercial", "commercial"),
    ("/sales", "commercial"),
    ("/customers", "commercial"),
    ("/pedidos-venda-abertos", "commercial"),
    ("/propostas-comerciais", "commercial"),
    ("/request-lookups", "commercial"),
    ("/health", "admin"),
    ("/public/quality-labels", "quality"),
    ("/public/scheduling", "scheduling"),
    ("/financeiro", "financial"),
    ("/financial", "financial"),
    ("/planejamento-orcamentario", "financial"),
    ("/quality", "quality"),
    ("/ppm", "quality"),
    ("/refugos", "quality"),
    ("/retrabalho", "quality"),
    ("/inspecoes", "inspection"),
    ("/process-inspection", "inspection"),
    ("/engineering", "engineering"),
    ("/hr", "hr"),
    ("/canal-denuncia", "hr"),
    ("/cultura-delpi", "hr"),
    ("/scheduling", "scheduling"),
    ("/dashboard", "dashboards"),
    ("/reports", "reports"),
    ("/guias-procedimentos", "engineering"),
    ("/lancamento-notas-fiscais", "financial"),
    ("/invoice-issuance", "financial"),
    ("/mural-acessos", "admin"),
    ("/public/mural-acessos", "admin"),
    ("/system", "admin"),
    ("/admin", "admin"),
    ("/gpt-actions", "admin"),
    ("/data/sql", "sql"),
    ("/mcp", "not_relevant"),
)


def api_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repo_root() -> Path:
    return api_root().parents[0]


def git_sha(ref: str = "HEAD") -> str:
    result = subprocess.run(
        ["git", "rev-parse", ref],
        cwd=repo_root(),
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def infer_domain(path: str) -> str:
    path_l = (path or "").lower()
    for prefix, domain in _DOMAIN_PREFIXES:
        if path_l == prefix or path_l.startswith(prefix + "/") or path_l.startswith(prefix):
            return domain
    return "other"


def _load_operation_id_constants() -> dict[str, str]:
    """Map Python constant name → operationId from OpenAPI agent metadata."""
    from app.interface.http import openapi_agent_metadata as meta

    mapping: dict[str, str] = {}
    for name, value in vars(meta).items():
        if name.startswith("_") or not isinstance(value, dict):
            continue
        oid = value.get("operation_id")
        if isinstance(oid, str) and oid.strip():
            mapping[name] = oid.strip()
    return mapping


def scan_route_authz() -> dict[str, dict[str, Any]]:
    """Best-effort source scan of route modules for permission decorators.

    PROVEN only when an operationId is bound to require_permission/require_any_permission
    in the same function decorator list. Otherwise omitted (caller uses TO_INVENTORY).
    """
    routes_dir = api_root() / "app/interface/http/routes"
    const_oids = _load_operation_id_constants()
    found: dict[str, dict[str, Any]] = {}

    for path in sorted(routes_dir.rglob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, SyntaxError):
            continue
        rel = str(path.relative_to(api_root()))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            op_ids: list[str] = []
            perms: list[str] = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call):
                    for kw in dec.keywords:
                        if kw.arg == "operation_id" and isinstance(kw.value, ast.Constant):
                            if isinstance(kw.value.value, str):
                                op_ids.append(kw.value.value)
                        if kw.arg is None and isinstance(kw.value, ast.Name):
                            mapped = const_oids.get(kw.value.id)
                            if mapped:
                                op_ids.append(mapped)
                    func = dec.func
                    func_name = ""
                    if isinstance(func, ast.Name):
                        func_name = func.id
                    elif isinstance(func, ast.Attribute):
                        func_name = func.attr
                    if func_name in {"require_permission", "require_any_permission"}:
                        for arg in dec.args:
                            if isinstance(arg, ast.Name):
                                perms.append(arg.id)
                            elif isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                                perms.append(arg.value)
            if not op_ids:
                continue
            for oid in op_ids:
                entry = found.setdefault(
                    oid,
                    {
                        "operationId": oid,
                        "route_module": rel,
                        "handler": node.name,
                        "permission_symbols": [],
                        "authz_evidence": "TO_INVENTORY",
                    },
                )
                if rel and entry.get("route_module") in (None, ""):
                    entry["route_module"] = rel
                entry["handler"] = node.name
                if perms:
                    merged = list(dict.fromkeys(list(entry.get("permission_symbols") or []) + perms))
                    entry["permission_symbols"] = merged
                    entry["authz_evidence"] = "PROVEN"
                    entry["backend_authz"] = "PROVEN"
                    entry["authz_mechanism"] = "route_decorator"
    return found


def load_baseline() -> dict[str, Any]:
    return json.loads(
        (api_root() / "app/content/openapi_baseline.json").read_text(encoding="utf-8")
    )


def build_actions(baseline: dict[str, Any] | None = None) -> list[TechnicalAction]:
    load_external_read_allowlist.cache_clear()
    payload = baseline if baseline is not None else load_baseline()
    allowlist = load_external_read_allowlist()
    return build_technical_actions_from_baseline(payload, allowlist=allowlist)


def mcp_tool_names() -> list[str]:
    """Canonical MCP tool surface from constants (not provider discovery)."""
    return [
        MCP_TOOL_DISCOVER_DELPI_INFORMATION,
        MCP_TOOL_EXECUTE_DELPI_INFORMATION,
    ]


def _param_names(action: TechnicalAction) -> list[str]:
    return [str(p.get("name")) for p in action.parameters if p.get("name")]


def _required_params(action: TechnicalAction) -> list[str]:
    out: list[str] = []
    for p in action.parameters:
        if p.get("required") and p.get("name"):
            out.append(str(p["name"]))
    path = action.path or ""
    for part in path.split("/"):
        if part.startswith("{") and part.endswith("}"):
            name = part[1:-1]
            if name not in out:
                out.append(name)
    return out


def _branch_semantics(action: TechnicalAction) -> str:
    names = {n.lower() for n in _param_names(action)}
    if "branch" not in names and "filial" not in names:
        return "not_applicable"
    required = {n.lower() for n in _required_params(action)}
    enums: list[str] = []
    for p in action.parameters:
        if str(p.get("name") or "").lower() in {"branch", "filial"}:
            raw = p.get("enum") or []
            enums = [str(x) for x in raw]
    if enums and set(enums) <= {"all", "01", "02"} and "all" in enums:
        if "branch" in required or "filial" in required:
            return "required_scope: all | 01 | 02"
        return "optional_consolidated: all | 01 | 02"
    if enums and set(enums) <= {"01", "02"}:
        return "required_concrete: 01 | 02"
    if "branch" in required or "filial" in required:
        return "required_filter_unspecified_enum"
    return "optional_filter"


def _pagination_model(action: TechnicalAction) -> str:
    names = {n.lower() for n in _param_names(action)}
    if "page" in names or "page_size" in names:
        return "page/page_size"
    if (action.shape or "") == "paged_list":
        return "paged_list_shape"
    return "none"


def technical_rows(
    actions: list[TechnicalAction],
    *,
    authz_index: dict[str, dict[str, Any]],
    capability_by_operation: dict[str, str],
) -> list[dict[str, Any]]:
    allowlist = load_external_read_allowlist()
    allow_ids = {
        str(item.get("operationId"))
        for item in (allowlist.get("operations") or [])
        if isinstance(item, dict) and item.get("operationId")
    }
    not_approved = {
        str(item.get("operationId")): item
        for item in (allowlist.get("explicitlyNotApproved") or [])
        if isinstance(item, dict) and item.get("operationId")
    }
    rows: list[dict[str, Any]] = []
    for action in sorted(actions, key=lambda a: (a.method, a.operation_id)):
        authz = authz_index.get(action.operation_id) or {}
        payload_risk = "low"
        if action.davi_status in {
            "NEEDS_NESTED_PROJECTION_SUPPORT",
            "STREAM_BINARY_OUT_OF_SCOPE",
        }:
            payload_risk = "high"
        elif action.davi_status == "NEEDS_MODEL_SAFE_PROJECTION":
            payload_risk = "medium"
        rows.append(
            {
                "operationId": action.operation_id,
                "http_path": action.path,
                "bounded_context": infer_domain(action.path),
                "route_module": authz.get("route_module") or "TO_INVENTORY",
                "handler": authz.get("handler") or "TO_INVENTORY",
                "method": action.method,
                "summary": action.summary,
                "description": action.description,
                "tags": list(action.tags),
                "owner": (
                    "api-delpi.product"
                    if infer_domain(action.path) == "product"
                    else f"api-delpi.{infer_domain(action.path)}"
                ),
                "owner_evidence": (
                    "PROVEN" if authz.get("route_module") else "TO_INVENTORY"
                ),
                "canonical_use_case": authz.get("handler") or "TO_INVENTORY",
                "repository_downstream_source": "TO_INVENTORY",
                "backend_permission_symbols": authz.get("permission_symbols") or [],
                "backend_authz": authz.get("backend_authz") or "TO_INVENTORY",
                "authz_mechanism": authz.get("authz_mechanism") or "TO_INVENTORY",
                "branch_semantics": _branch_semantics(action),
                "parameters": _param_names(action),
                "required_parameters": _required_params(action),
                "pagination_model": _pagination_model(action),
                "response_shape": action.shape,
                "response_schema": action.entity,
                "estimated_payload_risk": payload_risk,
                "binary": action.davi_status == "STREAM_BINARY_OUT_OF_SCOPE",
                "stream": action.davi_status == "STREAM_BINARY_OUT_OF_SCOPE",
                "admin": action.davi_status == "ADMIN_OUT_OF_SCOPE",
                "generic_sql": action.davi_status == "GENERIC_SQL_FORBIDDEN",
                "sensitive_high_volume": payload_risk == "high",
                "current_davi_disposition": action.davi_status,
                "current_blocker": (
                    None
                    if action.davi_status == "DAVI_ELIGIBLE_READ"
                    else action.davi_status
                ),
                "current_allowlist_presence": action.operation_id in allow_ids,
                "current_projection_support": bool(action.approved_response_fields),
                "current_aliases": list(action.semantic_aliases),
                "explicitly_not_approved": action.operation_id in not_approved,
                "semantic_capability_id": capability_by_operation.get(action.operation_id),
                "existing_tests": "TO_INVENTORY",
                "notes": (
                    (not_approved.get(action.operation_id) or {}).get("reason")
                    if action.operation_id in not_approved
                    else None
                ),
            }
        )
    return rows


def _cap(
    *,
    capability_id: str,
    business_name_ptbr: str,
    business_name_en: str,
    business_need: str,
    domain: str,
    technical_operations: list[str],
    primary_operation: str,
    owner: str,
    authoritative_source: str,
    canonical_use_case: str,
    backend_authz: str,
    semantic_contract: str,
    required_inputs: list[str],
    optional_inputs: list[str],
    output_allowlist_candidate: list[str],
    response_shape: str,
    projection_mode: str,
    branch_semantics: str,
    current_status: str,
    primary_blocker: str | None,
    wave_candidate: str | None,
    retrieval_aliases_ptbr: list[str],
    retrieval_aliases_en: list[str],
    **extra: Any,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "capability_id": capability_id,
        "business_name_ptbr": business_name_ptbr,
        "business_name_en": business_name_en,
        "business_need": business_need,
        "domain": domain,
        "technical_operations": technical_operations,
        "primary_operation": primary_operation,
        "owner": owner,
        "authoritative_source": authoritative_source,
        "canonical_use_case": canonical_use_case,
        "READ_PREPARE_ACT": extra.get("READ_PREPARE_ACT", "READ"),
        "identity_model": extra.get("identity_model", "END_USER_ACCOUNT"),
        "backend_authz": backend_authz,
        "business_authz_owner": "NONE",
        "semantic_contract": semantic_contract,
        "required_inputs": required_inputs,
        "optional_inputs": optional_inputs,
        "input_minimization": extra.get(
            "input_minimization",
            "Omit legacy/debug/sort internals; keep business identifiers and bounded paging/dates.",
        ),
        "output_business_fields": extra.get(
            "output_business_fields", output_allowlist_candidate
        ),
        "output_allowlist_candidate": output_allowlist_candidate,
        "response_shape": response_shape,
        "projection_mode": projection_mode,
        "pagination": extra.get("pagination", "none"),
        "branch_semantics": branch_semantics,
        "completeness_semantics": extra.get(
            "completeness_semantics",
            "Do not imply completeness unless canonical payload exposes is_complete/total.",
        ),
        "model_safety": extra.get("model_safety", "explicit_allowlist_no_wildcard"),
        "privacy_risk": extra.get("privacy_risk", "low"),
        "volume_risk": extra.get("volume_risk", "low"),
        "limits_required": extra.get(
            "limits_required",
            "Use global execute_max_response_bytes=65536 and execute_max_items=50.",
        ),
        "observability_required": extra.get(
            "observability_required",
            "Log action_id, actor id when allowed, status, latency, page/page_size, result_count, correlation id. No payload dump.",
        ),
        "retrieval_aliases_ptbr": retrieval_aliases_ptbr,
        "retrieval_aliases_en": retrieval_aliases_en,
        "redundant_with": extra.get("redundant_with") or [],
        "depends_on": extra.get("depends_on") or [],
        "current_status": current_status,
        "primary_blocker": primary_blocker,
        "implementation_complexity": extra.get("implementation_complexity", "MEDIUM"),
        "testability": extra.get("testability", "HIGH"),
        "live_test_candidate": extra.get("live_test_candidate", False),
        "wave_candidate": wave_candidate,
        "business_value": extra.get("business_value", "MEDIUM"),
        "runtime_risk": extra.get("runtime_risk", "LOW"),
        "negative_authz_test_required": extra.get("negative_authz_test_required", "YES"),
        "quarantine_delta_required": extra.get("quarantine_delta_required") or [],
        "seeded_decision": extra.get("seeded_decision"),
        "freeze_status": extra.get("freeze_status"),
        "owner_evidence": extra.get("owner_evidence", "PROVEN"),
        "source_evidence": extra.get("source_evidence", "PROVEN"),
        "evidence": extra.get("evidence") or [],
        "open_gaps": extra.get("open_gaps") or [],
        "time_semantics": extra.get("time_semantics"),
        "max_depth": extra.get("max_depth"),
        "max_items": extra.get("max_items", 50),
        "rate_limit_decision": extra.get(
            "rate_limit_decision",
            "current_global_limits_sufficient_pending_rollout_policy",
        ),
    }
    return row


def curated_capabilities() -> list[dict[str, Any]]:
    product_owner = "api-delpi Product bounded context"
    totvs_sb1 = "TOTVS Protheus SB1 via SearchProductsUseCase / product repositories"
    return [
        _cap(
            capability_id="product.master.search",
            business_name_ptbr="Buscar cadastro de produto",
            business_name_en="Search product master",
            business_need="Localizar produto por código, descrição ou grupo no cadastro DELPI.",
            domain="product",
            technical_operations=["search_products"],
            primary_operation="search_products",
            owner=product_owner,
            authoritative_source=totvs_sb1,
            canonical_use_case="SearchProductsUseCase",
            backend_authz="PROVEN: @require_any_permission(ENGINEERING_LMP_ACCESS)",
            semantic_contract="Paged Product Master slice: code, description, group.",
            required_inputs=[],
            optional_inputs=["code", "description", "group_code", "page", "page_size"],
            output_allowlist_candidate=[
                "product_code",
                "description",
                "group_category",
            ],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="not_applicable",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=[
                "produto",
                "buscar produto",
                "código do produto",
                "cadastro do produto",
            ],
            retrieval_aliases_en=["search products", "product code", "product master"],
            pagination="page/page_size max 50",
            business_value="HIGH",
            implementation_complexity="LOW",
            runtime_risk="LOW",
            live_test_candidate=True,
            evidence=[
                "davi_external_read_allowlist.json v5",
                "product_routes.search_products_route",
            ],
        ),
        _cap(
            capability_id="product.stock.availability",
            business_name_ptbr="Saldo de estoque do produto",
            business_name_en="Product stock availability",
            business_need="Consultar saldo/disponível de um produto por filial e armazém.",
            domain="product",
            technical_operations=["get_product_stock"],
            primary_operation="get_product_stock",
            owner=product_owner,
            authoritative_source="TOTVS Protheus SB2 via ListProductStock use case",
            canonical_use_case="ListProductStockUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Stock quantities by branch/warehouse; branch is query filter.",
            required_inputs=["code"],
            optional_inputs=["branch", "page", "page_size"],
            output_allowlist_candidate=[
                "product_code",
                "branch",
                "warehouse",
                "current_quantity",
                "available_quantity",
            ],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="optional_consolidated: all | 01 | 02",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=["estoque", "saldo", "saldo disponível"],
            retrieval_aliases_en=["stock", "available quantity", "product stock"],
            pagination="page/page_size max 50",
            business_value="HIGH",
            implementation_complexity="LOW",
            runtime_risk="LOW",
            live_test_candidate=True,
        ),
        _cap(
            capability_id="product.supplier.relationship",
            business_name_ptbr="Fornecedores do produto",
            business_name_en="Product suppliers",
            business_need="Saber quais fornecedores estão vinculados a um produto.",
            domain="product",
            technical_operations=["get_product_suppliers"],
            primary_operation="get_product_suppliers",
            owner=product_owner,
            authoritative_source="TOTVS Protheus SA5 via product suppliers repository",
            canonical_use_case="ListProductSuppliersUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Supplier identity and lead time; prices excluded.",
            required_inputs=["code"],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[
                "product_code",
                "supplier_code",
                "supplier_store",
                "supplier_name",
                "supplier_part_number",
                "unit",
                "registered_lead_time_days",
            ],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="not_applicable",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=["fornecedor", "fornecedores do produto"],
            retrieval_aliases_en=["supplier", "product suppliers"],
            pagination="page/page_size max 50",
            business_value="HIGH",
            implementation_complexity="LOW",
            runtime_risk="LOW",
        ),
        _cap(
            capability_id="product.customer.relationship",
            business_name_ptbr="Clientes do produto",
            business_name_en="Product customers",
            business_need="Saber quais clientes estão vinculados a um produto.",
            domain="product",
            technical_operations=["get_product_customers"],
            primary_operation="get_product_customers",
            owner=product_owner,
            authoritative_source="TOTVS Protheus customer-product relation via product repository",
            canonical_use_case="ListProductCustomersUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Customer identity and quantity; prices excluded.",
            required_inputs=["code"],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[
                "product_code",
                "customer_code",
                "store",
                "customer_name",
                "blocked",
                "customer_product_code",
                "unit",
                "total_quantity",
            ],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="not_applicable",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=["cliente", "clientes do produto"],
            retrieval_aliases_en=["customer", "product customers"],
            pagination="page/page_size max 50",
            business_value="HIGH",
            implementation_complexity="LOW",
            runtime_risk="LOW",
        ),
        _cap(
            capability_id="product.purchasing.history",
            business_name_ptbr="Compras do produto",
            business_name_en="Product purchase history",
            business_need="Ver pedidos de compra associados a um produto, sem preço unitário.",
            domain="product",
            technical_operations=["get_product_purchases"],
            primary_operation="get_product_purchases",
            owner=product_owner,
            authoritative_source="TOTVS Protheus SC7 via product purchases repository",
            canonical_use_case="ListProductPurchasesUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Purchase order identity, dates, quantities; unit_price excluded.",
            required_inputs=["code"],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[
                "order_number",
                "branch",
                "issue_date",
                "supplier_code",
                "store",
                "supplier_name",
                "product_code",
                "ordered_quantity",
            ],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="multi-branch collection",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=["compras do produto", "pedidos de compra do produto"],
            retrieval_aliases_en=["product purchases", "purchase orders for product"],
            pagination="page/page_size max 50",
            business_value="HIGH",
            implementation_complexity="LOW",
            runtime_risk="LOW",
        ),
        _cap(
            capability_id="product.structure.bom",
            business_name_ptbr="Estrutura / BOM do produto",
            business_name_en="Product bill of materials",
            business_need="Ver componentes da estrutura vigente de um produto.",
            domain="product",
            technical_operations=["get_product_structure"],
            primary_operation="get_product_structure",
            owner=product_owner,
            authoritative_source="TOTVS Protheus SG1 via ListProductStructure use case",
            canonical_use_case="ListProductStructureUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Bounded nested BOM without exclusivity flags.",
            required_inputs=["code"],
            optional_inputs=["max_depth", "page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="hierarchy",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=["estrutura", "bom", "componentes do produto"],
            retrieval_aliases_en=["product structure", "bill of materials"],
            pagination="page/page_size plus max_depth",
            max_depth=8,
            business_value="HIGH",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
        ),
        _cap(
            capability_id="product.production.status",
            business_name_ptbr="Situação produtiva do produto",
            business_name_en="Product production status",
            business_need="Saber se a produção do PA/PI iniciou e quais OPs existem na data de referência.",
            domain="product",
            technical_operations=["get_product_production_status"],
            primary_operation="get_product_production_status",
            owner=product_owner,
            authoritative_source="TOTVS Protheus SC2/SH6 via GetProductProductionStatusUseCase",
            canonical_use_case="GetProductProductionStatusUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Production orders and summary for a product; branch is filter.",
            required_inputs=["code"],
            optional_inputs=["branch", "reference_date", "max_depth"],
            output_allowlist_candidate=[],
            response_shape="playbook_report",
            projection_mode="nested",
            branch_semantics="optional_consolidated: all | 01 | 02",
            current_status="CURRENTLY_ELIGIBLE",
            primary_blocker=None,
            wave_candidate=None,
            retrieval_aliases_ptbr=[
                "status de produção",
                "ordem de produção",
                "produção do produto",
            ],
            retrieval_aliases_en=["production status", "production orders"],
            time_semantics="reference_date default today; no unbounded history in current contract",
            business_value="HIGH",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
        ),
        _cap(
            capability_id="product.factory.status",
            business_name_ptbr="Status fabril consolidado do produto",
            business_name_en="Product factory operational status",
            business_need=(
                "Entender a situação fabril de um PA: se há estrutura vigente, OP, "
                "produção iniciada e PA liberado para expedição — sem despejar as listas "
                "já cobertas por BOM, produção e expedição."
            ),
            domain="product",
            technical_operations=["get_product_factory_status"],
            primary_operation="get_product_factory_status",
            owner=product_owner,
            authoritative_source=(
                "GetProductFactoryStatusUseCase → ProductPlaybookRepository (SB1/SG1/SB2/SC2) "
                "+ GetProducedQuantityUseCase (SH6/SHB)"
            ),
            canonical_use_case="GetProductFactoryStatusUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS) on get_factory_status",
            semantic_contract=(
                "Classified factory_status plus product header, dates and section summaries/"
                "indicators. Items arrays of structure/stock/production/shipping are out of "
                "this capability (sibling capabilities already cover those slices)."
            ),
            required_inputs=["code"],
            optional_inputs=[
                "branch",
                "reference_date",
                "start_date",
                "end_date",
                "max_depth",
            ],
            output_allowlist_candidate=FACTORY_STATUS_OUTPUT_FIELDS,
            response_shape="composite_analysis",
            projection_mode="nested",
            branch_semantics="optional_consolidated: all | 01 | 02",
            current_status="READY_FOR_FREEZE",
            primary_blocker=None,
            wave_candidate="WAVE_1",
            retrieval_aliases_ptbr=[
                "status fabril",
                "situação fabril",
                "status na fábrica",
                "visão fabril do produto",
                "situação do produto na fábrica",
            ],
            retrieval_aliases_en=[
                "factory status",
                "factory situation",
                "product factory status",
                "shop-floor status",
            ],
            pagination="none — summaries only",
            time_semantics=(
                "reference_date default today; start_date/end_date default same day; "
                "implementation must bound interval (recommended max 31 days). "
                "Do not approve unbounded history."
            ),
            completeness_semantics=(
                "Summaries are complete relative to backend query; items are intentionally omitted, "
                "so the capability is a classified snapshot, not a full dump. truncated=false unless "
                "global byte budget truncates."
            ),
            max_depth=8,
            business_value="HIGH",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
            live_test_candidate=True,
            freeze_status="FROZEN_FOR_IMPLEMENTATION",
            seeded_decision="PROMOTE",
            quarantine_delta_required=[
                {
                    "token": "factory",
                    "action": "KEEP_GLOBAL_AND_OWN_VIA_ALIASES",
                    "rationale": (
                        "Do not remove global factory quarantine. Implementation must add aliases "
                        "so the eligible action owns the token and retrieval no longer treats it as foreign."
                    ),
                }
            ],
            volume_risk="LOW",
            privacy_risk="low",
            open_gaps=[
                "SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN (rollout, not freeze blocker)",
                "Date-interval hard cap is an implementation argument-validator decision (recommended 31 days)",
            ],
            evidence=[
                "product_routes.get_factory_status @require_permission(API_DELPI_ACCESS)",
                "GetProductFactoryStatusUseCase.classify_factory_status",
                "route_contract_registry get_product_factory_status composite_analysis",
                "generic nested projection already proven by get_product_structure / production_status",
            ],
        ),
        _cap(
            capability_id="product.structure.exclusivity",
            business_name_ptbr="Exclusividade de matérias-primas na estrutura",
            business_name_en="BOM raw-material exclusivity",
            business_need=(
                "Saber quais MPs da BOM vigente de um PA são exclusivas "
                "(presentes em apenas um PA válido)."
            ),
            domain="product",
            technical_operations=["get_product_structure_exclusivity"],
            primary_operation="get_product_structure_exclusivity",
            owner=product_owner,
            authoritative_source=(
                "GetProductStructureExclusivityUseCase → ProductPlaybookRepository."
                "fetch_structure_with_exclusivity (SG1/SB1)"
            ),
            canonical_use_case="GetProductStructureExclusivityUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS) on get_structure_exclusivity",
            semantic_contract=(
                "Flat leveled BOM rows with exclusive_raw_material flag and summary counts. "
                "Not a recursive tree dump; not a substitute for product.structure.bom."
            ),
            required_inputs=["code"],
            optional_inputs=["max_depth"],
            output_allowlist_candidate=STRUCTURE_EXCLUSIVITY_OUTPUT_FIELDS,
            response_shape="playbook_report",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="READY_FOR_FREEZE",
            primary_blocker=None,
            wave_candidate="WAVE_1",
            retrieval_aliases_ptbr=[
                "exclusividade",
                "matéria-prima exclusiva",
                "mp exclusiva",
                "componentes exclusivos",
                "exclusividade de mp",
            ],
            retrieval_aliases_en=[
                "exclusive raw material",
                "bom exclusivity",
                "exclusive components",
            ],
            pagination="max_items=50; max_depth default 8 cap 8",
            max_depth=8,
            completeness_semantics=(
                "If items truncated by max_items/max_depth, is_complete=false and truncated=true. "
                "summary totals remain backend-computed for the requested depth."
            ),
            business_value="HIGH",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
            live_test_candidate=True,
            freeze_status="FROZEN_FOR_IMPLEMENTATION",
            seeded_decision="PROMOTE",
            volume_risk="MEDIUM",
            input_minimization="Do not expose legacy boolean SIM/NAO toggle.",
            open_gaps=[
                "SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN",
                "Global exclusive-MP catalog is a separate capability (not Wave 1)",
            ],
            evidence=[
                "product_routes.get_structure_exclusivity",
                "fetch_structure_with_exclusivity exclusive_raw_material column",
                "summarize_structure totals",
            ],
            redundant_with=[],
        ),
        _cap(
            capability_id="product.shipping.status",
            business_name_ptbr="Status de expedição do produto",
            business_name_en="Product shipping / final-inspection status",
            business_need=(
                "Saber se o PA já passou pela inspeção final e quanto está liberado para expedição."
            ),
            domain="product",
            technical_operations=["get_product_shipping_status"],
            primary_operation="get_product_shipping_status",
            owner=product_owner,
            authoritative_source=(
                "GetProductShippingStatusUseCase → GetProducedQuantityUseCase.list_detail "
                "(SH6 + SHB inspeção final)"
            ),
            canonical_use_case="GetProductShippingStatusUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS) on get_shipping_status",
            semantic_contract=(
                "Shipping quantities and inspection losses for a product in a bounded date window. "
                "Distinct from production-status (OPs/apontamento) and from factory classified snapshot."
            ),
            required_inputs=["code"],
            optional_inputs=["branch", "reference_date", "start_date", "end_date"],
            output_allowlist_candidate=SHIPPING_STATUS_OUTPUT_FIELDS,
            response_shape="playbook_report",
            projection_mode="nested",
            branch_semantics="optional_consolidated: all | 01 | 02",
            current_status="READY_FOR_FREEZE",
            primary_blocker=None,
            wave_candidate="WAVE_1",
            retrieval_aliases_ptbr=[
                "expedição",
                "status de expedição",
                "liberado para expedição",
                "inspeção final do pa",
                "quantidade expedida",
            ],
            retrieval_aliases_en=[
                "shipping status",
                "final inspection",
                "released to ship",
                "shipped quantity",
            ],
            pagination="max_items=50",
            time_semantics=(
                "Default start=today; end=today. Implementation must bound interval "
                "(recommended max 31 days). Omit legacy date_start/date_end aliases."
            ),
            completeness_semantics=(
                "summary totals are over returned+truncated window; if items truncated, is_complete=false."
            ),
            business_value="HIGH",
            implementation_complexity="LOW",
            runtime_risk="LOW",
            live_test_candidate=True,
            freeze_status="FROZEN_FOR_IMPLEMENTATION",
            seeded_decision="PROMOTE",
            volume_risk="MEDIUM",
            input_minimization="Omit legacy flag and duplicate date_start/date_end query aliases.",
            open_gaps=["SECOND_USER_NEGATIVE_AUTHZ = TEST_NOT_RUN"],
            evidence=[
                "product_routes.get_shipping_status",
                "production_appointments_sql produced detail shipped_quantity/inspection_loss_quantity",
                "openapi_agent_metadata PRODUCT_SHIPPING_STATUS",
            ],
        ),
        _cap(
            capability_id="product.master.detail",
            business_name_ptbr="Ficha cadastral detalhada do produto",
            business_name_en="Product master detail",
            business_need="Same Product Master slice already served by search_products.",
            domain="product",
            technical_operations=["get_product_detail"],
            primary_operation="get_product_detail",
            owner=product_owner,
            authoritative_source="SearchProductsUseCase reused by get_product_detail",
            canonical_use_case="SearchProductsUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Not a distinct DAVI capability.",
            required_inputs=["code"],
            optional_inputs=["view"],
            output_allowlist_candidate=[],
            response_shape="product_snapshot",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="SEMANTICALLY_REDUNDANT",
            primary_blocker="SEMANTICALLY_REDUNDANT",
            wave_candidate=None,
            retrieval_aliases_ptbr=[],
            retrieval_aliases_en=[],
            seeded_decision="REDUNDANT",
            redundant_with=["product.master.search"],
            business_value="LOW",
            implementation_complexity="LOW",
            runtime_risk="LOW",
            evidence=["get_product_detail executes SearchProductsUseCase page_size=1"],
        ),
        _cap(
            capability_id="product.snapshot.summary",
            business_name_ptbr="Resumo leve do produto",
            business_name_en="Product lightweight summary",
            business_need=(
                "Composite cadastro + amostra de estoque + preços. Sem preços, o restante "
                "é reduntante com search+stock; com preços, pertence à onda econômica."
            ),
            domain="product",
            technical_operations=["get_product_summary"],
            primary_operation="get_product_summary",
            owner=product_owner,
            authoritative_source="SearchProducts + ListProductStock + GetProductPricing composed in route",
            canonical_use_case="get_product_summary (route composition)",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Do not promote raw composite; prices remain out until Wave 2.",
            required_inputs=["code"],
            optional_inputs=[],
            output_allowlist_candidate=[],
            response_shape="product_snapshot",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="NEEDS_SEMANTIC_CONTRACT",
            primary_blocker="SEMANTICALLY_REDUNDANT_WITHOUT_PRICES_OR_NEEDS_MODEL_SAFE_PROJECTION_FOR_PRICES",
            wave_candidate=None,
            retrieval_aliases_ptbr=["resumo do produto", "ficha rápida"],
            retrieval_aliases_en=["product summary"],
            seeded_decision="DEFER",
            redundant_with=["product.master.search", "product.stock.availability", "product.commercial.pricing"],
            business_value="MEDIUM",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
            quarantine_delta_required=[
                {"token": "resuma", "action": "KEEP", "rationale": "Avoid unconstrained summarize intents."}
            ],
        ),
        _cap(
            capability_id="product.commercial.pricing",
            business_name_ptbr="Preços comerciais do produto",
            business_name_en="Product commercial pricing",
            business_need="Consultar tabela de preço de venda de um produto.",
            domain="product",
            technical_operations=["get_product_pricing"],
            primary_operation="get_product_pricing",
            owner=product_owner,
            authoritative_source="GetProductPricingUseCase → DA1/DA0 + SB1",
            canonical_use_case="GetProductPricingUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Sale price tables; minimize discounts/max_price unless needed.",
            required_inputs=["code"],
            optional_inputs=[],
            output_allowlist_candidate=[
                "product.code",
                "product.description",
                "product.unit",
                "prices[].table_code",
                "prices[].table_description",
                "prices[].sale_price",
                "prices[].currency",
                "prices[].valid_from",
                "prices[].active",
            ],
            response_shape="scalar",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_2",
            retrieval_aliases_ptbr=["preço", "tabela de preço", "preço de venda"],
            retrieval_aliases_en=["price", "pricing", "sale price"],
            seeded_decision="DEFER",
            business_value="HIGH",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
            privacy_risk="medium",
            quarantine_delta_required=[
                {"token": "preco", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "price", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "pricing", "action": "NARROW_OR_OWN_VIA_ALIASES"},
            ],
        ),
        _cap(
            capability_id="product.purchase.price_history",
            business_name_ptbr="Histórico de preço de compra da MP",
            business_name_en="Raw-material purchase price history",
            business_need="Ver evolução do preço de compra de uma matéria-prima.",
            domain="product",
            technical_operations=["get_product_purchase_price_history"],
            primary_operation="get_product_purchase_price_history",
            owner=product_owner,
            authoritative_source="GetProductPurchasePriceHistoryUseCase → SD1 NFs",
            canonical_use_case="GetProductPurchasePriceHistoryUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Time-bounded NF purchase prices with variation; history_limit default 24 cap 50 for DAVI.",
            required_inputs=["code"],
            optional_inputs=["branch", "date_start", "date_end", "history_limit"],
            output_allowlist_candidate=[],
            response_shape="playbook_report",
            projection_mode="nested",
            branch_semantics="optional_consolidated: all | 01 | 02",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_2",
            retrieval_aliases_ptbr=["histórico de preço de compra", "preço de compra da mp"],
            retrieval_aliases_en=["purchase price history"],
            seeded_decision="DEFER",
            time_semantics="Bounded date range required; backend history_limit default 24 max 200 — DAVI must cap ≤50.",
            business_value="HIGH",
            implementation_complexity="MEDIUM",
            runtime_risk="MEDIUM",
            quarantine_delta_required=[
                {"token": "preco", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "price", "action": "NARROW_OR_OWN_VIA_ALIASES"},
            ],
        ),
        _cap(
            capability_id="product.raw_material.price_intelligence",
            business_name_ptbr="Inteligência de preço de matéria-prima",
            business_name_en="Raw-material price intelligence",
            business_need="Visão consolidada de última compra, variação e status de preço de MP.",
            domain="product",
            technical_operations=["get_product_raw_material_price_intelligence"],
            primary_operation="get_product_raw_material_price_intelligence",
            owner=product_owner,
            authoritative_source="GetProductRawMaterialPriceIntelligenceUseCase",
            canonical_use_case="GetProductRawMaterialPriceIntelligenceUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Composite economic intelligence; needs explicit nested allowlist and date bounds.",
            required_inputs=["code"],
            optional_inputs=["branch", "date_start", "date_end"],
            output_allowlist_candidate=[],
            response_shape="composite_analysis",
            projection_mode="nested",
            branch_semantics="optional_consolidated: all | 01 | 02",
            current_status="NEEDS_NESTED_PROJECTION_SUPPORT",
            primary_blocker="NEEDS_NESTED_PROJECTION_SUPPORT",
            wave_candidate="WAVE_2",
            retrieval_aliases_ptbr=["análise de preço de mp", "inteligência de preço"],
            retrieval_aliases_en=["raw material price intelligence"],
            seeded_decision="DEFER",
            business_value="HIGH",
            implementation_complexity="HIGH",
            runtime_risk="HIGH",
            quarantine_delta_required=[
                {"token": "preco", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "custo", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "cost", "action": "NARROW_OR_OWN_VIA_ALIASES"},
            ],
        ),
        _cap(
            capability_id="product.cost.impact_simulation",
            business_name_ptbr="Simulação de impacto de custo do PA",
            business_name_en="Finished-product cost impact simulation",
            business_need="Identificar MPs que mais impactam o custo de 1 PA e simular reajuste.",
            domain="product",
            technical_operations=["get_product_cost_impact_simulation"],
            primary_operation="get_product_cost_impact_simulation",
            owner=product_owner,
            authoritative_source="GetProductCostImpactSimulationUseCase → SG1 + cost/last purchase",
            canonical_use_case="GetProductCostImpactSimulationUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="PA-only simulation; derived fields need provenance; cap top_n and max_depth.",
            required_inputs=["code"],
            optional_inputs=["max_depth", "price_source", "adjustment_percent", "top_n"],
            output_allowlist_candidate=[],
            response_shape="composite_analysis",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="NEEDS_NESTED_PROJECTION_SUPPORT",
            primary_blocker="NEEDS_NESTED_PROJECTION_SUPPORT",
            wave_candidate="WAVE_2",
            retrieval_aliases_ptbr=["impacto de custo", "simulação de custo", "pareto de mp"],
            retrieval_aliases_en=["cost impact", "cost simulation"],
            seeded_decision="DEFER",
            business_value="HIGH",
            implementation_complexity="HIGH",
            runtime_risk="HIGH",
            READ_PREPARE_ACT="READ",
            quarantine_delta_required=[
                {"token": "custo", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "cost", "action": "NARROW_OR_OWN_VIA_ALIASES"},
            ],
            open_gaps=[
                "Confirm simulation is side-effect free (READ/PREPARE, not ACT) — source execute() is compute-only PROVEN",
            ],
        ),
        _cap(
            capability_id="product.where_used",
            business_name_ptbr="Onde o produto é usado",
            business_name_en="Product where-used / parents",
            business_need="Listar produtos pai que consomem o código (BOM reversa).",
            domain="product",
            technical_operations=["get_product_parents"],
            primary_operation="get_product_parents",
            owner=product_owner,
            authoritative_source="Product parents repository (SG1 reverse)",
            canonical_use_case="ListProductParentsUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Reverse BOM; nested hierarchy requires path allowlist and depth cap.",
            required_inputs=["code"],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="hierarchy",
            projection_mode="nested",
            branch_semantics="not_applicable",
            current_status="NEEDS_NESTED_PROJECTION_SUPPORT",
            primary_blocker="NEEDS_NESTED_PROJECTION_SUPPORT",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["onde é usado", "produtos pai", "where used"],
            retrieval_aliases_en=["where used", "parent products"],
            business_value="MEDIUM",
            implementation_complexity="MEDIUM",
        ),
        _cap(
            capability_id="product.routing.guide",
            business_name_ptbr="Roteiro de produção do produto",
            business_name_en="Product routing / operations guide",
            business_need="Consultar sequência operacional e centros de trabalho do item.",
            domain="product",
            technical_operations=["get_product_guide"],
            primary_operation="get_product_guide",
            owner=product_owner,
            authoritative_source="Product guide repository",
            canonical_use_case="ListProductGuideUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Paged routing steps; needs field allowlist.",
            required_inputs=["code"],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="not_applicable",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["roteiro", "roteiro de produção", "operações do produto"],
            retrieval_aliases_en=["routing", "operation guide"],
            business_value="MEDIUM",
            implementation_complexity="LOW",
        ),
        _cap(
            capability_id="product.quality.inspection",
            business_name_ptbr="Inspeção de qualidade do produto",
            business_name_en="Product quality inspection",
            business_need="Consultar dados de inspeção QP do item — sem anexos.",
            domain="product",
            technical_operations=["get_product_inspection"],
            primary_operation="get_product_inspection",
            owner=product_owner,
            authoritative_source="QP6/QP7/QP8 via product inspection repository",
            canonical_use_case="ListProductInspectionUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS)",
            semantic_contract="Inspection metadata; exclude free-text evidence/attachments.",
            required_inputs=["code"],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="not_applicable",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["inspeção do produto", "qp do produto"],
            retrieval_aliases_en=["product inspection"],
            business_value="MEDIUM",
            privacy_risk="medium",
        ),
        _cap(
            capability_id="product.raw_material.set_shortages",
            business_name_ptbr="Ruptura de MP no conjunto de OPs do PA",
            business_name_en="Raw-material set shortages for finished-product orders",
            business_need="Saber quais OPs abertas do PA ficarão sem matéria-prima no conjunto.",
            domain="product",
            technical_operations=["get_product_raw_material_set_shortages"],
            primary_operation="get_product_raw_material_set_shortages",
            owner=product_owner,
            authoritative_source="GetProductRawMaterialSetShortagesUseCase",
            canonical_use_case="GetProductRawMaterialSetShortagesUseCase",
            backend_authz="PROVEN: @require_permission(API_DELPI_ACCESS) + required concrete branch",
            semantic_contract="Composite shortage analysis; nested + high volume; branch required concrete.",
            required_inputs=["code", "branch"],
            optional_inputs=["max_depth"],
            output_allowlist_candidate=[],
            response_shape="composite_analysis",
            projection_mode="nested",
            branch_semantics="required_concrete: 01 | 02",
            current_status="NEEDS_NESTED_PROJECTION_SUPPORT",
            primary_blocker="NEEDS_NESTED_PROJECTION_SUPPORT",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["ruptura de mp", "falta de matéria-prima na op"],
            retrieval_aliases_en=["raw material shortage", "set shortage"],
            business_value="HIGH",
            implementation_complexity="HIGH",
            runtime_risk="HIGH",
            volume_risk="HIGH",
        ),
        _cap(
            capability_id="supplies.purchase_requests.status",
            business_name_ptbr="Status de solicitações de compra",
            business_name_en="Purchase request status",
            business_need="Entender cobertura e linhas de solicitações de compra abertas.",
            domain="supplies",
            technical_operations=[
                "get_supplies_purchase_requests_open_coverage",
                "get_supplies_purchase_request_lines",
            ],
            primary_operation="get_supplies_purchase_requests_open_coverage",
            owner="api-delpi Supplies bounded context",
            authoritative_source="Supplies purchase-request use cases / TOTVS SC1",
            canonical_use_case="TO_INVENTORY — route/use-case names in supplies routers",
            backend_authz="TO_INVENTORY",
            semantic_contract="One semantic capability over coverage + lines; not two Agent capabilities.",
            required_inputs=[],
            optional_inputs=["branch", "page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=[
                "solicitação de compra",
                "requisição de compra",
                "sc aberta",
            ],
            retrieval_aliases_en=["purchase request", "open purchase requests"],
            business_value="HIGH",
            owner_evidence="PROVEN path prefix /supplies",
            source_evidence="TO_INVENTORY",
            implementation_complexity="MEDIUM",
        ),
        _cap(
            capability_id="supplies.purchase_order.otd",
            business_name_ptbr="OTD de pedidos de compra",
            business_name_en="Purchase-order on-time delivery",
            business_need="Acompanhar pontualidade de pedidos de compra.",
            domain="supplies",
            technical_operations=[
                "get_supplies_purchase_order_otd",
                "get_supplies_purchase_order_otd_panel",
                "get_supplies_purchase_order_otd_series",
                "get_supplies_otd",
            ],
            primary_operation="get_supplies_purchase_order_otd",
            owner="api-delpi Supplies bounded context",
            authoritative_source="Supplies OTD use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Prefer summary/panel over line-level fan-out as first Supplies OTD capability.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["otd de compras", "pontualidade de pedido de compra"],
            retrieval_aliases_en=["purchase order otd", "supplier otd"],
            business_value="HIGH",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="supplies.stock.balances",
            business_name_ptbr="Saldos de estoque de suprimentos",
            business_name_en="Supplies stock balances",
            business_need="Visão agregada de saldos de estoque da empresa — distinta do estoque de um código.",
            domain="supplies",
            technical_operations=[
                "get_supplies_stock_balances_summary",
                "get_supplies_stock_balances_items",
                "get_supplies_stock_value",
            ],
            primary_operation="get_supplies_stock_balances_summary",
            owner="api-delpi Supplies bounded context",
            authoritative_source="Supplies stock-balances use cases / SB2",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Company/warehouse balances; do not duplicate product.stock.availability.",
            required_inputs=[],
            optional_inputs=["branch", "page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["saldo de estoque da empresa", "posição de estoque suprimentos"],
            retrieval_aliases_en=["stock balances", "inventory value"],
            business_value="HIGH",
            redundant_with=[],
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
            volume_risk="HIGH",
        ),
        _cap(
            capability_id="supplies.safety_stock.summary",
            business_name_ptbr="Resumo de estoque de segurança",
            business_name_en="Safety-stock summary",
            business_need="Acompanhar itens abaixo do estoque de segurança.",
            domain="supplies",
            technical_operations=[
                "get_supplies_safety_stock_summary",
                "get_supplies_safety_stock_items",
            ],
            primary_operation="get_supplies_safety_stock_summary",
            owner="api-delpi Supplies bounded context",
            authoritative_source="Safety-stock use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Prefer summary first; item details later. Supplier price history is Wave 2/economic.",
            required_inputs=[],
            optional_inputs=["branch"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["estoque de segurança", "abaixo do estoque de segurança"],
            retrieval_aliases_en=["safety stock"],
            business_value="HIGH",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="production.oee",
            business_name_ptbr="OEE de produção",
            business_name_en="Production OEE",
            business_need="Consultar efetividade global de equipamentos em um período.",
            domain="production",
            technical_operations=[
                "get_production_oee",
                "get_production_oee_series",
                "get_overall_equipment_effectiveness_pct",
            ],
            primary_operation="get_production_oee",
            owner="api-delpi Production bounded context",
            authoritative_source="Production OEE use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Aggregated OEE; exclude appointment-by-id until needed.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["oee", "eficiência de equipamento"],
            retrieval_aliases_en=["oee", "overall equipment effectiveness"],
            business_value="HIGH",
            time_semantics="Bounded period required.",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="production.otd",
            business_name_ptbr="OTD de produção",
            business_name_en="Production on-time delivery",
            business_need="Consultar pontualidade de entrega de produção.",
            domain="production",
            technical_operations=["get_on_time_delivery_pct"],
            primary_operation="get_on_time_delivery_pct",
            owner="api-delpi Production bounded context",
            authoritative_source="Production OTD KPI use case",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="KPI percentage; distinct from commercial sales-order OTD.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["otd de produção", "pontualidade de produção"],
            retrieval_aliases_en=["production otd"],
            business_value="HIGH",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="production.machine_load",
            business_name_ptbr="Carga de máquinas",
            business_name_en="Machine / work-center load",
            business_need="Ver carga de trabalho por centro/recurso.",
            domain="production",
            technical_operations=[
                "get_production_machine_load_work_centers",
                "get_production_machine_load_operations",
            ],
            primary_operation="get_production_machine_load_work_centers",
            owner="api-delpi Production bounded context",
            authoritative_source="Machine-load use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Prefer work-center aggregation over operation-level dump.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["carga de máquina", "carga de centro de trabalho"],
            retrieval_aliases_en=["machine load", "work center load"],
            business_value="MEDIUM",
            volume_risk="HIGH",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="production.appointments.summary",
            business_name_ptbr="Resumo de apontamentos de produção",
            business_name_en="Production appointments summary",
            business_need="Ver totais de apontamento em um período.",
            domain="production",
            technical_operations=[
                "get_production_appointments_summary",
                "get_production_appointments_produced_totals",
            ],
            primary_operation="get_production_appointments_summary",
            owner="api-delpi Production bounded context",
            authoritative_source="Production appointments use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Aggregates only; series/detail later. Distinct from product.shipping.status.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_3",
            retrieval_aliases_ptbr=["apontamentos", "resumo de apontamento"],
            retrieval_aliases_en=["production appointments", "produced totals"],
            business_value="MEDIUM",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="commercial.rol.summary",
            business_name_ptbr="ROL comercial resumido",
            business_name_en="Commercial ROL summary",
            business_need="Consultar receita operacional líquida agregada.",
            domain="commercial",
            technical_operations=[
                "get_commercial_rol_summary",
                "get_commercial_rol_series",
                "get_commercial_rol_by_branch",
            ],
            primary_operation="get_commercial_rol_summary",
            owner="api-delpi Commercial bounded context",
            authoritative_source="Commercial ROL use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Aggregated ROL; defer by-customer/by-product until projection exists.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["rol", "receita operacional líquida"],
            retrieval_aliases_en=["rol", "net operating revenue"],
            business_value="HIGH",
            privacy_risk="medium",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="commercial.sales_order.otd",
            business_name_ptbr="OTD de pedidos de venda",
            business_name_en="Sales-order on-time delivery",
            business_need="Acompanhar pontualidade de pedidos de venda.",
            domain="commercial",
            technical_operations=[
                "get_sales_order_otd",
                "get_sales_order_otd_summary",
                "get_sales_order_otd_panel",
            ],
            primary_operation="get_sales_order_otd_summary",
            owner="api-delpi Commercial bounded context",
            authoritative_source="Sales-order OTD use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Prefer summary/panel; line-detail is a later sibling.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["otd de vendas", "pontualidade de pedido de venda"],
            retrieval_aliases_en=["sales order otd"],
            business_value="HIGH",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="commercial.conversion.rate",
            business_name_ptbr="Taxa de conversão comercial",
            business_name_en="Sales conversion rate",
            business_need="Consultar conversão de propostas/pedidos.",
            domain="commercial",
            technical_operations=[
                "get_sales_conversion_rate",
                "get_sales_conversion_rate_series",
            ],
            primary_operation="get_sales_conversion_rate",
            owner="api-delpi Commercial bounded context",
            authoritative_source="Sales conversion use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="KPI + optional series; bounded dates.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["taxa de conversão", "conversão de vendas"],
            retrieval_aliases_en=["conversion rate"],
            business_value="MEDIUM",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="commercial.proposals.status",
            business_name_ptbr="Status de propostas comerciais",
            business_name_en="Commercial proposal status",
            business_need="Listar/consultar propostas — sem histórico de eventos completo na primeira versão.",
            domain="commercial",
            technical_operations=[
                "list_commercial_proposals",
                "get_commercial_proposal",
                "list_propostas_comerciais",
                "get_proposta_comercial",
            ],
            primary_operation="list_commercial_proposals",
            owner="api-delpi Commercial bounded context",
            authoritative_source="Commercial proposals use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="List + get as one capability; PT path /propostas-comerciais is the same slice, not a second capability. History events and PDF remain out.",
            required_inputs=[],
            optional_inputs=["page", "page_size"],
            output_allowlist_candidate=[],
            response_shape="paged_list",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["proposta comercial", "propostas"],
            retrieval_aliases_en=["commercial proposal"],
            business_value="MEDIUM",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="quality.nonconformity.summary",
            business_name_ptbr="Resumo de não conformidades",
            business_name_en="Nonconformity summary",
            business_need="Acompanhar série/resumo de NCs — sem evidências em anexo ou texto livre.",
            domain="quality",
            technical_operations=["get_nonconformity_series", "get_nonconformity_streak"],
            primary_operation="get_nonconformity_series",
            owner="api-delpi Quality bounded context",
            authoritative_source="Quality NC series use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Aggregates only. Attachments/export remain STREAM_BINARY_OUT_OF_SCOPE.",
            required_inputs=[],
            optional_inputs=["start_date", "end_date", "branch"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["não conformidade", "nc", "resumo de nc"],
            retrieval_aliases_en=["nonconformity", "nc summary"],
            business_value="HIGH",
            privacy_risk="medium",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="inspection.inbound.summary",
            business_name_ptbr="Resumo de inspeção de entrada",
            business_name_en="Inbound inspection summary",
            business_need="Ver pendências e resumo de inspeção de entrada.",
            domain="inspection",
            technical_operations=[
                "get_inspecoes_entrada_resumo",
                "get_inspecoes_entrada_pendentes",
            ],
            primary_operation="get_inspecoes_entrada_resumo",
            owner="api-delpi Inspection bounded context",
            authoritative_source="Inspeções de entrada use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Summary + pending counts; detail/history later. Exclude personal inspector ranking initially.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["inspeção de entrada", "pendências de inspeção de entrada"],
            retrieval_aliases_en=["inbound inspection"],
            business_value="HIGH",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="inspection.process.summary",
            business_name_ptbr="Resumo de inspeção de processo",
            business_name_en="Process inspection summary",
            business_need="Ver resumo de inspeção de processo.",
            domain="inspection",
            technical_operations=["get_inspecoes_processo_resumo"],
            primary_operation="get_inspecoes_processo_resumo",
            owner="api-delpi Inspection bounded context",
            authoritative_source="Inspeções de processo use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Summary only; ranking-by-person deferred for privacy.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["inspeção de processo"],
            retrieval_aliases_en=["process inspection"],
            business_value="MEDIUM",
            privacy_risk="medium",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="quality.audit_5s.summary",
            business_name_ptbr="Resumo de auditoria 5S",
            business_name_en="5S audit summary",
            business_need="Acompanhar resumo de auditorias 5S — sem anexos.",
            domain="quality",
            technical_operations=["get_audit_5s_summary", "get_audit_5s_summary_series"],
            primary_operation="get_audit_5s_summary",
            owner="api-delpi Quality bounded context",
            authoritative_source="Audit 5S use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Aggregates; attachments remain binary/out of scope.",
            required_inputs=[],
            optional_inputs=["branch", "start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["auditoria 5s", "resumo 5s"],
            retrieval_aliases_en=["5s audit"],
            business_value="MEDIUM",
            privacy_risk="medium",
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="engineering.lmp.dashboard",
            business_name_ptbr="Painel de LMPs",
            business_name_en="LMP engineering dashboard",
            business_need="Acompanhar resumo de Lista de Materiais de Projeto / LMP.",
            domain="engineering",
            technical_operations=[
                "get_lmps_dashboard_summary",
                "list_lmps_dashboard",
            ],
            primary_operation="get_lmps_dashboard_summary",
            owner="api-delpi Engineering bounded context",
            authoritative_source="LMP dashboard use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Dashboard summary; NC details/privacy later.",
            required_inputs=[],
            optional_inputs=[],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="not_applicable",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_4",
            retrieval_aliases_ptbr=["lmp", "painel de lmp"],
            retrieval_aliases_en=["lmp dashboard"],
            business_value="MEDIUM",
            owner_evidence="PROVEN path prefix /engineering/lmps",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="financial.overdue.summary",
            business_name_ptbr="Resumo de inadimplência",
            business_name_en="Overdue receivables summary",
            business_need="Ver posição agregada de inadimplência — não a listagem de títulos.",
            domain="financial",
            technical_operations=[
                "get_financeiro_inadimplencia_resumo",
                "get_financeiro_inadimplencia_faixas_atraso",
                "get_financeiro_inadimplencia_mensal",
            ],
            primary_operation="get_financeiro_inadimplencia_resumo",
            owner="api-delpi Financial bounded context",
            authoritative_source="Inadimplência use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Aggregates only. Titulos/clientes lists are a later minimized sibling.",
            required_inputs=[],
            optional_inputs=["start_date", "end_date"],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_MODEL_SAFE_PROJECTION",
            primary_blocker="NEEDS_MODEL_SAFE_PROJECTION",
            wave_candidate="WAVE_5",
            retrieval_aliases_ptbr=["inadimplência", "resumo de inadimplência"],
            retrieval_aliases_en=["overdue summary", "receivables aging"],
            business_value="HIGH",
            privacy_risk="high",
            quarantine_delta_required=[
                {"token": "financeiro", "action": "NARROW_OR_OWN_VIA_ALIASES"},
                {"token": "finance", "action": "NARROW_OR_OWN_VIA_ALIASES"},
            ],
            owner_evidence="PROVEN path prefix",
            source_evidence="TO_INVENTORY",
        ),
        _cap(
            capability_id="hr.workforce.snapshot",
            business_name_ptbr="Snapshot de RH",
            business_name_en="HR snapshot",
            business_need="TO_INVENTORY — route exists (get_hr_snapshot) but personal data risk is high.",
            domain="hr",
            technical_operations=["get_hr_snapshot", "get_hr_active_pdi_count"],
            primary_operation="get_hr_snapshot",
            owner="api-delpi HR bounded context",
            authoritative_source="HR snapshot use cases",
            canonical_use_case="TO_INVENTORY",
            backend_authz="TO_INVENTORY",
            semantic_contract="Out of normal DAVI promotion until privacy review.",
            required_inputs=[],
            optional_inputs=[],
            output_allowlist_candidate=[],
            response_shape="scalar",
            projection_mode="flat",
            branch_semantics="TO_INVENTORY",
            current_status="NEEDS_PRIVACY_REVIEW",
            primary_blocker="NEEDS_PRIVACY_REVIEW",
            wave_candidate=None,
            retrieval_aliases_ptbr=[],
            retrieval_aliases_en=[],
            business_value="TO_INVENTORY",
            privacy_risk="high",
            owner_evidence="PROVEN path prefix /hr",
            source_evidence="TO_INVENTORY",
        ),
    ]


# Fill output allowlists that were left empty for currently eligible nested ops from runtime allowlist.
def _hydrate_current_allowlists(caps: list[dict[str, Any]]) -> None:
    allow = load_external_read_allowlist()
    by_oid = {
        str(item.get("operationId")): item
        for item in (allow.get("operations") or [])
        if isinstance(item, dict)
    }
    for cap in caps:
        if cap["output_allowlist_candidate"]:
            continue
        entry = by_oid.get(cap["primary_operation"])
        if not entry:
            continue
        fields = [str(f) for f in (entry.get("approvedResponseFields") or []) if f]
        if fields:
            cap["output_allowlist_candidate"] = fields
            cap["output_business_fields"] = fields


FACTORY_STATUS_OUTPUT_FIELDS = [
    "product.product_code",
    "product.description",
    "product.product_type",
    "product.unit",
    "product.group_code",
    "reference_date",
    "start_date",
    "factory_status",
    "indicators.total_intermediates",
    "indicators.total_raw_materials",
    "indicators.total_exclusive_raw_materials",
    "indicators.total_raw_materials_without_stock_for_one_pa",
    "indicators.max_pa_producible_from_stock",
    "indicators.limiting_raw_material_code",
    "indicators.total_pa_orders",
    "indicators.total_pi_orders",
    "indicators.total_pa_reported_quantity",
    "indicators.total_pi_reported_quantity",
    "indicators.total_pa_shipped_quantity",
    "indicators.total_inspection_loss_quantity",
    "structure.summary.total_components",
    "structure.summary.total_intermediates",
    "structure.summary.total_raw_materials",
    "structure.summary.total_exclusive_raw_materials",
    "raw_material_stock.summary.total_raw_materials",
    "raw_material_stock.summary.total_without_stock_for_one_pa",
    "raw_material_stock.summary.max_pa_producible_from_stock",
    "raw_material_stock.summary.limiting_raw_material_code",
    "production.summary.total_pa_orders",
    "production.summary.total_pi_orders",
    "production.summary.pa_production_started",
    "production.summary.pi_production_started",
    "shipping.summary.total_shipped_quantity",
    "shipping.summary.total_inspection_loss_quantity",
    "shipping.summary.total_reports",
]

STRUCTURE_EXCLUSIVITY_OUTPUT_FIELDS = [
    "product.product_code",
    "product.description",
    "product.product_type",
    "product.unit",
    "items[].level",
    "items[].parent_code",
    "items[].parent_description",
    "items[].component_code",
    "items[].component_description",
    "items[].component_type",
    "items[].component_unit",
    "items[].quantity_per",
    "items[].accumulated_quantity",
    "items[].exclusive_raw_material",
    "items[].total_valid_finished_products_using_mp",
    "summary.total_components",
    "summary.total_intermediates",
    "summary.total_raw_materials",
    "summary.total_exclusive_raw_materials",
]

SHIPPING_STATUS_OUTPUT_FIELDS = [
    "product.product_code",
    "product.description",
    "product.product_type",
    "product.unit",
    "start_date",
    "items[].branch",
    "items[].product_code",
    "items[].production_order",
    "items[].work_center",
    "items[].shipped_quantity",
    "items[].inspection_loss_quantity",
    "items[].total_reports",
    "summary.total_shipped_quantity",
    "summary.total_inspection_loss_quantity",
    "summary.total_reports",
]


def redundancy_groups() -> list[dict[str, Any]]:
    return [
        {
            "group": "RG-PRODUCT-MASTER",
            "operations": ["search_products", "get_product_detail"],
            "semantic_capability": "product.master.search",
            "decision": "Keep search_products as the only Product Master DAVI capability. get_product_detail is SEMANTICALLY_REDUNDANT.",
        },
        {
            "group": "RG-PRODUCT-SUMMARY-COMPOSITE",
            "operations": [
                "get_product_summary",
                "search_products",
                "get_product_stock",
                "get_product_pricing",
            ],
            "semantic_capability": "product.snapshot.summary",
            "decision": "DEFER summary. Without prices it duplicates search+stock; with prices it belongs to Wave 2.",
        },
        {
            "group": "RG-PRODUCT-STRUCTURE",
            "operations": [
                "get_product_structure",
                "get_product_structure_excel",
                "get_product_structure_exclusivity",
                "list_exclusive_raw_materials_catalog",
            ],
            "semantic_capability": "product.structure.bom + product.structure.exclusivity",
            "decision": "BOM and exclusivity are distinct. Excel export remains STREAM_BINARY_OUT_OF_SCOPE. Global exclusive catalog is a later sibling, not Wave 1.",
        },
        {
            "group": "RG-PRODUCT-FACTORY-SLICES",
            "operations": [
                "get_product_factory_status",
                "get_product_production_status",
                "get_product_shipping_status",
                "get_product_structure",
            ],
            "semantic_capability": "product.factory.status (classified snapshot)",
            "decision": "Factory capability exposes summaries/indicators only. Do not dump sibling item arrays.",
        },
        {
            "group": "RG-PRODUCT-ECONOMIC",
            "operations": [
                "get_product_pricing",
                "get_product_purchase_price_history",
                "get_product_raw_material_price_intelligence",
                "get_product_cost_impact_simulation",
                "get_product_last_purchase",
            ],
            "semantic_capability": "Wave 2 economic cluster",
            "decision": "DEFER as a governed economic wave. Not confidentiality-blocked merely because monetary.",
        },
        {
            "group": "RG-STOCK-GRAIN",
            "operations": [
                "get_product_stock",
                "get_supplies_stock_balances_summary",
                "get_supplies_stock_balances_items",
                "get_supplies_stock_value",
            ],
            "semantic_capability": "product.stock.availability vs supplies.stock.balances",
            "decision": "Different grain (one code vs company/warehouse). Keep separate capabilities.",
        },
        {
            "group": "RG-OTD-SURFACES",
            "operations": [
                "get_on_time_delivery_pct",
                "get_supplies_purchase_order_otd",
                "get_sales_order_otd",
            ],
            "semantic_capability": "domain-specific OTD capabilities",
            "decision": "Do not merge production/supplies/commercial OTD into one alias set.",
        },
        {
            "group": "RG-COMMERCIAL-PROPOSALS-DUAL-PATH",
            "operations": [
                "list_commercial_proposals",
                "get_commercial_proposal",
                "list_propostas_comerciais",
                "get_proposta_comercial",
            ],
            "semantic_capability": "commercial.proposals.status",
            "decision": "English and Portuguese technical routes are one commercial proposal capability. PDF export remains binary/out of scope.",
        },
        {
            "group": "RG-PURCHASE-LANGUAGE",
            "operations": [
                "get_product_purchases",
                "get_supplies_purchase_request_lines",
                "get_supplies_purchase_requests_open_coverage",
            ],
            "semantic_capability": "product.purchasing.history vs supplies.purchase_requests.status",
            "decision": "Disambiguate aliases: compras do produto vs solicitação/requisição de compra.",
        },
    ]


def wave_plan() -> dict[str, Any]:
    return {
        "WAVE_1": {
            "theme": "Operational Product Intelligence (classified factory snapshot + MP exclusivity + shipping)",
            "capability_ids": [
                "product.factory.status",
                "product.structure.exclusivity",
                "product.shipping.status",
            ],
            "count": 3,
            "reason": (
                "Evidence-driven alternative to seeding product.snapshot.summary. These three expand "
                "distinct operational questions, reuse generic nested projection, keep MCP tools=3, "
                "and avoid promoting prices or redundant master/stock slices. Size 3 is enough to "
                "validate composite summaries, playbook_report lists, and sibling disambiguation."
            ),
        },
        "WAVE_2": {
            "theme": "Product Economic Intelligence",
            "capability_ids": [
                "product.commercial.pricing",
                "product.purchase.price_history",
                "product.raw_material.price_intelligence",
                "product.cost.impact_simulation",
            ],
            "reason": "High business value and proven backend AuthZ; blocked only by model-safe nested/flat projection + quarantine narrowing for price/cost tokens.",
        },
        "WAVE_3": {
            "theme": "Supplies / Production Operational Intelligence",
            "capability_ids": [
                "supplies.purchase_requests.status",
                "supplies.purchase_order.otd",
                "supplies.stock.balances",
                "supplies.safety_stock.summary",
                "production.oee",
                "production.otd",
                "production.machine_load",
                "production.appointments.summary",
                "product.raw_material.set_shortages",
                "product.routing.guide",
                "product.where_used",
            ],
            "reason": "Canonical routes exist; owner/AuthZ still TO_INVENTORY for several Supplies/Production handlers; projection and volume bounds required.",
        },
        "WAVE_4": {
            "theme": "Commercial / Quality / Inspection / Engineering",
            "capability_ids": [
                "commercial.rol.summary",
                "commercial.sales_order.otd",
                "commercial.conversion.rate",
                "commercial.proposals.status",
                "quality.nonconformity.summary",
                "inspection.inbound.summary",
                "inspection.process.summary",
                "quality.audit_5s.summary",
                "engineering.lmp.dashboard",
                "product.quality.inspection",
            ],
            "reason": "Aggregated business questions are evident from route semantics; privacy/attachment exclusions remain.",
        },
        "WAVE_5": {
            "theme": "Financial aggregates (not title-level PII dumps)",
            "capability_ids": ["financial.overdue.summary"],
            "reason": "Financial READ is not forbidden; start from aggregates. HR remains privacy-blocked.",
        },
    }


def _assert_no_wildcards(fields: list[str]) -> None:
    for field in fields:
        if "*" in field or field.endswith(".") or field in {".", "root", "items[]"}:
            raise ValueError(f"Wildcard or unbounded projection path forbidden: {field}")


def freeze_records(caps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    frozen = [c for c in caps if c.get("freeze_status") == "FROZEN_FOR_IMPLEMENTATION"]
    required = (
        "business_need",
        "owner",
        "authoritative_source",
        "canonical_use_case",
        "backend_authz",
        "semantic_contract",
        "required_inputs",
        "output_allowlist_candidate",
        "identity_model",
        "retrieval_aliases_ptbr",
        "projection_mode",
        "branch_semantics",
    )
    out: list[dict[str, Any]] = []
    for cap in frozen:
        missing = [k for k in required if not cap.get(k)]
        if missing:
            raise ValueError(f"{cap['capability_id']} missing freeze fields: {missing}")
        if not str(cap.get("backend_authz") or "").startswith("PROVEN"):
            raise ValueError(f"{cap['capability_id']} backend_authz is not PROVEN")
        _assert_no_wildcards(cap["output_allowlist_candidate"])
        if cap.get("owner_evidence") != "PROVEN":
            raise ValueError(f"{cap['capability_id']} owner not PROVEN")
        out.append(cap)
    return out


def operation_to_capability(caps: list[dict[str, Any]]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for cap in caps:
        for oid in cap["technical_operations"]:
            mapping.setdefault(oid, cap["capability_id"])
    return mapping


def _counts(actions: list[TechnicalAction]) -> dict[str, Any]:
    methods = Counter(a.method for a in actions)
    statuses = Counter(a.davi_status for a in actions)
    gets = [a for a in actions if a.method == "GET"]
    domains = Counter(infer_domain(a.path) for a in gets)
    eligible = [a for a in actions if is_dynamically_executable(a.davi_status)]
    return {
        "TOTAL_OPERATIONS": len(actions),
        "TOTAL_GET": methods.get("GET", 0),
        "TOTAL_WRITE_VERBS": sum(
            methods.get(m, 0) for m in ("POST", "PUT", "PATCH", "DELETE")
        ),
        "DAVI_ELIGIBLE_READ": len(eligible),
        "ELIGIBLE_OPERATION_IDS": sorted(a.operation_id for a in eligible),
        "STATUS_COUNTS": dict(sorted(statuses.items())),
        "GET_DOMAIN_COUNTS": dict(sorted(domains.items())),
        "ADMIN": statuses.get("ADMIN_OUT_OF_SCOPE", 0),
        "SQL": statuses.get("GENERIC_SQL_FORBIDDEN", 0),
        "BINARY": statuses.get("STREAM_BINARY_OUT_OF_SCOPE", 0),
        "WRITE_OUT_OF_SCOPE": statuses.get("WRITE_OUT_OF_SCOPE", 0),
        "DESTRUCTIVE": statuses.get("DESTRUCTIVE_OUT_OF_SCOPE", 0),
        "MODEL_SAFE_PROJECTION_BLOCKED": statuses.get("NEEDS_MODEL_SAFE_PROJECTION", 0),
        "NESTED_PROJECTION_BLOCKED": statuses.get("NEEDS_NESTED_PROJECTION_SUPPORT", 0),
        "SEMANTICALLY_REDUNDANT": statuses.get("SEMANTICALLY_REDUNDANT", 0),
    }


def build_inventory_document(
    *,
    source_head: str,
    origin_main: str,
) -> dict[str, Any]:
    baseline = load_baseline()
    actions = build_actions(baseline)
    counts = _counts(actions)
    tools = mcp_tool_names()
    caps = curated_capabilities()
    _hydrate_current_allowlists(caps)
    cap_map = operation_to_capability(caps)
    authz_index = scan_route_authz()
    tech = technical_rows(actions, authz_index=authz_index, capability_by_operation=cap_map)
    frozen = freeze_records(caps)
    budgets = load_dynamic_read_budgets()
    cap_status = Counter(c["current_status"] for c in caps)
    domain_summary: dict[str, dict[str, Any]] = {}
    get_rows = [r for r in tech if r["method"] == "GET"]
    for row in get_rows:
        domain = row["bounded_context"]
        bucket = domain_summary.setdefault(
            domain,
            {
                "domain": domain,
                "get_operations": 0,
                "semantic_capabilities": 0,
                "currently_eligible": 0,
                "freeze_candidates": 0,
                "main_blockers": Counter(),
            },
        )
        bucket["get_operations"] += 1
        bucket["main_blockers"][row["current_davi_disposition"]] += 1
        if row["current_davi_disposition"] == "DAVI_ELIGIBLE_READ":
            bucket["currently_eligible"] += 1
    for cap in caps:
        bucket = domain_summary.setdefault(
            cap["domain"],
            {
                "domain": cap["domain"],
                "get_operations": 0,
                "semantic_capabilities": 0,
                "currently_eligible": 0,
                "freeze_candidates": 0,
                "main_blockers": Counter(),
            },
        )
        bucket["semantic_capabilities"] += 1
        if cap.get("freeze_status") == "FROZEN_FOR_IMPLEMENTATION":
            bucket["freeze_candidates"] += 1
    for bucket in domain_summary.values():
        bucket["main_blockers"] = dict(bucket["main_blockers"])

    assigned = {r["operationId"] for r in get_rows if r.get("semantic_capability_id")}
    unassigned = [
        {
            "operationId": r["operationId"],
            "path": r["http_path"],
            "domain": r["bounded_context"],
            "davi_status": r["current_davi_disposition"],
        }
        for r in get_rows
        if r["operationId"] not in assigned
    ]
    unassigned_by_status = Counter(x["davi_status"] for x in unassigned)

    seeded = {
        "get_product_detail": "REDUNDANT",
        "get_product_summary": "DEFER",
        "get_product_factory_status": "PROMOTE",
        "get_product_structure_exclusivity": "PROMOTE",
        "get_product_pricing": "DEFER",
        "get_product_purchase_price_history": "DEFER",
        "get_product_raw_material_price_intelligence": "DEFER",
        "get_product_cost_impact_simulation": "DEFER",
    }

    return {
        "metadata": {
            "taskId": TASK_ID,
            "artifact_class": "EVIDENCE_NOT_RUNTIME_AUTHORITY",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_head": source_head,
            "origin_main": origin_main,
            "openapi_version": baseline.get("openapi_version"),
            "baseline_version": baseline.get("version"),
            "baseline_operation_count": baseline.get("operation_count"),
            "budgets": budgets,
        },
        "technical_operation_counts": counts,
        "mcp_tools": tools,
        "mcp_tool_count": len(tools),
        "semantic_capability_counts": {
            "TOTAL_SEMANTIC_CAPABILITIES": len(caps),
            "STATUS_COUNTS": dict(sorted(cap_status.items())),
            "CURRENTLY_ELIGIBLE": cap_status.get("CURRENTLY_ELIGIBLE", 0),
            "READY_FOR_FREEZE": cap_status.get("READY_FOR_FREEZE", 0),
            "SEMANTICALLY_REDUNDANT": cap_status.get("SEMANTICALLY_REDUNDANT", 0),
            "FROZEN_FOR_IMPLEMENTATION": len(frozen),
        },
        "domain_counts": {k: v["get_operations"] for k, v in sorted(domain_summary.items())},
        "domain_summary": [domain_summary[k] for k in sorted(domain_summary)],
        "seeded_candidate_decisions": seeded,
        "redundancy_groups": redundancy_groups(),
        "wave_plan": wave_plan(),
        "wave_1_freeze": {
            "status": "FROZEN_FOR_IMPLEMENTATION",
            "theme": wave_plan()["WAVE_1"]["theme"],
            "capability_ids": [c["capability_id"] for c in frozen],
            "count": len(frozen),
            "current_eligible": counts["DAVI_ELIGIBLE_READ"],
            "new_capabilities": len(frozen),
            "expected_eligible_after_implementation": counts["DAVI_ELIGIBLE_READ"]
            + len(frozen),
            "expected_mcp_tools_after_implementation": 3,
            "agent_instruction_change": "NO",
            "capabilities": frozen,
        },
        "capabilities": caps,
        "technical_operations": tech,
        "residual_gaps": {
            "unassigned_get_count": len(unassigned),
            "unassigned_by_status": dict(sorted(unassigned_by_status.items())),
            "unassigned_get_operations": unassigned,
            "second_user_negative_authz": "TEST_NOT_RUN",
            "mcp_rate_policy": "TO_INVENTORY — overall rollout decision remains separate",
            "hr_privacy_review": "REQUIRED before any HR capability promotion",
            "note": (
                "Unassigned GETs are intentionally not promoted to capabilities. "
                "endpoint != capability. Many are dashboards, admin, binary, or lack a coherent user need."
            ),
        },
        "runtime_invariants": {
            "allowlist_must_remain_unchanged": True,
            "eligible_must_remain": 7,
            "mcp_tools_must_remain": 3,
        },
    }


def render_markdown(doc: dict[str, Any]) -> str:
    counts = doc["technical_operation_counts"]
    sc = doc["semantic_capability_counts"]
    wave1 = doc["wave_1_freeze"]
    lines = [
        "# DAVI capability expansion inventory",
        "",
        "> Evidence artifact. **Not** runtime authority. **Not** the operational allowlist.",
        "",
        f"- Task: `{doc['metadata']['taskId']}`",
        f"- Source HEAD: `{doc['metadata']['source_head']}`",
        f"- origin/main: `{doc['metadata']['origin_main']}`",
        f"- OpenAPI/baseline: `{doc['metadata']['openapi_version']}` / v{doc['metadata']['baseline_version']}",
        f"- Generated at: `{doc['metadata']['generated_at']}`",
        "",
        "## Executive summary",
        "",
        "DAVI remains intelligence/orchestration over API DELPI. This inventory converts GET operations "
        "into semantic READ capabilities and freezes Wave 1 without promoting runtime eligibility.",
        "",
        f"- Technical operations: **{counts['TOTAL_OPERATIONS']}** (GET **{counts['TOTAL_GET']}**)",
        f"- Current `DAVI_ELIGIBLE_READ`: **{counts['DAVI_ELIGIBLE_READ']}**",
        f"- Current MCP tools: **{doc['mcp_tool_count']}** `{doc['mcp_tools']}`",
        f"- Proposed semantic capabilities: **{sc['TOTAL_SEMANTIC_CAPABILITIES']}**",
        f"- Wave 1 frozen: **{wave1['count']}** → expected eligible after implementation **{wave1['expected_eligible_after_implementation']}**",
        f"- Unassigned GETs (not capabilities): **{doc['residual_gaps']['unassigned_get_count']}**",
        "",
        "## Baseline",
        "",
        "```json",
        json.dumps(
            {
                "TOTAL_OPERATIONS": counts["TOTAL_OPERATIONS"],
                "TOTAL_GET": counts["TOTAL_GET"],
                "DAVI_ELIGIBLE_READ": counts["DAVI_ELIGIBLE_READ"],
                "ELIGIBLE_OPERATION_IDS": counts["ELIGIBLE_OPERATION_IDS"],
                "STATUS_COUNTS": counts["STATUS_COUNTS"],
            },
            indent=2,
        ),
        "```",
        "",
        "## Domain coverage (GET operations)",
        "",
        "| Domain | GET ops | Semantic capabilities | Currently eligible | Wave 1 freeze | Main technical blockers |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for bucket in doc["domain_summary"]:
        blockers = ", ".join(
            f"{k}:{v}"
            for k, v in sorted(
                bucket["main_blockers"].items(), key=lambda kv: (-kv[1], kv[0])
            )[:4]
        )
        lines.append(
            f"| `{bucket['domain']}` | {bucket['get_operations']} | {bucket['semantic_capabilities']} | "
            f"{bucket['currently_eligible']} | {bucket['freeze_candidates']} | {blockers} |"
        )
    lines.extend(
        [
            "",
            "## Semantic clusters",
            "",
        ]
    )
    for cap in doc["capabilities"]:
        lines.append(
            f"- `{cap['capability_id']}` — {cap['business_name_ptbr']} "
            f"[{cap['current_status']}] wave={cap.get('wave_candidate') or '—'} "
            f"ops={', '.join('`'+o+'`' for o in cap['technical_operations'])}"
        )
    lines.extend(["", "## Redundancies", ""])
    for group in doc["redundancy_groups"]:
        ops = ", ".join(f"`{o}`" for o in group["operations"])
        lines.append(
            f"- **{group['group']}**: {ops} → `{group['semantic_capability']}`. {group['decision']}"
        )
    lines.extend(["", "## High-value / seeded candidates", ""])
    for oid, decision in doc["seeded_candidate_decisions"].items():
        lines.append(f"- `{oid}` → **{decision}**")
    lines.extend(["", "## Wave plan", ""])
    for name, wave in doc["wave_plan"].items():
        caps = ", ".join(f"`{c}`" for c in wave.get("capability_ids") or [])
        lines.append(f"### {name} — {wave.get('theme')}")
        lines.append("")
        lines.append(caps)
        lines.append("")
        lines.append(wave.get("reason") or "")
        lines.append("")
    lines.extend(
        [
            "## Wave 1 freeze",
            "",
            f"Status: **{wave1['status']}**",
            "",
            f"Capabilities: {', '.join('`'+c+'`' for c in wave1['capability_ids'])}",
            "",
            "Normative freeze contract: `davi-capability-wave-001-freeze.md`.",
            "",
            "## Gaps",
            "",
            f"- Unassigned GET operations: {doc['residual_gaps']['unassigned_get_count']}",
            f"- Second-user negative AuthZ: `{doc['residual_gaps']['second_user_negative_authz']}`",
            f"- MCP rate policy: {doc['residual_gaps']['mcp_rate_policy']}",
            f"- HR: {doc['residual_gaps']['hr_privacy_review']}",
            "",
            "## Next step",
            "",
            "Architecture Acceptance → `DAVI-CAPABILITY-EXPANSION-WAVE-001` implementation. "
            "Do not implement in this evidence task.",
            "",
        ]
    )
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def render_freeze_markdown(doc: dict[str, Any]) -> str:
    wave1 = doc["wave_1_freeze"]
    lines = [
        "# DAVI Wave 1 capability freeze",
        "",
        "> **Normative for the next implementation task.** Evidence/governance only. Does not change runtime.",
        "",
        f"- Task: `{TASK_ID}`",
        f"- Source HEAD: `{doc['metadata']['source_head']}`",
        f"- Freeze status: `{wave1['status']}`",
        f"- Theme: {wave1['theme']}",
        f"- Current eligible: **{wave1['current_eligible']}**",
        f"- New Wave 1 capabilities: **{wave1['new_capabilities']}**",
        f"- Expected eligible after implementation: **{wave1['expected_eligible_after_implementation']}**",
        f"- Expected MCP tools after implementation: **{wave1['expected_mcp_tools_after_implementation']}**",
        f"- Agent instructions change: **{wave1['agent_instruction_change']}**",
        "",
        "## Architecture invariants (do not reopen)",
        "",
        "```text",
        "DAVI capability <= authenticated user capability",
        "DAVI_BUSINESS_AUTHZ_OWNER = NONE",
        "CANONICAL_BACKEND_AUTHZ = REQUIRED_FINAL",
        "DAVI_LOCAL_RBAC / BRANCH / OBJECT / ROLE AUTHZ = FORBIDDEN",
        "FILTER != AUTHORIZATION",
        "endpoint != capability",
        "backend AuthZ != raw model exposure",
        "MCP tools remain search_products + discover_delpi_information + execute_delpi_information",
        "```",
        "",
        "## Why this Wave 1 (not the seeded summary trio as-is)",
        "",
        doc["wave_plan"]["WAVE_1"]["reason"],
        "",
        "`get_product_summary` is **DEFER**: omitting prices makes it redundant with current "
        "search+stock; including prices belongs to Wave 2. `get_product_shipping_status` is the "
        "clearer unique operational sibling.",
        "",
    ]
    for cap in wave1["capabilities"]:
        lines.extend(
            [
                f"## {cap['capability_id']}",
                "",
                f"- **CAPABILITY ID:** `{cap['capability_id']}`",
                f"- **BUSINESS NAME:** {cap['business_name_ptbr']} / {cap['business_name_en']}",
                f"- **BUSINESS NEED:** {cap['business_need']}",
                f"- **OWNER:** {cap['owner']} (`{cap.get('owner_evidence')}`)",
                f"- **SOURCE OF TRUTH:** {cap['authoritative_source']}",
                f"- **CANONICAL OPERATION(S):** {', '.join('`'+o+'`' for o in cap['technical_operations'])}",
                f"- **CANONICAL USE CASE:** `{cap['canonical_use_case']}`",
                f"- **READ/PREPARE/ACT:** {cap['READ_PREPARE_ACT']}",
                f"- **IDENTITY:** {cap['identity_model']}",
                f"- **BACKEND AUTHZ:** {cap['backend_authz']}",
                f"- **BUSINESS AUTHZ OWNER:** {cap['business_authz_owner']}",
                f"- **SEMANTIC INPUT CONTRACT:** required={cap['required_inputs']} optional={cap['optional_inputs']}",
                f"- **APPROVED INPUT FIELDS:** {cap['required_inputs'] + cap['optional_inputs']}",
                f"- **INPUT MINIMIZATION:** {cap['input_minimization']}",
                f"- **SEMANTIC OUTPUT CONTRACT:** {cap['semantic_contract']}",
                "- **APPROVED RESPONSE FIELDS:**",
            ]
        )
        for field in cap["output_allowlist_candidate"]:
            lines.append(f"  - `{field}`")
        lines.extend(
            [
                f"- **SHAPE:** {cap['response_shape']}",
                f"- **PROJECTION MODE:** {cap['projection_mode']}",
                f"- **LIMITS:** {cap['limits_required']}; max_items={cap.get('max_items')}; max_depth={cap.get('max_depth')}",
                f"- **BRANCH:** {cap['branch_semantics']}",
                f"- **PAGINATION:** {cap['pagination']}",
                f"- **TIME SEMANTICS:** {cap.get('time_semantics')}",
                f"- **COMPLETENESS:** {cap['completeness_semantics']}",
                f"- **PROVENANCE:** Preserve canonical operationId/use case, reference/start dates, branch filter scope, truncated/is_complete. Do not expose SQL, hosts, or internals.",
                f"- **RETRIEVAL ALIASES PT-BR:** {cap['retrieval_aliases_ptbr']}",
                f"- **RETRIEVAL ALIASES EN:** {cap['retrieval_aliases_en']}",
                f"- **PRIVACY:** {cap['privacy_risk']}",
                f"- **RISK:** volume={cap['volume_risk']} runtime={cap['runtime_risk']}",
                f"- **OBSERVABILITY:** {cap['observability_required']}",
                f"- **TEST PLAN:** unit projection paths; discover aliases positive+collision; execute bounded payload; sibling non-match (produção vs fabril vs expedição vs exclusividade); negative AuthZ 403 with unauthorized identity when available.",
                f"- **LIVE ACCEPTANCE:** Agent Preview discover→candidate→execute for a real product code; verify allowlisted fields only; verify sibling questions still hit current seven plus new three without new MCP tools.",
                f"- **NEGATIVE AUTHZ PLAN:** `{cap['negative_authz_test_required']}` — authenticated user without `API_DELPI_ACCESS` must receive backend 403. SECOND_USER_NEGATIVE_AUTHZ remains TEST_NOT_RUN for broad publication.",
                f"- **QUARANTINE CHANGE REQUIRED:** {json.dumps(cap.get('quarantine_delta_required') or [], ensure_ascii=False)}",
                f"- **IMPLEMENTATION NOTES:** Add allowlist `operations[]` entry only. Do not add MCP tools, Agent prompt enumeration, DAVI RBAC, per-operation executor, or generic HTTP/SQL. Reuse generic nested projection. Bound max_depth≤8 and date interval. Omit `legacy` input.",
                f"- **OPEN GAPS:** {cap.get('open_gaps')}",
                f"- **FREEZE STATUS:** `{cap['freeze_status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Implementation handoff (do not execute here)",
            "",
            "Files expected to change later:",
            "",
            "- `api-delpi/app/content/davi_external_read_allowlist.json` (three new operations + aliases)",
            "- `api-delpi/tests/test_davi_dynamic_read.py` (eligible count 10, discover aliases, projection)",
            "- generated technical inventory after promotion (separate task)",
            "",
            "Must not change: MCP server tool surface, Agent Instructions, eligibility classifier semantics, "
            "executor genericity, API routes, use cases, repositories.",
            "",
            "Expected eligible after implementation: **10**. Expected MCP tools: **3**.",
            "",
        ]
    )
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def write_artifacts(doc: dict[str, Any], *, out_dir: Path | None = None) -> dict[str, Path]:
    target = out_dir or (api_root() / "docs/integrations/evidence")
    target.mkdir(parents=True, exist_ok=True)
    json_path = target / f"{ARTIFACT_STEM}.json"
    md_path = target / f"{ARTIFACT_STEM}.md"
    freeze_md = target / f"{FREEZE_STEM}.md"
    freeze_json = target / f"{FREEZE_STEM}.json"
    json_path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(doc), encoding="utf-8")
    freeze_md.write_text(render_freeze_markdown(doc), encoding="utf-8")
    freeze_json.write_text(
        json.dumps(
            {
                "metadata": doc["metadata"],
                "wave_1_freeze": doc["wave_1_freeze"],
                "artifact_class": "EVIDENCE_NOT_RUNTIME_AUTHORITY",
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return {
        "inventory_json": json_path,
        "inventory_md": md_path,
        "freeze_md": freeze_md,
        "freeze_json": freeze_json,
    }
