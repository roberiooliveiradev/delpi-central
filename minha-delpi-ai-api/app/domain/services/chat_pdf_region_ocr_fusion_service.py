"""Fusão de texto OCR multi-motor por região de desenho."""

from __future__ import annotations

import re
from typing import Any, Iterable

from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)
from app.domain.services.chat_drawing_patterns_service import ChatDrawingPatternsService


class ChatPdfRegionOcrFusionService:
    @classmethod
    def fuse(cls, texts: Iterable[str]) -> str:
        ordered: list[str] = []

        for text in texts:
            stripped = str(text or "").strip()

            if stripped:
                ordered.append(stripped)

        if not ordered:
            return ""

        if len(ordered) == 1:
            return ordered[0]

        lines: list[str] = []
        seen: set[str] = set()
        code_pattern = ChatDrawingPatternsService.component_code()

        def line_score(line: str) -> tuple[int, int]:
            codes = code_pattern.findall(line)
            return (len(codes), len(line))

        candidates: dict[str, str] = {}

        for source in ordered:
            for line in source.splitlines():
                token = line.strip()

                if not token:
                    continue

                key = re.sub(r"\s+", " ", token.upper())

                existing = candidates.get(key)

                if not existing or line_score(token) > line_score(existing):
                    candidates[key] = token

        for token in sorted(
            candidates.values(),
            key=lambda value: (-line_score(value)[0], -line_score(value)[1], value),
        ):
            key = re.sub(r"\s+", " ", token.upper())

            if key in seen:
                continue

            seen.add(key)
            lines.append(token)

        return "\n".join(lines)

    @classmethod
    def fuse_bom(
        cls,
        by_engine: dict[str, str],
        *,
        code_tokens_by_engine: dict[str, list[dict[str, Any]]] | None = None,
    ) -> str:
        if not by_engine:
            return ""

        if len(by_engine) == 1:
            only = next(iter(by_engine.values())).strip()
            return cls._refine_bom_lines(
                only,
                by_engine,
                code_tokens_by_engine=code_tokens_by_engine,
            )

        code_pattern = ChatDrawingPatternsService.component_code()
        weights = ChatDocumentVisionContentService.pdf_bom_engine_weights()

        def line_score(line: str, *, engine: str) -> tuple[float, int, int]:
            codes = code_pattern.findall(line)
            engine_weight = float(weights.get(engine, 1.0))
            return (engine_weight * (1 + len(codes)), len(codes), len(line))

        candidates: dict[str, tuple[str, str]] = {}

        for engine, source in by_engine.items():
            for line in str(source or "").splitlines():
                token = line.strip()

                if not token:
                    continue

                key = re.sub(r"\s+", " ", token.upper())
                existing = candidates.get(key)

                if not existing or line_score(token, engine=engine) > line_score(
                    existing[0],
                    engine=existing[1],
                ):
                    candidates[key] = (token, engine)

        clustered = cls._cluster_close_bom_lines(
            list(candidates.values()),
            code_pattern=code_pattern,
            max_edits=ChatDocumentVisionContentService.pdf_bom_fusion_max_digit_edits(),
            line_score=line_score,
        )

        lines: list[str] = []
        seen: set[str] = set()

        for token, _engine in sorted(
            clustered,
            key=lambda item: (
                -line_score(item[0], engine=item[1])[0],
                -line_score(item[0], engine=item[1])[1],
                item[0],
            ),
        ):
            key = re.sub(r"\s+", " ", token.upper())

            if key in seen:
                continue

            seen.add(key)
            lines.append(token)

        merged = "\n".join(lines)
        return cls._refine_bom_lines(
            merged,
            by_engine,
            code_tokens_by_engine=code_tokens_by_engine,
        )

    @classmethod
    def _refine_bom_lines(
        cls,
        fused_text: str,
        by_engine: dict[str, str],
        *,
        code_tokens_by_engine: dict[str, list[dict[str, Any]]] | None = None,
    ) -> str:
        if not fused_text.strip() or len(by_engine) < 2:
            return fused_text

        code_pattern = ChatDrawingPatternsService.component_code()
        weights = ChatDocumentVisionContentService.pdf_bom_engine_weights()
        max_edits = ChatDocumentVisionContentService.pdf_bom_fusion_max_digit_edits()
        tokens_by_engine = code_tokens_by_engine or {}

        refined_lines: list[str] = []

        for line in fused_text.splitlines():
            engine_lines = cls._matching_engine_lines(
                line,
                by_engine,
                code_pattern=code_pattern,
                max_edits=max_edits,
            )
            refined_lines.append(
                cls._refine_line_codes(
                    line,
                    engine_lines,
                    code_tokens_by_engine=tokens_by_engine,
                    max_edits=max_edits,
                    code_pattern=code_pattern,
                    weights=weights,
                )
            )

        return "\n".join(refined_lines)

    @classmethod
    def _cluster_close_bom_lines(
        cls,
        lines: list[tuple[str, str]],
        *,
        code_pattern: re.Pattern[str],
        max_edits: int,
        line_score: Any,
    ) -> list[tuple[str, str]]:
        clusters: list[list[tuple[str, str]]] = []

        for line, engine in lines:
            fused_codes = [match.group(1) for match in code_pattern.finditer(line)]
            placed = False

            for cluster in clusters:
                anchor_line, _anchor_engine = cluster[0]
                anchor_codes = [
                    match.group(1) for match in code_pattern.finditer(anchor_line)
                ]

                if len(anchor_codes) != len(fused_codes):
                    continue

                if all(
                    cls._codes_are_close(left, right, max_edits=max_edits)
                    for left, right in zip(anchor_codes, fused_codes)
                ):
                    cluster.append((line, engine))
                    placed = True
                    break

            if not placed:
                clusters.append([(line, engine)])

        resolved: list[tuple[str, str]] = []

        for cluster in clusters:
            resolved.append(
                max(
                    cluster,
                    key=lambda item: (
                        line_score(item[0], engine=item[1])[0],
                        line_score(item[0], engine=item[1])[1],
                    ),
                )
            )

        return resolved

    @classmethod
    def _matching_engine_lines(
        cls,
        fused_line: str,
        by_engine: dict[str, str],
        *,
        code_pattern: re.Pattern[str],
        max_edits: int,
    ) -> dict[str, str]:
        line_key = re.sub(r"\s+", " ", fused_line.strip().upper())
        fused_codes = [match.group(1) for match in code_pattern.finditer(fused_line)]
        matches: dict[str, str] = {}

        for engine, source in by_engine.items():
            for line in str(source or "").splitlines():
                token = line.strip()

                if not token:
                    continue

                if re.sub(r"\s+", " ", token.upper()) == line_key:
                    matches[engine] = token
                    break

                if not fused_codes:
                    continue

                engine_codes = [match.group(1) for match in code_pattern.finditer(token)]

                if len(engine_codes) != len(fused_codes):
                    continue

                if all(
                    cls._codes_are_close(left, right, max_edits=max_edits)
                    for left, right in zip(fused_codes, engine_codes)
                ):
                    matches[engine] = token
                    break

        return matches

    @classmethod
    def _refine_line_codes(
        cls,
        line: str,
        engine_lines: dict[str, str],
        *,
        code_tokens_by_engine: dict[str, list[dict[str, Any]]],
        max_edits: int,
        code_pattern: re.Pattern[str],
        weights: dict[str, float],
    ) -> str:
        if not engine_lines:
            return line

        fused_codes = [match.group(1) for match in code_pattern.finditer(line)]

        if not fused_codes:
            return line

        engine_code_lists: dict[str, list[str]] = {
            engine: [match.group(1) for match in code_pattern.finditer(engine_line)]
            for engine, engine_line in engine_lines.items()
        }

        refined = line

        for code_index, fused_code in enumerate(fused_codes):
            variants: list[tuple[str, float]] = []

            for engine, codes in engine_code_lists.items():
                if code_index >= len(codes):
                    continue

                candidate = codes[code_index]

                if not cls._codes_are_close(fused_code, candidate, max_edits=max_edits):
                    continue

                confidence = cls._lookup_token_confidence(
                    code_tokens_by_engine,
                    engine=engine,
                    code=candidate,
                    code_index=code_index,
                )
                variants.append(
                    (
                        candidate,
                        float(weights.get(engine, 1.0)) * confidence,
                    )
                )

            if len({code for code, _weight in variants}) <= 1:
                continue

            merged_code = cls._vote_code_digits(variants)

            if merged_code and merged_code != fused_code:
                refined = refined.replace(fused_code, merged_code, 1)

        return refined

    @classmethod
    def _lookup_token_confidence(
        cls,
        code_tokens_by_engine: dict[str, list[dict[str, Any]]],
        *,
        engine: str,
        code: str,
        code_index: int,
    ) -> float:
        for token in code_tokens_by_engine.get(engine) or []:
            if not isinstance(token, dict):
                continue

            if (
                str(token.get("code") or "") == code
                and int(token.get("codeIndex") or -1) == code_index
            ):
                confidence = float(token.get("confidence") or 0.0)
                return confidence if confidence > 0 else 1.0

        return 1.0

    @classmethod
    def _codes_are_close(cls, left: str, right: str, *, max_edits: int) -> bool:
        if left == right:
            return True

        if len(left) != len(right):
            return False

        edits = sum(a != b for a, b in zip(left, right))
        return 0 < edits <= max_edits

    @classmethod
    def _vote_code_digits(cls, variants: list[tuple[str, float]]) -> str:
        if not variants:
            return ""

        unique_codes = {code for code, _weight in variants}

        if len(unique_codes) == 1:
            return next(iter(unique_codes))

        length = len(variants[0][0])
        digits: list[str] = []

        for position in range(length):
            votes: dict[str, float] = {}

            for code, weight in variants:
                if len(code) != length:
                    continue

                digit = code[position]
                votes[digit] = votes.get(digit, 0.0) + max(weight, 0.0)

            if not votes:
                digits.append(variants[0][0][position])
                continue

            digits.append(max(votes.items(), key=lambda item: item[1])[0])

        return "".join(digits)
