import re
import unicodedata


class KnowledgeContentCleanerService:
    _CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
    _MULTI_SPACES = re.compile(r"[ \t]{2,}")
    _MULTI_NEWLINES = re.compile(r"\n{3,}")
    _BULLET_ARTIFACTS = re.compile(r"(?:\u2022|\u25cf|\uf0b7)\s*")

    def clean(self, text: str) -> str:
        normalized = unicodedata.normalize("NFKC", str(text or ""))
        normalized = self._CONTROL_CHARS.sub("", normalized)
        normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
        normalized = self._BULLET_ARTIFACTS.sub("- ", normalized)

        lines = []

        for raw_line in normalized.split("\n"):
            line = self._MULTI_SPACES.sub(" ", raw_line.strip())
            lines.append(line)

        collapsed = "\n".join(lines)
        collapsed = self._MULTI_NEWLINES.sub("\n\n", collapsed)

        return collapsed.strip()
