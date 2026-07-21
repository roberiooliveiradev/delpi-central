from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


def test_label_for_uses_content_dictionary():
    service = ExternalActionColumnLabelService()

    assert service.label_for("route_code") == "Cód. roteiro"
    assert service.label_for("operation_description") == "Descrição operação"


def test_label_for_prefers_openapi_schema_title():
    service = ExternalActionColumnLabelService()

    label = service.label_for(
        "route_code",
        schema_labels={"route_code": "Roteiro (OpenAPI)"},
    )

    assert label == "Roteiro (OpenAPI)"


def test_merge_meta_field_labels_overrides_schema_glossary():
    service = ExternalActionColumnLabelService()

    labels = service.merge_meta_field_labels(
        {"available_quantity": "Saldo (OpenAPI)"},
        {
            "meta": {
                "fields": {
                    "available_quantity": "Saldo disponível (atual - empenhado - reservado)",
                }
            }
        },
    )

    assert labels["available_quantity"] == "Saldo disponível (atual - empenhado - reservado)"


def test_resolve_schema_labels_from_openapi_response():
    service = ExternalActionColumnLabelService()

    labels = service.resolve_schema_labels(
        {
            "200": {
                "content": {
                    "application/json": {
                        "schema": {
                            "properties": {
                                "items": {
                                    "type": "array",
                                    "items": {
                                        "properties": {
                                            "route_code": {
                                                "type": "string",
                                                "title": "Cód. roteiro SG2",
                                            },
                                            "operation_code": {
                                                "type": "string",
                                                "title": "Operação",
                                            },
                                        }
                                    },
                                }
                            }
                        }
                    }
                }
            }
        }
    )

    assert labels["route_code"] == "Cód. roteiro SG2"
    assert labels["operation_code"] == "Operação"


def test_detect_guide_profile_for_sg2_schema():
    service = ExternalActionColumnLabelService()

    profile = service.detect_table_profile(
        {
            "branch": "01",
            "route_code": "01",
            "operation_code": "01",
            "operation_description": "EMBALAR",
        },
        path="/products/90260123/guide",
    )

    assert profile == "guide"


def test_label_for_eficiencia_fabril_summary_and_items():
    service = ExternalActionColumnLabelService()

    assert service.label_for("weighted_efficiency_pct") == "Eficiência ponderada (%)"
    assert service.label_for("total_mod_result") == "Resultado MOD total"
    assert service.label_for("appointment_count") == "Qtd. de apontamentos"
    assert service.label_for("tempo_real_horas") == "Tempo real (h)"
    assert service.label_for("eficiencia_percentual") == "Eficiência (%)"


def test_detect_eficiencia_fabril_profile():
    service = ExternalActionColumnLabelService()

    profile = service.detect_table_profile(
        {
            "filial": "01",
            "op": "24546401001",
            "eficiencia_percentual": 98.5,
            "tempo_real_horas": 1.2,
        },
        path="/production/eficiencia-fabril/dashboard",
    )

    assert profile == "eficienciaFabril"


def test_preferred_columns_for_guide_profile():
    service = ExternalActionColumnLabelService()
    row = {
        "branch": "01",
        "route_code": "01",
        "product_code": "90260123",
        "operation_code": "01",
        "operation_description": "EMBALAR",
        "work_center": "CT-19",
    }

    columns = service.preferred_columns("guide", row)

    assert ("route_code", "Cód. roteiro") in columns
    assert ("operation_code", "Cód. operação") in columns


def test_label_for_camel_case_product_summary_keys():
    service = ExternalActionColumnLabelService()

    assert service.label_for("groupCode") == "Grupo"
    assert service.label_for("lastPurchasePrice") == "Último preço de compra"
    assert service.label_for("customerReference") == "Referência cliente"


def test_label_for_resolves_snake_case_dictionary_from_camel_case_key():
    service = ExternalActionColumnLabelService()

    assert service.label_for("registeredLeadTimeDays") == "Lead time (dias)"


def test_label_for_humanizes_unknown_snake_and_camel_keys():
    service = ExternalActionColumnLabelService()

    assert service.label_for("some_custom_metric") == "Some Custom Metric"
    assert service.label_for("someCustomMetric") == "Some Custom Metric"


def test_format_field_value_applies_currency_percent_and_days():
    service = ExternalActionColumnLabelService()

    assert service.format_field_value("gross_revenue", 5138916.92) == "R$ 5.138.916,92"
    assert service.format_field_value("ebitda_over_rol_pct", 12.5) == "12,50%"
    assert service.format_field_value("pmr_days", 42) == "42 dias"


def test_format_field_value_unwraps_consolidated_envelope():
    service = ExternalActionColumnLabelService()

    assert service.format_field_value("realized", {"consolidated": None}) == "—"
    assert service.format_field_value("goals", {"consolidated": 95}) == "95"
    assert (
        ExternalActionColumnLabelService.unwrap_nested_scalar({"consolidated": 15000})
        == 15000
    )


def test_flatten_row_scalars_for_department_indicators():
    from app.domain.services.chat_presentation_operational_table_service import (
        ChatPresentationOperationalTableService,
    )

    row = ChatPresentationOperationalTableService.flatten_row_scalars(
        {
            "name": "Prazo",
            "value": None,
            "realized": {"consolidated": None},
            "goals": {"consolidated": 95.0},
        }
    )

    assert row["realized"] is None
    assert row["goals"] == 95.0


def test_merge_meta_field_formats_reads_api_meta():
    service = ExternalActionColumnLabelService()

    formats = service.merge_meta_field_formats(
        {},
        {
            "meta": {
                "fieldFormats": {
                    "custom_metric": "percent",
                }
            }
        },
    )

    assert formats["custom_metric"] == "percent"
    assert service.format_field_value(
        "custom_metric",
        10,
        schema_formats=formats,
    ) == "10,00%"


def test_presenter_kv_table_and_profile_rows():
    service = ExternalActionColumnLabelService()

    columns = service.kv_table_column_defs()

    assert columns == [
        {"key": "campo", "label": "Campo"},
        {"key": "valor", "label": "Valor"},
    ]

    rows = service.build_kv_profile_rows(
        {
            "code": "90260123",
            "description": "PARAFUSO",
            "blocked": "",
            "active": True,
        },
        extended=True,
    )

    assert rows[0] == {"campo": "Código", "valor": "90260123"}
    assert rows[1] == {"campo": "Descrição", "valor": "PARAFUSO"}
    assert all(row["campo"] != "Bloqueio" for row in rows)


def test_format_collection_total_and_structure_columns():
    service = ExternalActionColumnLabelService()

    assert service.format_collection_total(12) == "12 registro(s)"

    columns = service.fixed_table_columns("analyserStructureComponents")

    assert columns[0] == {"key": "parent_code", "label": "PI pai"}
    assert columns[-1] == {
        "key": "quantity",
        "label": "Qtde",
        "dataType": "quantity",
    }


def test_fixed_table_columns_for_billing_and_analyser():
    service = ExternalActionColumnLabelService()

    assert service.fixed_table_columns("lmpList")[0]["key"] == "sale_number"
    assert service.markdown_column_pairs("analyserInspectionDimensionalMarkdown")[2] == (
        "lab",
        "Labor.",
    )


def test_fixed_table_columns_removed_from_presenter_bundle():
    from app.domain.services.external_actions.external_action_column_label_service import (
        _column_labels_content,
        invalidate_column_label_cache,
    )

    invalidate_column_label_cache()
    presenter = (_column_labels_content().get("presenter") or {})

    assert "fixedTableColumns" not in presenter
    assert presenter.get("fixedTableColumnsDeprecated")
    assert "tableProfiles" in _column_labels_content()
    assert "lmpList" in (_column_labels_content().get("tableProfiles") or {})
