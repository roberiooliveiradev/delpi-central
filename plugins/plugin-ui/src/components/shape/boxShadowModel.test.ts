import { describe, expect, it } from "vitest";

import {
  DEFAULT_BOX_SHADOW_MODEL,
  boxShadowsEqual,
  formatBoxShadow,
  parseBoxShadow,
  patchBoxShadow,
  resolveBoxShadowModel,
} from "./boxShadowModel";

describe("boxShadowModel", () => {
  it("parseia presets atuais do comunicado", () => {
    expect(parseBoxShadow("0 4px 14px rgba(0, 0, 0, 0.28)")).toEqual({
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

  it("parseia spread e ignora camadas extras", () => {
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
  });

  it("serializa com round-trip estrutural dos presets", () => {
    const soft = "0 4px 14px rgba(0, 0, 0, 0.28)";
    const model = parseBoxShadow(soft)!;
    expect(boxShadowsEqual(formatBoxShadow(model), soft)).toBe(true);
    expect(formatBoxShadow(model)).toBe("0 4px 14px rgba(0, 0, 0, 0.28)");

    const withSpread = formatBoxShadow({
      ...DEFAULT_BOX_SHADOW_MODEL,
      spread: 2,
      opacity: 0.3,
    });
    expect(withSpread).toBe("0 4px 14px 2px rgba(0, 0, 0, 0.3)");
    expect(parseBoxShadow(withSpread)?.spread).toBe(2);
  });

  it("patchBoxShadow parte do default quando não há sombra", () => {
    expect(patchBoxShadow(undefined, { offsetY: 10 })).toBe(
      formatBoxShadow({ ...DEFAULT_BOX_SHADOW_MODEL, offsetY: 10 }),
    );
    expect(resolveBoxShadowModel(undefined)).toEqual(DEFAULT_BOX_SHADOW_MODEL);
  });
});
