import type { ComunicadoBackground, ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

export type ComunicadoSlideTheme = {
  key: string;
  label: string;
  background: ComunicadoBackground;
  textColor: string;
  accent: string;
  shapeStroke: string;
};

export const COMUNICADO_SLIDE_THEMES: ComunicadoSlideTheme[] = [
  {
    key: "delpi",
    label: "DELPI",
    background: { type: "gradient", from: "#05070a", to: "#0d2840", angle: 180 },
    textColor: "#ffffff",
    accent: "#089bdb",
    shapeStroke: "#e2e8f0",
  },
  {
    key: "midnight",
    label: "Meia-noite",
    background: { type: "color", value: "#0f172a" },
    textColor: "#f8fafc",
    accent: "#6366f1",
    shapeStroke: "#cbd5e1",
  },
  {
    key: "factory",
    label: "Fábrica",
    background: { type: "gradient", from: "#1e293b", to: "#334155", angle: 135 },
    textColor: "#f1f5f9",
    accent: "#f59e0b",
    shapeStroke: "#fde68a",
  },
  {
    key: "forest",
    label: "Verde",
    background: { type: "gradient", from: "#052e16", to: "#14532d", angle: 160 },
    textColor: "#ecfdf5",
    accent: "#34d399",
    shapeStroke: "#a7f3d0",
  },
  {
    key: "alert",
    label: "Alerta",
    background: { type: "gradient", from: "#450a0a", to: "#7f1d1d", angle: 180 },
    textColor: "#fef2f2",
    accent: "#f87171",
    shapeStroke: "#fecaca",
  },
  {
    key: "light",
    label: "Claro",
    background: { type: "color", value: "#f8fafc" },
    textColor: "#0f172a",
    accent: "#089bdb",
    shapeStroke: "#334155",
  },
];

export function applyComunicadoSlideTheme(
  config: ComunicadoConfig,
  theme: ComunicadoSlideTheme,
): ComunicadoConfig {
  const blocks = (config.blocks ?? []).map((block) => {
    if (block.type === "heading" || block.type === "text") {
      return {
        ...block,
        style: { ...block.style, color: theme.textColor },
      };
    }
    if (block.type === "shape") {
      return {
        ...block,
        style: {
          ...block.style,
          fill: theme.accent,
          stroke: theme.shapeStroke,
          color: theme.textColor,
        },
      };
    }
    return block;
  });
  return { ...config, background: theme.background, blocks };
}
