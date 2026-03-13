# app/application/dto/system_requests.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class GetTableRequest:
    table_name: str


@dataclass
class ListTableColumnsRequest:
    table_name: str
    page: int = 1
    limit: int = 50


@dataclass
class SearchTablesByDescriptionRequest:
    description: str
    page: int = 1
    limit: int = 20


@dataclass
class GetTableIndexesRequest:
    table_name: str


@dataclass
class GetTableRelationsRequest:
    table_name: str


@dataclass
class GetTableSchemaRequest:
    table_name: str


@dataclass
class SearchColumnsInTableRequest:
    table_name: str
    text: str


@dataclass
class SearchColumnsByDescriptionRequest:
    description: str
    page: int = 1
    limit: int = 20
    