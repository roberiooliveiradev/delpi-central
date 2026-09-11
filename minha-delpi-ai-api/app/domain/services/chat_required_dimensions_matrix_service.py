"""Matriz canônica de requiredDimensions (chat-ai-flow-families.md §4).

A matriz é authority. O corpus não pode declarar menos dimensões do que a
classe de risco exige. Condicionais do doc (§4) são materializados no máximo
seguro da classe quando o caso envolve tools/args/surfaces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

SOURCE_DOC = "docs/testing/chat-ai-flow-families.md#4-dimensoes-minimas-por-classe-de-teste"

# Chaves estáveis (inglês) ↔ classes §4.
CANONICAL_REQUIRED_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "direct_answer": ("R1", "R2", "R4", "R8", "R11"),
    "action_openapi_read": ("R1", "R2", "R3", "R4", "R8", "R9", "R10", "R11"),
    "action_write_admin_destructive": (
        "R1",
        "R2",
        "R3",
        "R4",
        "R8",
        "R9",
        "R10",
        "R11",
    ),
    "rag": ("R1", "R4", "R6", "R8", "R9", "R10", "R11"),
    # Follow-up com tool+args (interpretação segura das condicionais §4).
    "follow_up_multi_turn": ("R1", "R2", "R3", "R4", "R6", "R8", "R9", "R11"),
    "presentation": ("R4", "R5", "R8", "R9"),
    "presentation_multi_surface": ("R4", "R5", "R7", "R8", "R9"),
    # Simulate/paridade com tools.
    "simulate_parity": ("R1", "R2", "R3", "R4", "R6", "R7", "R9", "R10"),
    "compound": ("R1", "R2", "R3", "R4", "R6", "R8", "R9", "R10", "R11"),
    # Security com tool path.
    "security_adversarial": ("R2", "R3", "R4", "R10", "R11"),
}

# Mapeamento dos classId do corpus R1–R11 → classe da matriz §4.
CORPUS_CLASS_ID_TO_MATRIX_CLASS: dict[int, str] = {
    1: "action_openapi_read",  # specific vs generic
    2: "action_openapi_read",  # semantic siblings
    3: "action_openapi_read",  # multi-provider
    4: "direct_answer",  # no-tool
    5: "action_openapi_read",  # required present
    6: "action_openapi_read",  # required missing
    7: "action_openapi_read",  # enum/type
    8: "compound",
    9: "follow_up_multi_turn",
    10: "action_openapi_read",  # typo/synonym
    11: "action_openapi_read",  # unknown external OpenAPI
    12: "action_openapi_read",  # metamorphic rename
    13: "security_adversarial",  # unauthorized
    14: "action_write_admin_destructive",
    15: "security_adversarial",  # injection
    16: "presentation",
    17: "action_openapi_read",  # recommendations grounded (pós-action)
    18: "simulate_parity",
    19: "follow_up_multi_turn",  # persist/reload
    20: "compound",  # partial failure / goal coverage
}


@dataclass(frozen=True)
class RequiredDimensionsCaseFinding:
    case_id: str
    class_id: int | None
    matrix_class: str | None
    declared: tuple[str, ...]
    required_minimum: tuple[str, ...]
    missing: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.missing and self.matrix_class is not None


@dataclass(frozen=True)
class RequiredDimensionsCorpusReport:
    dataset_version: str | None
    findings: tuple[RequiredDimensionsCaseFinding, ...]
    source_doc: str = SOURCE_DOC

    @property
    def ok(self) -> bool:
        return bool(self.findings) and all(f.ok for f in self.findings)

    @property
    def failing(self) -> tuple[RequiredDimensionsCaseFinding, ...]:
        return tuple(f for f in self.findings if not f.ok)

    def as_dict(self) -> dict[str, Any]:
        return {
            "datasetVersion": self.dataset_version,
            "sourceDoc": self.source_doc,
            "ok": self.ok,
            "failingCount": len(self.failing),
            "findings": [
                {
                    "caseId": f.case_id,
                    "classId": f.class_id,
                    "matrixClass": f.matrix_class,
                    "declared": list(f.declared),
                    "requiredMinimum": list(f.required_minimum),
                    "missing": list(f.missing),
                    "ok": f.ok,
                }
                for f in self.findings
            ],
        }


class ChatRequiredDimensionsMatrixService:
    """Valida corpus contra a matriz canônica §4."""

    @classmethod
    def minimum_for_matrix_class(cls, matrix_class: str) -> tuple[str, ...]:
        key = str(matrix_class or "").strip()
        dims = CANONICAL_REQUIRED_DIMENSIONS.get(key)
        if dims is None:
            raise KeyError(f"matrix class desconhecida: {matrix_class!r}")
        return dims

    @classmethod
    def matrix_class_for_corpus_class_id(cls, class_id: int) -> str | None:
        return CORPUS_CLASS_ID_TO_MATRIX_CLASS.get(int(class_id))

    @classmethod
    def missing_dimensions(
        cls,
        declared: Iterable[str],
        *,
        matrix_class: str,
    ) -> tuple[str, ...]:
        required = cls.minimum_for_matrix_class(matrix_class)
        have = {str(d).strip().upper() for d in declared if str(d).strip()}
        return tuple(d for d in required if d not in have)

    @classmethod
    def validate_case(cls, case: dict[str, Any]) -> RequiredDimensionsCaseFinding:
        case_id = str(case.get("id") or "").strip() or "<missing-id>"
        raw_class = case.get("classId")
        class_id = int(raw_class) if isinstance(raw_class, (int, float, str)) and str(raw_class).isdigit() else None
        matrix_class = str(case.get("matrixClass") or "").strip() or None
        if matrix_class is None and class_id is not None:
            matrix_class = cls.matrix_class_for_corpus_class_id(class_id)

        declared_list = case.get("requiredDimensions") or []
        if not isinstance(declared_list, list):
            declared_list = []
        declared = tuple(str(d).strip().upper() for d in declared_list if str(d).strip())

        if matrix_class is None or matrix_class not in CANONICAL_REQUIRED_DIMENSIONS:
            return RequiredDimensionsCaseFinding(
                case_id=case_id,
                class_id=class_id,
                matrix_class=matrix_class,
                declared=declared,
                required_minimum=(),
                missing=("MATRIX_CLASS_UNRESOLVED",),
            )

        required = cls.minimum_for_matrix_class(matrix_class)
        missing = cls.missing_dimensions(declared, matrix_class=matrix_class)
        return RequiredDimensionsCaseFinding(
            case_id=case_id,
            class_id=class_id,
            matrix_class=matrix_class,
            declared=declared,
            required_minimum=required,
            missing=missing,
        )

    @classmethod
    def validate_corpus(cls, corpus: dict[str, Any]) -> RequiredDimensionsCorpusReport:
        cases = corpus.get("cases") if isinstance(corpus, dict) else None
        if not isinstance(cases, list):
            cases = []
        findings = tuple(cls.validate_case(case) for case in cases if isinstance(case, dict))
        return RequiredDimensionsCorpusReport(
            dataset_version=str(corpus.get("datasetVersion") or "") or None,
            findings=findings,
        )
