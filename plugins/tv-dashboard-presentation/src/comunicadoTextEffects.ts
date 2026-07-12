/** Efeitos tipográficos PPT (text-shadow / contorno) — presets + paint. */

import type { CSSProperties } from "react";

import { applyTextEffectStyleToCss } from "@delpi/plugin-ui/index";

export type ComunicadoTextEffectFields = {
  textShadow?: string;
  textStrokeColor?: string;
  textStrokeWidth?: number;
  textReflection?: boolean;
};

export type ComunicadoTextShadowPreset = {
  id: string;
  label: string;
  /** CSS `text-shadow`; omitido = sem sombra. */
  value?: string;
};

export const COMUNICADO_TEXT_SHADOW_PRESETS: readonly ComunicadoTextShadowPreset[] = [
  { id: "none", label: "Sem sombra" },
  { id: "soft", label: "Suave", value: "0 1px 2px rgba(0,0,0,0.35)" },
  { id: "offset", label: "Deslocada", value: "2px 2px 0 rgba(0,0,0,0.45)" },
  { id: "strong", label: "Forte", value: "0 2px 6px rgba(0,0,0,0.55)" },
  { id: "glow", label: "Brilho", value: "0 0 8px rgba(8,155,219,0.85)" },
] as const;

export function applyComunicadoTextEffectsToCss(
  style: ComunicadoTextEffectFields | null | undefined,
  css: CSSProperties,
): void {
  applyTextEffectStyleToCss(style, css);
}

export function resolveTextShadowPresetId(value: string | undefined): string {
  const normalized = value?.trim() ?? "";
  if (!normalized) return "none";
  const match = COMUNICADO_TEXT_SHADOW_PRESETS.find((preset) => (preset.value ?? "") === normalized);
  return match?.id ?? "custom";
}
