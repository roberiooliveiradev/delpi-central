/**
 * Logo institucional Delpi no palco — variante clara/escura conforme o fundo.
 * Custom master.logo (URL/asset) vence; sem custom → brand default em todo slide livre.
 */

import { relativeLuminance, tryParseCssColorToHex } from "@delpi/plugin-ui/index";

import logoDelpiOnDark from "./assets/logoDelpiOnDark.png";
import logoDelpiOnLight from "./assets/logoDelpiOnLight.png";
import {
  resolveComunicadoBackgroundUnderlay,
} from "./comunicadoBackgroundStyle";
import type { ComunicadoBackground } from "./comunicadoTypes";

export const DELPI_BRAND_LOGO_FRAME = { x: 2, y: 2, w: 14, h: 9 } as const;

export type DelpiBrandLogoVariant = "onDark" | "onLight";

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

/**
 * True quando o fundo efetivo é escuro (logo clara / onDark).
 * Gradiente: média das pontas; imagem: underlay; cor: valor.
 */
export function isComunicadoBackgroundDark(
  background: ComunicadoBackground | undefined,
): boolean {
  const underlay = resolveComunicadoBackgroundUnderlay(background);
  if (underlay.type === "gradient") {
    const from = luminanceOfCssColor(underlay.from, "#0f172a");
    const to = luminanceOfCssColor(underlay.to, "#0f172a");
    if (underlay.stops && underlay.stops.length >= 2) {
      const sum = underlay.stops.reduce(
        (acc, stop) => acc + luminanceOfCssColor(stop.color, "#0f172a"),
        0,
      );
      return sum / underlay.stops.length < 0.45;
    }
    return (from + to) / 2 < 0.45;
  }
  return luminanceOfCssColor(underlay.value, "#ffffff") < 0.45;
}

export function resolveDelpiBrandLogoVariant(
  background: ComunicadoBackground | undefined,
): DelpiBrandLogoVariant {
  return isComunicadoBackgroundDark(background) ? "onDark" : "onLight";
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
 * Logo a pintar no palco: custom master se houver URL; senão brand Delpi
 * (onDark em fundo escuro, onLight em fundo claro).
 */
export function resolveStageMasterLogo(args: {
  background: ComunicadoBackground | undefined;
  customLogo?: CustomLogo;
}): StageMasterLogo {
  const customUrl =
    typeof args.customLogo?.url === "string" ? args.customLogo.url.trim() : "";
  if (customUrl) {
    const frame = args.customLogo?.frame;
    return {
      url: customUrl,
      frame: {
        x: frame?.x ?? DELPI_BRAND_LOGO_FRAME.x,
        y: frame?.y ?? DELPI_BRAND_LOGO_FRAME.y,
        w: frame?.w ?? DELPI_BRAND_LOGO_FRAME.w,
        h: frame?.h ?? DELPI_BRAND_LOGO_FRAME.h,
      },
      opacity:
        typeof args.customLogo?.opacity === "number"
          ? Math.max(0, Math.min(1, args.customLogo.opacity))
          : 1,
      source: "custom",
    };
  }
  const variant = resolveDelpiBrandLogoVariant(args.background);
  return {
    url: delpiBrandLogoUrl(variant),
    frame: { ...DELPI_BRAND_LOGO_FRAME },
    opacity: 1,
    source: "brand",
    variant,
  };
}
