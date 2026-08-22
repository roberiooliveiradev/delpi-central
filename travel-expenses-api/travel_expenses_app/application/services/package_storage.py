from __future__ import annotations

from pathlib import Path

from travel_expenses_app.config import settings


class PackageStorageService:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base_dir = Path(base_dir or settings.TRAVEL_EXPENSES_PACKAGE_UPLOAD_DIR)

    def save(self, *, report_id: str, content: bytes) -> str:
        folder = self.base_dir / report_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / "package.pdf"
        path.write_bytes(content)
        return str(path)

    def read(self, *, report_id: str) -> bytes | None:
        path = (self.base_dir / report_id / "package.pdf").resolve()
        base = self.base_dir.resolve()
        try:
            path.relative_to(base)
        except ValueError:
            return None
        if not path.is_file():
            return None
        return path.read_bytes()
