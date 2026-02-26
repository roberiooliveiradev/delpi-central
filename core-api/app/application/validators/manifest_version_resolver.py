# app/application/validators/manifest_version_resolver.py

from typing import Dict


class ManifestVersionResolver:

    SUPPORTED_VERSIONS = {
        "1.0.0": "v1"
    }

    @classmethod
    def resolve(cls, manifest: Dict) -> str:
        version = manifest.get("schemaVersion")

        if version not in cls.SUPPORTED_VERSIONS:
            raise ValueError(f"schemaVersion '{version}' não suportado.")

        return cls.SUPPORTED_VERSIONS[version]