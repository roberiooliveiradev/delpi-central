import { describe, expect, it } from "vitest";

import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import {
  aggregateVisualBoxTextFormatStyle,
  isHomogeneousVisualBoxSelection,
} from "./selectionStyleAggregate";
import { resolveVisualBoxElementCapabilitiesForSelection } from "../components/selectionSections/visualBoxElementCapabilities";

function textBlock(
  id: string,
  style: NonNullable<ComunicadoBlock["style"]> = {},
): ComunicadoBlock {
  return {
    id,
    type: "text",
    content: id,
    frame: { x: 0, y: 0, w: 10, h: 10 },
    style,
  } as ComunicadoBlock;
}

describe("selectionStyleAggregate (visual-box)", () => {
  it("aggregateVisualBoxTextFormatStyle: fontFamily misto", () => {
    const agg = aggregateVisualBoxTextFormatStyle([
      textBlock("a", { fontFamily: "Inter", fontSize: 34 }),
      textBlock("b", { fontFamily: "Roboto", fontSize: 34 }),
    ]);
    expect(agg?.fontFamily).toBe("mixed");
    expect(agg?.fontSize).toBe(34);
  });

  it("isHomogeneousVisualBoxSelection", () => {
    expect(isHomogeneousVisualBoxSelection([textBlock("a"), textBlock("b")])).toBe(true);
    expect(
      isHomogeneousVisualBoxSelection([
        textBlock("a"),
        { id: "i", type: "image", src: "x", frame: { x: 0, y: 0, w: 1, h: 1 } } as ComunicadoBlock,
      ]),
    ).toBe(false);
  });
});

describe("resolveVisualBoxElementCapabilitiesForSelection", () => {
  it("AND: só visual-box → caps; heterogêneo → null", () => {
    const caps = resolveVisualBoxElementCapabilitiesForSelection([
      textBlock("a"),
      textBlock("b"),
    ]);
    expect(caps?.shapeChrome).toBe(true);
    expect(caps?.textHighlight).toBe(true);
    expect(
      resolveVisualBoxElementCapabilitiesForSelection([
        textBlock("a"),
        { id: "i", type: "image", src: "x", frame: { x: 0, y: 0, w: 1, h: 1 } } as ComunicadoBlock,
      ]),
    ).toBeNull();
  });
});
