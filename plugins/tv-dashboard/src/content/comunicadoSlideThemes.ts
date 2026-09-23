import type { ComunicadoBackground, ComunicadoConfig } from "@delpi/tv-dashboard-presentation";
import {
  getDelpiBrandMode,
  getDelpiBrandTheme,
  type DelpiBrandModeKey,
} from "@delpi/tv-dashboard-presentation";

export type ComunicadoSlideTheme = {
  key: string;
  label: string;
  background: ComunicadoBackground;
  textColor: string;
  accent: string;
  shapeStroke: string;
  /** Modo de marca Delpi quando aplicável. */
  brandMode?: DelpiBrandModeKey;
  /** Liga logo institucional ao aplicar este tema. */
  showLogo?: boolean;
};

function themeFromBrandBinding(binding: {
  key: string;
  label: string;
  mode: DelpiBrandModeKey;
  showLogo?: boolean;
}): ComunicadoSlideTheme {
  const mode = getDelpiBrandMode(binding.mode);
  return {
    key: binding.key,
    label: binding.label,
    background: mode.background as ComunicadoBackground,
    textColor: mode.colors.onBg,
    accent: mode.colors.accent,
    shapeStroke: mode.colors.shapeStroke,
    brandMode: binding.mode,
    showLogo: binding.showLogo !== false,
  };
}

const brandThemes: ComunicadoSlideTheme[] = getDelpiBrandTheme().slideThemeBindings.map(
  themeFromBrandBinding,
);

/** Temas não-Delpi (galeria). Delpi claro/escuro vêm do JSON canônico. */
const EXTRA_SLIDE_THEMES: ComunicadoSlideTheme[] = [
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
];

export const COMUNICADO_SLIDE_THEMES: ComunicadoSlideTheme[] = [
  ...brandThemes,
  ...EXTRA_SLIDE_THEMES,
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
  const next: ComunicadoConfig = {
    ...config,
    background: theme.background,
    blocks,
  };
  if (theme.showLogo && theme.brandMode) {
    next.brandThemeKey = theme.key;
  } else {
    delete next.brandThemeKey;
  }
  return next;
}
