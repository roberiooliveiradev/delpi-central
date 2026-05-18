import hashlib
import re


class KnowledgeChunkDeduplicatorService:
    _NORMALIZE_PATTERN = re.compile(r"\s+")

    def dedupe(self, chunks: list[str]) -> tuple[list[str], int]:
        unique: list[str] = []
        seen_hashes: set[str] = set()
        removed = 0

        for chunk in chunks:
            normalized = self._normalize(chunk)

            if not normalized:
                removed += 1
                continue

            digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

            if digest in seen_hashes:
                removed += 1
                continue

            seen_hashes.add(digest)
            unique.append(chunk.strip())

        return unique, removed

    def _normalize(self, text: str) -> str:
        lowered = str(text or "").strip().lower()
        return self._NORMALIZE_PATTERN.sub(" ", lowered)
