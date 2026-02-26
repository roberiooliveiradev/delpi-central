# core-api/app/application/validators/validation_result.py

from dataclasses import dataclass
from typing import List
from app.domain.plugins.manifest_rules import ManifestError


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: List[ManifestError]