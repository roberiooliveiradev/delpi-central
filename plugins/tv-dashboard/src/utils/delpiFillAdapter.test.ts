import { describe, expect, it } from "vitest";

import { DECK_SHAPE_DEFAULTS } from "@delpi/plugin-ui/index";
import {
  createIconBlock,
  createShapeBlock,
  resolveComunicadoIconColor,
  resolveStyleFillCss,
  type ComunicadoIconBlock,
} from "@delpi/tv-dashboard-presentation";

import { applyComunicadoBlockStylePatch } from "./applyComunicadoBlockStylePatch";
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
import { sparsePropertyPatch } from "./selectionPropertyApply";

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

  it("Cor sólida sobre gradient: sparse + patch remove fillPaint", () => {
    const block = {
      ...createShapeBlock("rectangle"),
      style: { fill: "#111111", fillPaint: gradient },
    };
    const sparse = sparsePropertyPatch(fillToFillStylePatch({ kind: "solid", color: "#ef4444" }));
    const next = applyComunicadoBlockStylePatch(block, sparse);
    expect(styleToFill(next.style)).toEqual({ kind: "solid", color: "#ef4444" });
    expect(next.style?.fillPaint).toBeUndefined();
    expect(resolveStyleFillCss(next.style)).toBe("#ef4444");
    expect(resolveStyleFillCss(next.style)).not.toContain("linear-gradient");
  });

  it("borda e texto seguem o mesmo contrato hex + paint", () => {
    expect(fillToStrokeStylePatch(gradient, { strokeWidth: 2 })).toMatchObject({
      stroke: "#111111",
      strokePaint: gradient,
      strokeWidth: 2,
    });
    expect(fillToColorStylePatch({ kind: "solid", color: "auto" })).toEqual({
      color: "auto",
      colorPaint: { kind: "solid", color: "auto" },
    });
    expect(styleToStrokeFill({ stroke: "transparent" })).toEqual({ kind: "none" });
    expect(styleToColorFill({ color: "#0f172a" })).toEqual({ kind: "solid", color: "#0f172a" });
  });

  it("cor sólida explícita grava colorPaint tipado — branco não é sentinela de ausência", () => {
    for (const color of ["#ffffff", "#9ca3af", "#089bdb", "#111111"]) {
      expect(fillToColorStylePatch({ kind: "solid", color })).toEqual({
        color,
        colorPaint: { kind: "solid", color },
      });
    }
    expect(fillToColorStylePatch({ kind: "none" })).toEqual({
      color: "transparent",
      colorPaint: undefined,
    });
    expect(fillToColorStylePatch(gradient)).toEqual({
      color: "#111111",
      colorPaint: gradient,
    });
  });

  it("round-trip branco explícito: pick → patch → merge → serialização → resolve ícone", () => {
    const block = createIconBlock("Star");
    const patch = sparsePropertyPatch(
      fillToColorStylePatch({ kind: "solid", color: "#ffffff" }),
    );
    const merged = applyComunicadoBlockStylePatch(block, patch);
    expect(merged.style?.colorPaint).toEqual({ kind: "solid", color: "#ffffff" });
    // Simula persistência + read-back (JSON round-trip da nativeConfig).
    const rehydrated = JSON.parse(JSON.stringify(merged));
    expect(rehydrated.style.colorPaint).toEqual({ kind: "solid", color: "#ffffff" });
    expect(resolveComunicadoIconColor(rehydrated as ComunicadoIconBlock)).toBe("#ffffff");
    // Picker reflete a escolha explícita (não «sem cor»).
    expect(styleToColorFill(rehydrated.style)).toEqual({ kind: "solid", color: "#ffffff" });
  });

  it("legado sem colorPaint continua recuando ao accent — compatibilidade preservada", () => {
    const legacy = createIconBlock("Star");
    legacy.style = { color: "#ffffff" };
    expect(resolveComunicadoIconColor(legacy as ComunicadoIconBlock)).toBe(DECK_SHAPE_DEFAULTS.fill);
  });

  it("re-pick sólido sobre gradiente limpa o paint antigo e grava o sólido", () => {
    const block = createIconBlock("Star");
    block.style = { color: "#111111", colorPaint: gradient };
    const patch = sparsePropertyPatch(
      fillToColorStylePatch({ kind: "solid", color: "#ffffff" }),
    );
    const next = applyComunicadoBlockStylePatch(block, patch);
    expect(next.style?.colorPaint).toEqual({ kind: "solid", color: "#ffffff" });
    expect(resolveComunicadoIconColor(next as ComunicadoIconBlock)).toBe("#ffffff");
  });

  it("transparente explícito limpa paint e resolve transparente — não volta ao accent", () => {
    const block = createIconBlock("Star");
    block.style = { color: "#089bdb", colorPaint: { kind: "solid", color: "#089bdb" } };
    const patch = sparsePropertyPatch(fillToColorStylePatch({ kind: "none" }));
    const next = applyComunicadoBlockStylePatch(block, patch);
    expect(next.style?.colorPaint).toBeUndefined();
    expect(resolveComunicadoIconColor(next as ComunicadoIconBlock)).toBe("transparent");
  });

  it("backgroundToFill lê underlay quando há imagem de fundo", () => {
    expect(
      backgroundToFill({
        type: "image",
        assetId: "bg-1",
        underlay: { type: "color", value: "#003866" },
      }),
    ).toEqual({ kind: "solid", color: "#003866" });
  });
});
