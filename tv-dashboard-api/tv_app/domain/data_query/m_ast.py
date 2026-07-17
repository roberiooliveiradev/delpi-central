"""AST imutável do perfil M DELPI v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from .m_diagnostics import SourceRange


@dataclass(frozen=True, slots=True)
class MNode:
    source_range: SourceRange


@dataclass(frozen=True, slots=True)
class MIdentifier(MNode):
    name: str
    quoted: bool = False


@dataclass(frozen=True, slots=True)
class MLiteral(MNode):
    value: str | int | float | bool | None


@dataclass(frozen=True, slots=True)
class MTypeExpression(MNode):
    name: str


@dataclass(frozen=True, slots=True)
class MListExpression(MNode):
    items: tuple["MExpression", ...]


@dataclass(frozen=True, slots=True)
class MRecordField(MNode):
    name: str
    value: "MExpression"


@dataclass(frozen=True, slots=True)
class MRecordExpression(MNode):
    fields: tuple[MRecordField, ...]


@dataclass(frozen=True, slots=True)
class MCallExpression(MNode):
    function_name: str
    arguments: tuple["MExpression", ...]


@dataclass(frozen=True, slots=True)
class MEachExpression(MNode):
    body: "MExpression"


@dataclass(frozen=True, slots=True)
class MIfExpression(MNode):
    condition: "MExpression"
    then_value: "MExpression"
    else_value: "MExpression"


@dataclass(frozen=True, slots=True)
class MBinaryExpression(MNode):
    operator: str
    left: "MExpression"
    right: "MExpression"


@dataclass(frozen=True, slots=True)
class MUnaryExpression(MNode):
    operator: str
    operand: "MExpression"


@dataclass(frozen=True, slots=True)
class MFieldAccess(MNode):
    field_name: str


@dataclass(frozen=True, slots=True)
class MParenthesizedExpression(MNode):
    expression: "MExpression"


@dataclass(frozen=True, slots=True)
class MFunctionExpression(MNode):
    parameters: tuple[str, ...]
    body: "MExpression"


MExpression: TypeAlias = (
    MIdentifier
    | MLiteral
    | MTypeExpression
    | MListExpression
    | MRecordExpression
    | MCallExpression
    | MEachExpression
    | MIfExpression
    | MBinaryExpression
    | MUnaryExpression
    | MFieldAccess
    | MParenthesizedExpression
    | MFunctionExpression
)


@dataclass(frozen=True, slots=True)
class MBinding(MNode):
    name: str
    expression: MExpression
    quoted: bool = False


@dataclass(frozen=True, slots=True)
class MLetExpression(MNode):
    bindings: tuple[MBinding, ...]
    output: MExpression


@dataclass(frozen=True, slots=True)
class MDocument(MNode):
    expression: MLetExpression
