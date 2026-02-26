# app/application/validators/manifest_normalizer.py

from typing import Dict


class ManifestNormalizer:

    @staticmethod
    def normalize(manifest: Dict) -> Dict:
        manifest = dict(manifest)

        manifest["id"] = str(manifest.get("id", "")).strip().lower()

        if manifest.get("routes") is None:
            manifest["routes"] = []

        if manifest.get("permissions") is None:
            manifest["permissions"] = []

        backend = manifest.get("backend")
        if backend:
            backend["issuer"] = str(backend.get("issuer") or "").strip()
            backend["audience"] = str(backend.get("audience") or "").strip()

        return manifest