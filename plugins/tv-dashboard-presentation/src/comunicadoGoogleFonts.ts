import { useEffect } from "react";

import type { ComunicadoConfig, ComunicadoTextBlock } from "./comunicadoTypes";
import { COMUNICADO_FONT_FAMILIES } from "./comunicadoTypes";

export type ComunicadoGoogleFontEntry = {
  id: string;
  label: string;
  /** Valor persistido em `style.fontFamily` / `contentRuns`. */
  fontFamily: string;
  googleFamily: string;
  weights?: string;
};

/** Subset curado para Painéis TV — sans + serif para títulos corporativos. */
export const COMUNICADO_GOOGLE_FONT_CATALOG: readonly ComunicadoGoogleFontEntry[] = [
  { id: "roboto", label: "Roboto", fontFamily: "Roboto, sans-serif", googleFamily: "Roboto" },
  {
    id: "open-sans",
    label: "Open Sans",
    fontFamily: '"Open Sans", sans-serif',
    googleFamily: "Open Sans",
  },
  { id: "lato", label: "Lato", fontFamily: "Lato, sans-serif", googleFamily: "Lato" },
  {
    id: "montserrat",
    label: "Montserrat",
    fontFamily: "Montserrat, sans-serif",
    googleFamily: "Montserrat",
  },
  { id: "oswald", label: "Oswald", fontFamily: "Oswald, sans-serif", googleFamily: "Oswald" },
  { id: "poppins", label: "Poppins", fontFamily: "Poppins, sans-serif", googleFamily: "Poppins" },
  { id: "raleway", label: "Raleway", fontFamily: "Raleway, sans-serif", googleFamily: "Raleway" },
  {
    id: "source-sans-3",
    label: "Source Sans 3",
    fontFamily: '"Source Sans 3", sans-serif',
    googleFamily: "Source Sans 3",
  },
  { id: "nunito", label: "Nunito", fontFamily: "Nunito, sans-serif", googleFamily: "Nunito" },
  { id: "ubuntu", label: "Ubuntu", fontFamily: "Ubuntu, sans-serif", googleFamily: "Ubuntu" },
  {
    id: "playfair",
    label: "Playfair Display",
    fontFamily: '"Playfair Display", serif',
    googleFamily: "Playfair Display",
    weights: "400;700",
  },
  {
    id: "merriweather",
    label: "Merriweather",
    fontFamily: "Merriweather, serif",
    googleFamily: "Merriweather",
    weights: "400;700",
  },
] as const;

export type ComunicadoFontFamilyOption = {
  value: string;
  label: string;
  source: "system" | "google";
};

const GOOGLE_FONT_BY_FAMILY = new Map(
  COMUNICADO_GOOGLE_FONT_CATALOG.map((entry) => [entry.fontFamily, entry]),
);

const GOOGLE_FONT_BY_GOOGLE_FAMILY = new Map(
  COMUNICADO_GOOGLE_FONT_CATALOG.map((entry) => [entry.googleFamily, entry]),
);

const loadedGoogleFamilies = new Set<string>();

export function comunicadoFontFamilyOptions(): ComunicadoFontFamilyOption[] {
  const system: ComunicadoFontFamilyOption[] = COMUNICADO_FONT_FAMILIES.map((fontFamily) => ({
    value: fontFamily,
    label: fontFamily.split(",")[0]?.trim() ?? fontFamily,
    source: "system",
  }));
  const google: ComunicadoFontFamilyOption[] = COMUNICADO_GOOGLE_FONT_CATALOG.map((entry) => ({
    value: entry.fontFamily,
    label: entry.label,
    source: "google",
  }));
  return [...system, ...google];
}

export function resolveGoogleFontEntry(fontFamily: string | undefined): ComunicadoGoogleFontEntry | null {
  if (!fontFamily?.trim()) return null;
  const trimmed = fontFamily.trim();
  const exact = GOOGLE_FONT_BY_FAMILY.get(trimmed);
  if (exact) return exact;
  const primary = trimmed.split(",")[0]?.trim().replace(/^["']|["']$/g, "");
  if (!primary) return null;
  return GOOGLE_FONT_BY_GOOGLE_FAMILY.get(primary) ?? null;
}

function collectFontFamiliesFromTextBlock(block: ComunicadoTextBlock, out: Set<string>): void {
  if (block.style?.fontFamily) out.add(block.style.fontFamily);
  for (const run of block.contentRuns ?? []) {
    if (run.style?.fontFamily) out.add(run.style.fontFamily);
  }
}

export function collectFontFamiliesFromComunicadoConfig(
  config: ComunicadoConfig | null | undefined,
): string[] {
  if (!config?.blocks?.length) return [];
  const families = new Set<string>();
  for (const block of config.blocks) {
    if (block.type === "heading" || block.type === "text") {
      collectFontFamiliesFromTextBlock(block, families);
    }
  }
  return [...families];
}

export function buildGoogleFontsStylesheetUrl(
  entries: readonly ComunicadoGoogleFontEntry[],
): string {
  const families = entries.map((entry) => {
    const weights = entry.weights ?? "400;700";
    const family = entry.googleFamily.replace(/ /g, "+");
    return `family=${family}:wght@${weights}`;
  });
  return `https://fonts.googleapis.com/css2?${families.join("&")}&display=swap`;
}

function injectGoogleFontStylesheet(entry: ComunicadoGoogleFontEntry): void {
  if (typeof document === "undefined") return;
  if (loadedGoogleFamilies.has(entry.googleFamily)) return;

  const linkId = `comunicado-gf-${entry.id}`;
  if (document.getElementById(linkId)) {
    loadedGoogleFamilies.add(entry.googleFamily);
    return;
  }

  const link = document.createElement("link");
  link.id = linkId;
  link.rel = "stylesheet";
  link.href = buildGoogleFontsStylesheetUrl([entry]);
  document.head.appendChild(link);
  loadedGoogleFamilies.add(entry.googleFamily);
}

/** Carrega sob demanda apenas famílias do catálogo Google usadas no slide. */
export function ensureComunicadoGoogleFontsLoaded(fontFamilies: readonly string[]): void {
  for (const fontFamily of fontFamilies) {
    const entry = resolveGoogleFontEntry(fontFamily);
    if (entry) injectGoogleFontStylesheet(entry);
  }
}

export function useComunicadoGoogleFonts(config: ComunicadoConfig | null | undefined): void {
  useEffect(() => {
    const families = collectFontFamiliesFromComunicadoConfig(config);
    ensureComunicadoGoogleFontsLoaded(families);
  }, [config]);
}

/** Apenas testes — reinicia cache de famílias já injetadas. */
export function resetComunicadoGoogleFontsForTests(): void {
  loadedGoogleFamilies.clear();
}
