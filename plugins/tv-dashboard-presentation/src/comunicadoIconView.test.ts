import { DECK_COLOR_SURFACE, DECK_SHAPE_DEFAULTS } from "@delpi/plugin-ui/index";
import { describe, expect, it } from "vitest";

import {
  resolveComunicadoIconColor,
  resolveComunicadoIconStrokeWidth,
} from "./comunicadoIconView";
import type { ComunicadoIconBlock } from "./comunicadoTypes";

function iconBlock(partial: Partial<ComunicadoIconBlock> = {}): ComunicadoIconBlock {
  return {
    id: "i1",
    type: "icon",
    iconName: "Star",
    frame: { x: 0, y: 0, w: 10, h: 10 },
    ...partial,
  };
}

describe("comunicadoIconView", () => {
  it("usa cor accent das formas por padrão (não branco)", () => {
    expect(resolveComunicadoIconColor(iconBlock())).toBe(DECK_SHAPE_DEFAULTS.fill);
    expect(resolveComunicadoIconColor(iconBlock({ style: {} }))).toBe(DECK_SHAPE_DEFAULTS.fill);
    expect(resolveComunicadoIconColor(iconBlock({ style: { color: "#ffffff" } }))).toBe(
      DECK_SHAPE_DEFAULTS.fill,
    );
    expect(resolveComunicadoIconColor(iconBlock({ style: { color: DECK_COLOR_SURFACE } }))).toBe(
      DECK_SHAPE_DEFAULTS.fill,
    );
  });

  it("preserva cor explícita diferente do legado branco", () => {
    expect(resolveComunicadoIconColor(iconBlock({ style: { color: "#ef4444" } }))).toBe("#ef4444");
  });

  it("strokeWidth padrão 2", () => {
    expect(resolveComunicadoIconStrokeWidth(iconBlock())).toBe(2);
    expect(resolveComunicadoIconStrokeWidth(iconBlock({ style: { strokeWidth: 3.5 } }))).toBe(3.5);
  });
});
