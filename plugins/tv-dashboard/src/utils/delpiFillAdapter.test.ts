import { describe, expect, it } from "vitest";

import {
  backgroundToFill,
  fillToBackground,
  fillToColorStylePatch,
  fillToFillStylePatch,
  fillToStrokeStylePatch,
  shouldApplyBackgroundSolidHex,
  styleToColorFill,
  styleToFill,
  styleToStrokeFill,
} from "./delpiFillAdapter";

const gradient = {
  kind: "gradient" as const,
  angle: 90,
  stops: [
    { color: "#111111", position: 0 },
    { color: "#eeeeee", position: 100 },
  ],
};

describe("delpiFillAdapter", () => {
  it("converte fundo legado from/to em DelpiFill com stops", () => {
    expect(
      backgroundToFill({ type: "gradient", from: "#0f172a", to: "#1e3a5f", angle: 180 }),
    ).toEqual({
      kind: "gradient",
      angle: 180,
      stops: [
        { color: "#0f172a", position: 0 },
        { color: "#1e3a5f", position: 100 },
      ],
    });
  });

  it("preserva stops ao ir e voltar do fundo", () => {
    const background = fillToBackground(gradient);
    expect(background).toMatchObject({
      type: "gradient",
      from: "#111111",
      to: "#eeeeee",
      angle: 90,
    });
    if (background.type !== "gradient") throw new Error("expected gradient");
    expect(background.stops).toEqual(gradient.stops);
    expect(backgroundToFill(background)).toEqual(gradient);
  });

  it("ida e volta de ângulo 45 e stop em 50%", () => {
    const fill = {
      kind: "gradient" as const,
      angle: 45,
      stops: [
        { color: "#112233", position: 0 },
        { color: "#445566", position: 50 },
        { color: "#778899", position: 100 },
      ],
    };
    const background = fillToBackground(fill);
    expect(background).toMatchObject({ type: "gradient", angle: 45 });
    if (background.type !== "gradient") throw new Error("expected gradient");
    expect(background.stops?.[1]).toEqual({ color: "#445566", position: 50 });
    expect(backgroundToFill(background)).toEqual(fill);
    expect(shouldApplyBackgroundSolidHex(background)).toBe(false);
    expect(shouldApplyBackgroundSolidHex({ type: "color", value: "#fff" })).toBe(true);
  });

  it("sólido limpa fillPaint; gradiente grava paint + hex do primeiro stop", () => {
    expect(fillToFillStylePatch({ kind: "solid", color: "#089bdb" })).toEqual({
      fill: "#089bdb",
      backgroundColor: "#089bdb",
      fillPaint: undefined,
    });
    expect(fillToFillStylePatch(gradient)).toEqual({
      fill: "#111111",
      backgroundColor: "#111111",
      fillPaint: gradient,
    });
    expect(styleToFill({ fill: "#111111", fillPaint: gradient })).toEqual(gradient);
  });

  it("borda e texto seguem o mesmo contrato hex + paint", () => {
    expect(fillToStrokeStylePatch(gradient, { strokeWidth: 2 })).toMatchObject({
      stroke: "#111111",
      strokePaint: gradient,
      strokeWidth: 2,
    });
    expect(fillToColorStylePatch({ kind: "solid", color: "auto" })).toEqual({
      color: "auto",
      colorPaint: undefined,
    });
    expect(styleToStrokeFill({ stroke: "transparent" })).toEqual({ kind: "none" });
    expect(styleToColorFill({ color: "#0f172a" })).toEqual({ kind: "solid", color: "#0f172a" });
  });
});
