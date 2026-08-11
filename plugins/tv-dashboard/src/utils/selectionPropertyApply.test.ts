import { describe, expect, it } from "vitest";

import {
  mergeSparseStyleProperties,
  resolveAppliedNumericProperty,
  sparsePropertyPatch,
} from "./selectionPropertyApply";

describe("selectionPropertyApply", () => {
  it("sparsePropertyPatch omite undefined", () => {
    expect(sparsePropertyPatch({ fontFamily: "Inter", color: undefined, fontSize: 14 })).toEqual({
      fontFamily: "Inter",
      fontSize: 14,
    });
  });

  it("sparsePropertyPatch preserva fillPaint undefined para o clear", () => {
    expect(sparsePropertyPatch({ fill: "#ef4444", fillPaint: undefined })).toEqual({
      fill: "#ef4444",
      fillPaint: undefined,
    });
  });

  it("mergeSparseStyleProperties apaga fillPaint e não apaga color de tipografia", () => {
    const cleared = mergeSparseStyleProperties(
      { fill: "#111111", fillPaint: { kind: "gradient", angle: 90, stops: [] } },
      { fill: "#ef4444", fillPaint: undefined },
    );
    expect(cleared.fill).toBe("#ef4444");
    expect(cleared.fillPaint).toBeUndefined();
    expect(Object.prototype.hasOwnProperty.call(cleared, "fillPaint")).toBe(false);

    const typography = mergeSparseStyleProperties(
      { fontFamily: "Inter", color: "#111" },
      { fontFamily: "Roboto", color: undefined },
    );
    expect(typography).toEqual({ fontFamily: "Roboto", color: "#111" });
  });

  it("mergeSparseStyleProperties não apaga props com patch parcial", () => {
    const next = mergeSparseStyleProperties(
      { fontFamily: "Inter", fontSize: 22, color: "#111", fontWeight: "bold" },
      { fontFamily: "Roboto" },
    );
    expect(next).toEqual({
      fontFamily: "Roboto",
      fontSize: 22,
      color: "#111",
      fontWeight: "bold",
    });
  });

  it("resolveAppliedNumericProperty absolute usa o valor", () => {
    expect(
      resolveAppliedNumericProperty({
        current: 22,
        value: 14,
        mode: "absolute",
        clamp: (n) => n,
      }),
    ).toBe(14);
  });

  it("resolveAppliedNumericProperty delta preserva hierarquia", () => {
    expect(
      resolveAppliedNumericProperty({
        current: 22,
        mode: "delta",
        delta: 2,
        clamp: (n) => n,
      }),
    ).toBe(24);
    expect(
      resolveAppliedNumericProperty({
        current: 12,
        mode: "delta",
        delta: 2,
        clamp: (n) => n,
      }),
    ).toBe(14);
  });
});
