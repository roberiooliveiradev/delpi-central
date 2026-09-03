from app.application.use_cases.execute_external_action_use_case import (
    ExecuteExternalActionUseCase,
)
from app.domain.services.chat_schema_driven_presentation_service import (
    ChatSchemaDrivenPresentationService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)


def _use_case():
    return ExecuteExternalActionUseCase(
        repository=None,
        gateway=None,
        policy=None,
        audit_repository=None,
    )


def test_should_apply_for_kpi_entity_and_generic_path():
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/supplies/cpv",
        entity="supplies_cpv",
    )
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/commercial/closing-rate",
        entity="sales_conversion_rate",
    )
    assert ChatSchemaDrivenPresentationService.should_apply(
        path="/products/90260144/stock",
        entity="product_stock",
    )


def test_extract_tabular_rows_from_system_tables_search_results():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "success": True,
            "total_records": 2,
            "results": [
                {"X2_ARQUIVO": "SB1010", "X2_NOME": "CADASTRO DE PRODUTOS"},
                {"X2_ARQUIVO": "SB2010", "X2_NOME": "GRUPO DE PRODUTOS"},
            ],
        }
    )

    assert len(rows) == 2
    assert rows[0]["X2_ARQUIVO"] == "SB1010"


def test_extract_tabular_rows_from_nested_last_purchase_object():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "product": {"product_code": "10080001"},
            "last_purchase": {
                "supplier_code": "000002",
                "unit_price": 0.089,
            },
        }
    )

    assert len(rows) == 1
    assert rows[0]["supplier_code"] == "000002"


def test_extract_tabular_rows_from_product_snapshot_fixture():
    """product_snapshot (data.product) deve virar 1 row — sem falso-vazio Automático."""
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture

    payload = load_api_delpi_fixture("product_detail_90269001.json")
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(payload)

    assert len(rows) == 1
    assert rows[0]["code"] == "90269001"
    assert rows[0]["description"]

    nested_only = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {"product": {"code": "10080031", "description": "TERM. FASTON"}}
    )
    assert nested_only == [{"code": "10080031", "description": "TERM. FASTON"}]


def test_build_raw_payload_markdown_for_unknown_shape():
    presenter = ExternalActionResultPresenter()
    payload = ChatSchemaDrivenPresentationService.build_raw_payload_markdown(
        presenter,
        {"custom_field": "valor", "count": 3},
        path="/external/demo",
    )

    assert isinstance(payload, dict)
    assert payload["type"] == "markdown"
    assert "custom_field" in payload["markdown"]
    assert "```json" in payload["markdown"]


def test_extract_tabular_rows_from_series_and_items():
    series_rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "series": [
                {"period": "jan/2026", "value": 12.5},
                {"period": "fev/2026", "value": 13.1},
            ]
        }
    )
    items_rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {"items": [{"branch": "01", "value": 100}]}
    )

    assert len(series_rows) == 2
    assert items_rows[0]["branch"] == "01"


def test_extract_tabular_rows_from_department_indicators_item_envelope():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "item": {
                "department_id": "engineering",
                "idd": 0.0,
                "indicators": [
                    {"indicator_id": "a", "name": "Prazo", "goal_value": 95.0},
                    {"indicator_id": "b", "name": "Transforma", "goal_value": 15000.0},
                ],
            }
        }
    )

    assert len(rows) == 2
    assert rows[0]["indicator_id"] == "a"


def test_extract_tabular_rows_from_nested_orders_items_envelope():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "summary": {"late_ops": 2, "on_time_ops": 8},
            "orders": {
                "items": [
                    {"op": "1", "status": "late", "days_diff": -3},
                    {"op": "2", "status": "late", "days_diff": -1},
                ]
            },
        }
    )

    assert len(rows) == 2
    assert rows[0]["status"] == "late"


def test_extract_tabular_rows_from_sql_resultsets_data():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "sql": "SELECT 1",
            "total_resultsets": 1,
            "resultsets": [
                {
                    "index": 1,
                    "columns": ["C2_OP", "COD_PRODUTO"],
                    "total": 2,
                    "data": [
                        {"C2_OP": "1", "COD_PRODUTO": "90260144"},
                        {"C2_OP": "2", "COD_PRODUTO": "90261805"},
                    ],
                }
            ],
        }
    )

    assert len(rows) == 2
    assert rows[0]["C2_OP"] == "1"


def test_extract_tabular_rows_from_preferred_nested_section_without_envelope_key():
    rows = ChatSchemaDrivenPresentationService.extract_tabular_rows(
        {
            "summary": {"total": 1},
            "production": {
                "items": [{"op": "A", "qty": 10}],
            },
        }
    )

    assert len(rows) == 1
    assert rows[0]["op"] == "A"


def test_build_kpi_from_scalar_metrics():
    presenter = ExternalActionResultPresenter()
    root = {
        "value": 82.5,
        "target": 90.0,
        "previous": 80.0,
        "unit": "%",
    }

    kpi = ChatSchemaDrivenPresentationService.build_kpi(
        presenter,
        root,
        path="/commercial/closing-rate",
        entity="sales_conversion_rate",
    )

    assert isinstance(kpi, dict)
    assert kpi["type"] == "kpi"
    assert kpi["cards"]


def test_build_text_for_time_series():
    presenter = ExternalActionResultPresenter()
    text = ChatSchemaDrivenPresentationService.build_text(
        presenter,
        {
            "series": [
                {"period": "jan/2026", "value": 10},
                {"period": "fev/2026", "value": 12},
            ]
        },
        path="/quality/nonconformities/series",
        entity="nonconformity_series",
    )

    assert isinstance(text, dict)
    assert text["type"] == "markdown"
    assert "série temporal" in text["markdown"].lower()


def test_schema_driven_metadata_for_commercial_kpi():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/commercial/closing-rate"},
        sanitized_data={
            "value": 82.5,
            "target": 90.0,
            "previous": 80.0,
            "unit": "%",
        },
        resolved_path="/commercial/closing-rate",
        request_parameters={},
    )

    kpi = meta.get("kpiPresentation") or meta.get("presentation")
    decision = meta.get("presentationDecision") or {}

    assert isinstance(kpi, dict)
    assert kpi["type"] == "kpi"
    assert "text" in meta["availableFormats"]
    assert meta["textPresentation"]["type"] == "markdown"
    assert decision.get("selected") in {"text", "kpi", "dashboard"}


def test_schema_driven_metadata_builds_table_for_generic_items():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={"path": "/commercial/proposals"},
        sanitized_data={
            "items": [
                {"proposal_number": "100", "customer_name": "Cliente A", "amount": 1500},
                {"proposal_number": "101", "customer_name": "Cliente B", "amount": 2300},
            ],
            "total": 2,
        },
        resolved_path="/commercial/proposals",
        request_parameters={},
    )

    assert "table" in meta["availableFormats"]
    table = meta.get("tablePresentation") or meta.get("presentation")
    assert isinstance(table, dict)
    assert table["type"] == "table"
    assert len(table["rows"]) == 2


def test_composite_bundle_for_safety_stock_detail_exposes_commitments_and_timeline():
    from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta

    envelope = load_api_delpi_fixture_with_meta(
        "supplies_safety_stock_item_details_10020113.json"
    )
    presenter = ExternalActionResultPresenter()
    bundle = ChatSchemaDrivenPresentationService.build_composite_bundle(
        presenter,
        envelope["data"],
        path="/supplies/safety-stock/items/10020113/details",
        entity="supplies_safety_stock_detail",
        sections=(envelope.get("meta") or {}).get("sections"),
    )

    tables = list(bundle.tables or ())
    titles = [str(table.get("title") or "") for table in tables]
    assert len(tables) >= 3
    assert "open_commitments" in titles
    assert "stock_projection" in titles
    assert "open_purchase_orders" in titles


def test_composite_bundle_for_protheus_table_schema_section_blocks():
    """Schema Protheus — seções canônicas `{items,total,truncated}` (Playbook 10)."""
    presenter = ExternalActionResultPresenter()
    payload = {
        "summary": {
            "tableName": "SB1010",
            "alias": "SB1",
            "description": "Descrição Genérica do Produto",
            "columnCount": 2,
            "indexCount": 1,
            "relationCount": 1,
        },
        "columns": {
            "items": [
                {"X3_CAMPO": "B1_COD", "X3_DESCRIC": "Codigo", "X3_TIPO": "C"},
                {"X3_CAMPO": "B1_DESC", "X3_DESCRIC": "Descricao", "X3_TIPO": "C"},
            ],
            "total": 2,
            "truncated": False,
        },
        "indexes": {
            "items": [{"INDICE": "SB1", "CHAVE": "B1_FILIAL+B1_COD", "ORDEM": "1"}],
            "total": 1,
            "truncated": False,
        },
        "relations": {
            "items": [{"X9_DOM": "SB1", "X9_CAMPO": "B1_COD", "X9_EXPDOM": "SB2"}],
            "total": 1,
            "truncated": False,
        },
        "table": {
            "items": [
                {
                    "TableName": "SB1010",
                    "X2_CHAVE": "SB1",
                    "X2_ARQUIVO": "SB1010",
                    "X2_NOME": "Descrição Genérica do Produto",
                }
            ],
            "total": 1,
            "truncated": False,
        },
    }
    sections = [
        {"key": "columns", "label": "Colunas (SX3)", "itemCount": 2, "truncated": False},
        {"key": "indexes", "label": "Índices (SIX)", "itemCount": 1, "truncated": False},
        {"key": "relations", "label": "Relacionamentos (SX9)", "itemCount": 1, "truncated": False},
        {"key": "table", "label": "Metadados da tabela (SX2)", "itemCount": 1, "truncated": False},
    ]

    bundle = ChatSchemaDrivenPresentationService.build_composite_bundle(
        presenter,
        payload,
        path="/system/tables/SB1010/schema",
        entity="protheus_table_schema",
        sections=sections,
    )

    tables = list(bundle.tables or ())
    assert len(tables) >= 3
    assert bundle.table is not None
    assert bundle.dashboard is None  # perfil system: compositeDashboardPolicy=skip
    primary_rows = bundle.table.get("rows") or []
    assert any(
        str(row.get("X3_CAMPO") or row.get("x3_campo") or "").upper() == "B1_COD"
        for row in primary_rows
    )
    titles = " | ".join(str(table.get("title") or "") for table in tables).lower()
    assert "coluna" in titles or "sx3" in titles


def test_extract_download_artifacts_normalizes_relative_path():
    artifacts = ChatSchemaDrivenPresentationService.extract_download_artifacts(
        {
            "message": "Arquivo Excel gerado com sucesso!",
            "filename": "Estrutura_90261757.xlsx",
            "downloadPath": "/products/90261757/structure/excel?format=xlsx",
        }
    )

    assert len(artifacts) == 1
    assert artifacts[0]["filename"] == "Estrutura_90261757.xlsx"
    assert artifacts[0]["href"] == (
        "/apps/api-delpi/products/90261757/structure/excel?format=xlsx"
    )
    assert "Baixar" in artifacts[0]["label"]


def test_schema_driven_metadata_builds_document_export_download_artifacts():
    use_case = _use_case()
    meta = use_case._build_presentation_metadata(
        action={
            "path": "/products/{code}/structure/excel",
            "operationId": "get_product_structure_excel",
        },
        sanitized_data={
            "success": True,
            "data": {
                "message": "Arquivo Excel gerado com sucesso!",
                "filename": "Estrutura_90261757.xlsx",
                "downloadPath": "/products/90261757/structure/excel?format=xlsx",
                "download_url": "/products/90261757/structure/excel?format=xlsx",
            },
            "meta": {
                "operationId": "get_product_structure_excel",
                "entity": "product_structure_excel",
                "shape": "document_export",
            },
        },
        resolved_path="/products/90261757/structure/excel",
        request_parameters={"code": "90261757"},
    )

    artifacts = meta.get("downloadArtifacts") or []
    assert len(artifacts) == 1
    assert artifacts[0]["href"].endswith(
        "/products/90261757/structure/excel?format=xlsx"
    )

    render_plan = meta.get("renderPlan") or {}
    kinds = [str(segment.get("kind") or "") for segment in render_plan.get("segments") or []]
    assert "download" in kinds
    assert meta.get("textPresentation", {}).get("type") == "markdown"


def test_build_bundle_skips_chart_when_stock_chart_policy_is_skip():
    """Perfil stock tem chart em viewOrder mas chartPolicy=skip — não montar chart."""
    presenter = ExternalActionResultPresenter()
    rows = [
        {
            "branch": "01",
            "warehouse": "01",
            "available_quantity": 0,
            "current_quantity": 10,
            "committed_quantity": 10,
        },
        {
            "branch": "01",
            "warehouse": "99",
            "available_quantity": 5,
            "current_quantity": 5,
            "committed_quantity": 0,
        },
        {
            "branch": "02",
            "warehouse": "01",
            "available_quantity": 2,
            "current_quantity": 2,
            "committed_quantity": 0,
        },
    ]
    data = {"items": rows, "summary": {"available_quantity": 7}}

    bundle = ChatSchemaDrivenPresentationService.build_bundle(
        presenter,
        data,
        path="/products/10090016/stock",
        entity="product_stock",
    )

    assert bundle.table is not None
    assert bundle.chart is None
    assert ChatSchemaDrivenPresentationService._chart_policy_is_skip(
        path="/products/10090016/stock",
        entity="product_stock",
    )
    assert not ChatSchemaDrivenPresentationService._profile_allows_chart(
        path="/products/10090016/stock",
        entity="product_stock",
    )


def test_build_kpi_returns_none_for_list_root():
    presenter = ExternalActionResultPresenter()
    kpi = ChatSchemaDrivenPresentationService.build_kpi(
        presenter,
        [{"name": "SB1010", "description": "Produtos"}],
        path="/system/tables/SB1010",
        entity="protheus_table",
    )

    assert kpi is None


def test_build_bundle_tolerates_list_data_without_raising():
    presenter = ExternalActionResultPresenter()
    bundle = ChatSchemaDrivenPresentationService.build_bundle(
        presenter,
        [{"X2_CHAVE": "SB1", "X2_NOME": "Cadastro de Produtos"}],
        path="/system/tables/SB1010",
        entity="protheus_table",
        response_shape="scalar",
    )

    assert bundle.kpi is None
    assert bundle.table is not None or bundle.text is not None
