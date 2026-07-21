import { DECK_COLOR_SURFACE, DECK_SHAPE_DEFAULTS } from "@delpi/plugin-ui/index";
import { describe, expect, it } from "vitest";

import { createBlock, normalizeIconBlockStyle } from "./comunicadoHelpers";
import {
  resolveComunicadoIconChromeStyle,
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

  it("iconStrokeWidth padrão 2 (e legado strokeWidth sem contorno)", () => {
    expect(resolveComunicadoIconStrokeWidth(iconBlock())).toBe(2);
    expect(
      resolveComunicadoIconStrokeWidth(iconBlock({ style: { iconStrokeWidth: 3.5 } })),
    ).toBe(3.5);
    expect(
      resolveComunicadoIconStrokeWidth(
        iconBlock({ style: { strokeWidth: 4, stroke: "transparent" } }),
      ),
    ).toBe(4);
  });

  it("chrome da caixa aplica fill, contorno, raio e sombra", () => {
    const chrome = resolveComunicadoIconChromeStyle(
      iconBlock({
        style: {
          fill: "#e8f4fc",
          stroke: "#089bdb",
          strokeWidth: 2,
          borderRadius: 12,
          boxShadow: "0 4px 12px rgba(0,0,0,.2)",
        },
      }),
    );
    expect(chrome.backgroundColor).toBe("#e8f4fc");
    expect(chrome.border).toBe("2px solid #089bdb");
    expect(chrome.borderRadius).toBe(12);
    expect(chrome.boxShadow).toBe("0 4px 12px rgba(0,0,0,.2)");
  });

  it("createBlock icon nasce com chrome transparente e iconStrokeWidth", () => {
    const created = createBlock("icon", "Factory") as ComunicadoIconBlock;
    expect(created.style?.fill).toBe("transparent");
    expect(created.style?.stroke).toBe("transparent");
    expect(created.style?.strokeWidth).toBe(0);
    expect(created.style?.iconStrokeWidth).toBe(2);
    expect(created.style?.opacity).toBe(1);
  });

  it("normalizeIconBlockStyle migra strokeWidth legado para iconStrokeWidth", () => {
    const migrated = normalizeIconBlockStyle({ strokeWidth: 3, color: "#089bdb" });
    expect(migrated.iconStrokeWidth).toBe(3);
    expect(migrated.strokeWidth).toBe(0);
    expect(migrated.stroke).toBe("transparent");
  });
});
