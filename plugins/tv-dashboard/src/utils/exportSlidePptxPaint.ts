import { isAutomaticTextColor, solidFromFill, type DelpiFill } from "@delpi/plugin-ui/index";
import type { ComunicadoBlockStyle } from "@delpi/tv-dashboard-presentation";

/**
 * Resolve cor hex (sem #) para PPTX a partir de paint rico ou legado.
 * Precedência: paint solid/gradient (1º stop) → hex legado → fallback.
 * Gradientes completos não são suportados pelo exportador — documentado.
 */
export function resolvePptxHexColor(
  paint: DelpiFill | undefined,
  legacyHex: string | undefined,
  fallback: string,
): string {
  if (paint?.kind === "solid") {
    const c = typeof paint.color === "string" ? paint.color.trim() : "";
    if (c && c !== "transparent" && !isAutomaticTextColor(c)) {
      return normalizePptxHex(c, fallback);
    }
  }
  if (paint?.kind === "gradient") {
    return normalizePptxHex(solidFromFill(paint), fallback);
  }
  if (paint?.kind === "none") {
    return normalizePptxHex("transparent", fallback);
  }
  return normalizePptxHex(legacyHex, fallback);
}

export function normalizePptxHex(value: string | undefined, fallback: string): string {
  const normalized = value?.trim().replace(/^#/, "");
  return normalized && /^[0-9a-f]{6}$/i.test(normalized) ? normalized : fallback;
}

export function resolvePptxTextColor(style: ComunicadoBlockStyle | undefined, fallback = "1F2937"): string {
  return resolvePptxHexColor(style?.colorPaint, style?.color, fallback);
}

export function resolvePptxFillColor(style: ComunicadoBlockStyle | undefined, fallback = "DCE6F1"): string {
  return resolvePptxHexColor(
    style?.fillPaint,
    style?.fill ?? style?.backgroundColor,
    fallback,
  );
}

export function resolvePptxStrokeColor(style: ComunicadoBlockStyle | undefined, fallback = "64748B"): string {
  return resolvePptxHexColor(
    style?.strokePaint,
    style?.stroke ?? style?.borderColor,
    fallback,
  );
}
