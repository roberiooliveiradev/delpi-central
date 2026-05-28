from si_app.application.dto.strategic_indicators.catalog_models import (
    StrategicDepartmentCatalogItem,
    StrategicIndicatorCatalogItem,
)
from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_resolved_indicators_catalog_repository import (
    PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository,
)


class _FakeCatalogRepository:
    def list_structural_indicators_catalog(self, *, department_id=None):
        return [
            StrategicIndicatorCatalogItem(
                indicator_id="rol-novos",
                department_id="commercial",
                indicator_name="% ROL de Novos Negócios",
                weight_pct=15,
                goal_label="Meta",
                goal_value=0.0,
                goal_periodicity="monthly",
                goal_mode="standard",
                monthly_targets=[],
                scope_type="per_unit",
                performance_direction="higher_is_better",
                strategic_description="",
                source_key="",
                value_unit="percent",
                value_prefix=None,
                value_suffix=None,
                value_decimals=2,
                branch_goals={},
                resolved_goal_scope_branch="",
                has_resolved_goal=False,
            )
        ]

    def list_departments_catalog(self):
        return [
            StrategicDepartmentCatalogItem(
                department_id="commercial",
                department_name="Comercial",
                short_name="Comercial",
                weight_pct=40,
                strategic_summary="",
                aggregation_mode="average_of_units",
            )
        ]


class _FakeIndicatorGoalsRepository:
    def list_latest_active_goals_map(
        self,
        *,
        indicator_ids,
        department_id,
        competence,
        start_date,
        end_date,
        scope_branch,
    ):
        return {}

    def list_latest_goals_ignoring_validity(
        self,
        *,
        indicator_ids,
        department_id,
        competence,
        scope_branch,
    ):
        return {}

    def list_branch_scoped_goals_map(
        self,
        *,
        indicator_ids,
        department_id,
        competence,
        start_date,
        end_date,
    ):
        assert indicator_ids == ["rol-novos"] or indicator_ids == ["rol-novos"]
        return {
            "rol-novos": {
                "01": {
                    "goal_label": "Meta",
                    "goal_value": 12.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
                "02": {
                    "goal_label": "Meta",
                    "goal_value": 12.0,
                    "goal_periodicity": "monthly",
                    "goal_mode": "standard",
                    "monthly_targets": [],
                },
            }
        }

    def list_branch_scoped_goals_ignoring_validity(
        self,
        *,
        indicator_ids,
        department_id,
        competence,
        start_date,
        end_date,
    ):
        return {}

    def list_resolved_goals_map(
        self,
        *,
        competence,
        start_date,
        end_date,
        department_id,
        scope_branch,
    ):
        # Simula cenário atual: a visão por filial não encontra goal "resolvido" no modelo antigo,
        # ficando dependente exclusivamente das metas por filial.
        return {}


def test_resolved_catalog_branch_view_uses_branch_scoped_goals_for_per_unit():
    # Evita inicializar conexão real do repositório (env de DB pode não existir no ambiente de teste).
    repo = object.__new__(PostgresStrategicIndicatorsResolvedIndicatorsCatalogRepository)
    repo._catalog_repository = _FakeCatalogRepository()
    repo._indicator_goals_repository = _FakeIndicatorGoalsRepository()

    items = repo.list_resolved_indicators_catalog(
        competence="2026-05",
        start_date=None,
        end_date=None,
        department_id="commercial",
        branch="02",
    )

    assert len(items) == 1
    indicator = items[0]

    assert indicator.has_resolved_goal is True
    assert indicator.resolved_goal_scope_branch == "02"
    assert indicator.goal_value == 12.0
    assert "02" in (indicator.branch_goals or {})
