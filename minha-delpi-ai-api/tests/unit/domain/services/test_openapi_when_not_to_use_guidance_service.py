from app.domain.services.openapi_when_not_to_use_guidance_service import (
    OpenApiWhenNotToUseGuidanceService,
)


def _scalar_action(**overrides) -> dict:
    payload = {
        "actionId": "ext.metrics.scalar",
        "path": "/metrics/scalar",
        "operationId": "get_metrics_scalar",
        "summary": "Scalar revenue KPI for one site",
        "description": (
            "KPI escalar de receita de um site. Use para «revenue of site X». "
            "Do not use for «revenue by site» tabular breakdown."
        ),
        "whenToUse": "Use for revenue of a specific site as a scalar KPI.",
        "whenNotToUse": (
            "Do not use for «revenue by site» tabular ranking — prefer /metrics/by-site."
        ),
    }
    payload.update(overrides)
    return payload


def _breakdown_action(**overrides) -> dict:
    payload = {
        "actionId": "ext.metrics.by-site",
        "path": "/metrics/by-site",
        "operationId": "get_metrics_by_site",
        "summary": "Revenue breakdown by site",
        "description": (
            "Lista comparando sites. Use para «revenue by site». "
            "Do not use for «revenue of site X» or a single-site scalar KPI."
        ),
        "whenToUse": "Use when the user wants revenue broken down across sites.",
        "whenNotToUse": (
            "Do not use for «revenue of site X» or a single-site scalar KPI "
            "— prefer /metrics/scalar."
        ),
    }
    payload.update(overrides)
    return payload


def test_quoted_negative_matches_single_entity_not_breakdown():
    breakdown = _breakdown_action()
    scalar = _scalar_action()

    assert OpenApiWhenNotToUseGuidanceService.matches_message(
        "What is the revenue of site 01 as a consolidated KPI?",
        breakdown,
    )
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(
        "What is the revenue of site 01 as a consolidated KPI?",
        scalar,
    )


def test_quoted_negative_matches_breakdown_not_scalar():
    breakdown = _breakdown_action()
    scalar = _scalar_action()

    assert OpenApiWhenNotToUseGuidanceService.matches_message(
        "Show revenue by site ranking for the period",
        scalar,
    )
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(
        "Show revenue by site ranking for the period",
        breakdown,
    )


def test_extracts_clause_from_folded_description_without_field():
    action = {
        "description": (
            "Lista tabular curta. Não use para «ROL da filial X», consolidado "
            "financeiro de uma filial — prefira /financial/rol."
        )
    }
    clause = OpenApiWhenNotToUseGuidanceService.resolve(action)
    assert clause.startswith("Não use")
    assert OpenApiWhenNotToUseGuidanceService.matches_message(
        "Qual o ROL da filial 01 em agosto? Quero o consolidado financeiro da filial.",
        action,
    )


def test_description_for_positive_match_strips_negative_clause():
    action = _breakdown_action()
    positive = OpenApiWhenNotToUseGuidanceService.description_for_positive_match(action)
    assert "Lista comparando sites" in positive
    assert "revenue of site X" not in positive
    assert "Do not use" not in positive


def test_negative_does_not_fire_on_unrelated_message():
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(
        "Qual a taxa de fechamento da filial 01?",
        _breakdown_action(),
    )
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(
        "Qual a taxa de fechamento da filial 01?",
        _scalar_action(),
    )


def test_folded_locale_quotes_steer_without_reading_paths():
    financial = {
        "path": "/alpha",
        "description": (
            "KPI escalar de ROL financeiro de uma filial e período. "
            "Use para «ROL da filial», consolidado financeiro da filial. "
            "Não use para ranking/breakdown tabular das filiais 01×02 "
            "(«ROL por filial»)."
        ),
    }
    breakdown = {
        "path": "/beta",
        "description": (
            "Lista tabular curta comparando ROL das filiais. Use para "
            "«ROL por filial». Não use para «ROL da filial X», consolidado "
            "financeiro de uma filial ou KPI escalar."
        ),
    }
    filial_msg = (
        "Qual o ROL da filial 01 em agosto 2026? "
        "Quero o consolidado financeiro da filial."
    )
    por_filial_msg = "Mostre o ROL por filial em agosto 2026, ranking 01 e 02."

    assert OpenApiWhenNotToUseGuidanceService.matches_message(filial_msg, breakdown)
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(filial_msg, financial)
    assert OpenApiWhenNotToUseGuidanceService.matches_positive(filial_msg, financial)
    assert not OpenApiWhenNotToUseGuidanceService.matches_positive(filial_msg, breakdown)
    assert OpenApiWhenNotToUseGuidanceService.matches_message(por_filial_msg, financial)
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(
        por_filial_msg, breakdown
    )


def test_quoted_estoque_saldo_disponivel_match_stock_request():
    sibling = {
        "whenNotToUse": (
            "Do not use when the user asked for «estoque», «saldo» or "
            "«disponível» — prefer /stock."
        )
    }
    stock = {
        "whenToUse": "Use for «estoque», «saldo» or «disponível» of a product code."
    }
    message = "Consulte o estoque do produto 10080001"
    sibling_msg = "Qual o saldo disponível do produto 10080001?"
    assert OpenApiWhenNotToUseGuidanceService.matches_message(message, sibling)
    assert OpenApiWhenNotToUseGuidanceService.matches_positive(message, stock)
    assert OpenApiWhenNotToUseGuidanceService.matches_message(sibling_msg, sibling)
    assert not OpenApiWhenNotToUseGuidanceService.matches_message(
        "inspeção de qualidade do produto 10080001",
        sibling,
    )


def _stock_vs_summary():
    stock = {
        "actionId": "ext.products.stock",
        "whenToUse": "Use for «estoque», «saldo» or «disponível» of a product code.",
        "description": "Stock balance and warehouse positions for a product code.",
    }
    summary = {
        "actionId": "ext.products.summary",
        "whenToUse": "Use for «descrição», «cadastro» or «ficha» of a product.",
        "whenNotToUse": (
            "Do not use when the user asked for «estoque», «saldo» or "
            "«disponível» — prefer the stock action."
        ),
        "description": "Light cadastro overview of a product.",
    }
    return stock, summary


def test_prefer_descricao_keeps_summary_not_stock():
    stock, summary = _stock_vs_summary()
    message = "descrição 10080011"
    kept = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
        message,
        [stock, summary],
        raw_action_of=lambda item: item,
    )
    ids = [item["actionId"] for item in kept]
    assert ids == ["ext.products.summary"]


def test_prefer_compound_estoque_and_descricao_keeps_both():
    stock, summary = _stock_vs_summary()
    kept = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
        "estoque e descrição do produto 10080011",
        [stock, summary],
        raw_action_of=lambda item: item,
    )
    ids = {item["actionId"] for item in kept}
    assert ids == {"ext.products.stock", "ext.products.summary"}


def test_prefer_estoque_keeps_stock_not_summary():
    stock, summary = _stock_vs_summary()
    kept = OpenApiWhenNotToUseGuidanceService.prefer_candidates(
        "Consulte o estoque do produto 10080001",
        [stock, summary],
        raw_action_of=lambda item: item,
    )
    ids = [item["actionId"] for item in kept]
    assert ids == ["ext.products.stock"]


def test_filter_compound_keeps_summary_when_when_to_use_also_matches():
    stock, summary = _stock_vs_summary()
    kept = OpenApiWhenNotToUseGuidanceService.filter_candidates(
        "estoque e descrição do produto 10080011",
        [stock, summary],
        raw_action_of=lambda item: item,
    )
    ids = {item["actionId"] for item in kept}
    assert ids == {"ext.products.stock", "ext.products.summary"}


def test_filter_estoque_only_drops_summary():
    stock, summary = _stock_vs_summary()
    kept = OpenApiWhenNotToUseGuidanceService.filter_candidates(
        "Consulte o estoque do produto 10080001",
        [stock, summary],
        raw_action_of=lambda item: item,
    )
    ids = [item["actionId"] for item in kept]
    assert ids == ["ext.products.stock"]
