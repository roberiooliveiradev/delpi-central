"""Domínio puro de consultas e planos tabulares."""

from .m_diagnostics import Diagnostic, DiagnosticSeverity, SourceRange
from .m_types import ColumnSchema, ColumnTypeSource, MType, MTypeKind
from .transform_plan import TransformOperation, TransformPlan

__all__ = [
    "ColumnSchema",
    "ColumnTypeSource",
    "Diagnostic",
    "DiagnosticSeverity",
    "MType",
    "MTypeKind",
    "SourceRange",
    "TransformOperation",
    "TransformPlan",
]
