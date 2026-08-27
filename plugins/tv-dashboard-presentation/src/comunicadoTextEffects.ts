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

/** Alinhado a {@link COMUNICADO_BOX_SHADOW_PRESETS} (forma) — sem Interna/spread. */
export const COMUNICADO_TEXT_SHADOW_PRESETS: readonly ComunicadoTextShadowPreset[] = [
  { id: "none", label: "Sem sombra" },
  { id: "soft", label: "Suave", value: "0 4px 14px rgba(0, 0, 0, 0.28)" },
  { id: "medium", label: "Média", value: "0 8px 24px rgba(0, 0, 0, 0.35)" },
  { id: "hard", label: "Forte", value: "0 2px 10px rgba(0, 0, 0, 0.55)" },
  {
    id: "elevated",
    label: "Elevada",
    value: "0 1px 3px rgba(0, 0, 0, 0.2), 0 12px 28px rgba(0, 0, 0, 0.12)",
  },
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
  if (match) return match.id;
  return "custom";
}
