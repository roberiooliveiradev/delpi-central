import type { ComunicadoBlockStyle } from "@delpi/tv-dashboard-presentation";

/** Alinhado ao campo Rotação do frame (−180…180). */
export const COMUNICADO_ROTATION_MIN = -180;
export const COMUNICADO_ROTATION_MAX = 180;

export function normalizeRotationDeg(deg: number): number {
  if (!Number.isFinite(deg)) return 0;
  let next = deg % 360;
  if (next > 180) next -= 360;
  if (next < -180) next += 360;
  return Math.round(next * 10) / 10;
}

export function clampRotationDeg(deg: number): number {
  const n = normalizeRotationDeg(deg);
  return Math.min(COMUNICADO_ROTATION_MAX, Math.max(COMUNICADO_ROTATION_MIN, n));
}

/** Soma delta à rotação atual e normaliza. */
export function rotateBlockStyle(
  style: ComunicadoBlockStyle | null | undefined,
  deltaDeg: number,
): ComunicadoBlockStyle {
  const current = style?.rotation ?? 0;
  return {
    ...(style ?? {}),
    rotation: clampRotationDeg(current + deltaDeg),
  };
}

function flipScale(value: number | undefined): number {
  const current = value == null || !Number.isFinite(value) || value === 0 ? 1 : value;
  return current * -1;
}

/** Espelha no eixo X (esquerda ↔ direita). */
export function flipHorizontalStyle(
  style: ComunicadoBlockStyle | null | undefined,
): ComunicadoBlockStyle {
  return {
    ...(style ?? {}),
    scaleX: flipScale(style?.scaleX),
  };
}

/** Espelha no eixo Y (cima ↔ baixo). */
export function flipVerticalStyle(
  style: ComunicadoBlockStyle | null | undefined,
): ComunicadoBlockStyle {
  return {
    ...(style ?? {}),
    scaleY: flipScale(style?.scaleY),
  };
}

/** Monta `transform` CSS a partir de rotation + scaleX/Y. */
export function buildBlockTransformCss(style: ComunicadoBlockStyle | null | undefined): string | undefined {
  if (!style) return undefined;
  const parts: string[] = [];
  const sx = style.scaleX;
  const sy = style.scaleY;
  if (sx != null && Number.isFinite(sx) && sx !== 1) parts.push(`scaleX(${sx})`);
  if (sy != null && Number.isFinite(sy) && sy !== 1) parts.push(`scaleY(${sy})`);
  if (style.rotation) parts.push(`rotate(${style.rotation}deg)`);
  return parts.length > 0 ? parts.join(" ") : undefined;
}
