# app/composition/system_composer.py

from app.infrastructure.persistence.totvs.system_repositories.system_repository import SystemRepository

from app.application.use_cases.system.get_table_use_case import GetTableUseCase
from app.application.use_cases.system.list_table_columns_use_case import ListTableColumnsUseCase
from app.application.use_cases.system.search_tables_by_description_use_case import SearchTablesByDescriptionUseCase
from app.application.use_cases.system.get_table_indexes_use_case import GetTableIndexesUseCase
from app.application.use_cases.system.get_table_relations_use_case import GetTableRelationsUseCase
from app.application.use_cases.system.search_columns_in_table_use_case import SearchColumnsInTableUseCase
from app.application.use_cases.system.search_columns_by_description_use_case import SearchColumnsByDescriptionUseCase
from app.application.use_cases.system.get_table_schema_use_case import GetTableSchemaUseCase


def _build_system_repository() -> SystemRepository:
    return SystemRepository()


def build_get_table_use_case() -> GetTableUseCase:
    return GetTableUseCase(_build_system_repository())


def build_list_table_columns_use_case() -> ListTableColumnsUseCase:
    return ListTableColumnsUseCase(_build_system_repository())


def build_search_tables_by_description_use_case() -> SearchTablesByDescriptionUseCase:
    return SearchTablesByDescriptionUseCase(_build_system_repository())


def build_get_table_indexes_use_case() -> GetTableIndexesUseCase:
    return GetTableIndexesUseCase(_build_system_repository())


def build_get_table_relations_use_case() -> GetTableRelationsUseCase:
    return GetTableRelationsUseCase(_build_system_repository())


def build_search_columns_in_table_use_case() -> SearchColumnsInTableUseCase:
    return SearchColumnsInTableUseCase(_build_system_repository())


def build_search_columns_by_description_use_case() -> SearchColumnsByDescriptionUseCase:
    return SearchColumnsByDescriptionUseCase(_build_system_repository())


def build_get_table_schema_use_case() -> GetTableSchemaUseCase:
    return GetTableSchemaUseCase(_build_system_repository())