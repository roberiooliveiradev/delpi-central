from abc import ABC, abstractmethod
from typing import Dict, List
from app.domain.plugins.manifest_rules import ManifestError


class ManifestValidationStrategy(ABC):

    @abstractmethod
    def validate(self, manifest: Dict) -> List[ManifestError]:
        pass