"""Regressão: writes PAC com histórico precisam de lease único.

Sem ``@plugins_unit_of_work`` / ``with self.db():``, o pool devolve a
conexão com rollback entre os ``execute(auto_commit=False)`` e o
``commit()`` posterior não persiste — a API devolve sucesso
(``deleted: true``) sem excluir o plano.
"""
from __future__ import annotations

from contextlib import contextmanager

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    plugins_unit_of_work,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)
from app.infrastructure.persistence.plugins.repositories.quality_action_plans.quality_action_plan_revision_mixin import (
    QualityActionPlanRevisionMixin,
)


def _assert_unit_of_work(method) -> None:
    assert getattr(method, "__plugins_unit_of_work__", False), (
        f"{method.__qualname__} deve usar @plugins_unit_of_work "
        "(lease único antes de execute(auto_commit=False) em sequência)"
    )


def test_pac_multi_statement_writes_use_unit_of_work() -> None:
    _assert_unit_of_work(PostgresQualityActionPlanRepository.create_plan)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.update_plan)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.update_plan_status)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.reopen_plan)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.delete_plan)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.upsert_ishikawa)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.upsert_five_whys)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.create_actions)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.update_action)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.delete_action)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.submit_effectiveness_review)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.approve_effectiveness_review)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.reject_effectiveness_review)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.record_effectiveness_review)
    _assert_unit_of_work(PostgresQualityActionPlanRepository.upsert_rnc_8d_report)
    _assert_unit_of_work(QualityActionPlanRevisionMixin.restore_plan_revision)


def test_plugins_unit_of_work_opens_lease_when_absent() -> None:
    class FakeRepo(PluginBaseRepository):
        def __init__(self) -> None:
            super().__init__(connection=None)
            self.db_entered = 0

        @contextmanager
        def db(self):
            self.db_entered += 1
            yield object()

        @plugins_unit_of_work
        def mutate(self) -> str:
            return "ok"

    repo = FakeRepo()
    assert repo.mutate() == "ok"
    assert repo.db_entered == 1


def test_plugins_unit_of_work_skips_when_connection_injected() -> None:
    class FakeRepo(PluginBaseRepository):
        def __init__(self) -> None:
            super().__init__(connection=object())
            self.db_entered = 0

        @contextmanager
        def db(self):
            self.db_entered += 1
            yield object()

        @plugins_unit_of_work
        def mutate(self) -> str:
            return "ok"

    repo = FakeRepo()
    assert repo.mutate() == "ok"
    assert repo.db_entered == 0
