export const TYPED_SIGNATURE_FONT_FAMILY =
  '"Segoe Script", "Brush Script MT", "Apple Chancery", cursive';

export type BlobFromTypedSignatureNameOptions = {
  width?: number;
  height?: number;
  minFontSize?: number;
  maxFontSize?: number;
  horizontalPadding?: number;
  verticalPadding?: number;
};

type TextMetricsLike = Pick<
  TextMetrics,
  "width" | "actualBoundingBoxAscent" | "actualBoundingBoxDescent"
>;

function measureTypedSignature(
  ctx: CanvasRenderingContext2D,
  text: string,
  fontSize: number,
): TextMetricsLike {
  ctx.font = `italic ${fontSize}px ${TYPED_SIGNATURE_FONT_FAMILY}`;
  const metrics = ctx.measureText(text);
  const ascent = metrics.actualBoundingBoxAscent || fontSize * 0.72;
  const descent = metrics.actualBoundingBoxDescent || fontSize * 0.28;
  return {
    width: metrics.width,
    actualBoundingBoxAscent: ascent,
    actualBoundingBoxDescent: descent,
  };
}

/** Calcula font-size que cabe no canvas sem cortar início/fim de fontes script. */
export function fitTypedSignatureFontSize(
  ctx: CanvasRenderingContext2D,
  text: string,
  maxWidth: number,
  maxHeight: number,
  minFontSize: number,
  maxFontSize: number,
): number {
  let low = minFontSize;
  let high = maxFontSize;
  let best = minFontSize;

  while (low <= high) {
    const candidate = Math.floor((low + high) / 2);
    const metrics = measureTypedSignature(ctx, text, candidate);
    const textHeight =
      (metrics.actualBoundingBoxAscent ?? candidate) +
      (metrics.actualBoundingBoxDescent ?? candidate * 0.28);
    if (metrics.width <= maxWidth && textHeight <= maxHeight) {
      best = candidate;
      low = candidate + 1;
    } else {
      high = candidate - 1;
    }
  }

  return best;
}

/** Gera PNG transparente com nome em fonte cursiva, sem cortar bordas. */
export async function blobFromTypedSignatureName(
  text: string,
  width = 640,
  height = 220,
  options: BlobFromTypedSignatureNameOptions = {},
): Promise<Blob | null> {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const horizontalPadding = options.horizontalPadding ?? 32;
  const verticalPadding = options.verticalPadding ?? 20;
  const minFontSize = options.minFontSize ?? 22;
  const maxFontSize = options.maxFontSize ?? 56;
  const maxTextWidth = Math.max(1, width - horizontalPadding * 2);
  const maxTextHeight = Math.max(1, height - verticalPadding * 2);

  const canvas = document.createElement("canvas");
  const dpr = Math.max(1, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  const ctx = canvas.getContext("2d");
  if (!ctx) return null;

  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#0f172a";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";

  const fontSize = fitTypedSignatureFontSize(
    ctx,
    trimmed,
    maxTextWidth,
    maxTextHeight,
    minFontSize,
    maxFontSize,
  );
  ctx.font = `italic ${fontSize}px ${TYPED_SIGNATURE_FONT_FAMILY}`;
  ctx.fillText(trimmed, width / 2, height / 2);

  return new Promise((resolve) => {
    canvas.toBlob((blob) => resolve(blob), "image/png");
  });
}
