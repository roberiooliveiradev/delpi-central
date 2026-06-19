"""Fusão multi-fonte de texto PDF — chat base (embedded, pypdf, OCR, regiões)."""

from __future__ import annotations

from typing import Any


class ChatPdfTextFusionService:
    @classmethod
    def fuse(
        cls,
        sources: list[dict[str, Any]],
        *,
        min_embedded_chars: int = 80,
    ) -> dict[str, Any]:
        ranked = cls._rank_sources(sources, min_embedded_chars=min_embedded_chars)

        if not ranked:
            return {
                "fullText": "",
                "charCount": 0,
                "primarySource": None,
                "sources": [],
            }

        primary = ranked[0]
        full_text = str(primary.get("text") or "").strip()
        primary_name = str(primary.get("name") or "unknown")
        used_names = {primary_name}

        for candidate in ranked[1:]:
            name = str(candidate.get("name") or "")
            text = str(candidate.get("text") or "").strip()

            if not text or name in used_names:
                continue

            if cls._should_merge_supplement(full_text, text, candidate):
                full_text = cls._merge_texts(full_text, text)
                used_names.add(name)

        return {
            "fullText": full_text,
            "charCount": len(full_text),
            "primarySource": primary_name,
            "sources": [
                {
                    "name": str(item.get("name") or ""),
                    "charCount": len(str(item.get("text") or "")),
                    "score": int(item.get("score") or 0),
                    "used": str(item.get("name") or "") in used_names,
                }
                for item in ranked
            ],
        }

    @classmethod
    def _rank_sources(
        cls,
        sources: list[dict[str, Any]],
        *,
        min_embedded_chars: int,
    ) -> list[dict[str, Any]]:
        ranked: list[dict[str, Any]] = []

        for source in sources:
            if not isinstance(source, dict):
                continue

            text = str(source.get("text") or "").strip()

            if not text:
                continue

            name = str(source.get("name") or "unknown")
            score = int(source.get("score") or 0)
            char_count = len(text)

            if name == "fitz_embedded":
                score += 40

                if char_count >= min_embedded_chars:
                    score += 30

                if int(source.get("annotationCount") or 0) > 0:
                    score += min(50, int(source.get("annotationCount") or 0))

            elif name == "fitz_embedded_annotations":
                score += 35

            elif name == "pypdf":
                score += 10

            elif name.endswith("_region"):
                score += 20

            ranked.append({**source, "text": text, "score": score})

        ranked.sort(
            key=lambda item: (int(item.get("score") or 0), len(str(item.get("text") or ""))),
            reverse=True,
        )

        return ranked

    @classmethod
    def _should_merge_supplement(
        cls,
        primary_text: str,
        supplement_text: str,
        candidate: dict[str, Any],
    ) -> bool:
        name = str(candidate.get("name") or "")

        if name.endswith("_region"):
            return supplement_text not in primary_text

        if len(supplement_text) < 40:
            return False

        overlap = cls._overlap_ratio(primary_text, supplement_text)

        return overlap < 0.65

    @classmethod
    def _overlap_ratio(cls, left: str, right: str) -> float:
        left_lines = {line.strip() for line in left.splitlines() if line.strip()}
        right_lines = {line.strip() for line in right.splitlines() if line.strip()}

        if not right_lines:
            return 1.0

        shared = left_lines & right_lines

        return len(shared) / float(len(right_lines))

    @classmethod
    def _merge_texts(cls, primary: str, supplement: str) -> str:
        if supplement in primary:
            return primary

        return f"{primary}\n\n{supplement}".strip()
