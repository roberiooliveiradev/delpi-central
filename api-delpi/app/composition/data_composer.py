# app/composition/data_composer.py
from app.application.use_cases.data.run_sql_use_case import RunSqlUseCase
from app.infrastructure.persistence.totvs.data_repositories.data_repository import DataRepository


def build_run_sql_use_case():

    repository = DataRepository()

    return RunSqlUseCase(repository)