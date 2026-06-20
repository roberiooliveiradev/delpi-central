"""P2 — pipeline data-only: não gerar prosa template quando LLM narrará o turno."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_prose_delivery_service import (
    MODE_LLM,
    ChatPresentationProseDeliveryService,
)


class ChatPresentationDataOnlyProseService:
    FLAG = "dataOnlyPresentation"
    STRUCTURED_HUMANIZED_KEYS = ("sqlRows",)

    @classmethod
    def should_apply(cls, user_message: str | None, *, path: str | None = None) -> bool:
        return ChatPresentationProseDeliveryService.should_skip_template_prose_in_pipeline(
            user_message,
            path=path,
        )

    @classmethod
    def is_data_only_metadata(cls, metadata: dict[str, Any] | None) -> bool:
        if not isinstance(metadata, dict):
            return False

        if metadata.get(cls.FLAG):
            return True

        return ChatPresentationProseDeliveryService.is_llm_decoupled_metadata(metadata)

    @classmethod
    def mark_metadata(cls, metadata: dict[str, Any]) -> None:
        metadata[cls.FLAG] = True
        metadata["proseDeliveryMode"] = MODE_LLM

        decision = metadata.get("presentationDecision")

        if not isinstance(decision, dict):
            decision = {}
            metadata["presentationDecision"] = decision

        decision["proseSource"] = MODE_LLM

    @classmethod
    def archive_and_strip_humanized(cls, metadata: dict[str, Any]) -> None:
        if not isinstance(metadata, dict):
            return

        humanized = metadata.get("humanizedSummary")
        archived_humanized: dict[str, Any] | None = None

        if isinstance(humanized, dict):
            archived_humanized = {
                key: value
                for key, value in humanized.items()
                if value not in (None, "", [])
            }

        text_presentation = metadata.get("textPresentation")
        archived_markdown = ""

        if isinstance(text_presentation, dict):
            archived_markdown = str(text_presentation.get("markdown") or "").strip()

        if archived_markdown or archived_humanized:
            archive = metadata.get("templateProseArchive")

            if not isinstance(archive, dict):
                archive = {}

            if archived_markdown:
                archive["textPresentationMarkdown"] = archived_markdown

            if archived_humanized:
                archive["humanizedSummary"] = archived_humanized

            metadata["templateProseArchive"] = archive

        if isinstance(text_presentation, dict):
            text_presentation["markdown"] = ""

        if isinstance(humanized, dict):
            humanized["linhas"] = []
            humanized["linhas_detalhe"] = []

        metadata.pop("storyPresentation", None)

    @classmethod
    def prepare_humanized_for_metadata(
        cls,
        metadata: dict[str, Any],
        humanized: dict[str, Any] | None,
    ) -> dict[str, Any] | None:
        if not cls.is_data_only_metadata(metadata):
            return humanized

        if not isinstance(humanized, dict):
            return humanized

        titulo = str(humanized.get("titulo") or "").strip()
        linhas = [
            str(line).strip()
            for line in (humanized.get("linhas") or [])
            if str(line or "").strip()
        ]
        detail_lines = [
            str(line).strip()
            for line in (humanized.get("linhas_detalhe") or [])
            if str(line or "").strip()
        ]

        if linhas or detail_lines:
            archive = metadata.get("templateProseArchive")

            if not isinstance(archive, dict):
                archive = {}

            archive["humanizedSummary"] = {
                **({"titulo": titulo} if titulo else {}),
                **({"linhas": linhas} if linhas else {}),
                **({"linhas_detalhe": detail_lines} if detail_lines else {}),
            }
            metadata["templateProseArchive"] = archive

        return {"titulo": titulo} if titulo else None

    @classmethod
    def resolve_humanized_summary(
        cls,
        presenter,
        data,
        *,
        path: str,
        metadata: dict[str, Any],
    ) -> dict | Any | None:
        if not cls.is_data_only_metadata(metadata):
            return presenter.present(data, path=path)

        titulo = cls._resolve_title_only(presenter, data, path=path, metadata=metadata)

        if titulo == "Lista de LMPs" and (
            "eficiencia-fabril" in path.lower() or "eficiencia_fabril" in path.lower()
        ):
            titulo = "Eficiência fabril"

        structured = cls._resolve_structured_humanized_fields(
            presenter,
            data,
            path=path,
            metadata=metadata,
            titulo=titulo,
        )

        if not titulo and not structured:
            return None

        result: dict[str, Any] = {}

        if titulo:
            result["titulo"] = titulo

        result.update(structured)
        return result

    @classmethod
    def _resolve_structured_humanized_fields(
        cls,
        presenter,
        data,
        *,
        path: str,
        metadata: dict[str, Any],
        titulo: str,
    ) -> dict[str, Any]:
        lowered = str(path or "").lower()

        if "/data/sql" not in lowered:
            return {}

        full = presenter.present(data, path=path)

        if not isinstance(full, dict):
            return {}

        linhas = [
            str(line).strip()
            for line in (full.get("linhas") or [])
            if str(line or "").strip()
        ]
        detail_lines = [
            str(line).strip()
            for line in (full.get("linhas_detalhe") or [])
            if str(line or "").strip()
        ]

        if linhas or detail_lines:
            archive = metadata.get("templateProseArchive")

            if not isinstance(archive, dict):
                archive = {}

            archive["humanizedSummary"] = {
                **({"titulo": titulo} if titulo else {}),
                **({"linhas": linhas} if linhas else {}),
                **({"linhas_detalhe": detail_lines} if detail_lines else {}),
            }
            metadata["templateProseArchive"] = archive

        structured: dict[str, Any] = {}
        sql_rows = full.get("sqlRows")

        if isinstance(sql_rows, list) and sql_rows:
            structured["sqlRows"] = sql_rows

        return structured

    @classmethod
    def _resolve_title_only(
        cls,
        presenter,
        data,
        *,
        path: str,
        metadata: dict[str, Any],
    ) -> str:
        code = cls._extract_product_code(presenter, data, path)
        profile_key = str((metadata.get("dataAnswer") or {}).get("profileKey") or "").strip()

        from app.domain.services.chat_presentation_prose_delivery_content_service import (
            ChatPresentationProseDeliveryContentService,
        )

        spec = (
            ChatPresentationProseDeliveryContentService.data_only_title_spec(profile_key)
            if profile_key
            else None
        )

        if spec:
            detail_key = spec.get("productDetailKey")

            if detail_key:
                from app.domain.services.chat_assistant_content_service import (
                    ChatAssistantContentService,
                )

                template = str(
                    ChatAssistantContentService.get(
                        "presenter_content",
                        "productDetailTitles",
                        detail_key,
                        default="",
                    )
                    or ""
                ).strip()

                if template and code:
                    return template.format(code=code)

            route_namespace = spec.get("routeNamespace")

            if route_namespace:
                with_code_key = spec.get("withCodeKey") or "titleWithCode"
                generic_key = spec.get("genericKey") or "titleGeneric"

                if code:
                    return presenter._route_presentation(
                        route_namespace,
                        with_code_key,
                        code=code,
                    )

                return presenter._route_presentation(route_namespace, generic_key)

        api_meta = metadata.get("apiDelpiResponseMeta")

        if isinstance(api_meta, dict):
            entity = str(api_meta.get("entity") or "").strip()

            if entity:
                from app.domain.services.chat_operational_response_profile_service import (
                    ChatOperationalResponseProfileService,
                )

                if ChatOperationalResponseProfileService.is_playbook_operational_entity(
                    entity,
                ):
                    return presenter._playbook_report()._playbook_entity_title(
                        entity,
                        table=False,
                    )

        fragment = presenter._presenter_content()._path_fragment_title(
            path.rstrip("/").rsplit("/", 1)[-1],
        )

        if fragment:
            return fragment

        fallback = presenter._fallback_title(path)

        if fallback:
            return fallback

        return presenter._presenter_text("generic", "queryResultTitle")

    @classmethod
    def _extract_product_code(cls, presenter, data, path: str) -> str:
        root = presenter._unwrap_data(data)

        if isinstance(root, dict):
            product = root.get("product")

            if isinstance(product, dict):
                code = str(product.get("code") or product.get("product_code") or "").strip()

                if code:
                    return code

        return str(presenter._extract_product_code_from_path(path) or "").strip()

    @classmethod
    def finalize_metadata(cls, metadata: dict[str, Any]) -> None:
        if not cls.is_data_only_metadata(metadata):
            return

        cls.archive_and_strip_humanized(metadata)
        cls.mark_metadata(metadata)
        metadata["llmProseDecoupled"] = True

        from app.domain.services.chat_presentation_render_pipeline_service import (
            ChatPresentationRenderPipelineService,
        )

        ChatPresentationRenderPipelineService.finalize(metadata)
