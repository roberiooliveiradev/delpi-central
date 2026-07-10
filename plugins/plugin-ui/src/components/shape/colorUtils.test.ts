import { describe, expect, it } from "vitest";

import {
  buildThemeColorGrid,
  colorToCss,
  cssToColorValue,
  normalizeHex,
  parseHexColor,
  rgbToHex,
} from "./colorUtils";
import { DELPI_THEME_BASE_COLORS } from "./colorPalettes";

describe("shape colorUtils", () => {
  it("normaliza hex curto para 6 dígitos", () => {
    expect(normalizeHex("#abc")).toBe("#aabbcc");
  });

  it("converte rgb para hex", () => {
    expect(rgbToHex(8, 155, 219)).toBe("#089bdb");
  });

  it("parseia cor com alpha", () => {
    const parsed = parseHexColor("#089bdb", 0.5);
    expect(parsed?.hex).toBe("#089bdb");
    expect(parsed?.alpha).toBe(0.5);
    expect(colorToCss(parsed!)).toBe("rgba(8, 155, 219, 0.5)");
  });

  it("interpreta transparent como alpha zero", () => {
    expect(cssToColorValue("transparent").alpha).toBe(0);
  });

  it("gera grade 6×10 do tema", () => {
    const grid = buildThemeColorGrid(DELPI_THEME_BASE_COLORS);
    expect(grid).toHaveLength(6);
    expect(grid[0]).toHaveLength(10);
  });
});
