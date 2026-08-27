import { describe, expect, it } from "vitest";

import {
  DEFAULT_TEXT_SHADOW_MODEL,
  addTextShadowLayer,
  boxShadowCssToTextShadowCss,
  buildTextShadowPresetsFromBox,
  formatTextShadow,
  formatTextShadowStack,
  parseTextShadow,
  parseTextShadowStack,
  patchTextShadow,
  removeTextShadowLayer,
  resolveTextShadowModel,
  textShadowsEqual,
} from "./textShadowModel";

const BOX_PRESETS = [
  { key: "none", label: "Nenhuma", value: undefined },
  { key: "soft", label: "Suave", value: "0 4px 14px rgba(0, 0, 0, 0.28)" },
  { key: "medium", label: "Média", value: "0 8px 24px rgba(0, 0, 0, 0.35)" },
  { key: "hard", label: "Forte", value: "0 2px 10px rgba(0, 0, 0, 0.55)" },
  {
    key: "elevated",
    label: "Elevada",
    value: "0 1px 3px rgba(0, 0, 0, 0.2), 0 12px 28px -4px rgba(0, 0, 0, 0.12)",
  },
  { key: "inset", label: "Interna", value: "inset 0 2px 8px rgba(0, 0, 0, 0.28)" },
] as const;

describe("textShadowModel", () => {
  it("parseia presets do comunicado", () => {
    expect(parseTextShadow("0 4px 14px rgba(0, 0, 0, 0.28)")).toEqual({
      offsetX: 0,
      offsetY: 4,
      blur: 14,
      colorHex: "#000000",
      opacity: 0.28,
    });
    expect(parseTextShadow("0 8px 24px rgba(0, 0, 0, 0.35)")?.blur).toBe(24);
  });

  it("parseia múltiplas camadas", () => {
    const stack = parseTextShadowStack(
      "0 1px 3px rgba(0, 0, 0, 0.2), 0 12px 28px rgba(0, 0, 0, 0.12)",
    );
    expect(stack?.layers).toHaveLength(2);
    expect(stack?.layers[0]).toMatchObject({ offsetY: 1, blur: 3, opacity: 0.2 });
    expect(stack?.layers[1]).toMatchObject({ offsetY: 12, blur: 28, opacity: 0.12 });
  });

  it("retorna null para none / vazio", () => {
    expect(parseTextShadow(undefined)).toBeNull();
    expect(parseTextShadow("none")).toBeNull();
    expect(parseTextShadowStack("")).toBeNull();
  });

  it("round-trip serialização", () => {
    const soft = "0 4px 14px rgba(0, 0, 0, 0.28)";
    expect(textShadowsEqual(formatTextShadow(parseTextShadow(soft)!), soft)).toBe(true);

    const dual = formatTextShadowStack({
      layers: [
        { ...DEFAULT_TEXT_SHADOW_MODEL, opacity: 0.2 },
        { ...DEFAULT_TEXT_SHADOW_MODEL, offsetY: 12, blur: 28, opacity: 0.12 },
      ],
    });
    expect(dual.includes(", ")).toBe(true);
    expect(parseTextShadowStack(dual)?.layers).toHaveLength(2);
  });

  it("patch / add / remove camadas", () => {
    const patched = patchTextShadow(undefined, { offsetY: 10 });
    expect(patched).toBe(formatTextShadow({ ...DEFAULT_TEXT_SHADOW_MODEL, offsetY: 10 }));
    expect(resolveTextShadowModel(undefined)).toEqual(DEFAULT_TEXT_SHADOW_MODEL);

    const withSecond = addTextShadowLayer(patched);
    expect(parseTextShadowStack(withSecond)?.layers).toHaveLength(2);

    const onlyFirst = removeTextShadowLayer(withSecond, 1);
    expect(parseTextShadowStack(onlyFirst)?.layers).toHaveLength(1);
  });

  it("boxShadowCssToTextShadowCss omite inset e spread", () => {
    expect(boxShadowCssToTextShadowCss("0 4px 14px rgba(0, 0, 0, 0.28)")).toBe(
      "0 4px 14px rgba(0, 0, 0, 0.28)",
    );
    const elevated = boxShadowCssToTextShadowCss(
      "0 1px 3px rgba(0, 0, 0, 0.2), 0 12px 28px -4px rgba(0, 0, 0, 0.12)",
    );
    expect(elevated).toContain("0 1px 3px");
    expect(elevated).toContain("0 12px 28px");
    expect(elevated).not.toContain("-4px");
    expect(boxShadowCssToTextShadowCss("inset 0 2px 8px rgba(0, 0, 0, 0.28)")).toBeUndefined();
  });

  it("buildTextShadowPresetsFromBox gera preset Elevada com 2 camadas", () => {
    const presets = buildTextShadowPresetsFromBox(BOX_PRESETS);
    expect(presets.find((item) => item.id === "inset")).toBeUndefined();
    const elevated = presets.find((item) => item.id === "elevated");
    expect(elevated?.value).toBeTruthy();
    expect(parseTextShadowStack(elevated?.value)?.layers).toHaveLength(2);
  });
});
