/** Centraliza a tinta opaca de um PNG transparente em um canvas de destino. */

export type CenterSignatureOptions = {
  targetWidth?: number;
  targetHeight?: number;
  padding?: number;
  alphaThreshold?: number;
  /** Margem extra ao recortar a tinta — preserva anti-alias e hastes de fonte script. */
  cropInset?: number;
};

const DEFAULTS = {
  targetWidth: 640,
  targetHeight: 220,
  padding: 24,
  alphaThreshold: 8,
  cropInset: 4,
} as const;

/**
 * Recorta a tinta (pixels com alpha) e redesenha centralizada no tamanho alvo.
 * Se não houver tinta ou o ambiente falhar, devolve o blob original.
 */
export async function centerSignaturePngBlob(
  source: Blob,
  options: CenterSignatureOptions = {},
): Promise<Blob> {
  const targetWidth = options.targetWidth ?? DEFAULTS.targetWidth;
  const targetHeight = options.targetHeight ?? DEFAULTS.targetHeight;
  const padding = options.padding ?? DEFAULTS.padding;
  const alphaThreshold = options.alphaThreshold ?? DEFAULTS.alphaThreshold;
  const cropInset = options.cropInset ?? DEFAULTS.cropInset;

  try {
    const bitmap = await createImageBitmap(source);
    const sourceCanvas = document.createElement("canvas");
    sourceCanvas.width = bitmap.width;
    sourceCanvas.height = bitmap.height;
    const sourceCtx = sourceCanvas.getContext("2d");
    if (!sourceCtx) {
      bitmap.close();
      return source;
    }
    sourceCtx.drawImage(bitmap, 0, 0);
    bitmap.close();

    const { data, width, height } = sourceCtx.getImageData(
      0,
      0,
      sourceCanvas.width,
      sourceCanvas.height,
    );
    let minX = width;
    let minY = height;
    let maxX = -1;
    let maxY = -1;
    for (let y = 0; y < height; y += 1) {
      for (let x = 0; x < width; x += 1) {
        const alpha = data[(y * width + x) * 4 + 3];
        if (alpha > alphaThreshold) {
          if (x < minX) minX = x;
          if (y < minY) minY = y;
          if (x > maxX) maxX = x;
          if (y > maxY) maxY = y;
        }
      }
    }
    if (maxX < 0 || maxY < 0) return source;

    minX = Math.max(0, minX - cropInset);
    minY = Math.max(0, minY - cropInset);
    maxX = Math.min(width - 1, maxX + cropInset);
    maxY = Math.min(height - 1, maxY + cropInset);

    const inkW = maxX - minX + 1;
    const inkH = maxY - minY + 1;
    const availW = Math.max(1, targetWidth - padding * 2);
    const availH = Math.max(1, targetHeight - padding * 2);
    const scale = Math.min(availW / inkW, availH / inkH);
    const drawW = inkW * scale;
    const drawH = inkH * scale;
    const dx = (targetWidth - drawW) / 2;
    const dy = (targetHeight - drawH) / 2;

    const out = document.createElement("canvas");
    out.width = targetWidth;
    out.height = targetHeight;
    const outCtx = out.getContext("2d");
    if (!outCtx) return source;
    outCtx.clearRect(0, 0, targetWidth, targetHeight);
    outCtx.drawImage(sourceCanvas, minX, minY, inkW, inkH, dx, dy, drawW, drawH);

    return await new Promise<Blob>((resolve) => {
      out.toBlob((blob) => resolve(blob ?? source), "image/png");
    });
  } catch {
    return source;
  }
}
