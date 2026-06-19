"""Análise de layout de página — XY-Cut + classificação semântica (DLA).

Pipeline inspirado em engines usadas com VLMs (Azure prebuilt-layout, MinerU 2.5,
DocLayNet): estágio 1 detecta blocos por projeção recursiva; estágio 2 classifica
e funde em regiões DELPI (carimbo, BOM, cotas, título).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_assistant_content_service import ChatAssistantContentService

_BUNDLE = "drawing_stamp"
_ALGORITHM = "xy_cut_semantic_v1"


@dataclass(frozen=True)
class LayoutBlock:
    bbox: tuple[float, float, float, float]
    category: str
    confidence: float
    reading_order: int
    area_ratio: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "bbox": [round(value, 4) for value in self.bbox],
            "category": self.category,
            "confidence": round(self.confidence, 4),
            "readingOrder": self.reading_order,
            "areaRatio": round(self.area_ratio, 6),
        }


@dataclass(frozen=True)
class PageLayoutAnalysisResult:
    blocks: tuple[LayoutBlock, ...]
    semantic_regions: dict[str, list[float]]
    confidence: float
    algorithm: str
    page_size: tuple[int, int]
    used_static_fallback: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "algorithm": self.algorithm,
            "confidence": round(self.confidence, 4),
            "pageWidthPx": self.page_size[0],
            "pageHeightPx": self.page_size[1],
            "usedStaticFallback": self.used_static_fallback,
            "semanticRegions": {
                key: [round(value, 4) for value in bbox]
                for key, bbox in self.semantic_regions.items()
            },
            "blocks": [block.to_dict() for block in self.blocks],
            "readingOrder": [block.category for block in sorted(self.blocks, key=lambda item: item.reading_order)],
        }


class ChatDrawingPageLayoutAnalysisService:
    _SEMANTIC_REGIONS = ("stamp", "title", "bom", "dimensions", "drawing_body")

    @classmethod
    def analyze_fitz_page(
        cls,
        page: Any,
        *,
        matrix: Any | None = None,
    ) -> PageLayoutAnalysisResult | None:
        image = cls._render_page_image(page, matrix=matrix)

        if image is None:
            return None

        return cls.analyze_page_image(image)

    @classmethod
    def analyze_page_image(cls, image: Any) -> PageLayoutAnalysisResult:
        from PIL import Image

        if not isinstance(image, Image.Image):
            raise TypeError("image must be a PIL.Image.Image")

        thumbnail, scale = cls._thumbnail(image)
        mask = cls._binary_mask(thumbnail)
        height, width = mask.shape
        blocks_px = cls._xy_cut_blocks(
            mask,
            bbox=(0, 0, width, height),
            depth=0,
        )
        classified = cls._classify_blocks(blocks_px, mask, page_area=width * height)
        reading_order = cls._reading_order(classified)
        blocks = cls._normalize_blocks(classified, reading_order, width=width, height=height)
        semantic_regions, confidence = cls._merge_semantic_regions(blocks)
        semantic_regions = cls._refine_with_static_priors(semantic_regions, confidence)

        if confidence < cls._min_confidence_for_adaptive():
            static = cls._static_region_bboxes()
            semantic_regions = dict(static)
            used_fallback = True
            confidence = min(confidence, cls._static_prior_confidence())
        else:
            used_fallback = False

        return PageLayoutAnalysisResult(
            blocks=blocks,
            semantic_regions=semantic_regions,
            confidence=confidence,
            algorithm=_ALGORITHM,
            page_size=(int(image.width), int(image.height)),
            used_static_fallback=used_fallback,
        )

    @classmethod
    def resolve_semantic_bboxes(
        cls,
        page: Any,
        *,
        matrix: Any | None = None,
    ) -> tuple[dict[str, list[float]], dict[str, Any]]:
        if not cls._enabled():
            return cls._static_region_bboxes(), {}

        result = cls.analyze_fitz_page(page, matrix=matrix)

        if result is None:
            return cls._static_region_bboxes(), {"layoutAnalysis": {"usedStaticFallback": True}}

        bboxes = {
            key: list(result.semantic_regions[key])
            for key in _DRAWING_REGION_KEYS
            if key in result.semantic_regions
        }

        for key, bbox in cls._static_region_bboxes().items():
            bboxes.setdefault(key, list(bbox))

        return bboxes, {"layoutAnalysis": result.to_metadata()}

    @classmethod
    def _enabled(cls) -> bool:
        node = cls._layout_config()

        return bool(node.get("enabled", True))

    @classmethod
    def _layout_config(cls) -> dict[str, Any]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "layoutAnalysis")

        return dict(node) if isinstance(node, dict) else {}

    @classmethod
    def _static_region_bboxes(cls) -> dict[str, list[float]]:
        node = ChatAssistantContentService.get_node(_BUNDLE, "regionBboxes") or {}

        if not isinstance(node, dict):
            node = {}

        resolved: dict[str, list[float]] = {}

        for key in _DRAWING_REGION_KEYS:
            value = node.get(key)

            if isinstance(value, list) and len(value) == 4:
                resolved[key] = [float(item) for item in value]

        return resolved or dict(_DEFAULT_STATIC_BBOXES)

    @classmethod
    def _min_confidence_for_adaptive(cls) -> float:
        try:
            return float(cls._layout_config().get("minConfidenceForAdaptiveBboxes") or 0.65)
        except (TypeError, ValueError):
            return 0.65

    @classmethod
    def _static_prior_confidence(cls) -> float:
        try:
            return float(cls._layout_config().get("staticFallbackConfidence") or 0.55)
        except (TypeError, ValueError):
            return 0.55

    @classmethod
    def _thumbnail_max_edge(cls) -> int:
        try:
            return max(256, int(cls._layout_config().get("thumbnailMaxEdgePx") or 1200))
        except (TypeError, ValueError):
            return 1200

    @classmethod
    def _binarize_threshold(cls) -> int:
        try:
            return int(cls._layout_config().get("binarizeThreshold") or 210)
        except (TypeError, ValueError):
            return 210

    @classmethod
    def _xy_cut_min_gap_ratio(cls) -> float:
        try:
            return float(cls._layout_config().get("xyCutMinGapRatio") or 0.018)
        except (TypeError, ValueError):
            return 0.018

    @classmethod
    def _xy_cut_min_block_area_ratio(cls) -> float:
        try:
            return float(cls._layout_config().get("xyCutMinBlockAreaRatio") or 0.003)
        except (TypeError, ValueError):
            return 0.003

    @classmethod
    def _xy_cut_max_depth(cls) -> int:
        try:
            return max(1, int(cls._layout_config().get("xyCutMaxDepth") or 5))
        except (TypeError, ValueError):
            return 5

    @classmethod
    def _render_page_image(cls, page: Any, *, matrix: Any | None) -> Any | None:
        try:
            from PIL import Image
        except ImportError:
            return None

        try:
            if matrix is None:
                pixmap = page.get_pixmap(alpha=False)
            else:
                pixmap = page.get_pixmap(matrix=matrix, alpha=False)

            return Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        except Exception:
            return None

    @classmethod
    def _thumbnail(cls, image: Any) -> tuple[Any, float]:
        from PIL import Image

        max_edge = cls._thumbnail_max_edge()
        width, height = image.size
        scale = 1.0

        if max(width, height) > max_edge:
            scale = max_edge / float(max(width, height))
            resized = image.resize(
                (max(1, int(width * scale)), max(1, int(height * scale))),
                Image.Resampling.BILINEAR,
            )
            return resized, scale

        return image.copy(), scale

    @classmethod
    def _binary_mask(cls, image: Any) -> Any:
        import numpy as np

        gray = np.asarray(image.convert("L"))
        threshold = cls._binarize_threshold()
        return gray < threshold

    @classmethod
    def _xy_cut_blocks(
        cls,
        mask: Any,
        *,
        bbox: tuple[int, int, int, int],
        depth: int,
    ) -> list[tuple[int, int, int, int]]:
        import numpy as np

        x0, y0, x1, y1 = bbox
        sub = mask[y0:y1, x0:x1]

        if sub.size == 0:
            return []

        page_area = mask.shape[0] * mask.shape[1]
        min_area = page_area * cls._xy_cut_min_block_area_ratio()

        if sub.size < min_area or depth >= cls._xy_cut_max_depth():
            return [bbox]

        height, width = sub.shape
        min_gap_h = max(2, int(height * cls._xy_cut_min_gap_ratio()))
        min_gap_w = max(2, int(width * cls._xy_cut_min_gap_ratio()))

        horizontal_splits = cls._projection_gaps(
            sub.sum(axis=1),
            min_gap=min_gap_h,
        )

        if horizontal_splits:
            blocks: list[tuple[int, int, int, int]] = []
            cursor = 0

            for split_end in horizontal_splits + [height]:
                if split_end - cursor < min_gap_h:
                    continue

                child = (x0, y0 + cursor, x1, y0 + split_end)

                if (child[2] - child[0]) * (child[3] - child[1]) >= min_area:
                    blocks.extend(cls._xy_cut_blocks(mask, bbox=child, depth=depth + 1))

                cursor = split_end

            if len(blocks) > 1:
                return blocks

        vertical_splits = cls._projection_gaps(
            sub.sum(axis=0),
            min_gap=min_gap_w,
        )

        if vertical_splits:
            blocks = []
            cursor = 0

            for split_end in vertical_splits + [width]:
                if split_end - cursor < min_gap_w:
                    continue

                child = (x0 + cursor, y0, x0 + split_end, y1)

                if (child[2] - child[0]) * (child[3] - child[1]) >= min_area:
                    blocks.extend(cls._xy_cut_blocks(mask, bbox=child, depth=depth + 1))

                cursor = split_end

            if len(blocks) > 1:
                return blocks

        return [bbox]

    @classmethod
    def _projection_gaps(cls, projection: Any, *, min_gap: int) -> list[int]:
        import numpy as np

        if projection.size == 0:
            return []

        peak = float(projection.max() or 0.0)

        if peak <= 0:
            return []

        threshold = peak * 0.08
        low = projection <= threshold
        gaps: list[int] = []
        start: int | None = None

        for index, is_low in enumerate(low):
            if is_low and start is None:
                start = index
                continue

            if not is_low and start is not None:
                if index - start >= min_gap:
                    gaps.append(start + (index - start) // 2)

                start = None

        if start is not None and len(low) - start >= min_gap:
            gaps.append(start + (len(low) - start) // 2)

        return gaps

    @classmethod
    def _classify_blocks(
        cls,
        blocks_px: list[tuple[int, int, int, int]],
        mask: Any,
        *,
        page_area: int,
    ) -> list[tuple[tuple[int, int, int, int], str, float]]:
        import numpy as np

        classified: list[tuple[tuple[int, int, int, int], str, float]] = []

        for x0, y0, x1, y1 in blocks_px:
            width = max(1, x1 - x0)
            height = max(1, y1 - y0)
            area_ratio = (width * height) / max(1, page_area)
            nx0, ny0, nx1, ny1 = (
                x0 / mask.shape[1],
                y0 / mask.shape[0],
                x1 / mask.shape[1],
                y1 / mask.shape[0],
            )
            cx = (nx0 + nx1) / 2.0
            cy = (ny0 + ny1) / 2.0
            aspect = width / height
            sub = mask[y0:y1, x0:x1]
            ink_ratio = float(np.mean(sub)) if sub.size else 0.0
            category, confidence = cls._classify_bbox(
                bbox=(nx0, ny0, nx1, ny1),
                cx=cx,
                cy=cy,
                aspect=aspect,
                area_ratio=area_ratio,
                ink_ratio=ink_ratio,
            )
            classified.append(((x0, y0, x1, y1), category, confidence))

        return classified

    @classmethod
    def _classify_bbox(
        cls,
        *,
        bbox: tuple[float, float, float, float],
        cx: float,
        cy: float,
        aspect: float,
        area_ratio: float,
        ink_ratio: float,
    ) -> tuple[str, float]:
        _x0, y0, _x1, y1 = bbox

        if cx >= 0.48 and cy >= 0.58 and area_ratio <= 0.28:
            return "stamp", 0.82 + min(0.12, ink_ratio)

        if cy <= 0.16 and 0.18 <= cx <= 0.82 and (y1 - y0) <= 0.16:
            return "title", 0.78

        if cx <= 0.58 and cy <= 0.42 and area_ratio <= 0.35 and aspect >= 0.65:
            if ink_ratio >= 0.02:
                return "bom", 0.74 + min(0.15, ink_ratio * 2.0)

        if cy >= 0.10 and cy <= 0.68 and area_ratio >= 0.08:
            return "dimensions", 0.68

        if area_ratio >= 0.20:
            return "drawing_body", 0.62

        return "text_block", 0.45

    @classmethod
    def _reading_order(
        cls,
        classified: list[tuple[tuple[int, int, int, int], str, float]],
    ) -> list[int]:
        import numpy as np

        if not classified:
            return []

        centers = []

        for index, (bbox, _category, _confidence) in enumerate(classified):
            x0, y0, x1, y1 = bbox
            centers.append((index, (x0 + x1) / 2.0, (y0 + y1) / 2.0))

        xs = [item[1] for item in centers]
        median_x = float(np.median(xs)) if xs else 0.0

        def sort_key(item: tuple[int, float, float]) -> tuple[int, float, float]:
            _idx, cx, cy = item
            col = 0 if cx < median_x else 1
            return (col, cy, cx)

        ordered = sorted(centers, key=sort_key)

        ranks = [0] * len(classified)

        for order, (index, _cx, _cy) in enumerate(ordered):
            ranks[index] = order

        return ranks

    @classmethod
    def _normalize_blocks(
        cls,
        classified: list[tuple[tuple[int, int, int, int], str, float]],
        reading_order: list[int],
        *,
        width: int,
        height: int,
    ) -> tuple[LayoutBlock, ...]:
        blocks: list[LayoutBlock] = []

        for index, ((x0, y0, x1, y1), category, confidence) in enumerate(classified):
            nx0, ny0, nx1, ny1 = (
                x0 / width,
                y0 / height,
                x1 / width,
                y1 / height,
            )
            area_ratio = ((x1 - x0) * (y1 - y0)) / max(1, width * height)
            blocks.append(
                LayoutBlock(
                    bbox=(nx0, ny0, nx1, ny1),
                    category=category,
                    confidence=confidence,
                    reading_order=reading_order[index] if index < len(reading_order) else index,
                    area_ratio=area_ratio,
                )
            )

        return tuple(blocks)

    @classmethod
    def _merge_semantic_regions(
        cls,
        blocks: tuple[LayoutBlock, ...],
    ) -> tuple[dict[str, list[float]], float]:
        buckets: dict[str, list[tuple[float, float, float, float]]] = {
            region: [] for region in cls._SEMANTIC_REGIONS
        }
        confidences: list[float] = []

        mapping = {
            "stamp": "stamp",
            "title": "title",
            "bom": "bom",
            "dimensions": "dimensions",
            "drawing_body": "drawing_body",
            "text_block": "dimensions",
        }

        for block in blocks:
            target = mapping.get(block.category)

            if not target:
                continue

            buckets[target].append(block.bbox)
            confidences.append(block.confidence)

        semantic: dict[str, list[float]] = {}

        for region, items in buckets.items():
            if not items:
                continue

            semantic[region] = cls._union_bbox(items)

        if "dimensions" not in semantic and buckets["drawing_body"]:
            semantic["dimensions"] = cls._union_bbox(buckets["drawing_body"])

        overall = sum(confidences) / len(confidences) if confidences else 0.0

        return semantic, overall

    @classmethod
    def _union_bbox(cls, boxes: list[tuple[float, float, float, float]]) -> list[float]:
        x0 = min(box[0] for box in boxes)
        y0 = min(box[1] for box in boxes)
        x1 = max(box[2] for box in boxes)
        y1 = max(box[3] for box in boxes)

        return [
            max(0.0, min(1.0, x0)),
            max(0.0, min(1.0, y0)),
            max(0.0, min(1.0, x1)),
            max(0.0, min(1.0, y1)),
        ]

    @classmethod
    def _refine_with_static_priors(
        cls,
        semantic: dict[str, list[float]],
        confidence: float,
    ) -> dict[str, list[float]]:
        static = cls._static_region_bboxes()
        blend = max(0.35, min(0.85, confidence))
        refined: dict[str, list[float]] = {}

        for key in _DRAWING_REGION_KEYS:
            detected = semantic.get(key)
            prior = static.get(key)

            if detected and prior:
                refined[key] = [
                    blend * detected[index] + (1.0 - blend) * prior[index]
                    for index in range(4)
                ]
            elif detected:
                refined[key] = list(detected)
            elif prior:
                refined[key] = list(prior)

        return refined


_DRAWING_REGION_KEYS = ("stamp", "title", "bom", "dimensions")
_DEFAULT_STATIC_BBOXES = {
    "stamp": [0.5, 0.62, 1.0, 1.0],
    "title": [0.2, 0.0, 0.8, 0.12],
    "bom": [0.0, 0.0, 0.55, 0.35],
    "dimensions": [0.0, 0.12, 1.0, 0.62],
}
