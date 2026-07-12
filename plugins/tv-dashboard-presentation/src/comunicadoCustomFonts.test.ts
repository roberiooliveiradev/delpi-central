import { afterEach, describe, expect, it } from "vitest";

import {
  buildCustomFontFamilyCss,
  comunicadoCustomFontFamilyOptions,
  ensureComunicadoCustomFontsLoaded,
} from "./comunicadoCustomFonts";
import { parseComunicadoConfig, serializeComunicadoConfig } from "./comunicadoHelpers";

describe("comunicadoCustomFonts", () => {
  afterEach(() => {
    document.getElementById("td-custom-fonts")?.remove();
  });

  it("monta opção e @font-face para fonte personalizada", () => {
    const font = {
      assetId: "font-1",
      familyName: "Minha Fonte",
      url: "/media/font-1",
    };

    expect(buildCustomFontFamilyCss(font.familyName)).toBe('"Minha Fonte", sans-serif');
    expect(comunicadoCustomFontFamilyOptions([font])).toEqual([
      {
        value: '"Minha Fonte", sans-serif',
        label: "Minha Fonte",
        source: "custom",
      },
    ]);

    ensureComunicadoCustomFontsLoaded([font]);
    const style = document.getElementById("td-custom-fonts");
    expect(style?.textContent).toContain('font-family:"Minha Fonte"');
    expect(style?.textContent).toContain('url("/media/font-1")');
  });

  it("preserva URL só em memória e serializa a referência estável", () => {
    const parsed = parseComunicadoConfig({
      blocks: [],
      customFonts: [
        { assetId: "font-1", familyName: "Minha Fonte", url: "/media/font-1" },
      ],
    });
    expect(parsed.customFonts?.[0]?.url).toBe("/media/font-1");
    expect(serializeComunicadoConfig(parsed).customFonts).toEqual([
      { assetId: "font-1", familyName: "Minha Fonte" },
    ]);
  });
});
