import { describe, expect, it } from "vitest";

import {
  resolveTextPartColumnBoxLayout,
  textAlignToAlignItems,
  verticalAlignToJustifyContent,
} from "./textPartBoxLayout";

describe("textPartBoxLayout", () => {
  it("mapeia verticalAlign para justifyContent (coluna)", () => {
    expect(verticalAlignToJustifyContent("top")).toBe("flex-start");
    expect(verticalAlignToJustifyContent("middle")).toBe("center");
    expect(verticalAlignToJustifyContent("bottom")).toBe("flex-end");
  });

  it("mapeia textAlign para alignItems (eixo cruzado)", () => {
    expect(textAlignToAlignItems("left")).toBe("flex-start");
    expect(textAlignToAlignItems("right")).toBe("flex-end");
    expect(textAlignToAlignItems("center")).toBe("center");
  });

  it("resolve caixa coluna com fillHost e alinhamentos", () => {
    expect(
      resolveTextPartColumnBoxLayout({
        textAlign: "right",
        verticalAlign: "bottom",
      }),
    ).toEqual({
      display: "flex",
      flexDirection: "column",
      boxSizing: "border-box",
      width: "100%",
      height: "100%",
      justifyContent: "flex-end",
      alignItems: "flex-end",
      textAlign: "right",
    });
  });
});
