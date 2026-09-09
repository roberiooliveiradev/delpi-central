"""PresentationConstraints — extração transversal da mensagem do usuário."""

from app.domain.services.presentation_constraints_extractor_service import (
    PresentationConstraintsExtractorService,
)
from app.domain.services.presentation_composer_policy_service import (
    PresentationComposerPolicyService,
)
from app.domain.services.presentation_intelligence_orchestrator_service import (
    PresentationIntelligenceOrchestratorService,
)


_LONG_MULTI_CONSTRAINT_MESSAGE = (
    "Busque estoque e vendas, compare por filial, "
    "tabela compacta só 3 colunas (filial, produto, saldo), "
    "esconda a coluna unidade, ordene do maior saldo, "
    "destaque saldo baixo, 3 KPIs no topo, "
    "monte um dashboard e coloque na lousa"
)


def test_extracts_multi_constraint_portuguese_message():
    constraints = PresentationConstraintsExtractorService.extract(
        _LONG_MULTI_CONSTRAINT_MESSAGE,
    )

    assert constraints.get("density") == "compact"
    assert constraints.get("columnCount") == 3
    assert "filial" in (constraints.get("fields") or [])
    assert "unidade" in (constraints.get("hiddenFields") or [])
    assert constraints.get("preferCanvas") is True
    assert constraints.get("dashboardPanels") is True
    assert constraints.get("kpiMeasures")
    assert constraints.get("sort") or constraints.get("emphasis")


def test_complex_constraints_invoke_composer_policy():
    constraints = PresentationConstraintsExtractorService.extract(
        _LONG_MULTI_CONSTRAINT_MESSAGE,
    )

    assert PresentationComposerPolicyService.should_invoke(
        summary={"needsComposer": False, "specApplied": False, "bindConfidence": 0.5},
        constraints=constraints,
    )


def test_orchestrator_attaches_presentation_constraints():
    metadata = {
        "path": "/external/stock",
        "chartPresentation": {
            "type": "chart",
            "chartType": "bar",
            "title": "Estoque",
            "data": [{"branch": "01", "balance": 10}],
            "config": {},
        },
    }

    PresentationIntelligenceOrchestratorService.apply_before_render_plan(
        metadata,
        user_message=_LONG_MULTI_CONSTRAINT_MESSAGE,
    )

    constraints = metadata.get("presentationConstraints")
    assert isinstance(constraints, dict)
    assert constraints.get("density") == "compact"
    assert constraints.get("preferCanvas") is True
    assert metadata.get("presentationIntelligence", {}).get("constraintsPresent") is True
