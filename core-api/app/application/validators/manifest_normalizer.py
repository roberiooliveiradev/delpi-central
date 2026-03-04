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

        # normalize entry global
        entry = manifest.get("entry")
        if isinstance(entry, str):
            entry = entry.strip()
            manifest["entry"] = entry if entry else None

        # normalize route entries
        for route in manifest.get("routes", []):
            if not isinstance(route, dict):
                continue

            entry = route.get("entry")

            if isinstance(entry, str):
                entry = entry.strip()
                route["entry"] = entry if entry else None

        backend = manifest.get("backend")
        if backend:
            backend["issuer"] = str(backend.get("issuer") or "").strip()
            backend["audience"] = str(backend.get("audience") or "").strip()

        return manifest