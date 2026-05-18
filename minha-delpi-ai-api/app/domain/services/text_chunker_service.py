class TextChunkerService:
    def __init__(self, chunk_size: int = 1400, overlap: int = 200):
        if overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")

        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        normalized = self._normalize(text)

        if not normalized:
            return []

        chunks: list[str] = []
        start = 0

        while start < len(normalized):
            end = start + self.chunk_size
            chunk = normalized[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= len(normalized):
                break

            start = end - self.overlap

        return chunks

    def _normalize(self, text: str) -> str:
        return "\n".join(
            line.strip()
            for line in str(text or "").splitlines()
            if line.strip()
        )
