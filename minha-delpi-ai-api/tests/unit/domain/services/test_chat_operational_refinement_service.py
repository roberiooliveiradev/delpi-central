from types import SimpleNamespace

from app.domain.services.chat_operational_refinement_service import (
    ChatOperationalRefinementService,
)


def _stock_assistant_message(product_code: str = "10080022"):
    return SimpleNamespace(
        role="assistant",
        content=f"Estoque do produto {product_code}",
        metadata={
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{product_code}/stock",
                        "actionId": "get_product_stock",
                    },
                }
            ]
        },
    )


def test_detect_stock_refinement_with_branch_from_history():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        _stock_assistant_message(),
    ]

    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=history,
    )

    assert refinement is not None
    assert refinement.kind == "stock_refinement"
    assert refinement.product_code == "10080022"
    assert refinement.branch == "02"


def test_detect_stock_refinement_with_unresolved_path_template():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        {
            "role": "assistant",
            "content": "Estoque do produto 10080022",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "get_product_stock",
                            "parameters": {"code": "10080022", "page": 1, "page_size": 50},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/{code}/stock",
                            "actionId": "get_product_stock",
                        },
                    }
                ]
            },
        },
    ]

    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=history,
    )

    assert refinement is not None
    assert refinement.kind == "stock_refinement"
    assert refinement.product_code == "10080022"
    assert refinement.branch == "02"


def test_detect_ignores_refinement_without_stock_context():
    refinement = ChatOperationalRefinementService.detect(
        "filtre filial 02",
        previous_messages=[{"role": "user", "content": "olá"}],
    )

    assert refinement is None


def test_plan_stock_follow_ups_for_multiple_products():
    history = [
        {"role": "user", "content": "estoque dos produtos 10080047 e 10080055"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    },
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080055/stock",
                        },
                    },
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_stock_follow_ups(
        "filtre filial 01",
        previous_messages=history,
    )

    assert len(planned) == 2
    assert {item.product_code for item in planned} == {"10080047", "10080055"}
    assert all(item.branch == "01" for item in planned)


def test_plan_stock_reset_for_multiple_products():
    history = [
        {"role": "user", "content": "estoque dos produtos 10080047 e 10080055"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    },
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080055/stock",
                            "branch": "01",
                        },
                    },
                ]
            },
        },
        {"role": "user", "content": "filtre filial 01"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/stock",
                        },
                    },
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080055/stock",
                        },
                    },
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_stock_follow_ups(
        "completo de novo",
        previous_messages=history,
    )

    assert len(planned) == 2
    assert all(item.kind == "stock_reset" for item in planned)
    assert all(item.branch is None for item in planned)


def test_plan_metric_follow_up_after_cpv():
    history = [
        {"role": "user", "content": "qual o cpv"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/cpv"},
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filtre filial 02",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].metric_kind == "supplies"
    assert planned[0].branch == "02"


def test_plan_metric_follow_up_after_stock_value_bare_branch():
    history = [
        {"role": "user", "content": "qual o valor total de estoque da empresa"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/stock-value"},
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filial 01",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].metric_path_token == "stock-value"
    assert planned[0].branch == "01"


def test_is_operational_follow_up_for_stock_value_bare_branch():
    history = [
        {"role": "user", "content": "qual o valor total de estoque da empresa"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/stock-value"},
                    }
                ]
            },
        },
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "filial 01",
        previous_messages=history,
    )


def test_plan_metric_follow_up_with_filial_typo():
    history = [
        {"role": "user", "content": "qual o valor total de estoque da empresa"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {"ok": True, "path": "/supplies/stock-value"},
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filail 01",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].branch == "01"


def test_is_operational_follow_up_enables_fast_path():
    history = [
        {"role": "user", "content": "estoque do produto 10080022"},
        _stock_assistant_message(),
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "filtre filial 02",
        previous_messages=history,
    )


def test_plan_metric_follow_up_after_commercial_kpi():
    history = [
        {"role": "user", "content": "faturamento comercial"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/commercial/billing",
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filtre filial 02",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].metric_kind == "department_kpi"
    assert planned[0].branch == "02"


def test_plan_metric_follow_up_skips_when_fresh_kpi_differs_from_sticky():
    """«meta comercial» não herda sticky de novos negócios só porque citou filial."""
    history = [
        {"role": "user", "content": "meta de novos negócios"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/commercial/branch_new_business_rol_target_pct",
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "qual a meta para comercial desse mês filial 02?",
        previous_messages=history,
    )

    assert planned == []


def test_plan_metric_follow_up_skips_when_other_department_mentioned():
    """«meta engenharia» (mesmo com typo) não herda sticky comercial + filial."""
    from app.domain.services.chat_operational_api_domain_service import (
        invalidate_operational_api_domain_cache,
    )

    invalidate_operational_api_domain_cache()

    history = [
        {"role": "user", "content": "qual a meta para comercial desse mês filial 02?"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/commercial/branch_rol_target_pct",
                        },
                    }
                ]
            },
        },
    ]

    for message in (
        "qual a meta para engenharia desse mês filial 02?",
        "qual a meta para egenharia desse mês filial 02?",
        "qual a meta para financeiro desse mês filial 02?",
    ):
        planned = ChatOperationalRefinementService.plan_metric_follow_ups(
            message,
            previous_messages=history,
        )
        assert planned == [], message


def test_plan_metric_follow_up_keeps_sticky_when_scope_only_after_same_kpi():
    history = [
        {"role": "user", "content": "qual a meta percentual de ROL da filial?"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/commercial/branch_rol_target_pct",
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_metric_follow_ups(
        "filial 02",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "metric_refinement"
    assert planned[0].metric_path_token == "branch_rol_target_pct"
    assert planned[0].branch == "02"


def test_plan_product_route_follow_up_after_structure():
    """Follow-up operacional reutiliza lote recente de sub-rota produto."""
    history = [
        {"role": "user", "content": "estrutura do produto 10080047"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080047/structure",
                        },
                    }
                ]
            },
        },
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "e os pais desse produto",
        previous_messages=history,
    )


def test_plan_pagination_follow_up_increases_page_size():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "parents-action",
                            "parameters": {
                                "code": "10080022",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                            "dataCoverageNotice": {"kind": "pagination"},
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "aumente para 50 linhas",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "pagination_refinement"
    assert planned[0].action_id == "parents-action"
    assert planned[0].page_size == 50
    assert planned[0].page is None


def test_is_operational_follow_up_for_pagination_request():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                        },
                    }
                ]
            },
        },
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "aumente para 50 linhas",
        previous_messages=history,
    )


def test_plan_pagination_follow_up_without_tool_calls_in_history():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "content": "Produtos pai (onde é usado)",
            "metadata": {},
        },
    ]

    planned = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "aumente para 50 linhas",
        conversation_context="path=/products/10080022/parents",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "pagination_refinement"
    assert planned[0].product_code == "10080022"
    assert planned[0].route_segment == "parents"
    assert planned[0].page_size == 50
    assert planned[0].action_id is None


def test_is_operational_follow_up_for_pagination_without_tool_calls():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {"role": "assistant", "content": "Produtos pai (onde é usado)", "metadata": {}},
    ]

    assert ChatOperationalRefinementService.is_operational_follow_up(
        "aumente para 50 linhas",
        conversation_context="path=/products/10080022/parents",
        previous_messages=history,
    )


def test_plan_next_page_follow_up():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "parameters": {
                                "code": "10080022",
                                "page": 1,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                            "dataCoverageNotice": {
                                "kind": "pagination",
                                "details": {
                                    "pagination": {
                                        "page": 1,
                                        "pageSize": 25,
                                        "total": 419,
                                        "totalPages": 17,
                                    }
                                },
                            },
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "proxima pagina",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].page == 2
    assert planned[0].page_size is None


def test_plan_next_page_follow_up_without_tool_calls():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {"role": "assistant", "content": "Produtos pai (onde é usado)", "metadata": {}},
        {"role": "user", "content": "aumente para 50 linhas"},
        {"role": "assistant", "content": "Produtos pai (onde é usado)", "metadata": {}},
    ]

    planned = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "proxima pagina",
        conversation_context="path=/products/10080022/parents",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].page == 2
    assert planned[0].route_segment == "parents"


def test_plan_prev_page_follow_up():
    history = [
        {"role": "user", "content": "onde é usado o 10080022"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "parameters": {
                                "code": "10080022",
                                "page": 2,
                                "page_size": 25,
                            },
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/products/10080022/parents",
                            "actionId": "parents-action",
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "pagina anterior",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].page == 1


def test_plan_next_page_follow_up_for_table_columns_preview():
    history = [
        {"role": "user", "content": "colunas da tabela SB1"},
        {
            "role": "assistant",
            "metadata": {
                "toolCalls": [
                    {
                        "name": "execute_external_action",
                        "arguments": {
                            "actionId": "table-columns-action",
                            "parameters": {"tableName": "SB1"},
                        },
                        "metadata": {
                            "ok": True,
                            "path": "/system/tables/SB1/columns",
                            "actionId": "table-columns-action",
                            "dataCoverageNotice": {
                                "kind": "preview",
                                "message": (
                                    "A tabela exibe 25 linha(s) de 318 registro(s) retornados "
                                    "(prévia limitada a 100)."
                                ),
                                "details": {
                                    "tablePreview": {
                                        "shown": 25,
                                        "total": 318,
                                    }
                                },
                            },
                        },
                    }
                ]
            },
        },
    ]

    planned = ChatOperationalRefinementService.plan_pagination_follow_ups(
        "proxima pagina",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "pagination_refinement"
    assert planned[0].action_id == "table-columns-action"
    assert planned[0].page == 2
    assert planned[0].previous_parameters["tableName"] == "SB1"


def _consumption_top_items_assistant_message(*, group_by: str = "general"):
    return {
        "role": "assistant",
        "content": "Itens mais consumidos",
        "metadata": {
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "arguments": {
                        "actionId": "production-consumption-top-items",
                        "parameters": {
                            "date_start": "2026-03-01",
                            "date_end": "2026-03-31",
                            "limit": 50,
                            "group_by": group_by,
                        },
                    },
                    "metadata": {
                        "ok": True,
                        "path": "/production/consumption/top-items",
                        "actionId": "production-consumption-top-items",
                    },
                }
            ]
        },
    }


def test_plan_consumption_group_follow_up_reuses_top_items_action():
    history = [
        {"role": "user", "content": "Quais são os top 50 itens de maior consumo na produção?"},
        _consumption_top_items_assistant_message(),
    ]

    planned = ChatOperationalRefinementService.plan_operational_group_by_follow_ups(
        "queria um agrupamento por grupo e saber quais deles mais consome da listagem",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].kind == "operational_group_by_refinement"
    assert planned[0].action_id == "production-consumption-top-items"
    assert planned[0].group_by == "product_group"
    assert planned[0].previous_parameters["limit"] == 50


def test_plan_consumption_group_follow_up_skips_when_already_grouped():
    history = [
        _consumption_top_items_assistant_message(group_by="product_group"),
    ]

    planned = ChatOperationalRefinementService.plan_operational_group_by_follow_ups(
        "agrupar por grupo",
        previous_messages=history,
    )

    assert planned == []


def test_detect_consumption_group_refinement_from_history():
    history = [
        _consumption_top_items_assistant_message(),
    ]

    refinement = ChatOperationalRefinementService.detect(
        "colocar grupo e consumo em um gráfico de barras",
        previous_messages=history,
    )

    assert refinement is not None
    assert refinement.kind == "operational_group_by_refinement"
    assert refinement.group_by == "product_group"


def test_plan_operational_group_by_follow_up_for_unit():
    history = [
        _consumption_top_items_assistant_message(),
    ]

    planned = ChatOperationalRefinementService.plan_operational_group_by_follow_ups(
        "consumo por unidade",
        previous_messages=history,
    )

    assert len(planned) == 1
    assert planned[0].group_by == "unit"
