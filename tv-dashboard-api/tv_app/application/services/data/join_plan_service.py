"""Descoberta determinística de chaves de merge entre schemas tabulares."""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from tv_app.domain.presentation_intelligence.models import JoinPlanProposal

# Ordem = preferência (maior prioridade primeiro).
_PREFERRED_KEYS: tuple[str, ...] = (
    "branch",
    "filial",
    "codfilial",
    "codigo",
    "code",
    "sku",
    "id",
    "idd",
    "n_op",
    "nop",
    "op",
    "periodo",
    "period",
    "data",
    "date",
    "produto",
    "product",
    "cliente",
    "customer",
)


def _norm(name: str) -> str:
    return "".join(ch for ch in str(name or "").strip().lower() if ch.isalnum() or ch == "_")


def _column_map(columns: Sequence[str] | None) -> dict[str, str]:
    """normalized → original column name (first wins)."""
    out: dict[str, str] = {}
    for raw in columns or ():
        original = str(raw or "").strip()
        if not original:
            continue
        key = _norm(original)
        if key and key not in out:
            out[key] = original
    return out


class JoinPlanService:
    """Owner canônico de join-key discovery (VISTA + Data Builder)."""

    MIN_CONFIDENCE = 0.55

    @classmethod
    def preferred_keys(cls) -> tuple[str, ...]:
        return _PREFERRED_KEYS

    @classmethod
    def candidate_keys_from_columns(
        cls, columns: Sequence[str] | None, *, limit: int = 5
    ) -> list[str]:
        """Colunas da amostra que são boas candidatas a chave de merge."""
        col_map = _column_map(columns)
        if not col_map:
            return []
        preferred = {_norm(k): i for i, k in enumerate(_PREFERRED_KEYS)}
        ranked = sorted(
            col_map.keys(),
            key=lambda name: (
                preferred.get(name, 10_000),
                len(name),
                name,
            ),
        )
        out: list[str] = []
        for norm_name in ranked:
            if norm_name not in preferred and len(out) >= 1:
                # Após preferidas, no máximo 1 genérica.
                if len(out) >= limit:
                    break
            out.append(col_map[norm_name])
            if len(out) >= limit:
                break
        return out

    @classmethod
    def propose(
        cls,
        *,
        left_columns: Sequence[str] | None,
        right_columns: Sequence[str] | None,
        preferred_left_key: str | None = None,
        preferred_right_key: str | None = None,
    ) -> JoinPlanProposal | None:
        left_map = _column_map(left_columns)
        right_map = _column_map(right_columns)
        diagnostics: list[str] = []

        if preferred_left_key and preferred_right_key:
            lk = str(preferred_left_key).strip()
            rk = str(preferred_right_key).strip()
            if lk and rk:
                left_ok = _norm(lk) in left_map or not left_map
                right_ok = _norm(rk) in right_map or not right_map
                if left_ok and right_ok:
                    return JoinPlanProposal(
                        left_key=left_map.get(_norm(lk), lk),
                        right_key=right_map.get(_norm(rk), rk),
                        confidence=1.0,
                        diagnostics=("explicit_keys",),
                    )
                diagnostics.append("explicit_keys_missing_from_schema")

        if not left_map or not right_map:
            diagnostics.append("missing_column_schema")
            # Sem schema: não inventar chave arbitrária.
            return None

        common = sorted(set(left_map) & set(right_map))
        if not common:
            diagnostics.append("no_common_columns")
            return None

        ranked = cls._rank_common(common)
        best_norm = ranked[0]
        confidence = cls._confidence(best_norm, common)
        diagnostics.append(f"matched:{best_norm}")
        return JoinPlanProposal(
            left_key=left_map[best_norm],
            right_key=right_map[best_norm],
            confidence=confidence,
            diagnostics=tuple(diagnostics),
        )

    @classmethod
    def _rank_common(cls, common: Iterable[str]) -> list[str]:
        preferred_index = {_norm(k): i for i, k in enumerate(_PREFERRED_KEYS)}
        return sorted(
            common,
            key=lambda name: (
                preferred_index.get(name, 10_000),
                len(name),
                name,
            ),
        )

    @classmethod
    def _confidence(cls, best_norm: str, common: Sequence[str]) -> float:
        preferred = {_norm(k) for k in _PREFERRED_KEYS}
        if best_norm in preferred:
            return 0.92 if len(common) == 1 else 0.85
        if len(common) == 1:
            return 0.7
        return 0.58

    @classmethod
    def merge_step_for_source(
        cls,
        proposal: JoinPlanProposal,
        *,
        source_id: str,
    ) -> dict[str, Any]:
        return {
            "op": "merge",
            "sourceId": str(source_id).strip(),
            "leftKey": proposal.left_key,
            "rightKey": proposal.right_key,
            "join": proposal.join or "left",
        }
