"""Regiões gráficas normalizadas para OCR hierárquico de desenhos (Onda 14)."""

from __future__ import annotations

import os
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService
from app.domain.services.chat_document_vision_content_service import (
    ChatDocumentVisionContentService,
)

_DEFAULT_BBOXES: dict[str, list[float]] = {
    "stamp": [0.5, 0.62, 1.0, 1.0],
    "title": [0.2, 0.0, 0.8, 0.12],
    "bom": [0.0, 0.0, 0.55, 0.35],
    "dimensions": [0.0, 0.12, 1.0, 0.62],
}

_DRAWING_REGION_ORDER = ("stamp", "title", "bom", "dimensions")


class ChatDrawingRegionService:
    @classmethod
    def region_bboxes(cls) -> dict[str, list[float]]:
        node = ChatAssistantContentService.get_node("drawing_stamp", "regionBboxes")

        if not isinstance(node, dict):
            return dict(_DEFAULT_BBOXES)

        resolved: dict[str, list[float]] = {}

        for key, value in node.items():
            if isinstance(value, list) and len(value) == 4:
                resolved[str(key)] = [float(item) for item in value]

        return resolved or dict(_DEFAULT_BBOXES)

    @classmethod
    def resolve_region_bboxes_for_page(
        cls,
        page: Any,
        *,
        matrix: Any,
    ) -> tuple[dict[str, list[float]], dict[str, Any]]:
        from app.domain.services.chat_drawing_page_layout_analysis_service import (
            ChatDrawingPageLayoutAnalysisService,
        )

        return ChatDrawingPageLayoutAnalysisService.resolve_semantic_bboxes(
            page,
            matrix=matrix,
        )

    @classmethod
    def detail_ocr_config(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node("drawing_stamp", "detailOcr")

        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def detail_ocr_regions(cls) -> tuple[str, ...]:
        config = cls.detail_ocr_config()
        regions = config.get("enabledRegions")

        if not isinstance(regions, list):
            return ("stamp", "bom")

        return tuple(str(item).strip() for item in regions if str(item).strip())

    @classmethod
    def detail_zoom_multiplier(cls) -> float:
        config = cls.detail_ocr_config()

        try:
            value = float(config.get("zoomMultiplier") or 2.5)
        except (TypeError, ValueError):
            value = 2.5

        return max(1.0, value)

    @classmethod
    def detail_tesseract_config(cls, region: str) -> str:
        config = cls.detail_ocr_config().get("tesseractConfig")

        if isinstance(config, dict):
            token = str(config.get(region) or "").strip()

            if token:
                return token

        return "--psm 6 -c preserve_interword_spaces=1"

    @classmethod
    def detail_sub_regions(cls, region: str) -> list[dict[str, Any]]:
        config = cls.detail_ocr_config().get("subRegions")

        if not isinstance(config, dict):
            return []

        items = config.get(region)

        if not isinstance(items, list):
            return []

        resolved: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            bbox = item.get("bbox")

            if not isinstance(bbox, list) or len(bbox) != 4:
                continue

            resolved.append(
                {
                    "id": str(item.get("id") or region),
                    "bbox": [float(value) for value in bbox],
                }
            )

        return resolved

    @classmethod
    def bom_candidate_bboxes(cls) -> list[dict[str, Any]]:
        node = ChatAssistantContentService.get_node("drawing_stamp", "bomCandidateBboxes")
        default_bbox = list(cls.region_bboxes().get("bom") or _DEFAULT_BBOXES["bom"])
        resolved: list[dict[str, Any]] = []

        if isinstance(node, list):
            for item in node:
                if not isinstance(item, dict):
                    continue

                bbox = item.get("bbox")

                if not isinstance(bbox, list) or len(bbox) != 4:
                    continue

                resolved.append(
                    {
                        "id": str(item.get("id") or "bom_candidate"),
                        "bbox": [float(value) for value in bbox],
                    }
                )

        if not resolved:
            resolved.append({"id": "bom_default", "bbox": default_bbox})

        limit = ChatDocumentVisionContentService.pdf_region_ocr_max_bom_candidates()
        return resolved[:limit]

    @classmethod
    def stamp_bbox(cls) -> list[float]:
        return list(cls.region_bboxes().get("stamp") or _DEFAULT_BBOXES["stamp"])

    @classmethod
    def fitz_rect(cls, page: Any, bbox: list[float] | tuple[float, ...]) -> Any:
        import fitz

        width = float(page.rect.width)
        height = float(page.rect.height)
        x0, y0, x1, y1 = (float(value) for value in bbox)

        return fitz.Rect(
            width * x0,
            height * y0,
            width * x1,
            height * y1,
        )

    @classmethod
    def _scale_matrix(cls, matrix: Any, multiplier: float) -> Any:
        import fitz

        try:
            scale_x = float(matrix.a)
            scale_y = float(matrix.d)
        except AttributeError:
            scale_x = scale_y = 1.0

        return fitz.Matrix(scale_x * multiplier, scale_y * multiplier)

    @classmethod
    def _preprocess_region_image(cls, image: Any) -> Any:
        from PIL import ImageFilter, ImageOps

        config = cls.detail_ocr_config().get("preprocess")

        if not isinstance(config, dict):
            config = {}

        if config.get("grayscale", True):
            image = image.convert("L")

        if config.get("medianFilter", False):
            image = image.filter(ImageFilter.MedianFilter(size=3))

        if config.get("autocontrast", True):
            image = ImageOps.autocontrast(image)

        if config.get("sharpen", True):
            image = image.filter(ImageFilter.SHARPEN)

        if config.get("binarize", False):
            try:
                threshold = int(config.get("binarizeThreshold") or 165)
            except (TypeError, ValueError):
                threshold = 165

            image = image.point(lambda value: 255 if value >= threshold else 0, mode="L")

        return image

    @classmethod
    def _render_region_image(
        cls,
        page: Any,
        *,
        bbox: list[float] | tuple[float, ...],
        matrix: Any,
    ) -> Any | None:
        try:
            from PIL import Image
        except ImportError:
            return None

        try:
            rect = cls.fitz_rect(page, bbox)
            pixmap = page.get_pixmap(matrix=matrix, clip=rect, alpha=False)
            return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        except Exception:
            return None

    @classmethod
    def ocr_region_text(
        cls,
        page: Any,
        *,
        bbox: list[float] | tuple[float, ...],
        matrix: Any,
        lang: str,
        tesseract_config: str = "",
        region: str | None = None,
    ) -> str:
        image = cls._render_region_image(page, bbox=bbox, matrix=matrix)

        if image is None:
            return ""

        from app.domain.services.chat_pdf_region_ocr_engine_service import (
            ChatPdfRegionOcrEngineService,
        )

        try:
            config = str(tesseract_config or "").strip()
            result = ChatPdfRegionOcrEngineService.recognize(
                image,
                lang=lang,
                tesseract_config=config,
                region=region,
            )

            return str(result.get("text") or "").strip()
        except Exception:
            return ""

    @classmethod
    def merge_region_ocr_texts(cls, base_text: str, detail_text: str) -> str:
        detail = str(detail_text or "").strip()
        base = str(base_text or "").strip()

        if not detail:
            return base

        if not base:
            return detail

        if detail == base:
            return base

        lines: list[str] = []
        seen: set[str] = set()

        for source in (detail, base):
            for line in source.splitlines():
                token = line.strip()

                if not token:
                    continue

                key = token.upper()

                if key in seen:
                    continue

                seen.add(key)
                lines.append(token)

        return "\n".join(lines)

    @classmethod
    def ocr_region_text_detailed(
        cls,
        page: Any,
        *,
        region: str,
        bbox: list[float] | tuple[float, ...],
        matrix: Any,
        lang: str,
    ) -> tuple[str, dict[str, Any]]:
        detail_matrix = cls._scale_matrix(matrix, cls.detail_zoom_multiplier())
        tesseract_config = cls.detail_tesseract_config(region)
        sub_regions = cls.detail_sub_regions(region)
        chunks: list[str] = []
        sub_meta: list[dict[str, Any]] = []

        targets = sub_regions or [{"id": region, "bbox": list(bbox)}]

        for target in targets:
            target_bbox = target.get("bbox")

            if not isinstance(target_bbox, list) or len(target_bbox) != 4:
                continue

            image = cls._render_region_image(page, bbox=target_bbox, matrix=detail_matrix)

            if image is None:
                continue

            try:
                from app.domain.services.chat_pdf_region_ocr_engine_service import (
                    ChatPdfRegionOcrEngineService,
                )

                processed = cls._preprocess_region_image(image)
                ocr_result = ChatPdfRegionOcrEngineService.recognize(
                    processed,
                    lang=lang,
                    tesseract_config=tesseract_config,
                    region=region,
                )
                text = str(ocr_result.get("text") or "").strip()
                ocr_engine = str(ocr_result.get("engine") or "tesseract")
            except Exception:
                text = ""
                ocr_engine = "tesseract"

            if not text:
                continue

            chunks.append(text)
            sub_meta.append(
                {
                    "id": str(target.get("id") or region),
                    "bbox": list(target_bbox),
                    "charCount": len(text),
                    "engine": ocr_engine,
                }
            )

        detail_text = "\n\n".join(chunks).strip()

        return detail_text, {
            "detailPass": True,
            "zoomMultiplier": cls.detail_zoom_multiplier(),
            "engine": "multi_engine_detail",
            "subRegions": sub_meta,
            "tesseractConfig": tesseract_config,
        }

    @classmethod
    def build_region_metadata(
        cls,
        *,
        region: str,
        bbox: list[float],
        char_count: int,
        engine: str = "tesseract",
        detail_pass: bool = False,
        base_char_count: int | None = None,
        detail_meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "bbox": list(bbox),
            "charCount": int(char_count),
            "engine": engine,
        }

        if detail_pass:
            payload["detailPass"] = True

        if base_char_count is not None:
            payload["baseCharCount"] = int(base_char_count)

        if isinstance(detail_meta, dict) and detail_meta:
            payload["detail"] = detail_meta

        return payload

    @classmethod
    def _ocr_region_bundle(
        cls,
        page: Any,
        *,
        region: str,
        bbox: list[float],
        matrix: Any,
        lang: str,
        candidate_id: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        detail_regions = set(cls.detail_ocr_regions())
        base_text = cls.ocr_region_text(
            page,
            bbox=bbox,
            matrix=matrix,
            lang=lang,
            region=region,
        ).strip()
        merged_text = base_text
        detail_meta: dict[str, Any] | None = None
        engine = "tesseract"
        base_char_count = len(base_text)

        if region in detail_regions:
            detail_text, detail_meta = cls.ocr_region_text_detailed(
                page,
                region=region,
                bbox=bbox,
                matrix=matrix,
                lang=lang,
            )
            merged_text = cls.merge_region_ocr_texts(base_text, detail_text).strip()

            if detail_text:
                engine = "tesseract_hybrid"

        metadata = cls.build_region_metadata(
            region=region,
            bbox=bbox,
            char_count=len(merged_text),
            engine=engine,
            detail_pass=bool(detail_meta and detail_meta.get("detailPass")),
            base_char_count=base_char_count,
            detail_meta=detail_meta,
        )

        if candidate_id:
            metadata["candidateId"] = candidate_id

        return merged_text, metadata

    @classmethod
    def _ocr_bom_region(
        cls,
        page: Any,
        *,
        matrix: Any,
        lang: str,
        region_bboxes: dict[str, list[float]] | None = None,
    ) -> tuple[str, list[float], dict[str, Any]]:
        from app.domain.services.chat_document_vision_bom_service import (
            ChatDocumentVisionBomService,
        )

        resolved_bboxes = region_bboxes if isinstance(region_bboxes, dict) else cls.region_bboxes()
        best_text = ""
        best_bbox = list(resolved_bboxes.get("bom") or _DEFAULT_BBOXES["bom"])
        best_meta: dict[str, Any] = {}
        best_score = -1
        candidates = [{"id": "layout_bom", "bbox": best_bbox}, *cls.bom_candidate_bboxes()]
        seen: set[tuple[float, float, float, float]] = set()

        for candidate in candidates:
            bbox = candidate.get("bbox")

            if not isinstance(bbox, list) or len(bbox) != 4:
                continue

            bbox_key = tuple(float(value) for value in bbox)

            if bbox_key in seen:
                continue

            seen.add(bbox_key)
            merged_text, metadata = cls._ocr_region_bundle(
                page,
                region="bom",
                bbox=[float(value) for value in bbox],
                matrix=matrix,
                lang=lang,
                candidate_id=str(candidate.get("id") or ""),
            )

            if not merged_text:
                continue

            score = ChatDocumentVisionBomService.score_bom_text(merged_text)

            if score > best_score:
                best_score = score
                best_text = merged_text
                best_bbox = [float(value) for value in bbox]
                best_meta = metadata

        if not best_text:
            return "", best_bbox, best_meta

        best_meta["selectionScore"] = best_score
        return best_text, best_bbox, best_meta

    @classmethod
    def stamp_position_is_bottom_right(cls) -> bool:
        bbox = cls.stamp_bbox()

        return len(bbox) == 4 and bbox[0] >= 0.45 and bbox[1] >= 0.5

    @classmethod
    def ocr_drawing_regions(
        cls,
        page: Any,
        *,
        matrix: Any,
        lang: str,
    ) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
        texts: dict[str, str] = {}
        metadata: dict[str, dict[str, Any]] = {}
        region_bboxes, layout_meta = cls.resolve_region_bboxes_for_page(
            page,
            matrix=matrix,
        )

        for region in _DRAWING_REGION_ORDER:
            if region == "bom":
                merged_text, bbox, region_meta = cls._ocr_bom_region(
                    page,
                    matrix=matrix,
                    lang=lang,
                    region_bboxes=region_bboxes,
                )

                if not merged_text:
                    continue

                texts[region] = merged_text
                metadata[region] = region_meta
                continue

            bbox = region_bboxes.get(region)

            if not bbox:
                continue

            merged_text, region_meta = cls._ocr_region_bundle(
                page,
                region=region,
                bbox=bbox,
                matrix=matrix,
                lang=lang,
            )

            if not merged_text:
                continue

            texts[region] = merged_text
            metadata[region] = region_meta

        if layout_meta:
            metadata["_layoutAnalysis"] = layout_meta.get("layoutAnalysis") or layout_meta

        return texts, metadata

    @classmethod
    def ocr_multipage_drawing_regions(
        cls,
        document: Any,
        *,
        page_limit: int,
        matrix: Any,
        lang: str,
    ) -> tuple[dict[str, str], dict[str, Any], int]:
        page_count = min(int(document.page_count or 0), max(1, int(page_limit)))

        if page_count < 1:
            return {}, {}, 0

        region_texts: dict[str, str] = {}
        regions: dict[str, Any] = {}
        aggregated_bom = ""
        supplemental_pages: list[str] = []

        for index in range(page_count):
            page = document.load_page(index)

            if index == 0:
                page_texts, page_regions = cls.ocr_drawing_regions(
                    page,
                    matrix=matrix,
                    lang=lang,
                )
                region_texts = dict(page_texts)
                regions = dict(page_regions)
                aggregated_bom = str(page_texts.get("bom") or "").strip()
                continue

            if not cls._should_ocr_bom_on_subsequent_pages():
                break

            bom_text, _, bom_meta = cls._ocr_bom_region(
                page,
                matrix=matrix,
                lang=lang,
            )

            if not bom_text and cls._should_ocr_full_page_on_subsequent_pages():
                bom_text = cls.ocr_region_text(
                    page,
                    bbox=[0.0, 0.0, 1.0, 1.0],
                    matrix=matrix,
                    lang=lang,
                    region="bom",
                ).strip()
                bom_meta = cls.build_region_metadata(
                    region="bom",
                    bbox=[0.0, 0.0, 1.0, 1.0],
                    char_count=len(bom_text),
                    engine="tesseract_full_page",
                )

            if not bom_text:
                continue

            supplemental_pages.append(bom_text)
            aggregated_bom = cls.merge_region_ocr_texts(aggregated_bom, bom_text).strip()
            regions[f"bom_page_{index}"] = bom_meta

        if aggregated_bom:
            region_texts["bom"] = aggregated_bom

            if isinstance(regions.get("bom"), dict):
                regions["bom"]["multipageMerged"] = True
                regions["bom"]["charCount"] = len(aggregated_bom)
            else:
                regions["bom"] = {
                    "charCount": len(aggregated_bom),
                    "multipageMerged": True,
                }

        if supplemental_pages:
            regions["multipageSupplementalPages"] = len(supplemental_pages)

        return region_texts, regions, page_count

    @classmethod
    def _should_ocr_full_page_on_subsequent_pages(cls) -> bool:
        from app.domain.services.chat_drawing_patterns_service import (
            ChatDrawingPatternsService,
        )

        return ChatDrawingPatternsService.multipage_ocr_full_page_text_on_subsequent_pages()

    @classmethod
    def _should_ocr_bom_on_subsequent_pages(cls) -> bool:
        from app.domain.services.chat_drawing_patterns_service import (
            ChatDrawingPatternsService,
        )

        return (
            ChatDrawingPatternsService.multipage_ocr_bom_on_all_pages()
            and ChatDrawingPatternsService.multipage_ocr_full_layout_first_page_only()
        )

    @classmethod
    def ocr_selected_drawing_regions(
        cls,
        storage_path: str,
        regions: tuple[str, ...] | list[str],
        *,
        dpi_multiplier: float = 1.5,
        engines: tuple[str, ...] | list[str] | None = None,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """OCR focal Tesseract em regiões nomeadas (confirmação pós-confiança baixa)."""
        try:
            import fitz
        except ImportError:
            return {}, {}

        try:
            document = fitz.open(storage_path)
        except Exception:
            return {}, {}

        from app.domain.services.chat_domain_config_service import ChatDomainConfigService
        from app.domain.services.chat_pdf_region_ocr_engine_service import (
            ChatPdfRegionOcrEngineService,
        )

        lang = os.getenv("CHAT_DOCUMENT_VISION_TESSERACT_LANG", "por+eng").strip() or "por+eng"
        dpi = max(72, int(ChatDomainConfigService.chat_document_vision_dpi()))
        zoom = (dpi / 72.0) * max(1.0, float(dpi_multiplier or 1.0))
        matrix = fitz.Matrix(zoom, zoom)
        engines_override = list(engines) if engines else ["tesseract"]

        region_texts: dict[str, str] = {}
        regions_meta: dict[str, Any] = {}

        try:
            if int(document.page_count or 0) < 1:
                return {}, {}

            page = document.load_page(0)
            region_bboxes = cls.region_bboxes()
            selected = cls._normalize_selected_regions(regions)

            with ChatPdfRegionOcrEngineService.region_ocr_engines_override(engines_override):
                for region in selected:
                    if region == "bom":
                        merged_text, bbox, region_meta = cls._ocr_bom_region(
                            page,
                            matrix=matrix,
                            lang=lang,
                            region_bboxes=region_bboxes,
                        )

                        if merged_text:
                            region_texts[region] = merged_text
                            regions_meta[region] = region_meta

                        continue

                    bbox = region_bboxes.get(region)

                    if not bbox:
                        continue

                    merged_text, region_meta = cls._ocr_region_bundle(
                        page,
                        region=region,
                        bbox=bbox,
                        matrix=matrix,
                        lang=lang,
                    )

                    if merged_text:
                        region_texts[region] = merged_text
                        regions_meta[region] = region_meta
        finally:
            document.close()

        return region_texts, regions_meta

    @classmethod
    def _normalize_selected_regions(cls, regions: tuple[str, ...] | list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []

        for region in _DRAWING_REGION_ORDER:
            if region in regions and region not in seen:
                ordered.append(region)
                seen.add(region)

        for region in regions:
            token = str(region).strip().lower()

            if token and token not in seen:
                ordered.append(token)
                seen.add(token)

        return ordered
