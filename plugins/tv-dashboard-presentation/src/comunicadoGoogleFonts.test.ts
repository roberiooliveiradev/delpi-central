import { afterEach, describe, expect, it } from "vitest";

import {
  buildGoogleFontsStylesheetUrl,
  collectFontFamiliesFromComunicadoConfig,
  COMUNICADO_GOOGLE_FONT_CATALOG,
  comunicadoFontFamilyOptions,
  ensureComunicadoGoogleFontsLoaded,
  resetComunicadoGoogleFontsForTests,
  resolveGoogleFontEntry,
} from "./comunicadoGoogleFonts";
import { COMUNICADO_FONT_FAMILIES } from "./comunicadoTypes";

describe("comunicadoGoogleFonts", () => {
  afterEach(() => {
    resetComunicadoGoogleFontsForTests();
    document.head.querySelectorAll('link[id^="comunicado-gf-"]').forEach((node) => node.remove());
  });

  it("expõe opções sistema + Google no catálogo", () => {
    const options = comunicadoFontFamilyOptions();
    expect(options.length).toBe(COMUNICADO_FONT_FAMILIES.length + COMUNICADO_GOOGLE_FONT_CATALOG.length);
    expect(options.some((opt) => opt.source === "google" && opt.label === "Roboto")).toBe(true);
    expect(options.some((opt) => opt.source === "system")).toBe(true);
  });

  it("resolve entrada Google por fontFamily persistido", () => {
    const entry = resolveGoogleFontEntry('"Open Sans", sans-serif');
    expect(entry?.googleFamily).toBe("Open Sans");
    expect(resolveGoogleFontEntry("Arial, Helvetica, sans-serif")).toBeNull();
  });

  it("monta URL CSS2 com pesos e display=swap", () => {
    const url = buildGoogleFontsStylesheetUrl([COMUNICADO_GOOGLE_FONT_CATALOG[0]]);
    expect(url).toContain("fonts.googleapis.com/css2?");
    expect(url).toContain("family=Roboto:wght@400;700");
    expect(url).toContain("display=swap");
  });

  it("coleta fontFamily de bloco e contentRuns", () => {
    const families = collectFontFamiliesFromComunicadoConfig({
      blocks: [
        {
          id: "1",
          type: "heading",
          content: "T",
          frame: { x: 0, y: 0, w: 100, h: 10 },
          style: { fontFamily: "Montserrat, sans-serif" },
        },
        {
          id: "2",
          type: "text",
          content: "Corpo",
          frame: { x: 0, y: 10, w: 100, h: 10 },
          contentRuns: [{ text: "A", style: { fontFamily: "Lato, sans-serif" } }],
        },
      ],
    });
    expect(families).toEqual(
      expect.arrayContaining(["Montserrat, sans-serif", "Lato, sans-serif"]),
    );
  });

  it("injeta link lazy apenas para fontes Google usadas", () => {
    ensureComunicadoGoogleFontsLoaded(["Roboto, sans-serif", "Arial, Helvetica, sans-serif"]);
    const link = document.getElementById("comunicado-gf-roboto") as HTMLLinkElement | null;
    expect(link?.rel).toBe("stylesheet");
    expect(link?.href).toContain("family=Roboto");
    expect(document.getElementById("comunicado-gf-open-sans")).toBeNull();

    ensureComunicadoGoogleFontsLoaded(["Roboto, sans-serif"]);
    expect(document.querySelectorAll('link[id^="comunicado-gf-"]').length).toBe(1);
  });
});
