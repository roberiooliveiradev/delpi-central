import type { CSSProperties } from "react";
import { fillToCssBackground } from "@delpi/plugin-ui/index";

import type { ComunicadoBackground, ComunicadoBackgroundUnderlay } from "./comunicadoTypes";

export const DEFAULT_IMAGE_BACKGROUND_UNDERLAY: ComunicadoBackgroundUnderlay = {
  type: "color",
  value: "#ffffff",
};

/** URL persistida/enriquecida da imagem de fundo do slide. */
export function comunicadoBackgroundImageUrl(
  background: ComunicadoBackground | undefined,
): string | undefined {
  if (!background || background.type !== "image") return undefined;
  const raw = background.url ?? background.value;
  if (typeof raw !== "string") return undefined;
  const trimmed = raw.trim();
  return trimmed || undefined;
}

function cssUrl(url: string): string {
  return `url(${JSON.stringify(url)})`;
}

function underlayCssProperties(underlay: ComunicadoBackgroundUnderlay): CSSProperties {
  if (underlay.type === "gradient") {
    const stops =
      underlay.stops && underlay.stops.length >= 2
        ? underlay.stops
        : [
            { color: underlay.from, position: 0 },
            { color: underlay.to, position: 100 },
          ];
    return {
      backgroundImage: fillToCssBackground({
        kind: "gradient",
        angle: underlay.angle ?? 180,
        stops,
      }),
    };
  }
  return { backgroundColor: underlay.value || "#ffffff" };
}

/** Underlay efetivo: explícito em image ou o próprio background color/gradient. */
export function resolveComunicadoBackgroundUnderlay(
  background: ComunicadoBackground | undefined,
): ComunicadoBackgroundUnderlay {
  if (!background) return DEFAULT_IMAGE_BACKGROUND_UNDERLAY;
  if (background.type === "image") {
    return background.underlay ?? DEFAULT_IMAGE_BACKGROUND_UNDERLAY;
  }
  if (background.type === "gradient") {
    return {
      type: "gradient",
      from: background.from,
      to: background.to,
      angle: background.angle ?? 180,
      ...(background.stops && background.stops.length >= 2 ? { stops: background.stops } : {}),
    };
  }
  return { type: "color", value: background.value || "#ffffff" };
}

/**
 * Pintura CSS do fundo (cor / gradiente / fallback da imagem).
 * A imagem em tela cheia vai na camada `<img>` (`RichComunicadoBackground`)
 * com `object-fit: cover` — CSS `background-size` sozinho falhava quando a
 * moldura não tinha caixa explícita ou a URL tinha query string.
 */
export function comunicadoBackgroundCssProperties(
  background: ComunicadoBackground | undefined,
  imageUrl?: string,
): CSSProperties {
  const bg = background ?? { type: "color", value: "#ffffff" };
  const resolvedImage = imageUrl?.trim() || comunicadoBackgroundImageUrl(bg);

  if (bg.type === "image" && resolvedImage) {
    return {
      ...underlayCssProperties(resolveComunicadoBackgroundUnderlay(bg)),
      backgroundImage: cssUrl(resolvedImage),
      backgroundSize: "cover",
      backgroundPosition: "center center",
      backgroundRepeat: "no-repeat",
    };
  }

  if (bg.type === "image") {
    return underlayCssProperties(resolveComunicadoBackgroundUnderlay(bg));
  }

  return underlayCssProperties(resolveComunicadoBackgroundUnderlay(bg));
}

/** Cor/gradiente no root; imagem fica só na camada cover (evita crop duplo). */
export function comunicadoBackgroundRootStyle(
  background: ComunicadoBackground | undefined,
): CSSProperties {
  return underlayCssProperties(resolveComunicadoBackgroundUnderlay(background));
}
