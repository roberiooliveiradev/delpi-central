import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

export type ImagePasteFrameOptions = {
  designWidth?: number;
  designHeight?: number;
  /** Largura máxima do quadro (% da página). */
  maxWidthPercent?: number;
  /** Altura máxima do quadro (% da página). */
  maxHeightPercent?: number;
  xPercent?: number;
  yPercent?: number;
};

/**
 * Frame % que preserva a proporção da imagem dentro de um teto na página.
 * Evita colar PNG largo num retângulo 80×56 default (distorce com object-fit fill/crop).
 */
export function frameForImageNaturalSize(
  naturalWidth: number,
  naturalHeight: number,
  options: ImagePasteFrameOptions = {},
): ComunicadoFrame {
  const designWidth = options.designWidth ?? 1920;
  const designHeight = options.designHeight ?? 1080;
  const maxWidthPercent = options.maxWidthPercent ?? 36;
  const maxHeightPercent = options.maxHeightPercent ?? 32;
  const xPercent = options.xPercent ?? 10;
  const yPercent = options.yPercent ?? 15;

  if (
    !Number.isFinite(naturalWidth) ||
    !Number.isFinite(naturalHeight) ||
    naturalWidth <= 0 ||
    naturalHeight <= 0
  ) {
    return { x: xPercent, y: yPercent, w: maxWidthPercent, h: maxHeightPercent };
  }

  const maxWPx = (maxWidthPercent / 100) * designWidth;
  const maxHPx = (maxHeightPercent / 100) * designHeight;
  const scale = Math.min(maxWPx / naturalWidth, maxHPx / naturalHeight);
  const wPx = Math.max(1, naturalWidth * scale);
  const hPx = Math.max(1, naturalHeight * scale);

  return {
    x: xPercent,
    y: yPercent,
    w: (wPx / designWidth) * 100,
    h: (hPx / designHeight) * 100,
  };
}

/** Lê dimensões naturais de um File de imagem (bitmap ou Image). */
export async function readImageNaturalSize(
  file: File,
): Promise<{ width: number; height: number } | null> {
  if (typeof createImageBitmap === "function") {
    try {
      const bitmap = await createImageBitmap(file);
      const size = { width: bitmap.width, height: bitmap.height };
      bitmap.close?.();
      return size;
    } catch {
      /* fallback Image */
    }
  }

  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const img = new Image();
    img.onload = () => {
      const size = { width: img.naturalWidth, height: img.naturalHeight };
      URL.revokeObjectURL(url);
      resolve(size.width > 0 && size.height > 0 ? size : null);
    };
    img.onerror = () => {
      URL.revokeObjectURL(url);
      resolve(null);
    };
    img.src = url;
  });
}
