"""Tipos puros do perfil M DELPI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class MTypeKind(StrEnum):
    ANY = "any"
    NULL = "null"
    TEXT = "text"
    NUMBER = "number"
    LOGICAL = "logical"
    DATE = "date"
    DATETIME = "datetime"
    DURATION = "duration"
    TABLE = "table"
    LIST = "list"
    RECORD = "record"
    ERROR = "error"


class ColumnTypeSource(StrEnum):
    DECLARED = "declared"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class MType:
    kind: MTypeKind
    nullable: bool = False


@dataclass(frozen=True, slots=True)
class ColumnSchema:
    key: str
    label: str
    m_type: MType
    type_source: ColumnTypeSource = ColumnTypeSource.UNKNOWN

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("ColumnSchema.key é obrigatório.")

    def to_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "label": self.label or self.key,
            "type": self.m_type.kind.value,
            "nullable": self.m_type.nullable,
            "typeSource": self.type_source.value,
        }
