"""PaddleOCR adapter — experimental local OCR engine (R7-06).

Optional dependency — absent → ``provider_unavailable``. Implements
``OcrExtractionPort`` with governed model provisioning:

- ``ENG_DRAWING_OCR_MODEL_DIR`` — directory with pre-provisioned
  ``text_detection``/``text_recognition`` model dirs (approved process,
  checksum/provenance recorded outside the request path). When set, the
  adapter points PaddleOCR at those exact dirs — paddlex never
  downloads implicitly.
- ``ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD`` = ``"true"`` — development
  only: allows PaddleOCR to fetch official models to its local cache.
  Default/absent → download forbidden; missing models yield
  ``model_not_provisioned`` honestly.
- ``ENG_DRAWING_OCR_TIMEOUT_SECONDS`` — per-call wall clock (default
  120s). A timed-out native call cannot be killed in-thread; the bound
  is enforced on the future and the limitation is recorded.
- ``DISABLE_MODEL_SOURCE_CHECK`` is always set — no connectivity probe
  / egress on init.

Local execution only: CPU, no SaaS, no telemetry, no credentials.
"""

from __future__ import annotations

import concurrent.futures
import io
import os
import time
from pathlib import Path

from engineering_app.application.drawing.extraction_ports import (
    OcrResult,
    OcrToken,
    ProviderCapability,
)
from engineering_app.application.drawing.pdf_text_extractor import (
    PdfExtractionError,
)

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore

    _CV2_AVAILABLE = True
except Exception:  # pragma: no cover - environment-dependent
    cv2 = None  # type: ignore
    np = None  # type: ignore
    _CV2_AVAILABLE = False

try:
    os.environ.setdefault("DISABLE_MODEL_SOURCE_CHECK", "True")
    import paddleocr  # type: ignore
    from paddleocr import PaddleOCR  # type: ignore

    _PADDLEOCR_AVAILABLE = True
    _PADDLEOCR_VERSION = getattr(paddleocr, "__version__", "unknown")
    try:
        import paddle  # type: ignore

        _PADDLE_VERSION = getattr(paddle, "__version__", "unknown")
    except Exception:
        _PADDLE_VERSION = "unknown"
except Exception:  # pragma: no cover - environment-dependent
    paddleocr = None  # type: ignore
    PaddleOCR = None  # type: ignore
    _PADDLEOCR_AVAILABLE = False
    _PADDLEOCR_VERSION = "not_installed"
    _PADDLE_VERSION = "not_installed"

_MAX_IMAGE_BYTES = 40 * 1024 * 1024
_MAX_PIXELS = 40_000_000
_MAX_TOKENS = 2000
_MODEL_DIR_ENV = "ENG_DRAWING_OCR_MODEL_DIR"
_DOWNLOAD_ENV = "ENG_DRAWING_OCR_ALLOW_MODEL_DOWNLOAD"
_TIMEOUT_ENV = "ENG_DRAWING_OCR_TIMEOUT_SECONDS"
_LANG_ENV = "ENG_DRAWING_OCR_LANG"
_DEFAULT_TIMEOUT_S = 120.0


def _env_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() == "true"


def _timeout_seconds() -> float:
    raw = os.getenv(_TIMEOUT_ENV, "").strip()
    try:
        value = float(raw) if raw else _DEFAULT_TIMEOUT_S
    except ValueError:
        return _DEFAULT_TIMEOUT_S
    return min(max(value, 5.0), 600.0)


class PaddleOcrAdapter:
    """Implements OcrExtractionPort via PaddleOCR (lazy engine init)."""

    provider_id = "paddleocr_experimental"

    def __init__(self) -> None:
        self._engine = None
        self._engine_error: str | None = None
        self._model_source: str = "unresolved"
        self._det_dir: str | None = None
        self._rec_dir: str | None = None

    # -- governed engine resolution -------------------------------------

    def _resolve_models(self) -> bool:
        """Decide model source WITHOUT instantiating the engine.

        Returns True when a usable source exists; otherwise leaves the
        honest reason in ``self._engine_error``.
        """
        base = os.getenv(_MODEL_DIR_ENV, "").strip()
        if base:
            root = Path(base)
            det = root / "text_detection"
            rec = root / "text_recognition"
            if not root.is_dir():
                self._engine_error = (
                    f"model_not_provisioned:{_MODEL_DIR_ENV}_missing_dir"
                )
                return False
            # aceita layout dedicado {det,rec} ou raiz com modelos oficiais
            if det.is_dir() and rec.is_dir():
                self._det_dir = str(det)
                self._rec_dir = str(rec)
                self._model_source = f"provisioned_dir:{root}"
                return True
            if any(root.iterdir()):
                # diretório provisionado único — paddlex resolve nomes
                # oficiais dentro dele sem rede.
                self._model_source = f"provisioned_dir:{root}"
                return True
            self._engine_error = (
                f"model_not_provisioned:{_MODEL_DIR_ENV}_empty_dir"
            )
            return False
        if _env_flag(_DOWNLOAD_ENV):
            self._model_source = "paddlex_official_auto_download"
            return True
        self._engine_error = (
            "model_not_provisioned:set_"
            f"{_MODEL_DIR_ENV}_or_{_DOWNLOAD_ENV}=true(dev_only)"
        )
        return False

    def _get_engine(self):
        if self._engine is not None:
            return self._engine
        if self._engine_error:
            raise PdfExtractionError(self._engine_error)
        if not (_PADDLEOCR_AVAILABLE and _CV2_AVAILABLE):
            raise PdfExtractionError(
                "provider_unavailable:paddleocr_not_installed"
            )
        if not self._resolve_models():
            raise PdfExtractionError(self._engine_error)
        kwargs: dict = {
            "lang": os.getenv(_LANG_ENV, "en").strip() or "en",
            "use_doc_orientation_classify": False,
            "use_doc_unwarping": False,
            "use_textline_orientation": False,
        }
        if self._det_dir and self._rec_dir:
            kwargs["text_detection_model_dir"] = self._det_dir
            kwargs["text_recognition_model_dir"] = self._rec_dir
        try:
            self._engine = PaddleOCR(**kwargs)
        except Exception as exc:
            self._engine_error = (
                f"model_load_failed:{exc.__class__.__name__}"
            )
            raise PdfExtractionError(self._engine_error) from exc
        return self._engine

    # -- OcrExtractionPort ------------------------------------------------

    def extract_text(self, image_bytes: bytes) -> OcrResult:
        if not (_PADDLEOCR_AVAILABLE and _CV2_AVAILABLE):
            raise PdfExtractionError(
                "provider_unavailable:paddleocr_not_installed"
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

        engine = self._get_engine()
        timeout_s = _timeout_seconds()
        t0 = time.monotonic()
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(engine.predict, img)
        try:
            results = future.result(timeout=timeout_s)
        except concurrent.futures.TimeoutError as exc:
            future.cancel()
            executor.shutdown(wait=False)
            self._engine = None
            raise PdfExtractionError(
                f"ocr_timeout:{timeout_s:.0f}s_exceeded"
            ) from exc
        except Exception as exc:
            executor.shutdown(wait=False)
            # O predictor Paddle permanece inválido depois de
            # RuntimeError; a próxima página não reutiliza essa instância.
            self._engine = None
            raise PdfExtractionError(
                f"ocr_failed:{exc.__class__.__name__}"
            ) from exc
        executor.shutdown(wait=False)
        duration_ms = round((time.monotonic() - t0) * 1000)

        tokens: list[OcrToken] = []
        limitations: list[str] = []
        for res in results or []:
            texts = list(res.get("rec_texts") or [])
            scores = list(res.get("rec_scores") or [])
            polys = res.get("rec_polys")
            if polys is None:
                polys = res.get("dt_polys")
            if polys is None:
                polys = res.get("rec_boxes")
            for i, text in enumerate(texts):
                if len(tokens) >= _MAX_TOKENS:
                    limitations.append(
                        f"token_limit:{_MAX_TOKENS}_reached"
                    )
                    break
                conf = (
                    float(scores[i])
                    if i < len(scores) and scores[i] is not None
                    else None
                )
                box = _normalize_box(polys, i)
                tokens.append(OcrToken(text=str(text), confidence=conf, box=box))

        text = "\n".join(t.text for t in tokens)
        return OcrResult(
            provider_id=self.provider_id,
            text=text,
            tokens=tokens,
            duration_ms=duration_ms,
            limitations=limitations,
            metadata={
                "engine": "paddleocr",
                "paddleocr_version": _PADDLEOCR_VERSION,
                "paddle_version": _PADDLE_VERSION,
                "model_source": self._model_source,
                "lang": os.getenv(_LANG_ENV, "en").strip() or "en",
                "device": "cpu",
                "coordinate_system": "pixels_top_left_polygon4",
                "timeout_seconds": timeout_s,
                "image_width": width,
                "image_height": height,
                "ocr_text_only": True,
            },
        )

    def capability_descriptor(self) -> ProviderCapability:
        available = _PADDLEOCR_AVAILABLE and _CV2_AVAILABLE
        return ProviderCapability(
            provider_id=self.provider_id,
            version=_PADDLEOCR_VERSION,
            status="experimental" if available else "unavailable",
            capabilities={
                "ocr": available,
                "bounding_boxes": available,
                "confidence": available,
                "rotated_text": False,
                "scanned_pdf": available,
            },
            formats=["png", "jpeg"],
            runs_local=True,
            requires_credentials=False,
            license="Apache-2.0",
            limits={
                "max_image_bytes": _MAX_IMAGE_BYTES,
                "max_pixels": _MAX_PIXELS,
                "max_tokens": _MAX_TOKENS,
                "timeout_seconds": _DEFAULT_TIMEOUT_S,
                "device": "cpu",
                "model_dir_env": _MODEL_DIR_ENV,
            },
            license_notes=(
                "Apache-2.0 — paddleocr+paddlepaddle; modelos PP-OCR "
                "oficiais PaddlePaddle (Apache-2.0); execução local CPU, "
                "sem egress SaaS quando provisionada."
            ),
        )


def _normalize_box(polys, index: int) -> list[float] | None:
    """Provider polygon → flat [x1,y1,...,x4,y4] list (JSON-safe)."""
    if polys is None:
        return None
    try:
        poly = polys[index]
    except Exception:
        return None
    try:
        pts = np.asarray(poly, dtype=float).reshape(-1, 2)
    except Exception:
        try:
            pts = [[float(v) for v in poly]]
        except Exception:
            return None
    return [round(float(v), 2) for pair in pts for v in pair]
