from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadFileResult:
    content: bytes
    filename: str
    content_type: str
