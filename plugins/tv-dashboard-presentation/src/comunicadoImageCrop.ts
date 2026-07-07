import type { CSSProperties } from "react";

export type ComunicadoImageCrop = {
  /** Origem horizontal visível (% da largura da imagem). */
  x: number;
  /** Origem vertical visível (% da altura da imagem). */
  y: number;
  /** Largura visível (% da imagem). */
  w: number;
  /** Altura visível (% da imagem). */
  h: number;
};

export const COMUNICADO_IMAGE_CROP_FULL: ComunicadoImageCrop = {
  x: 0,
  y: 0,
  w: 100,
  h: 100,
};

export function normalizeComunicadoImageCrop(value: unknown): ComunicadoImageCrop | undefined {
  if (!value || typeof value !== "object") return undefined;
  const raw = value as Record<string, unknown>;
  const num = (key: keyof ComunicadoImageCrop, fallback: number) => {
    const parsed = typeof raw[key] === "number" ? raw[key] : Number(raw[key]);
    return Number.isFinite(parsed) ? parsed : fallback;
  };
  const w = Math.max(5, Math.min(100, num("w", 100)));
  const h = Math.max(5, Math.min(100, num("h", 100)));
  const x = Math.max(0, Math.min(100 - w, num("x", 0)));
  const y = Math.max(0, Math.min(100 - h, num("y", 0)));
  if (x === 0 && y === 0 && w >= 100 && h >= 100) return undefined;
  return { x, y, w, h };
}

export function isFullComunicadoImageCrop(crop: ComunicadoImageCrop | undefined): boolean {
  if (!crop) return true;
  return crop.x === 0 && crop.y === 0 && crop.w >= 100 && crop.h >= 100;
}

/** Posiciona a imagem para exibir só a região recortada dentro do frame. */
export function comunicadoImageCropCssProperties(
  crop: ComunicadoImageCrop | undefined,
  objectFit: "cover" | "contain" = "contain",
): CSSProperties {
  if (!crop || isFullComunicadoImageCrop(crop)) {
    return { objectFit };
  }
  const safeW = Math.max(crop.w, 1);
  const safeH = Math.max(crop.h, 1);
  return {
    objectFit: "fill",
    width: `${(100 / safeW) * 100}%`,
    height: `${(100 / safeH) * 100}%`,
    maxWidth: "none",
    maxHeight: "none",
    marginLeft: `${-(crop.x / safeW) * 100}%`,
    marginTop: `${-(crop.y / safeH) * 100}%`,
  };
}
