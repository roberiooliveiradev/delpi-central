import { describe, expect, it } from "vitest";

import { createKpiViewBlock, createShapeBlock } from "@delpi/tv-dashboard-presentation";

import { applyComunicadoBlockStylePatch } from "./applyComunicadoBlockStylePatch";

describe("applyComunicadoBlockStylePatch", () => {
  it("remove boxShadow ao limpar (undefined / string vazia) em qualquer bloco", () => {
    const shape = {
      ...createShapeBlock("rectangle"),
      style: { zIndex: 2, boxShadow: "0 4px 14px rgba(0, 0, 0, 0.28)" },
    };
    expect(applyComunicadoBlockStylePatch(shape, { boxShadow: undefined }).style?.boxShadow).toBeUndefined();
    expect(applyComunicadoBlockStylePatch(shape, { boxShadow: "" }).style?.boxShadow).toBeUndefined();

    const kpi = {
      ...createKpiViewBlock(),
      style: { zIndex: 2, boxShadow: "0 8px 24px rgba(0, 0, 0, 0.35)" },
    };
    expect(applyComunicadoBlockStylePatch(kpi, { boxShadow: undefined }).style?.boxShadow).toBeUndefined();
  });

  it("mantém outras chaves ao limpar só a sombra", () => {
    const block = {
      ...createShapeBlock("rectangle"),
      style: { zIndex: 3, opacity: 0.8, boxShadow: "0 2px 10px rgba(0, 0, 0, 0.55)" },
    };
    const next = applyComunicadoBlockStylePatch(block, { boxShadow: undefined });
    expect(next.style?.boxShadow).toBeUndefined();
    expect(next.style?.zIndex).toBe(3);
    expect(next.style?.opacity).toBe(0.8);
  });
});
