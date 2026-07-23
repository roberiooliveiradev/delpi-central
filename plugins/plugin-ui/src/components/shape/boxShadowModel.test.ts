import { describe, expect, it } from "vitest";

import {
  DEFAULT_BOX_SHADOW_MODEL,
  addBoxShadowLayer,
  boxShadowCssToDropShadowFilter,
  boxShadowsEqual,
  formatBoxShadow,
  formatBoxShadowStack,
  parseBoxShadow,
  parseBoxShadowStack,
  patchBoxShadow,
  removeBoxShadowLayer,
  resolveBoxShadowModel,
} from "./boxShadowModel";

describe("boxShadowModel", () => {
  it("parseia presets atuais do comunicado", () => {
    expect(parseBoxShadow("0 4px 14px rgba(0, 0, 0, 0.28)")).toEqual({
      inset: false,
      offsetX: 0,
      offsetY: 4,
      blur: 14,
      spread: 0,
      colorHex: "#000000",
      opacity: 0.28,
    });
    expect(parseBoxShadow("0 8px 24px rgba(0, 0, 0, 0.35)")?.blur).toBe(24);
    expect(parseBoxShadow("0 2px 10px rgba(0, 0, 0, 0.55)")?.opacity).toBe(0.55);
  });

  it("parseia inset e múltiplas camadas", () => {
    const inset = parseBoxShadow("inset 0 2px 6px rgba(0, 0, 0, 0.35)");
    expect(inset).toMatchObject({ inset: true, offsetY: 2, blur: 6, opacity: 0.35 });

    const stack = parseBoxShadowStack(
      "0 1px 3px rgba(0, 0, 0, 0.2), 0 8px 24px -4px rgba(0, 0, 0, 0.12)",
    );
    expect(stack?.layers).toHaveLength(2);
    expect(stack?.layers[0]).toMatchObject({ offsetY: 1, blur: 3, opacity: 0.2 });
    expect(stack?.layers[1]).toMatchObject({ offsetY: 8, blur: 24, spread: -4, opacity: 0.12 });
  });

  it("parseia spread e ignora camadas extras na igualdade parcial", () => {
    const model = parseBoxShadow("2px 4px 8px 3px rgba(15, 23, 42, 0.4), 0 0 0 1px #fff");
    expect(model).toMatchObject({
      offsetX: 2,
      offsetY: 4,
      blur: 8,
      spread: 3,
      colorHex: "#0f172a",
      opacity: 0.4,
    });
  });

  it("retorna null para none / vazio", () => {
    expect(parseBoxShadow(undefined)).toBeNull();
    expect(parseBoxShadow("")).toBeNull();
    expect(parseBoxShadow("none")).toBeNull();
    expect(parseBoxShadowStack(undefined)).toBeNull();
  });

  it("serializa inset e pilha", () => {
    const soft = "0 4px 14px rgba(0, 0, 0, 0.28)";
    expect(boxShadowsEqual(formatBoxShadow(parseBoxShadow(soft)!), soft)).toBe(true);

    const insetCss = formatBoxShadow({ ...DEFAULT_BOX_SHADOW_MODEL, inset: true, offsetY: 2 });
    expect(insetCss.startsWith("inset ")).toBe(true);
    expect(parseBoxShadow(insetCss)?.inset).toBe(true);

    const dual = formatBoxShadowStack({
      layers: [
        { ...DEFAULT_BOX_SHADOW_MODEL, opacity: 0.2 },
        { ...DEFAULT_BOX_SHADOW_MODEL, offsetY: 12, blur: 28, spread: -4, opacity: 0.12 },
      ],
    });
    expect(dual.includes(", ")).toBe(true);
    expect(parseBoxShadowStack(dual)?.layers).toHaveLength(2);
  });

  it("patch / add / remove camadas", () => {
    const patched = patchBoxShadow(undefined, { offsetY: 10 });
    expect(patched).toBe(formatBoxShadow({ ...DEFAULT_BOX_SHADOW_MODEL, offsetY: 10 }));
    expect(resolveBoxShadowModel(undefined)).toEqual(DEFAULT_BOX_SHADOW_MODEL);

    const withSecond = addBoxShadowLayer(patched);
    expect(parseBoxShadowStack(withSecond)?.layers).toHaveLength(2);

    const onlyFirst = removeBoxShadowLayer(withSecond, 1);
    expect(parseBoxShadowStack(onlyFirst)?.layers).toHaveLength(1);

    const layer1Patch = patchBoxShadow(withSecond, { blur: 40 }, 1);
    expect(parseBoxShadowStack(layer1Patch)?.layers[1]?.blur).toBe(40);
  });

  it("boxShadowsEqual considera inset e camadas", () => {
    expect(boxShadowsEqual("0 4px 14px rgba(0,0,0,0.28)", "0 4px 14px rgba(0, 0, 0, 0.28)")).toBe(
      true,
    );
    expect(
      boxShadowsEqual("inset 0 2px 6px rgba(0,0,0,0.3)", "0 2px 6px rgba(0,0,0,0.3)"),
    ).toBe(false);
    expect(
      boxShadowsEqual(
        "0 1px 2px rgba(0,0,0,0.2), 0 8px 20px rgba(0,0,0,0.1)",
        "0 1px 2px rgba(0,0,0,0.2)",
      ),
    ).toBe(false);
  });

  it("boxShadowCssToDropShadowFilter segue alpha (sem inset/spread)", () => {
    expect(boxShadowCssToDropShadowFilter("0 4px 14px rgba(0, 0, 0, 0.28)")).toBe(
      "drop-shadow(0 4px 14px rgba(0, 0, 0, 0.28))",
    );
    expect(
      boxShadowCssToDropShadowFilter(
        "0 1px 2px rgba(15, 23, 42, 0.06), 0 12px 28px rgba(15, 23, 42, 0.1)",
      ),
    ).toContain("drop-shadow(0 1px 2px");
    expect(boxShadowCssToDropShadowFilter("inset 0 2px 6px rgba(0,0,0,0.3)")).toBeNull();
    expect(boxShadowCssToDropShadowFilter("none")).toBeNull();
  });
});
