"""Regras de domínio da biblioteca de templates de slide."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from tv_app.application.services.slide_template_mdd_service import (
    SlideTemplateMddError,
    build_slide_template_mdd,
    load_mdd_templates,
    parse_slide_template_mdd,
)
from tv_app.infrastructure.persistence.repositories.slide_template_repository import (
    SlideTemplateRepository,
    slugify_template_key,
)


class SlideTemplateConflictError(Exception):
    def __init__(self, current: dict[str, Any]):
        super().__init__("Versão desatualizada. Recarregue o template.")
        self.current = current


class SlideTemplateNotFoundError(LookupError):
    pass


class SlideTemplateForbiddenError(PermissionError):
    pass


class SlideTemplateValidationError(ValueError):
    pass


def validate_native_config(native_config: Any) -> dict[str, Any]:
    if not isinstance(native_config, dict):
        raise SlideTemplateValidationError("nativeConfig deve ser um objeto.")
    blocks = native_config.get("blocks")
    if blocks is not None and not isinstance(blocks, list):
        raise SlideTemplateValidationError("nativeConfig.blocks deve ser uma lista.")
    version = native_config.get("version")
    if version is not None:
        try:
            int(version)
        except (TypeError, ValueError) as exc:
            raise SlideTemplateValidationError("nativeConfig.version inválido.") from exc
    return dict(native_config)


def parse_and_validate_mdd(raw: bytes) -> dict[str, Any]:
    try:
        parsed = parse_slide_template_mdd(raw)
    except SlideTemplateMddError as exc:
        raise SlideTemplateValidationError(str(exc)) from exc
    native = validate_native_config(parsed.get("nativeConfig") or {})
    parsed["nativeConfig"] = native
    if not str(parsed.get("label") or "").strip():
        raise SlideTemplateValidationError("Template MDD sem label.")
    return parsed


class SlideTemplateLibraryService:
    def __init__(self, repo: SlideTemplateRepository | None = None):
        self._repo = repo or SlideTemplateRepository()

    def list_published(self) -> list[dict[str, Any]]:
        return self._repo.list(status="published", exclude_archived_by_default=False)

    def list_library(
        self,
        *,
        status: str | None = None,
        q: str | None = None,
        is_system: bool | None = None,
    ) -> list[dict[str, Any]]:
        return self._repo.list(
            status=status,
            q=q,
            is_system=is_system,
            exclude_archived_by_default=status is None,
        )

    def get(self, template_id: UUID) -> dict[str, Any]:
        item = self._repo.get(template_id)
        if not item:
            raise SlideTemplateNotFoundError(str(template_id))
        return item

    def create(
        self,
        *,
        label: str,
        description: str | None,
        native_config: dict[str, Any],
        native_screen_key: str = "custom_message",
        duration_sec: int | None = 45,
        key: str | None = None,
        status: str = "draft",
        publish_now: bool = False,
        owner_user_id: str | None = None,
        updated_by: str | None = None,
    ) -> dict[str, Any]:
        validated = validate_native_config(native_config)
        label_clean = (label or "").strip()
        if not label_clean:
            raise SlideTemplateValidationError("label obrigatório.")
        if status not in ("draft", "published", "archived"):
            raise SlideTemplateValidationError("status inválido.")
        final_status = "published" if publish_now else status
        base_key = key or slugify_template_key(label_clean)
        unique_key = self._repo.allocate_unique_key(base_key)
        return self._repo.create(
            key=unique_key,
            label=label_clean,
            description=description,
            native_screen_key=native_screen_key or "custom_message",
            native_config=validated,
            duration_sec=duration_sec,
            status=final_status,
            is_system=False,
            owner_user_id=owner_user_id,
            updated_by=updated_by,
        )

    def update(
        self,
        template_id: UUID,
        *,
        expected_version: int,
        label: str | None = None,
        description: str | None = None,
        native_config: dict[str, Any] | None = None,
        native_screen_key: str | None = None,
        duration_sec: int | None = None,
        updated_by: str | None = None,
    ) -> dict[str, Any]:
        content_changed = native_config is not None or native_screen_key is not None
        validated = validate_native_config(native_config) if native_config is not None else None
        result = self._repo.update(
            template_id,
            expected_version=expected_version,
            label=label,
            description=description,
            native_config=validated,
            native_screen_key=native_screen_key,
            duration_sec=duration_sec,
            content_changed=content_changed,
            updated_by=updated_by,
        )
        if result is None:
            raise SlideTemplateNotFoundError(str(template_id))
        if result.get("_conflict"):
            raise SlideTemplateConflictError(result["current"])
        return result

    def publish(self, template_id: UUID, *, updated_by: str | None) -> dict[str, Any]:
        item = self.get(template_id)
        if item["status"] == "archived":
            raise SlideTemplateValidationError("Template arquivado não pode ser publicado.")
        return self._repo.set_status(template_id, status="published", updated_by=updated_by) or item

    def unpublish(self, template_id: UUID, *, updated_by: str | None) -> dict[str, Any]:
        item = self.get(template_id)
        if item.get("isSystem"):
            raise SlideTemplateForbiddenError(
                "Templates de sistema não podem ser despublicados. Duplique para editar uma cópia."
            )
        if item["status"] != "published":
            raise SlideTemplateValidationError("Somente templates publicados podem ser despublicados.")
        return self._repo.set_status(template_id, status="draft", updated_by=updated_by) or item

    def archive(self, template_id: UUID, *, updated_by: str | None) -> dict[str, Any]:
        item = self.get(template_id)
        if item.get("isSystem"):
            raise SlideTemplateForbiddenError("Templates de sistema não podem ser arquivados.")
        return self._repo.set_status(template_id, status="archived", updated_by=updated_by) or item

    def delete(self, template_id: UUID) -> dict[str, Any]:
        item = self.get(template_id)
        if item.get("isSystem"):
            raise SlideTemplateForbiddenError("Templates de sistema não podem ser excluídos.")
        deleted = self._repo.delete(template_id)
        if not deleted:
            raise SlideTemplateNotFoundError(str(template_id))
        return deleted

    def clone(self, template_id: UUID, *, updated_by: str | None, owner_user_id: str | None) -> dict[str, Any]:
        item = self.get(template_id)
        label = f"{item['label']} (cópia)"
        return self.create(
            label=label,
            description=item.get("description"),
            native_config=dict(item.get("nativeConfig") or {}),
            native_screen_key=str(item.get("nativeScreenKey") or "custom_message"),
            duration_sec=item.get("durationSec"),
            key=f"{item['key']}_copy",
            status="draft",
            owner_user_id=owner_user_id,
            updated_by=updated_by,
        )

    def from_slide(
        self,
        *,
        label: str,
        description: str | None,
        native_config: dict[str, Any],
        native_screen_key: str = "custom_message",
        duration_sec: int | None = 45,
        owner_user_id: str | None = None,
        updated_by: str | None = None,
    ) -> dict[str, Any]:
        return self.create(
            label=label,
            description=description,
            native_config=native_config,
            native_screen_key=native_screen_key,
            duration_sec=duration_sec,
            status="draft",
            owner_user_id=owner_user_id,
            updated_by=updated_by,
        )

    def import_preview(self, raw: bytes) -> dict[str, Any]:
        return parse_and_validate_mdd(raw)

    def import_apply(
        self,
        raw: bytes,
        *,
        publish_now: bool = False,
        owner_user_id: str | None = None,
        updated_by: str | None = None,
    ) -> dict[str, Any]:
        parsed = parse_and_validate_mdd(raw)
        return self.create(
            label=str(parsed.get("label") or parsed.get("key") or "Importado"),
            description=parsed.get("description"),
            native_config=dict(parsed.get("nativeConfig") or {}),
            native_screen_key=str(parsed.get("nativeScreenKey") or "custom_message"),
            duration_sec=parsed.get("durationSec"),
            key=str(parsed.get("key") or "imported"),
            status="draft",
            publish_now=publish_now,
            owner_user_id=owner_user_id,
            updated_by=updated_by,
        )

    def export_mdd(self, template_id: UUID, *, exported_by: str | None = None) -> tuple[bytes, str]:
        item = self.get(template_id)
        return build_slide_template_mdd(
            key=item["key"],
            label=item["label"],
            description=item.get("description"),
            title=str(item.get("title") or item["label"]),
            duration_sec=item.get("durationSec"),
            native_config=dict(item.get("nativeConfig") or {}),
            native_screen_key=str(item.get("nativeScreenKey") or "custom_message"),
            exported_by=exported_by,
        )

    def seed_from_disk(self) -> dict[str, Any]:
        """Upsert system templates from content/slide_templates/*.mdd."""
        loaded = load_mdd_templates()
        upserted = 0
        skipped = 0
        errors: list[str] = []
        for item in loaded:
            try:
                native = validate_native_config(item.get("nativeConfig") or {})
                self._repo.upsert_system(
                    key=str(item.get("key") or "template"),
                    label=str(item.get("label") or item.get("key") or "Template"),
                    description=item.get("description"),
                    native_screen_key=str(item.get("nativeScreenKey") or "custom_message"),
                    native_config=native,
                    duration_sec=item.get("durationSec"),
                )
                upserted += 1
            except Exception as exc:  # noqa: BLE001 — seed best-effort per file
                skipped += 1
                errors.append(str(exc))
        return {"upserted": upserted, "skipped": skipped, "errors": errors}
