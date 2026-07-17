"""Parser LALR/contextual singleton do perfil M DELPI v1."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from lark import Lark, Token, Transformer, UnexpectedInput, v_args
from lark.visitors import Discard

from tv_app.domain.data_query.m_ast import (
    MBinaryExpression,
    MBinding,
    MCallExpression,
    MDocument,
    MEachExpression,
    MFieldAccess,
    MFunctionExpression,
    MIdentifier,
    MIfExpression,
    MLetExpression,
    MListExpression,
    MLiteral,
    MParenthesizedExpression,
    MRecordExpression,
    MRecordField,
    MTypeExpression,
    MUnaryExpression,
)
from tv_app.domain.data_query.m_diagnostics import (
    Diagnostic,
    DiagnosticSeverity,
    SourceRange,
)

GRAMMAR_PATH = Path(__file__).with_name("m_delpi_v1.lark")


class MParseError(ValueError):
    def __init__(self, diagnostic: Diagnostic) -> None:
        super().__init__(diagnostic.message)
        self.diagnostic = diagnostic


@lru_cache(maxsize=1)
def get_m_parser() -> Lark:
    """Constrói uma única tabela LALR; o lexer contextual limita tokens válidos."""

    return Lark(
        GRAMMAR_PATH.read_text(encoding="utf-8"),
        parser="lalr",
        lexer="contextual",
        propagate_positions=True,
        maybe_placeholders=False,
        start="start",
    )


def m_syntax_tokens(script: str) -> tuple[dict[str, Any], ...]:
    """Expõe classificação léxica server-side para realce sem parser no browser."""

    categories = {
        "LET": "keyword",
        "IN": "keyword",
        "EACH": "keyword",
        "IF": "keyword",
        "THEN": "keyword",
        "ELSE": "keyword",
        "TYPE": "keyword",
        "TRUE": "literal",
        "FALSE": "literal",
        "NULL": "literal",
        "NUMBER": "number",
        "STRING": "string",
        "QUOTED_IDENTIFIER": "identifier",
        "QUALIFIED_IDENTIFIER": "function",
        "IDENTIFIER": "identifier",
    }
    try:
        tokens = get_m_parser().lex(script)
        return tuple(
            {
                "kind": categories.get(str(token.type), "operator"),
                "startOffset": int(token.start_pos),
                "endOffset": int(token.end_pos),
            }
            for token in tokens
            if token.start_pos is not None and token.end_pos is not None
        )
    except UnexpectedInput:
        return ()


def _range(meta: Any) -> SourceRange:
    return SourceRange(
        start_line=meta.line,
        start_column=meta.column,
        end_line=meta.end_line,
        end_column=meta.end_column,
        start_offset=meta.start_pos,
        end_offset=meta.end_pos,
    )


def _decode_quoted(raw: str, *, prefix: int = 1) -> str:
    return raw[prefix + 1 : -1].replace('""', '"')


@v_args(meta=True)
class _AstTransformer(Transformer):
    def LET(self, _token: Token) -> Discard:
        return Discard

    def IN(self, _token: Token) -> Discard:
        return Discard

    def EACH(self, _token: Token) -> Discard:
        return Discard

    def IF(self, _token: Token) -> Discard:
        return Discard

    def THEN(self, _token: Token) -> Discard:
        return Discard

    def ELSE(self, _token: Token) -> Discard:
        return Discard

    def TYPE(self, _token: Token) -> Discard:
        return Discard

    def FAT_ARROW(self, _token: Token) -> Discard:
        return Discard

    def FUNCTION_PARAMS(self, token: Token) -> tuple[str, ...]:
        raw = str(token)[1:-1].strip()
        return tuple(part.strip() for part in raw.split(",") if part.strip())

    def start(self, meta: Any, children: list[Any]) -> MDocument:
        return MDocument(_range(meta), children[0])

    def let_expression(self, meta: Any, children: list[Any]) -> MLetExpression:
        return MLetExpression(_range(meta), tuple(children[:-1]), children[-1])

    def binding(self, meta: Any, children: list[Any]) -> MBinding:
        identifier, _equal, expression = children
        return MBinding(_range(meta), identifier.name, expression, identifier.quoted)

    def simple_identifier(self, meta: Any, children: list[Any]) -> MIdentifier:
        return MIdentifier(_range(meta), str(children[0]), False)

    def quoted_identifier(self, meta: Any, children: list[Any]) -> MIdentifier:
        return MIdentifier(_range(meta), _decode_quoted(str(children[0])), True)

    def shared_identifier(self, meta: Any, _children: list[Any]) -> MIdentifier:
        return MIdentifier(_range(meta), "#shared", False)

    def string(self, meta: Any, children: list[Any]) -> MLiteral:
        return MLiteral(_range(meta), _decode_quoted(str(children[0]), prefix=0))

    def number(self, meta: Any, children: list[Any]) -> MLiteral:
        raw = str(children[0])
        value: int | float = float(raw) if any(char in raw for char in ".eE") else int(raw)
        return MLiteral(_range(meta), value)

    def true(self, meta: Any, _children: list[Any]) -> MLiteral:
        return MLiteral(_range(meta), True)

    def false(self, meta: Any, _children: list[Any]) -> MLiteral:
        return MLiteral(_range(meta), False)

    def null(self, meta: Any, _children: list[Any]) -> MLiteral:
        return MLiteral(_range(meta), None)

    def type_expression(self, meta: Any, children: list[Any]) -> MTypeExpression:
        return MTypeExpression(_range(meta), str(children[0]))

    def argument_list(self, _meta: Any, children: list[Any]) -> tuple[Any, ...]:
        return tuple(children)

    def list_expression(self, meta: Any, children: list[Any]) -> MListExpression:
        items = children[0] if children else ()
        return MListExpression(_range(meta), tuple(items))

    def record_field(self, meta: Any, children: list[Any]) -> MRecordField:
        identifier, _equal, value = children
        return MRecordField(_range(meta), identifier.name, value)

    def record_fields(self, _meta: Any, children: list[Any]) -> tuple[MRecordField, ...]:
        return tuple(children)

    def record_expression(self, meta: Any, children: list[Any]) -> MRecordExpression:
        fields = children[0] if children else ()
        return MRecordExpression(_range(meta), tuple(fields))

    def callable_name(self, _meta: Any, children: list[Any]) -> str:
        return ".".join(item.name for item in children)

    def qualified_symbol(self, meta: Any, children: list[Any]) -> MIdentifier:
        return MIdentifier(_range(meta), ".".join(item.name for item in children), False)

    def call_expression(self, meta: Any, children: list[Any]) -> MCallExpression:
        arguments = children[1] if len(children) > 1 else ()
        return MCallExpression(_range(meta), children[0], tuple(arguments))

    def each_expression(self, meta: Any, children: list[Any]) -> MEachExpression:
        return MEachExpression(_range(meta), children[0])

    def if_expression(self, meta: Any, children: list[Any]) -> MIfExpression:
        return MIfExpression(_range(meta), children[0], children[1], children[2])

    def field_access(self, meta: Any, children: list[Any]) -> MFieldAccess:
        return MFieldAccess(_range(meta), children[0].name)

    def parenthesized(self, meta: Any, children: list[Any]) -> MParenthesizedExpression:
        return MParenthesizedExpression(_range(meta), children[0])

    def function_expression(self, meta: Any, children: list[Any]) -> MFunctionExpression:
        if len(children) == 1:
            return MFunctionExpression(_range(meta), (), children[0])
        return MFunctionExpression(_range(meta), tuple(children[0]), children[-1])

    def unary_not(self, meta: Any, children: list[Any]) -> MUnaryExpression:
        return MUnaryExpression(_range(meta), "not", children[-1])

    def unary_sign(self, meta: Any, children: list[Any]) -> MUnaryExpression:
        return MUnaryExpression(_range(meta), str(children[0]), children[1])

    def _binary(self, meta: Any, children: list[Any]) -> Any:
        current = children[0]
        for index in range(1, len(children), 2):
            current = MBinaryExpression(
                _range(meta),
                str(children[index]),
                current,
                children[index + 1],
            )
        return current

    or_expression = _binary
    and_expression = _binary
    comparison_expression = _binary
    concat_expression = _binary
    additive_expression = _binary
    multiplicative_expression = _binary


def _syntax_range(script: str, exc: UnexpectedInput) -> SourceRange:
    line = max(1, int(getattr(exc, "line", 1) or 1))
    column = max(1, int(getattr(exc, "column", 1) or 1))
    offset = max(0, int(getattr(exc, "pos_in_stream", 0) or 0))
    end_offset = min(len(script), offset + 1)
    return SourceRange(line, column, line, column + max(1, end_offset - offset), offset, end_offset)


def parse_m_script(script: str) -> MDocument:
    try:
        tree = get_m_parser().parse(script)
        return _AstTransformer().transform(tree)
    except UnexpectedInput as exc:
        raise MParseError(
            Diagnostic(
                code="m.syntax_error",
                severity=DiagnosticSeverity.ERROR,
                message="Sintaxe M inválida.",
                source_range=_syntax_range(script, exc),
                hint="Revise o token indicado e a estrutura let … in.",
            )
        ) from exc
