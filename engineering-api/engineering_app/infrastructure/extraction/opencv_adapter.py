"""OpenCV preprocessing adapter — experimental visual pipeline (R7-05).

Optional dependency — absent → ``provider_unavailable``, never
fabricated output. Implements ``ImagePreprocessingPort`` with a small
closed set of governed, reproducible profiles — each transformation is
controlled and traceable (``ops_applied``); no free-form op chaining and
no geometric distortion that would invalidate dimensions.

Profiles:
- ``raw_render`` — decode/re-encode only (control condition).
- ``grayscale`` — luminance conversion.
- ``adaptive_threshold`` — grayscale + mean-c adaptive threshold
  (text-vs-background separation for OCR on drawings).
"""

from __future__ import annotations

from engineering_app.application.drawing.extraction_ports import (
    PreprocessResult,
    ProviderCapability,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
)

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    _CV2_AVAILABLE = True
    _CV2_VERSION = getattr(cv2, "__version__", "unknown")
except Exception:  # pragma: no cover - environment-dependent
    cv2 = None  # type: ignore
    np = None  # type: ignore
    _CV2_AVAILABLE = False
    _CV2_VERSION = "not_installed"

_MAX_IMAGE_BYTES = 40 * 1024 * 1024  # 40 MB raster input
_MAX_PIXELS = 40_000_000  # ~6300x6300 — bound de memória por página

PREPROCESS_PROFILES: tuple[str, ...] = (
    "raw_render",
    "grayscale",
    "adaptive_threshold",
)


class OpencvPreprocessingAdapter:
    """Implements ImagePreprocessingPort via cv2 when present."""

    provider_id = "opencv_preprocess_experimental"

    def preprocess(
        self, image_bytes: bytes, *, mode: str = "grayscale"
    ) -> PreprocessResult:
        if not _CV2_AVAILABLE:
            raise PdfExtractionError(
                "provider_unavailable:opencv_not_installed"
            )
        profile = (mode or "grayscale").strip()
        if profile not in PREPROCESS_PROFILES:
            raise PdfExtractionError(
                f"unknown_preprocess_profile:{profile}"
            )
        if not image_bytes:
            raise PdfExtractionError("empty_image")
        if len(image_bytes) > _MAX_IMAGE_BYTES:
            raise PdfExtractionError(
                f"image_too_large:{len(image_bytes)}>{_MAX_IMAGE_BYTES}"
            )
        try:
            arr = np.frombuffer(image_bytes, dtype=np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        except Exception as exc:
            raise PdfExtractionError(
                f"unreadable_image:{exc.__class__.__name__}"
            ) from exc
        if img is None:
            raise PdfExtractionError("unreadable_image:imdecode_failed")
        height, width = int(img.shape[0]), int(img.shape[1])
        if height * width > _MAX_PIXELS:
            raise PdfExtractionError(
                f"image_pixels_limit:{height * width}>{_MAX_PIXELS}"
            )

        ops: list[str] = []
        if profile == "raw_render":
            out = img
            ops.append("decode_reencode")
        elif profile == "grayscale":
            out = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ops.append("grayscale")
        else:  # adaptive_threshold
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            out = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY,
                blockSize=35,
                C=11,
            )
            ops.extend(["grayscale", "adaptive_threshold_mean_c"])

        ok, encoded = cv2.imencode(".png", out)
        if not ok:
            raise PdfExtractionError("image_encode_failed:png")
        return PreprocessResult(
            image_bytes=encoded.tobytes(),
            profile=profile,
            ops_applied=ops,
            width=width,
            height=height,
            provider_id=self.provider_id,
        )

    def capability_descriptor(self) -> ProviderCapability:
        return ProviderCapability(
            provider_id=self.provider_id,
            version=_CV2_VERSION,
            status=(
                "experimental" if _CV2_AVAILABLE else "unavailable"
            ),
            capabilities={
                "preprocess": _CV2_AVAILABLE,
                "profiles": _CV2_AVAILABLE,
                "geometric_correction": False,
                "ocr": False,
            },
            formats=["png", "jpeg"],
            runs_local=True,
            requires_credentials=False,
            license="Apache-2.0",
            limits={
                "max_image_bytes": _MAX_IMAGE_BYTES,
                "max_pixels": _MAX_PIXELS,
                "profiles": list(PREPROCESS_PROFILES),
            },
            license_notes=(
                "Apache-2.0 — opencv-python-headless; sem GUI/telemetria."
            ),
        )


def detect_graphic_primitives(image_bytes: bytes) -> dict | None:
    """Detecta primitivas gráficas (linhas/retângulos) por morphological
    opening — evidência de bordas de tabela/carimbo (R8.2.2, AC03).

    Retorna dict {h_lines, v_lines, rects} em pixels (top-left) ou
    None quando cv2 indisponível. Determinístico; cada primitiva é
    evidência, não verdade técnica.
    """
    if not _CV2_AVAILABLE:
        return None
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    bin_ = cv2.adaptiveThreshold(
        img, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 12
    )
    # kernels proporcionais ao tamanho — mínimo ~20px de comprimento
    hw, hh = img.shape[1], img.shape[0]
    kh = max(15, hw // 60)
    kv = max(15, hh // 60)
    horiz = cv2.morphologyEx(
        bin_, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (kh, 1)),
    )
    vert = cv2.morphologyEx(
        bin_, cv2.MORPH_OPEN,
        cv2.getStructuringElement(cv2.MORPH_RECT, (1, kv)),
    )
    merged = cv2.bitwise_or(horiz, vert)
    contours, _ = cv2.findContours(
        merged, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )
    rects = []
    page_area = float(hw) * hh
    for c in contours:
        x, y, w2, h2 = cv2.boundingRect(c)
        area = float(w2) * h2
        if w2 >= kh and h2 >= kv and area < page_area * 0.90:
            rects.append([int(x), int(y), int(x + w2), int(y + h2)])
    # linhas longas individuais
    h_lines = []
    for y in range(hh):
        row = horiz[y]
        runs, start = [], None
        for x in range(hw):
            if row[x]:
                start = start if start is not None else x
            elif start is not None:
                if x - start >= kh:
                    runs.append([start, y, x - 1, y])
                start = None
        h_lines.extend(runs)
    v_lines = []
    for x in range(hw):
        col = vert[:, x]
        start = None
        for y in range(hh):
            if col[y]:
                start = start if start is not None else y
            elif start is not None:
                if y - start >= kv:
                    v_lines.append([x, start, x, y - 1])
                start = None
    return {
        "h_lines": h_lines[:400],
        "v_lines": v_lines[:400],
        "rects": sorted(rects, key=lambda r: (r[3]-r[1])*(r[2]-r[0]), reverse=True)[:80],
        "count": {"h": len(h_lines), "v": len(v_lines), "rects": len(rects)},
    }
