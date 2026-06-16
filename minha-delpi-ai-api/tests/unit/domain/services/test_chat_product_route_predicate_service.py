from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_product_route_predicate_service import (
    ChatProductRoutePredicateService,
)
from app.domain.services.operational_route_matcher_service import (
    OperationalRouteMatcherService,
)


def test_registered_route_predicates_include_product_routes():
    predicates = ChatProductRoutePredicateService.registered_predicates()

    assert "purchasesRoute" in predicates
    assert "productSummaryRoute" in predicates
    assert "genericInvoiceRoute" in predicates


def test_purchases_route_excludes_last_purchase_playbook():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "ultima compra do produto 10080001"
    )

    assert not ChatProductRoutePredicateService.matches("purchasesRoute", normalized)
    assert ChatProductRoutePredicateService.matches(
        "purchasesRoute",
        ChatMessageNormalizationService.normalize_for_matching(
            "historico de compras do produto 10080001"
        ),
    )


def test_product_summary_route_any_of_branches():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "resumo do produto 10080001"
    )

    assert ChatProductRoutePredicateService.matches("productSummaryRoute", normalized)

    assert not ChatProductRoutePredicateService.matches(
        "productSummaryRoute",
        ChatMessageNormalizationService.normalize_for_matching(
            "resumo kaizen do produto 10080001"
        ),
    )


def test_matcher_resolves_route_predicates_from_registry():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "roteiro do produto 90260142"
    )

    assert OperationalRouteMatcherService.matches_custom_predicate(
        "guideRoute",
        normalized,
    )


def test_playbook_predicates_include_directives_and_production():
    predicates = ChatProductRoutePredicateService.registered_predicates()

    assert "directives" in predicates
    assert "productionStatus" in predicates
    assert "lastPurchase" in predicates


def test_directives_playbook_predicate_requires_product_scope():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "diretivas do produto 90260142"
    )

    assert ChatProductRoutePredicateService.matches("directives", normalized)

    assert not ChatProductRoutePredicateService.matches(
        "directives",
        ChatMessageNormalizationService.normalize_for_matching("diretivas em geral"),
    )


def test_factory_status_excludes_production_apontamento():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "O produto 90269002 já tem apontamento na OP?"
    )

    assert not ChatProductRoutePredicateService.matches("factoryStatus", normalized)
    assert ChatProductRoutePredicateService.matches("productionStatus", normalized)


def test_shipping_status_matches_expedicao_with_product_scope():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "Quanto do produto 90269002 já foi liberado para expedição?"
    )

    assert ChatProductRoutePredicateService.matches("shippingStatus", normalized)


def test_sub_intent_stock_and_sales_predicates():
    stock = ChatMessageNormalizationService.normalize_for_matching(
        "estoque do produto 10080001"
    )
    sale_price = ChatMessageNormalizationService.normalize_for_matching(
        "Qual o preço de venda do produto 10080001?"
    )

    assert ChatProductRoutePredicateService.matches("stockQuestion", stock)
    assert not ChatProductRoutePredicateService.matches("salesQuestion", stock)
    assert ChatProductRoutePredicateService.matches("salePricingRoute", sale_price)
    assert not ChatProductRoutePredicateService.matches("salesQuestion", sale_price)


def test_parents_question_regex_from_json():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "onde o produto 90269002 e usado"
    )

    assert ChatProductRoutePredicateService.matches("parentsQuestion", normalized)


def test_domain_predicates_sale_orders_and_lmp():
    sale_orders = ChatMessageNormalizationService.normalize_for_matching(
        "listar ov do periodo"
    )
    lmp = ChatMessageNormalizationService.normalize_for_matching(
        "lmp da ordem de venda 123456"
    )

    assert ChatProductRoutePredicateService.matches("saleOrdersList", sale_orders)
    assert ChatProductRoutePredicateService.matches("lmpQuestion", lmp)
    assert ChatProductRoutePredicateService.matches("lmpHasSaleNumber", lmp)


def test_supplies_otd_domain_predicate():
    normalized = ChatMessageNormalizationService.normalize_for_matching(
        "otd de compras do fornecedor"
    )

    assert ChatProductRoutePredicateService.matches("suppliesOtdRoute", normalized)


def test_system_predicates_metadata_routes():
    columns = ChatMessageNormalizationService.normalize_for_matching(
        "colunas da tabela sb1"
    )
    relations = ChatMessageNormalizationService.normalize_for_matching(
        "relacionamentos da tabela sb1"
    )
    table_search = ChatMessageNormalizationService.normalize_for_matching(
        "qual tabela guarda clientes"
    )

    assert ChatProductRoutePredicateService.matches("systemMetadataQuestion", columns)
    assert ChatProductRoutePredicateService.matches("systemWantsColumns", columns)
    assert ChatProductRoutePredicateService.matches("systemHasTableName", columns)
    assert ChatProductRoutePredicateService.matches("systemWantsRelations", relations)
    assert ChatProductRoutePredicateService.matches("systemWantsTableSearch", table_search)


def test_product_search_predicates_description_and_group():
    by_description = ChatMessageNormalizationService.normalize_for_matching(
        "busque produtos parafuso sextavado"
    )
    by_group = ChatMessageNormalizationService.normalize_for_matching(
        "busque produtos do grupo abc"
    )
    web_query = ChatMessageNormalizationService.normalize_for_matching(
        "pesquise na web sobre delpi conexoes eletricas"
    )
    audit_5s = ChatMessageNormalizationService.normalize_for_matching(
        "liste candidatas a nc 5s"
    )

    assert ChatProductRoutePredicateService.matches("productSearchQuestion", by_description)
    assert ChatProductRoutePredicateService.matches("productSearchWithGroupCode", by_group)
    assert not ChatProductRoutePredicateService.matches("productSearchQuestion", web_query)
    assert not ChatProductRoutePredicateService.matches("productSearchQuestion", audit_5s)
    assert not ChatProductRoutePredicateService.matches(
        "productSearchWithGroupCode",
        by_description,
    )
