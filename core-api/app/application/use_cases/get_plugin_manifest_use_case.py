# app/application/use_cases/get_plugin_manifest_use_case.py

from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from app.application.unit_of_work import UnitOfWork


@dataclass(frozen=True)
class GetPluginManifestResult:
    success: bool
    manifest: Optional[Dict[str, Any]] = None
    errors: Optional[List[Dict[str, Any]]] = None


class GetPluginManifestUseCase:
    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    def execute(self, plugin_id: str) -> GetPluginManifestResult:
        try:
            manifest = self._uow.plugin_manifests.get(plugin_id)
            if not manifest:
                return GetPluginManifestResult(
                    success=False,
                    manifest=None,
                    errors=[{"code": "plugin.manifest_not_found", "message": "Manifest not found", "path": "_global"}],
                )
            return GetPluginManifestResult(success=True, manifest=manifest, errors=None)
        except Exception as e:
            return GetPluginManifestResult(
                success=False,
                manifest=None,
                errors=[{"code": "plugin.get_manifest_failed", "message": str(e), "path": "_global"}],
            )