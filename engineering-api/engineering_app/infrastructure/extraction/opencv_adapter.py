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
    # E1/VAL-01 B2-R2 — segmentos arbitrários (diagonais/dobras): o
    # opening com kernels retos destrói traços inclinados; HoughLinesP
    # sobre o residual (binarização sem as máscaras h/v) recupera
    # segmentos livres sem duplicar o canal eixo-alinhado. Ângulo
    # agudo 8°–82° filtra o que já é coberto por h_lines/v_lines.
    # Evidência candidata com proveniência — nunca verdade técnica.
    segments: list[dict] = []
    try:
        residual = cv2.bitwise_and(
            bin_, cv2.bitwise_not(cv2.bitwise_or(horiz, vert))
        )
        det_lines = cv2.HoughLinesP(
            residual, 1, np.pi / 180,
            threshold=40,
            minLineLength=max(30, kh),
            maxLineGap=6,
        )
        if det_lines is not None:
            for l in det_lines[:, 0]:
                x1, y1, x2, y2 = (float(v) for v in l)
                dx, dy = x2 - x1, y2 - y1
                length = float((dx * dx + dy * dy) ** 0.5)
                if length <= 0:
                    continue
                ang = float(
                    np.degrees(np.arctan2(abs(dy), abs(dx)))
                )
                if not (8.0 < ang < 82.0):
                    continue
                segments.append({
                    "points_px": [x1, y1, x2, y2],
                    "angle_deg": round(ang, 1),
                    "length_px": round(length, 1),
                    "source": "hough_lines_p_residual",
                })
            # cap determinístico: traços mais longos primeiro —
            # líderes são linhas deliberadas, ruído de texto é curto.
            segments.sort(key=lambda s: -s["length_px"])
            segments = segments[:400]
    except cv2.error:
        segments = []
    # E1/VAL-01 B1 — primitivas circulares (balões de item): HoughCircles
    # sobre a imagem original em tons de cinza. O opening morfológico
    # acima usa kernels retos e descarta curvas; sem este canal a
    # identificação de balões é no-op. Evidência candidata, não verdade.
    circles: list[dict] = []
    try:
        blur = cv2.GaussianBlur(img, (5, 5), 1.2)
        mindim = min(hw, hh)
        det = cv2.HoughCircles(
            blur,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=max(10, mindim // 120),
            param1=120,
            param2=32,
            minRadius=max(4, mindim // 300),
            maxRadius=max(10, mindim // 28),
        )
        if det is not None:
            for x, y, r in np.round(det[0]).astype(int)[:200]:
                circles.append(
                    {
                        "type": "circle",
                        "bounding_box_px": [
                            int(x - r), int(y - r),
                            int(x + r), int(y + r),
                        ],
                        "center_px": [int(x), int(y)],
                        "radius_px": int(r),
                    }
                )
    except cv2.error:
        circles = []
    # E1/VAL-01 B1-R1 — contornos fechados em traço colorido (balões de
    # anotação em cor): a decodificação em grayscale acima descarta cor;
    # traços magenta/azul de balão não produzem voto suficiente no
    # HoughCircles. O canal de saturação isola traço colorido de texto
    # e linhas pretas; o flood-fill da borda na máscara invertida
    # revela interiores delimitados por contorno colorido — genérico a
    # qualquer matiz, posição e layout. Evidência candidata: rótulo,
    # região e associação são decididos a jusante.
    enclosures: list[dict] = []
    try:
        cimg = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if cimg is not None:
            sat = cv2.cvtColor(cimg, cv2.COLOR_BGR2HSV)[:, :, 1]
            walls = cv2.dilate(
                (sat > 60).astype(np.uint8),
                np.ones((3, 3), np.uint8),
                iterations=1,
            )
            free = cv2.copyMakeBorder(
                (1 - walls).astype(np.uint8), 1, 1, 1, 1,
                cv2.BORDER_CONSTANT, value=1,
            )
            cv2.floodFill(
                free,
                np.zeros(
                    (free.shape[0] + 2, free.shape[1] + 2), np.uint8),
                (0, 0), 2,
            )
            enclosed = (free[1:-1, 1:-1] == 1).astype(np.uint8)
            _n, _lab, stats, _cen = cv2.connectedComponentsWithStats(
                enclosed, connectivity=8,
            )
            for i in range(1, _n):
                x, y, ew, eh, _area = stats[i]
                if (
                    ew < 16 or eh < 16
                    or ew > hw // 2 or eh > hh // 2
                ):
                    continue
                enclosures.append(
                    {
                        "type": "enclosure",
                        "bounding_box_px": [
                            int(x), int(y),
                            int(x + ew), int(y + eh),
                        ],
                        "identification_method":
                            "colored_outline_enclosure",
                    }
                )
            enclosures = enclosures[:300]
    except cv2.error:
        enclosures = []
    # E1/VAL-01 B3 — medidas visuais genéricas por região candidata:
    # cobertura de saturação, matiz dominante e razão de aspecto no
    # decode em cor já realizado acima. São observações geométrico-
    # cromáticas (barra alongada saturada × região compacta × mista),
    # não classificação semântica — a leitura de "o que a região
    # representa" e a distinção cor-de-material × cor-de-anotação são
    # decididas a jusante com proveniência. Ausente quando o decode em
    # cor falha (região permanece mensurável só por geometria).
    region_observations: list[dict] = []
    rects_out = sorted(
        rects, key=lambda r: (r[3] - r[1]) * (r[2] - r[0]),
        reverse=True)[:80]
    try:
        cimg = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if cimg is not None:
            hsv_img = cv2.cvtColor(cimg, cv2.COLOR_BGR2HSV)
            sat_ch = hsv_img[:, :, 1]
            hue_ch = hsv_img[:, :, 0]
            boxes = (
                list(rects_out)
                + [e["bounding_box_px"] for e in enclosures]
                + [c["bounding_box_px"] for c in circles]
            )
            for bx in boxes:
                x1, y1, x2, y2 = (
                    max(0, int(bx[0])), max(0, int(bx[1])),
                    min(hw, int(bx[2])), min(hh, int(bx[3])),
                )
                if x2 - x1 < 2 or y2 - y1 < 2:
                    continue
                roi_sat = sat_ch[y1:y2, x1:x2]
                mask = roi_sat > 60
                n_sat = int(mask.sum())
                box_area = float((x2 - x1) * (y2 - y1))
                inner = sum(
                    1
                    for o in boxes
                    if o is not bx
                    and o[0] >= x1 - 2 and o[1] >= y1 - 2
                    and o[2] <= x2 + 2 and o[3] <= y2 + 2
                    and (o[2] - o[0]) * (o[3] - o[1]) < 0.95 * box_area
                )
                entry = {
                    "box_px": [x1, y1, x2, y2],
                    "aspect_ratio": round(
                        max(x2 - x1, y2 - y1)
                        / max(1.0, min(x2 - x1, y2 - y1)), 2),
                    "area_fraction": round(
                        box_area / float(hw * hh), 6),
                    "sat_coverage": round(
                        n_sat / float(mask.size), 3),
                    "dominant_hue": None,
                    "dominant_hue_fraction": 0.0,
                    "saturated_px": n_sat,
                    "inner_primitive_count": inner,
                    # fail-closed: nenhum emissor declara aqui que o
                    # preenchimento é cor de material — cor de
                    # contorno/anotação/esquemático nunca é promovida.
                    "fill_semantics": "schematic_or_unknown",
                }
                if n_sat:
                    hist = np.bincount(
                        hue_ch[y1:y2, x1:x2][mask].ravel(),
                        minlength=180,
                    )
                    dom = int(hist.argmax())
                    entry["dominant_hue"] = dom
                    entry["dominant_hue_fraction"] = round(
                        float(hist[dom]) / n_sat, 2)
                region_observations.append(entry)
    except cv2.error:
        region_observations = []
    return {
        "h_lines": h_lines[:400],
        "v_lines": v_lines[:400],
        "segments": segments,
        "rects": rects_out,
        "circles": circles,
        "enclosures": enclosures,
        "region_observations": region_observations,
        "count": {
            "h": len(h_lines), "v": len(v_lines), "rects": len(rects),
            "circles": len(circles), "enclosures": len(enclosures),
            "region_observations": len(region_observations),
            "segments": len(segments),
        },
    }
