import {
  normalizeFillAngle,
  normalizeGradientStops,
  type DelpiFill,
} from "@delpi/plugin-ui/index";

import { DEFAULT_IMAGE_BACKGROUND_UNDERLAY } from "./comunicadoBackgroundStyle";
import type { ComunicadoBackground, ComunicadoBackgroundUnderlay } from "./comunicadoTypes";

function underlayToBackground(underlay: ComunicadoBackgroundUnderlay): ComunicadoBackground {
  if (underlay.type === "color") {
    return { type: "color", value: underlay.value };
  }
  return {
    type: "gradient",
    from: underlay.from,
    to: underlay.to,
    angle: underlay.angle ?? 180,
    ...(underlay.stops && underlay.stops.length >= 2 ? { stops: underlay.stops } : {}),
  };
}

function backgroundToUnderlay(background: ComunicadoBackground): ComunicadoBackgroundUnderlay {
  if (background.type === "color") {
    return { type: "color", value: background.value };
  }
  return {
    type: "gradient",
    from: background.from,
    to: background.to,
    angle: background.angle ?? 180,
    ...(background.stops && background.stops.length >= 2 ? { stops: background.stops } : {}),
  };
}

export function fillToBackgroundUnderlay(fill: DelpiFill): ComunicadoBackgroundUnderlay {
  if (fill.kind === "none") {
    return { type: "color", value: "transparent" };
  }
  if (fill.kind === "solid") {
    return { type: "color", value: fill.color };
  }
  const stops = normalizeGradientStops(fill.stops);
  return {
    type: "gradient",
    from: stops[0]?.color ?? "#0f172a",
    to: stops[stops.length - 1]?.color ?? "#1e3a5f",
    angle: normalizeFillAngle(fill.angle),
    stops,
  };
}

/** Cor/gradiente do picker: patch underlay quando há imagem; senão substitui o fundo. */
export function patchBackgroundUnderlay(
  background: ComunicadoBackground | undefined,
  fill: DelpiFill,
): ComunicadoBackground {
  const underlay = fillToBackgroundUnderlay(fill);
  if (background?.type === "image") {
    return { ...background, underlay };
  }
  return underlayToBackground(underlay);
}

/** Upload/biblioteca: mantém underlay explícito ou promove cor/gradiente atual. */
export function applyBackgroundImagePreservingUnderlay(
  current: ComunicadoBackground | undefined,
  imagePatch: { assetId?: string; url?: string; value?: string },
): ComunicadoBackground {
  const underlay =
    current?.type === "image"
      ? (current.underlay ?? DEFAULT_IMAGE_BACKGROUND_UNDERLAY)
      : current
        ? backgroundToUnderlay(current)
        : DEFAULT_IMAGE_BACKGROUND_UNDERLAY;

  return {
    type: "image",
    ...imagePatch,
    underlay,
  };
}

/** Remove a imagem cover e restaura o underlay como fundo principal. */
export function removeBackgroundImage(
  background: ComunicadoBackground | undefined,
): ComunicadoBackground {
  if (!background || background.type !== "image") {
    return background ?? { type: "color", value: "#ffffff" };
  }
  return underlayToBackground(background.underlay ?? DEFAULT_IMAGE_BACKGROUND_UNDERLAY);
}
