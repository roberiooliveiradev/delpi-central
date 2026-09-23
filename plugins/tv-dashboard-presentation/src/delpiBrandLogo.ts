/**
 * Logo institucional Delpi no palco — só quando o slide usa tema Delpi
 * (`brandThemeKey`) ou há logo custom do master.
 * Variante clara/escura vem do modo do tema (não de qualquer fundo).
 */

import { relativeLuminance, tryParseCssColorToHex } from "@delpi/plugin-ui/index";

import logoDelpiOnDark from "./assets/logoDelpiOnDark.png";
import logoDelpiOnLight from "./assets/logoDelpiOnLight.png";
import {
  resolveComunicadoBackgroundUnderlay,
} from "./comunicadoBackgroundStyle";
import type { ComunicadoBackground } from "./comunicadoTypes";
import {
  getDelpiBrandLuminanceThreshold,
  getDelpiBrandLogoConfig,
  getDelpiBrandMode,
  isDelpiBrandSlideThemeKey,
  resolveDelpiBrandLogoFrame,
  resolveDelpiBrandModeFromThemeKey,
  type DelpiBrandLogoVariant,
  type DelpiBrandModeKey,
} from "./delpiBrandTheme";

export type { DelpiBrandLogoVariant };

const logoCfg = getDelpiBrandLogoConfig();

export const DELPI_BRAND_LOGO_SAFE_MARGIN = logoCfg.safeMarginPct;
export const DELPI_BRAND_LOGO_OPACITY = logoCfg.opacity;
export const DELPI_BRAND_LOGO_FRAME = resolveDelpiBrandLogoFrame(logoCfg);

export type StageMasterLogo = {
  url: string;
  frame: { x: number; y: number; w: number; h: number };
  opacity: number;
  source: "custom" | "brand";
  variant?: DelpiBrandLogoVariant;
};

function luminanceOfCssColor(value: string | undefined, fallbackHex: string): number {
  const hex = tryParseCssColorToHex(value) ?? tryParseCssColorToHex(fallbackHex) ?? fallbackHex;
  return relativeLuminance(hex.startsWith("#") ? hex : `#${hex}`);
}

function darkParseFallback(): string {
  return getDelpiBrandLogoConfig().parseFallback.dark;
}

function lightParseFallback(): string {
  return getDelpiBrandLogoConfig().parseFallback.light;
}

/**
 * True quando o fundo efetivo é escuro (logo clara / onDark).
 * Gradiente: média das pontas; imagem: underlay; cor: valor.
 */
export function isComunicadoBackgroundDark(
  background: ComunicadoBackground | undefined,
): boolean {
  const threshold = getDelpiBrandLuminanceThreshold();
  const underlay = resolveComunicadoBackgroundUnderlay(background);
  const darkFb = darkParseFallback();
  if (underlay.type === "gradient") {
    const from = luminanceOfCssColor(underlay.from, darkFb);
    const to = luminanceOfCssColor(underlay.to, darkFb);
    if (underlay.stops && underlay.stops.length >= 2) {
      const sum = underlay.stops.reduce(
        (acc, stop) => acc + luminanceOfCssColor(stop.color, darkFb),
        0,
      );
      return sum / underlay.stops.length < threshold;
    }
    return (from + to) / 2 < threshold;
  }
  return luminanceOfCssColor(underlay.value, lightParseFallback()) < threshold;
}

export function resolveDelpiBrandModeKey(
  background: ComunicadoBackground | undefined,
): DelpiBrandModeKey {
  return isComunicadoBackgroundDark(background) ? "dark" : "light";
}

export function resolveDelpiBrandLogoVariant(
  background: ComunicadoBackground | undefined,
): DelpiBrandLogoVariant {
  return getDelpiBrandMode(resolveDelpiBrandModeKey(background)).logoVariant;
}

export function delpiBrandLogoUrl(variant: DelpiBrandLogoVariant): string {
  return variant === "onDark" ? logoDelpiOnDark : logoDelpiOnLight;
}

type CustomLogo = {
  url?: string | null;
  frame?: { x?: number; y?: number; w?: number; h?: number } | null;
  opacity?: number | null;
} | null;

/**
 * Logo a pintar no palco.
 * - custom master com URL → sempre;
 * - tema Delpi (`brandThemeKey`) → logo institucional do modo;
 * - demais slides → sem logo automática.
 */
export function resolveStageMasterLogo(args: {
  background: ComunicadoBackground | undefined;
  customLogo?: CustomLogo;
  /** Chave do tema de cor Delpi (`delpi-dark` | `delpi-light`). */
  brandThemeKey?: string | null;
  /** Alias: modo direto quando não há key. */
  brandTheme?: DelpiBrandModeKey | null;
}): StageMasterLogo | null {
  const frameDefault = resolveDelpiBrandLogoFrame();
  const customUrl =
    typeof args.customLogo?.url === "string" ? args.customLogo.url.trim() : "";
  if (customUrl) {
    const frame = args.customLogo?.frame;
    return {
      url: customUrl,
      frame: {
        x: frame?.x ?? frameDefault.x,
        y: frame?.y ?? frameDefault.y,
        w: frame?.w ?? frameDefault.w,
        h: frame?.h ?? frameDefault.h,
      },
      opacity:
        typeof args.customLogo?.opacity === "number"
          ? Math.max(0, Math.min(1, args.customLogo.opacity))
          : 1,
      source: "custom",
    };
  }

  const modeFromKey = resolveDelpiBrandModeFromThemeKey(args.brandThemeKey);
  const mode: DelpiBrandModeKey | null =
    modeFromKey ??
    (args.brandTheme === "dark" || args.brandTheme === "light" ? args.brandTheme : null);

  if (!mode) return null;
  if (args.brandThemeKey && !isDelpiBrandSlideThemeKey(args.brandThemeKey)) return null;

  const variant = getDelpiBrandMode(mode).logoVariant;
  return {
    url: delpiBrandLogoUrl(variant),
    frame: { ...frameDefault },
    opacity: getDelpiBrandLogoConfig().opacity,
    source: "brand",
    variant,
  };
}
