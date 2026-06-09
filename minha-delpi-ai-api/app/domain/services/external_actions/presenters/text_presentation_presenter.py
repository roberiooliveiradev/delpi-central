"""Apresentação em texto/árvore — Fase 3A lote 12."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.domain.services.external_actions.external_action_result_presenter import (
        ExternalActionResultPresenter,
    )


class ExternalActionTextPresentationPresenter:
    def __init__(self, host: ExternalActionResultPresenter) -> None:
        self._host = host

    def _build_parents_text_presentation(self, root: dict, path: str) -> dict | None:
        root_node = root.get("root") if isinstance(root.get("root"), dict) else {}
        code = str(root_node.get("code") or "").strip()
        total = root.get("total")
        items = root.get("items") if isinstance(root.get("items"), list) else []
        shown = len(items)

        from app.domain.services.chat_product_operational_content_service import (
            ChatProductOperationalContentService,
        )

        title = (
            ChatProductOperationalContentService.format(
                "presenter",
                "parents",
                "titleWithCode",
                code=code,
            )
            if code
            else ChatProductOperationalContentService.get(
                "presenter",
                "parents",
                "titleGeneric",
            )
        )

        description = (
            str(root_node.get("description") or "").strip()
            or self._host._route_narrative("parents", "noDescription")
        )
        summary_parts = [
            self._host._route_narrative(
                "parents",
                "productLine",
                code=code,
                description=description,
            ),
        ]

        if total is not None:
            summary_parts.append(
                self._host._route_narrative(
                    "parents",
                    "totalFound",
                    total=str(total),
                )
            )

            if shown and int(total) > shown:
                summary_parts.append(
                    self._host._route_narrative(
                        "parents",
                        "pagePartial",
                        shown=str(shown),
                    )
                )
        elif shown:
            summary_parts.append(
                self._host._route_narrative(
                    "parents",
                    "shownLinks",
                    shown=str(shown),
                )
            )

        if items:
            summary_parts.append(self._host._route_narrative("parents", "treeAndTable"))
        else:
            summary_parts.append(self._host._analyser_markdown("parentsEmpty"))

        markdown = "\n\n".join([f"### {title}", "", *summary_parts])

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    def _build_structure_text_presentation(self, root: dict, path: str) -> dict | None:
        root_node = root.get("root") if isinstance(root.get("root"), dict) else {}
        code = str(root_node.get("code") or "").strip()
        total = root.get("total")
        items = root.get("items") if isinstance(root.get("items"), list) else []

        title = (
            self._host._route_narrative("structure", "titleWithCode", code=code)
            if code
            else self._host._route_narrative("structure", "titleGeneric")
        )
        description = (
            str(root_node.get("description") or "").strip()
            or self._host._route_narrative("parents", "noDescription")
        )

        summary_parts = [
            self._host._route_narrative(
                "structure",
                "productLine",
                code=code,
                description=description,
            ),
        ]

        component_total = total if total is not None else (len(items) if items else None)

        if component_total is not None:
            summary_parts.append(
                self._host._route_narrative(
                    "structure",
                    "totalComponents",
                    total=str(component_total),
                )
            )

        if items or total:
            summary_parts.append(self._host._route_narrative("structure", "treeAndTable"))

        markdown = "\n\n".join([f"### {title}", "", *summary_parts])

        return {
            "type": "markdown",
            "title": title,
            "markdown": markdown,
        }

    def build_text_presentation(self, data, *, path: str = "") -> dict | None:
        """Markdown legível para a aba Texto do chat (complementa tabela/gráfico)."""
        root = self._host._unwrap_data(data)
        lowered = str(path or "").lower()

        if isinstance(root, dict) and "/analyser" in lowered:
            root = self._host._normalize_analyser_root(root)

        if isinstance(root, dict) and isinstance(root.get("product"), dict):
            if "/analyser" in lowered:
                product = self._host._normalize_api_section(root["product"])

                return self._host._build_product_analyser_text_presentation(
                    root,
                    product,
                    path,
                )

            if "/factory-status" in lowered:
                return self._host._build_factory_status_text_presentation(root, path)

            if "/production-status" in lowered:
                return self._host._build_production_status_text_presentation(root, path)

            if "/shipping-status" in lowered:
                return self._host._build_shipping_status_text_presentation(root, path)

            if "/structure/exclusivity" in lowered:
                return self._host._build_structure_exclusivity_text_presentation(root, path)

            if "/raw-material-price-intelligence" in lowered:
                return self._host._build_raw_material_price_intelligence_text_presentation(
                    root,
                    path,
                )

            if "/cost-impact-simulation" in lowered:
                return self._host._build_cost_impact_simulation_text_presentation(root, path)

        if isinstance(root, dict) and "/parents" in lowered:
            from app.domain.services.chat_product_structure_presentation_service import (
                ChatProductStructurePresentationService,
            )

            normalized = ChatProductStructurePresentationService._normalize_parents_payload(
                root
            )

            if normalized is not None:
                root = normalized

        if (
            isinstance(root, dict)
            and isinstance(root.get("root"), dict)
            and isinstance(root.get("items"), list)
        ):
            if "/parents" in lowered:
                return self._build_parents_text_presentation(root, path)

            if "/structure" in lowered:
                return self._build_structure_text_presentation(root, path)

        humanized = self._host.present(data, path=path)

        if not isinstance(humanized, dict):
            return self._schema_text_fallback(data, root, path)

        lines = humanized.get("linhas") or []
        detail_lines = humanized.get("linhas_detalhe") or []
        title = str(humanized.get("titulo") or "").strip()
        summary_parts = [str(line).strip() for line in lines if str(line).strip()]

        if not summary_parts and not title and not detail_lines:
            return self._schema_text_fallback(data, root, path)

        markdown_parts: list[str] = []

        if title:
            markdown_parts.append(f"### {title}")

        if "/stock" in lowered and detail_lines:
            markdown_parts.extend(summary_parts)
            detail_header = self._host._presenter_text("generic", "stockTextDetailHeader")
            markdown_parts.append(f"**{detail_header}**")
            markdown_parts.extend(
                f"- {line}" if not str(line).strip().startswith("-") else str(line).strip()
                for line in detail_lines
            )
        else:
            markdown_parts.extend(summary_parts)
            for line in detail_lines:
                cleaned = str(line).strip()

                if cleaned:
                    markdown_parts.append(cleaned)

        markdown = "\n\n".join(markdown_parts).strip()

        if not markdown:
            return self._schema_text_fallback(data, root, path)

        return {
            "type": "markdown",
            "title": title
            or self._host._fallback_title(path)
            or self._host._presenter_text("generic", "textPresentationFallback"),
            "markdown": markdown,
        }

    def _schema_text_fallback(self, data, root, path: str) -> dict | None:
        from app.domain.services.chat_api_delpi_response_profile_service import (
            ChatApiDelpiResponseProfileService,
        )
        from app.domain.services.chat_schema_driven_presentation_service import (
            ChatSchemaDrivenPresentationService,
        )

        profile = ChatApiDelpiResponseProfileService.resolve(data, path=path)

        return ChatSchemaDrivenPresentationService.build_text(
            self._host,
            root if isinstance(root, dict) else {},
            path=path,
            entity=profile.entity,
        )

    def build_tree_presentation(self, data, *, path: str = "") -> dict | None:
        from app.domain.services.chat_product_structure_presentation_service import (
            ChatProductStructurePresentationService,
        )

        return ChatProductStructurePresentationService.build_tree_presentation(
            data,
            source_path=path,
            path=path,
        )
