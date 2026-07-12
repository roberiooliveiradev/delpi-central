import { useEffect } from "react";

import type { ComunicadoCustomFontRef } from "./comunicadoTypes";

export type ComunicadoLoadedCustomFont = {
  familyName: string;
  url: string;
};

export function buildCustomFontFamilyCss(familyName: string): string {
  const escaped = familyName.trim().replace(/\\/g, "\\\\").replace(/"/g, '\\"');
  return `"${escaped}", sans-serif`;
}

function cssString(value: string): string {
  return value.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\n|\r/g, "");
}

export function ensureComunicadoCustomFontsLoaded(
  fonts: readonly ComunicadoLoadedCustomFont[],
): void {
  if (typeof document === "undefined") return;
  const validFonts = fonts.filter((font) => font.familyName.trim() && font.url.trim());
  const existing = document.getElementById("td-custom-fonts");
  if (validFonts.length === 0) {
    existing?.remove();
    return;
  }
  const style = existing ?? document.createElement("style");
  style.id = "td-custom-fonts";
  style.textContent = validFonts
    .map(
      (font) =>
        `@font-face{font-family:"${cssString(font.familyName.trim())}";src:url("${cssString(font.url.trim())}");font-display:swap;}`,
    )
    .join("\n");
  if (!existing) document.head.appendChild(style);
}

export function useComunicadoCustomFonts(
  fonts: readonly ComunicadoCustomFontRef[] | null | undefined,
): void {
  useEffect(() => {
    ensureComunicadoCustomFontsLoaded(
      (fonts ?? []).flatMap((font) =>
        font.url ? [{ familyName: font.familyName, url: font.url }] : [],
      ),
    );
  }, [fonts]);
}

export function comunicadoCustomFontFamilyOptions(
  fonts: readonly ComunicadoCustomFontRef[] | null | undefined,
) {
  return (fonts ?? [])
    .filter((font) => font.familyName.trim())
    .map((font) => ({
      value: buildCustomFontFamilyCss(font.familyName),
      label: font.familyName.trim(),
      source: "custom" as const,
    }));
}
